#!/usr/bin/env python

import socket
import time
import getpass

host = '127.0.0.1'
port = 8085
BUFFERSIZE = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

command = ''
while command != 'bye':
    print s.recv(BUFFERSIZE),
    command = raw_input()
    s.sendall(command)
s.close()
