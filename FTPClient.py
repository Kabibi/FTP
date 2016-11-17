#!/usr/bin/env python

import socket

host = '127.0.0.1'
port = 8085
BUFFERSIZE = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

command = ''
while command != 'bye':
    # get file from server, but if the file size is so long, client may not get the full file.
    if len(command.split()) == 2 and command.split()[0] == 'get':
        content = s.recv(BUFFERSIZE)
        file = open(command.split()[1] + '_', 'a')
        file.write(content)
        print 'Done!'
        s.sendall('Done')
        command = ''
        continue
    print s.recv(BUFFERSIZE),
    command = raw_input()
    s.sendall(command)
s.close()
