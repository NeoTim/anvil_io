import socket
import sys

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Connect the socket to the port on the server given by the caller
    server_ip = '10.123.165.53'
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    server_address = (server_ip, 10000)

    while True:
        message = raw_input('message to send: ')
        print 'sending "%s"' % message
        sock.sendto(message, server_address)
        data, addr = sock.recvfrom(1024)
        print data, 'from', addr

finally:
    sock.close()
