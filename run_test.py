import socket
from struct import *
from core import tkutil

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('192.168.145.14', 12345))

ping_start = tkutil.get_current_millisecond_clamped()

sock.sendto(
    pack(
        '<ciic',
        '\x12',
        ping_start,
        10001,
        '\x06'
    ),
    ('192.168.145.14', 10000)
)

echo, len = sock.recvfrom(1024)
print 'rtt', tkutil.get_current_millisecond_clamped() - ping_start