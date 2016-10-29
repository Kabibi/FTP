#!/usr/bin/env python
# coding=utf-8

import socket
import os
import SocketServer


class MyFTPRequestHandler(SocketServer.StreamRequestHandler):
    '''ftp server, the default path at /var/ftp/, make sure that you already
    have the dir and have the access to it before you start the server'''

    def handle(self):
        # get mode and working path
        self.mode, self.path = self.auth()
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        os.chdir(self.path)
        self.run()

    def auth(self):
        '''
        验证用户名和密码是否正确
        :return:
        '''
        try:
            configFile = open('server_config.txt')
        except IOError, e:
            print "could find or open file:", e

        # allLines = configFile.readLines()
        allLines = configFile.readlines()


        while True:
            self.request.sendall("Username: ")
            self.name = self.request.recv(BUFFERSIZE).strip('\n')
            self.request.sendall("Password: ")
            self.passwd = self.request.recv(BUFFERSIZE).strip('\n')

            for line in allLines:
                formatted = [x for x in line.split() if x != '|']
                if formatted[0] == '1':
                    if self.name == formatted[1] and self.passwd == formatted[2]:
                        # return capability and working dir
                        return formatted[3], formatted[4]
            self.request.sendall("Username doesn't exist or password is incorrect. Please try again!\n")
            #########==========================================
            # self.type = 0 if self.name == 'ftp' else 1
            #########==========================================
            # break

    def getPrompt(self):
        return '\033[1m' + self.name + '@' + os.getcwd() + ': ' + '\033[0m'

    def getfile(self, filename):
        try:
            ##f_name = self.path + filename
            fd = file(filename, 'rb')
            # self.request.sendall('OK\n')
        except IndexError:
            self.request.sendall('Usage: get file_name\n')
        except IOError:
            self.request.sendall('file not exists or is a directory\n')
        else:
            while 1:
                filedata = fd.read(BUFFERSIZE)
                if not filedata: break
                self.request.sendall(filedata)
            print 'send %s to server %s\n' % (filename, self.client_address)

    def sendfile(self, filename):
        ##f_name = self.path + filename
        fd = file(filename, 'wb')
        while True:
            data2 = self.request.recv(BUFFERSIZE)
            if data2 == 'file_send_done':
                break
            fd.write(data2)
        fd.close()
        print 'receive %s' % filename
        response = '0K'
        self.request.sendall(response)

    def cdpath(self, pathname):
        if not os.path.isdir(pathname):
            self.request.sendall('%s not exist or is not a directory\n' % pathname)
        else:
            # don't need to print 'OK'
            # self.request.sendall('OK\n')
            os.chdir(pathname)

    def run(self):
        while True:
            # show current working path
            self.request.sendall(self.getPrompt())
            # help message
            response = '\033[31;1m' \
                       'ls\t\tshow the current directory\n' \
                       'get\t\tget the file from ftp server\n' \
                       'send\t\tsend the file to ftp server\n' \
                       'cd\t\tchange directory\n' \
                       '\033[0m'
            # 获取Client端命令
            data = self.request.recv(BUFFERSIZE).strip()
            # 输出Server端提示信息
            print 'receive from %s : %s' % (self.client_address, data)
            # help
            if data == '?' or data == 'help':
                self.request.sendall(response)
            # quit
            elif data == 'q' or data == 'quit':
                break
            # show the current directory
            elif data == 'ls' or data == 'll':
                currentDir = os.getcwd()
                for item in os.listdir(currentDir):
                    if os.path.isdir(item):
                        self.request.sendall(item + '/' + '\n')
                    else:
                        self.request.sendall(item + '\n')

            # change directory
            elif data.split()[0] == 'cd':
                self.cdpath(data.split()[1])
            # get the file from ftp server
            elif data.split()[0] == 'get':  # 需要完善
                self.getfile(data.split()[1])
            # send the file to ftp server
            elif data.split()[0] == 'send':
                self.sendfile(data.split()[1])
            else:
                response = 'invalid command, see help\n'
                self.request.sendall(response)

    def finish(self):
        return SocketServer.BaseRequestHandler.finish(self)


if __name__ == '__main__':
    HOST = '0.0.0.0'
    # PORT = 6670
    PORT = 6668
    BUFFERSIZE = 4096
    # authenticate, <user: password>
    auth_dic = {'liqin': '123456', 'aaron': '123456'}

    server = SocketServer.ThreadingTCPServer((HOST, PORT), MyFTPRequestHandler)
    server.serve_forever()
