# FTP Server and Client Implemented by Epoll

## Introduction

* It is a simple FTP Server and Client. The server is implemented by 
epoll and use passive mode to transform data. The client is 
just a simple command-line TCP-based interactive program.

* On client, it supports common shell commands, such as ls, cd. Besides 
those commands, it also supports basic client commands such as login, get, 
put and bye.

* The server is implemented by epoll and administrator can configure usernames,
 passwords, capabilities and working directories.
 
* The project only supports Python 2.

## Getting started

Make sure you run server before client, or you will get error 
message like 'Connection refused'. Once you have run both server
and client, have fun with it.

### login

Before you login, you can use all command this program supports 
except 'get' and 'put'. That means you are denied to put or get file 
to and from server as a guest. Users' permissions are set in 'server_config.txt'.

|Permission|explanation                          |
|----------|-------------------------------------|
| r        | client can get file from server            | 
| w        | client can put file to server              |
|rw        | client can get and put file from/to server |

### ll or ls

By type 'll' or 'ls', you can list all file and directories
in current directory. Try it!

### cd

Change directory. All the same as the shell.

### get

You can download file from server by typing 'get filename'. But make sure 
the file you want is in your current directory and whether your have the 
'get' permission. 

If the file you get conflicts with your file. Then basename of file will 
be appended with '_get'. For example, you want to download 'a.txt' from server,
but it already exists in your current directory, then this file will be named 
to 'a_get.txt'.

### put

You can upload file to server by typing 'put filename'. Make
sure file you want to upload exists and you have the permission to 'put'.

Just like 'get', if filename conflicts, the file you upload will be named to 'a_put.txt'.

### bye

Say good bye to server.

### configure file

The configure file is 'server_config.txt'. Everything is easy to understand and
one thing worth explaining is the 'State'.

If the state is 1, the user is able to login. Otherwise the user is not permitted
to login. This column is especially useful when you don't want someone to login temporarily.

```
    State | Username | Password | Capabilities | Working Directory
    ---------------------------------------------------------------
    1     |  aaron   |   12345  |   w          |   /home/
    1     |  liqin   |   qqqqq  |   rw         |   /home/ftp
    1     |  Rachel  |   1996   |   r          |   /home/
    0     |  sky     |   abcd   |   rw         |   /tmp
```

