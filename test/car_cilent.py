# -*- coding: utf-8 -*-
import socket
import sys


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = '192.168.147.127'
    server_port = 10000
    sock.connect((server_ip, server_port))
    while True:
        data = sock.recv(1024)
        if data:
            print 'received from server: ' + data

if __name__ == '__main__':
    main()
