"""
login bug
"""
import os
import select
import socket
import sys


class MyFTPServer():
    def __init__(self, host, port):
        self.serveraddress = (host, port)
        self.responses = {}
        self.requests = {}
        self.connections = {}
        self.capabilities = {}
        self.workdir = {}
        self.helpmessage = '\033[31;1m' \
                           'ls or ll       - show all file and directories in current working directory\n' \
                           'get filename   - get file from ftp server\n' \
                           'put filename   - send file to ftp server\n' \
                           'cd [directory] - change directory\n' \
                           'help or ?      - show help message\n' \
                           '\033[0m'
        # Usernames and password entered by clients
        self.usernames = {}
        self.passwords = {}
        # mode 0: without username nor password
        # mode 1: entered username but not enter password
        # mode 2: both have entered and authenticate successfully
        self.authenticated = {}
        self.state = 0
        self.lastRequests = {}
        self.error1 = 'Error 1: file doesn\'t exist\n'
        self.error2 = 'Error 2: Permission denied\n'
        # create server socket
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set option
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.serversocket.bind(self.serveraddress)
        self.serversocket.listen(1)
        self.serversocket.setblocking(0)
        # create a epoll object
        self.epoll = select.epoll()
        # register read interests
        self.epoll.register(self.serversocket.fileno(), select.EPOLLIN)

    def auth(self, fileno, username, password):
        """
        authenticate client with the username and password provided
        :param fileno:
        :param username:
        :param password:
        :return: boolean
        """
        # Read the configuration file
        try:
            configFile = open('server_config.txt')
            allLines = configFile.readlines()
            for line in allLines:
                formatted = [x for x in line.split() if x != '|']
                if formatted[0] == '1':
                    # formatted[1] is username, formatted[2] is password
                    # formatted[3] is capabilities, formatted[4] is working directory
                    if username == formatted[1] and password == formatted[2]:
                        self.usernames[fileno] = username
                        self.capabilities[fileno] = formatted[3]
                        self.workdir[fileno] = formatted[4]
                        return True
            return False
        except Exception:
            print Exception.message

    def getPrompt(self, fileno):
        """
        print Prompt information to client console
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

    def putfile(self, filename, content, fileno):
        """
        upload file to the server with putfile method
        :param filename: filename
        :param content: the content of the file
        :param fileno: the integer file description of the socket
        :return: none
        """
        if os.path.exists(filename):

            basename, extension = os.path.splitext(filename)
            fd = file(basename + '_put' + extension, 'wb')
        else:
            fd = file(filename, 'wb')
        fd.write(content)
        fd.close()

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
        self.authenticated[fileno] = 0
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
        'r' -- have get permission
        'w' -- have put permission
        'rw' - have both get and put permission
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
            pass
        return False

    def responseAfterPut(self, fileno, req):
        """
        client send 'put XXX' to server, after 'put XXX' command,
        server is still interest in read events. The server then waits for
        file's content or error message.
        This method used to construct response according to string sent
        by client.
        :param fileno:
        :param req: request
        :return: none
        """
        # Permission denied
        if not self.verify(fileno, 'put'):
            self.responses[fileno] = self.error2 + '\n' + self.getPrompt(fileno)
            return
        if req not in (self.error1):
            # write to file
            __console__ = sys.stdout
            file = open(self.lastRequests[fileno].split()[1] + '_', 'w')
            sys.stdout = file
            print req
            sys.stdout = __console__
        else:
            # req is error1 or error2
            self.responses[fileno] = req + '\n' + self.getPrompt(fileno)

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
                        self.connections[connection.fileno()] = connection
                        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        self.serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        self.setInfo(connection.fileno())
                        self.connections[connection.fileno()].sendall(
                            'Welcome to my FTP Server!\n' + self.getPrompt(connection.fileno()))
                        # set unblocking
                        connection.setblocking(0)
                        # register read events on this socket
                        self.epoll.register(connection.fileno(), select.EPOLLIN)

                    # Read event occurs
                    elif event == select.EPOLLIN:
                        # get request
                        self.requests[fileno] = self.connections[fileno].recv(BUFFERSIZE).strip()
                        req = self.requests[fileno]

                        if self.lastRequests[fileno].split()[0] == 'put':
                            # construct response
                            self.responseAfterPut(fileno, req)
                            # modify interest
                            self.epoll.modify(fileno, select.EPOLLOUT)
                            continue
                        # if last request is login, then req is username
                        if self.lastRequests[fileno] == 'login':
                            self.usernames[fileno] = req
                            self.responses[fileno] = 'Password:'
                            self.lastRequests[fileno] = 'username'
                            self.epoll.modify(fileno, select.EPOLLOUT)
                            continue
                        if self.lastRequests[fileno] == 'username':
                            self.passwords[fileno] = req
                            if self.auth(fileno, self.usernames[fileno], self.passwords[fileno]):
                                self.authenticated[fileno] = 1
                                self.responses[fileno] = self.getPrompt(fileno)
                            else:
                                self.responses[fileno] = 'username or password is incorrect!' + '\n' + self.getPrompt(
                                    fileno)
                            self.lastRequests[fileno] = 'none'
                            self.epoll.modify(fileno, select.EPOLLOUT)
                            continue

                        # login
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
                            self.responses[fileno] = self.helpmessage + self.getPrompt(fileno)
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
                            # prepare to receive content or error message
                            self.lastRequests[fileno] = req
                            # modify interest (still focus on read events)
                            continue
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
                            '''
                            step:
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
                                        fd = file(filename, 'rb')
                                        while True:
                                            content = fd.read(BUFFERSIZE)
                                            if not content:
                                                self.connections[fileno].send('\r\n\rDone!\n' + self.getPrompt(fileno))
                                                break
                                            else:
                                                self.connections[fileno].send(content)
                                    else:
                                        # file doesn't exist
                                        self.connections[fileno].send(self.error1 + self.getPrompt(fileno))
                                # permission denied
                                else:
                                    self.connections[fileno].send(self.error2 + self.getPrompt(fileno))
                            # file doesn't exist
                            else:
                                self.connections[fileno].sendall(self.error1 + self.getPrompt(fileno))
                            self.epoll.modify(fileno, select.EPOLLIN)
                        else:
                            self.epoll.modify(fileno, select.EPOLLIN)
                            # send response
                            self.connections[fileno].sendall(self.responses[fileno])
                    else:
                        self.release(fileno)

        except Exception:
            print Exception.message
        finally:
            self.run()


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8085
    # port = 8089
    BUFFERSIZE = 4096
    server = MyFTPServer(host, port)
    server.run()
