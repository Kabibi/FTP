"""
login bug
"""
import os
import select
import socket
import time


class MyFTPServer():
    def __init__(self, host, port):
        self.serveraddress = (host, port)
        self.responses = {}
        self.requests = {}
        self.connections = {}
        self.capabilities = {}
        self.workdir = {}
        self.usernames = {}
        self.passwords = {}
        self.authenticated = {}
        self.lastRequests = {}
        self.configLines = self.getConfigLines('server_config.txt')
        self.error1 = 'Error 1: file doesn\'t exist\n'
        self.error2 = 'Error 2: Permission denied\n'
        self.help = '\033[31;1m' \
                    'ls or ll       - show all file and directories in current directory\n' \
                    'get filename   - get file from ftp server\n' \
                    'put filename   - send file to ftp server\n' \
                    'cd [directory] - change directory\n' \
                    'help or ?      - show help message\n' \
                    'bye            - exit\n' \
                    '\033[0m'
        # create server socket
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set option
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the server socket to the port specified of all available IPv4 addresses on this machine
        self.serversocket.bind(self.serveraddress)
        # start accepting incoming connections from clients
        self.serversocket.listen(1)
        self.serversocket.setblocking(0)
        # create a epoll object
        self.epoll = select.epoll()
        # register interest in read events on serversocket
        self.epoll.register(self.serversocket.fileno(), select.EPOLLIN)

    def getConfigLines(self, filename):
        """
        get all lines in configure file
        :param filename:
        :return: all lines
        """
        try:
            configFile = open(filename, 'r')
            allLines = configFile.readlines()
            configFile.close()
            return allLines
        except IOError as msg:
            print msg

    def auth(self, fileno, username, password):
        """
        authenticate client with the username and password provided
        :return: boolean
        """
        for line in self.configLines:
            formatted = [x for x in line.split() if x != '|']
            if formatted[0] == '1':
                # formatted[1] -> username, formatted[2] -> password
                # formatted[3] -> capabilities, formatted[4] -> working directory
                if username == formatted[1] and password == formatted[2]:
                    self.usernames[fileno] = username
                    self.capabilities[fileno] = formatted[3]
                    self.workdir[fileno] = formatted[4]
                    return True
        return False

    def getPrompt(self, fileno):
        """
        print prompt information to client console
        :param fileno: the integer file description of the socket
        :return: string
        """
        if self.authenticated[fileno]:
            return '\033[1m' + self.usernames[fileno] + '@' + os.getcwd() + ':' + '\033[0m'
        else:
            return '\033[1m' + 'guest' + '@' + os.getcwd() + ':' + '\033[0m'

    def cdpath(self, pathname, fileno):
        """
        Change to specific directory
        :param pathname: must be a directory
        :param fileno: the integer file description of the socket
        :return: none
        """

        if not os.path.isdir(pathname):
            self.responses[fileno] = pathname + ' not exist or is not a directory\n'
        else:
            os.chdir(pathname)

    def release(self, fileno):
        """
        release resource
        :param fileno:
        :return: none
        """
        self.epoll.unregister(fileno)
        self.connections[fileno].close()
        del self.authenticated[fileno]
        del self.capabilities[fileno]
        del self.connections[fileno]
        del self.workdir[fileno]
        del self.usernames[fileno]
        del self.passwords[fileno]
        del self.responses[fileno]
        del self.requests[fileno]

    def setInfo(self, fileno):
        """
        set initialized information for a new created client socket
        :param fileno:
        :return:
        """
        self.authenticated[fileno] = False
        self.capabilities[fileno] = ''
        self.workdir[fileno] = '/tmp'
        self.usernames[fileno] = 'guest'
        self.passwords[fileno] = ''
        self.responses[fileno] = ''
        self.requests[fileno] = ''
        self.lastRequests[fileno] = 'none'

    def verify(self, fileno, cmd):
        """
        varify capabilities of username
        'r' -- can get
        'w' -- can put
        'rw' - can get as well as put
        :param fileno: the integer file description of the socket
        :param cmd: 'put' or 'get'
        :return: bool
        """
        if cmd == 'get':
            if 'r' in self.capabilities[fileno]:
                return True
        elif cmd == 'put':
            if 'w' in self.capabilities[fileno]:
                return True
        else:
            return False

    def handle_last_req(self, fileno, last_req, req):
        """
        handle last request
        :param fileno:
        :param last_req:
        :param req:
        :return: return True if need 'continue'
        """
        if last_req.split()[0] == 'put':
            time.sleep(0.1)
            # check if error1 happens
            # req = self.connections[fileno].recv(buffersize)
            if req == self.error1:
                self.responses[fileno] = self.error1 + self.getPrompt(fileno)
            else:
                filename = self.lastRequests[fileno].split()[1]
                basename, extension = os.path.splitext(filename)
                file = open(basename + '_put' + extension, 'a')
                content = req
                while '\r\n\r' not in content:
                    file.write(content)
                    content = self.connections[fileno].recv(buffersize)
                file.write(content.split('\r\n\r')[0])
                file.close()
                self.responses[fileno] = 'Done!\n' + self.getPrompt(fileno)
            self.epoll.modify(fileno, select.EPOLLOUT)
            self.lastRequests[fileno] = 'none'
            return True
        elif last_req == 'login':
            self.usernames[fileno] = req.strip()
            self.responses[fileno] = 'Password:'
            self.lastRequests[fileno] = 'username'
            self.epoll.modify(fileno, select.EPOLLOUT)
            return True
        elif last_req == 'username':
            self.passwords[fileno] = req.strip()
            if self.auth(fileno, self.usernames[fileno], self.passwords[fileno]):
                self.authenticated[fileno] = True
                self.responses[fileno] = self.getPrompt(fileno)
            else:
                self.responses[fileno] = 'username or password is incorrect!' + '\n' + self.getPrompt(
                    fileno)
            self.lastRequests[fileno] = 'none'
            self.epoll.modify(fileno, select.EPOLLOUT)
            return True
        elif last_req == 'get':
            '''
            steps:
                1. verify the length of command. If illegal, print error1
                2. verify the capabilities of the client. If denied, print error2
                3. verify the existence of the specific file. If not exist, print error1
            '''
            # verify the length of command
            if len(self.requests[fileno].split()) == 2:
                # verify capabilities of the client
                if self.verify(fileno, 'get'):
                    filename = self.requests[fileno].split()[1]
                    # verify the existence of the file
                    if os.path.exists(filename):
                        fd = open(filename, 'rb')
                        while True:
                            content = fd.read(buffersize)
                            if not content:
                                self.connections[fileno].sendall(
                                    '\r\n\rDone!\n' + self.getPrompt(fileno))
                                break
                            else:
                                self.connections[fileno].sendall(content)
                    else:
                        # file doesn't exist
                        self.connections[fileno].sendall(self.error1 + self.getPrompt(fileno))
                # permission denied
                else:
                    self.connections[fileno].sendall(self.error2 + self.getPrompt(fileno))
            # file doesn't exist
            else:
                self.connections[fileno].sendall(self.error1 + self.getPrompt(fileno))
            self.epoll.modify(fileno, select.EPOLLIN)
            return True
        else:
            return False

    def run(self):
        """
        endless running of server
        :return: none
        """
        try:
            while True:
                events = self.epoll.poll(1)
                for fileno, event in events:
                    # create new socket and monitor events on this socket
                    if fileno == self.serversocket.fileno():
                        connection, clientaddress = self.serversocket.accept()
                        # save connection to dictionary
                        self.connections[connection.fileno()] = connection
                        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        # set basic information for this socket
                        self.setInfo(connection.fileno())
                        # set command prompt
                        self.connections[connection.fileno()].sendall(self.getPrompt(connection.fileno()))
                        # set unblocking
                        connection.setblocking(0)
                        # register read events on this socket
                        self.epoll.register(connection.fileno(), select.EPOLLIN)

                    # Read event occurs
                    elif event == select.EPOLLIN:
                        # get request
                        self.requests[fileno] = self.connections[fileno].recv(buffersize)
                        req = self.requests[fileno]

                        # handle last request ('put' and 'login' commands rely on last request to decide what to do next)
                        if self.handle_last_req(fileno, self.lastRequests[fileno], req):
                            continue

                        req = req.strip()
                        if 'bye' in self.requests[fileno]:
                            # modify interest
                            self.epoll.modify(fileno, 0)
                            self.connections[fileno].shutdown(socket.SHUT_RDWR)
                        elif 'll' == req or 'ls' == req:
                            # construct response
                            currentDir = os.getcwd()
                            self.responses[fileno] = ''
                            for item in os.listdir(currentDir):
                                if os.path.isdir(item):
                                    self.responses[fileno] += item + '/' + '\n'
                                else:
                                    self.responses[fileno] += item + '\n'
                            self.responses[fileno] += self.getPrompt(fileno)
                            # modify interest
                            self.epoll.modify(fileno, select.EPOLLOUT)
                        elif '?' == req or 'help' == req or '' == req:
                            # construct response
                            self.responses[fileno] = self.help + self.getPrompt(fileno)
                            # modify interest
                            self.epoll.modify(fileno, select.EPOLLOUT)
                        elif 'cd' == req.split()[0]:
                            # construct response
                            if len(req.split()) == 1:  # change to working dir
                                self.cdpath(self.workdir[fileno], fileno)
                            else:
                                self.cdpath(req.split()[1], fileno)
                            self.responses[fileno] = self.getPrompt(fileno)
                            # modify interest
                            self.epoll.modify(fileno, select.EPOLLOUT)
                        elif 'get' == req.split()[0]:
                            # only modify interest
                            self.epoll.modify(fileno, select.EPOLLOUT)
                        elif 'put' == req.split()[0]:
                            # verify capabilities
                            if self.verify(fileno, 'put'):
                                self.responses[fileno] = 'Permission admitted'
                                # 'put' command relies on what last request is
                                self.lastRequests[fileno] = req
                            else:
                                # response: permission denied
                                self.responses[fileno] = self.error2 + self.getPrompt(fileno)
                            self.epoll.modify(fileno, select.EPOLLOUT)
                        elif 'login' == req:
                            # construct response
                            self.responses[fileno] = 'Username:'
                            self.lastRequests[fileno] = 'login'
                            # modify interest
                            self.epoll.modify(fileno, select.EPOLLOUT)
                        else:
                            # construct response
                            self.responses[fileno] = 'Command not found\n' + self.getPrompt(fileno)
                            # modify interest
                            self.epoll.modify(fileno, select.EPOLLOUT)
                        print "Receive from %s:%d %s" % (
                            clientaddress[0], clientaddress[1], self.requests[fileno].split('\n')[0])

                    # Write event occurs
                    elif event == select.EPOLLOUT:
                        if 'get' == self.requests[fileno].split()[0]:
                            # verify capabilities, length of command and other things for file sending
                            self.handle_last_req(fileno, 'get', self.requests[fileno].split())
                        else:
                            # send response
                            self.connections[fileno].sendall(self.responses[fileno])
                            self.epoll.modify(fileno, select.EPOLLIN)

                    # Other event occurs, such as disconnection
                    else:
                        # release resources held by this client
                        self.release(fileno)

        except socket.error as msg:
            print msg
        except IOError as msg:
            print msg
        finally:
            self.run()


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8085
    buffersize = 4096
    server = MyFTPServer(host, port)
    server.run()
