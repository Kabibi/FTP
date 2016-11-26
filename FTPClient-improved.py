# coding: utf-8

import os
import socket
host = '127.0.0.1'
port = 8085
buffersize = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
error1 = 'Error 1: file doesn\'t exist\n'
error2 = 'Error 2: Permission denied\n'
s.connect((host, port))

command = ' '
while command != 'bye':
    received = s.recv(buffersize)
    # because received string maybe the content of the file,
    # so if clause must be ahead of print statement
    if len(command.split()) == 2 and command.split()[0] == 'get':
        if error1 not in received and error2 not in received:
            filename = command.split()[1]
            basename, extension = os.path.splitext(command.split()[1])
            if os.path.exists(filename):
                file = open(basename + '_get' + extension, 'a')
            else:
                file = open(filename, 'a')
            while '\r\n\r' not in received:
                file.write(received)
                received = s.recv(buffersize)
            file.write(received.split('\r\n\r')[0])
            received = received.split('\r\n\r')[1]
            file.close()
    # first print, then input
    print received,
    command = raw_input()
    if command == '':
        command = 'help'
    elif len(command.split()) == 1 and command.split()[0] == 'put':
        command = 'put \\'
    s.send(command)

    if len(command.split()) == 2 and command.split()[0] == 'put':
        permission = s.recv(buffersize)
        if permission == 'Permission admitted':
            # send content of the file
            filename = command.split()[1]
            # verify existence of the file
            if not os.path.exists(filename):
                s.send(error1)
            else:
                file = open(filename, 'r')
                while True:
                    content = file.read(buffersize)
                    if not content:
                        s.send('\r\n\r')
                        break
                    else:
                        s.send(content)
                # 这里加close()会出现: [Errno 9] Bad file descriptor
                # s.close()
                file.close()
        else:
            print permission,
            command = raw_input()
            s.send(command)
s.close()
