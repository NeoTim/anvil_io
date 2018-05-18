import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect the socket to the port on the server given by the caller
    server_ip = '192.168.137.1'
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    server_address = (server_ip, 10000)
    print 'connecting to %s port %s' % server_address
    sock.connect(server_address)

    while True:
        message = raw_input('message to send: ')
        print 'sending "%s"' % message
        sock.sendall(message)
        data = sock.recv(255)
        print 'received "%s"' % data

finally:
    sock.close()
