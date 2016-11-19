# coding: utf-8
import socket, select
import os


class MyFTPServer():
    def __init__(self, host, port):
        self.serveraddress = (host, port)
        self.responses = {}
        self.requests = {}
        self.connections = {}
        self.capability = {}
        self.workdir = {}
        self.helpmessage = '\033[31;1m' \
                           'ls or ll       - show all file and directories in current working directory\n' \
                           'get filename   - get file from ftp server\n' \
                           'put filename   - send file to ftp server\n' \
                           'cd [directory] - change directory\n' \
                           'help or ?      - show help message\n' \
                           '\033[0m'
        # username for all clients
        self.names = {}
        # create server socket
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.bind(self.serveraddress)
        self.serversocket.listen(1)
        self.serversocket.setblocking(0)
        # create a epoll object
        self.epoll = select.epoll()
        self.epoll.register(self.serversocket.fileno(), select.EPOLLIN)

    def auth(self, clientsocket):
        """
        Authenticate the specific connection socket
        with the username and password inputted by the user
        :param clientsocket: socket used to connect the client and server
        :return: none
        """
        # Read the configuration file
        try:
            configFile = open('server_config.txt')
            allLines = configFile.readlines()
            while True:
                # input username
                self.connections[clientsocket.fileno()].send('Username:')
                username = clientsocket.recv(BUFFERSIZE).strip('\n')
                # input password
                self.connections[clientsocket.fileno()].send('Password:')
                password = clientsocket.recv(BUFFERSIZE).strip('\n')

                for line in allLines:
                    formatted = [x for x in line.split() if x != '|']
                    if formatted[0] == '1':
                        # formatted[1] is username, formatted[2] is password
                        # formatted[3] is capability, formatted[4] is working directory
                        if username == formatted[1] and password == formatted[2]:
                            # store the username
                            self.names[clientsocket.fileno()] = username
                            # store the capability
                            self.capability[clientsocket.fileno()] = formatted[3]
                            # store the working directory
                            self.workdir[clientsocket.fileno()] = formatted[4]
                            return
                self.connections[clientsocket.fileno()].send("Authenticate failed. Please try again!\n")
        except IOError:
            print "couldn't find or open file:"

    def getPrompt(self, clientsocket):
        return '\033[1m' + self.names[clientsocket.fileno()] + '@' + os.getcwd() + ':' + '\033[0m'

    def cdpath(self, pathname, fileno):
        if not os.path.isdir(pathname):
            self.responses[fileno] = pathname + ' not exist or is not a directory\n'
        else:
            os.chdir(pathname)

    def getfile(self, filename, fileno):
        try:
            if not os.path.exists(filename):
                self.responses[fileno] = 'Oops, file doesn\'t exist on server!\n'
                return
            fd = file(filename, 'rb')
        except IndexError:
            self.responses[fileno] = 'Useage: get filename\n'
        except IOError:
            self.responses[fileno] = 'file doesn\'t exists or is a directory\n'
        else:
            while 1:
                filedata = fd.read(BUFFERSIZE)
                if not filedata: break
                self.responses[fileno] += filedata
            fd.close()

    def putfile(self, filename, content, fileno):
        fd = file(filename + 'put', 'wb')
        fd.write(content)
        fd.close()

    def run(self):
        try:
            while True:
                events = self.epoll.poll(1)
                for fileno, event in events:
                    # 每次有一个新的client请求，就会创建新的套接字并注册
                    if fileno == self.serversocket.fileno():
                        connection, clientaddress = self.serversocket.accept()
                        self.connections[connection.fileno()] = connection
                        self.requests[connection.fileno()] = b''
                        # authenticate the username and password
                        self.auth(connection)
                        connection.send(self.getPrompt(connection))
                        # set unblocking
                        connection.setblocking(0)
                        # register read events on this socket
                        self.epoll.register(connection.fileno(), select.EPOLLIN)

                    elif event == select.EPOLLIN:
                        self.requests[fileno] = self.connections[fileno].recv(BUFFERSIZE).strip()
                        req = self.requests[fileno]
                        # enter 'bye'
                        if 'bye' in self.requests[fileno]:
                            self.epoll.modify(fileno, 0)
                            self.connections[fileno].shutdown(socket.SHUT_RDWR)
                        # enter 'ls' or 'll'
                        elif 'll' == req or 'ls' == req:
                            currentDir = os.getcwd()
                            self.responses[fileno] = ''
                            for item in os.listdir(currentDir):
                                if os.path.isdir(item):
                                    self.responses[fileno] += item + '/' + '\n'
                                else:
                                    self.responses[fileno] += item + '\n'
                        elif '?' == req or 'help' == req or '' == req:
                            self.responses[fileno] = self.helpmessage
                        # change directory
                        elif 'cd' == req.split()[0]:
                            # if input 'cd', then change to working dir
                            if len(req.split()) == 1:
                                self.cdpath(self.workdir[fileno], fileno)
                            else:
                                self.cdpath(req.split()[1], fileno)
                        # get file from ftp server
                        elif req.split()[0] == 'get':
                            if (len(req.split())) == 1:
                                self.responses[fileno] = 'please enter the filename\n!'
                            else:
                                self.getfile(req.split()[1], fileno)
                        # send file to ftp server
                        elif req.split()[0] == 'put':
                            content_list = req.split('\n')[1:]  # remove 'put XXX'
                            content = ''
                            # compose content from content_list
                            for i in range(len(content_list)):
                                content = content + content_list[i] + '\n'
                            self.putfile(req.split()[1], content, fileno)
                            self.responses[fileno] = 'Done!\n'
                        elif req == 'Undone':
                            self.responses[fileno] = 'Undone!\n'
                        elif req == 'Done':
                            self.responses[fileno] = 'Done!\n'

                        else:
                            self.responses[fileno] = 'Command not found\n'

                        # 输入回车，切换监听read事件改为write事件
                        self.epoll.modify(fileno, select.EPOLLOUT)
                        print "Receive from %s:%d %s" % (
                            clientaddress[0], clientaddress[1], self.requests[fileno].split('\n')[0])

                    elif event == select.EPOLLOUT:
                        self.connections[fileno].send(
                            self.responses[fileno] + self.getPrompt((self.connections[fileno])))
                        # clear responses
                        self.responses[fileno] = ''
                        self.epoll.modify(fileno, select.EPOLLIN)
                    else:
                        self.epoll.unregister(fileno)
                        self.connections[fileno].close()
                        del self.connections[fileno]
        except Exception:
            print Exception.message
        finally:
            self.run()


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8085
    BUFFERSIZE = 2 ** 20
    server = MyFTPServer(host, port)
    server.run()
