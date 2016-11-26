# coding: utf-8

import os
import socket


class FTPClient():
    def __init__(self, host, port):
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.error1 = 'Error 1: file doesn\'t exist\n'
        self.error2 = 'Error 2: Permission denied\n'
        self.clientsocket.connect((host, port))

    def get_rcvContent(self, received, command):
        """
        if not permission denied, then write what server sent to file
        """
        if self.error1 not in received and self.error2 not in received:
            filename = command.split()[1]
            basename, extension = os.path.splitext(command.split()[1])
            if os.path.exists(filename):
                file = open(basename + '_get' + extension, 'a')
            else:
                file = open(filename, 'a')
            while '\r\n\r' not in received:
                file.write(received)
                received = self.clientsocket.recv(buffersize)
            file.write(received.split('\r\n\r')[0])
            recv = received.split('\r\n\r')[1]
            file.close()
            return recv
        else:
            return received

    def put_mkDecision(self, command):
        """
        if client want to put file to server,then make decision on
        what to send (file doesn't exist or content of the file)
        """
        permission = self.clientsocket.recv(buffersize)
        if permission == 'Permission admitted':
            # send content of the file
            filename = command.split()[1]
            # verify existence of the file
            if not os.path.exists(filename):
                self.clientsocket.send(self.error1)
            else:
                file = open(filename, 'r')
                while True:
                    content = file.read(buffersize)
                    if not content:
                        self.clientsocket.send('\r\n\r')
                        break
                    else:
                        self.clientsocket.send(content)
                file.close()
        else:
            print permission,
            command = raw_input()
            self.clientsocket.send(command)

    def handledCmd(self, command):
        # handle command to another form for convenience of handling
        if command == '':
            return 'help'
        # if entered 'put' without filename, then change it to 'put \\'
        elif len(command.split()) == 1 and command.split()[0] == 'put':
            return 'put \\'
        else:
            return command

    def start(self):
        command = ' '
        while command != 'bye':
            # Step 1. receive from server
            received = self.clientsocket.recv(buffersize)
            # because received string maybe the content of the file,
            # so if clause must be ahead of print statement
            if len(command.split()) == 2 and command.split()[0] == 'get':
                received = self.get_rcvContent(received, command)
            print received,

            # Step 2. input command
            command = raw_input()
            # handle command to another form for convenience of handling
            command = self.handledCmd(command)

            # Step 3. send command to server
            self.clientsocket.send(command)
            # if client want to put file to server,
            # then make decision on what to send (file doesn't exist or content of the file)
            if len(command.split()) == 2 and command.split()[0] == 'put':
                self.put_mkDecision(command)
        self.clientsocket.close()


if __name__ == '__main__':
    host = '127.0.0.1'
    port = 8085
    buffersize = 4096
    client = FTPClient(host, port)
    client.start()
