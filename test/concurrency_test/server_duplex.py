import socket
import time


def server_send(sock_s, addr_c, pkg_num):
    sock_s.sendto(str(pkg_num), addr_c)


def server_run(sock_s):
    addr_c = None
    while True:
        data, addr = sock_s.recvfrom(1024)
        if data:
            sock_s.sendto(data, addr)

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 20000))
    server_run(sock)
