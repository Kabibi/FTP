# coding: utf-8

import os
import socket

host = '127.0.0.1'
port = 8085
BUFFERSIZE = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
error1 = 'Error 1: file doesn\'t exist\n'
error2 = 'Error 2: Permission denied\n'

command = ' '
while command != 'bye':
    received = s.recv(BUFFERSIZE)
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
                received = s.recv(BUFFERSIZE)
            file.write(received.split('\r\n\r')[0])
            received = received.split('\r\n\r')[1]
            file.close()
    # first print, then input
    print received,
    command = raw_input()
    if command == '':
        command = 'help'

    if len(command.split()) == 2 and command.split()[0] == 'put':
        filename = command.split()[1]
        if not os.path.exists(filename):
            # print filename + ' not exists!'
            command = error1
        else:
            file = open(filename, 'r')
            content = file.read()
            command = content
    s.sendall(command)
s.close()
