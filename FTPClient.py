# coding: utf-8

import socket
import os

host = '127.0.0.1'
port = 8085
BUFFERSIZE = 2 ** 20
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

command = ' '
while command != 'bye':
    received = s.recv(BUFFERSIZE)
    # because received string maybe the content of the file,
    # so if clause must be ahead of print statement
    if len(command.split()) == 2 and command.split()[0] == 'get':
        if 'Oops, file doesn\'t exist on server!\n' not in received:
            filename = command.split()[1]
            basename, extension = os.path.splitext(command.split()[1])
            # if exist the file with the same filename
            if os.path.exists(filename):
                file = open(basename + '_1' + extension, 'a')
            else:
                file = open(filename, 'a')
            file.write(received)
            file.close()
            command = 'Done'
            s.sendall(command)
            continue
    # first print, then input
    print received,
    command = raw_input()
    if command == '':
        command = 'help'

    if len(command.split()) == 2 and command.split()[0] == 'put':
        filename = command.split()[1]
        if not os.path.exists(filename):
            print filename + ' not exists!'
            command = 'Undone'
        else:
            file = open(filename, 'r')
            content = file.read()
            # command looks like 'put filename\ncontent'
            command = command + '\n' + content

    s.sendall(command)
s.close()
