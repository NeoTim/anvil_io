import socket
from struct import *
import time


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 10000))
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            if data:
                cid = unpack('<i', data[5:9])[0]
                data_sent = pack(
                    '<ciic',
                    '\x12',
                    int(time.time()),
                    cid,
                    '\x08'
                )
                d_len = sock.sendto(data_sent, addr)
                print d_len, 'bytes sent'
    finally:
        print 'socket close'
        sock.close()
