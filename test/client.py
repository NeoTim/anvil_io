import socket
import sys
import time

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 12345))


try:
    # Connect the socket to the port on the server given by the caller
    server_ip = '192.168.145.128'
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    server_address = (server_ip, 10000)

    print 'server addr', server_address

    send_count = 0

    while True:
        # message = raw_input('message to send: ')

        if send_count > 150000:
            break

        """
            Very tricky part:
            
            on windows, if firstly send a UDP package to server and then recv through the same UDP socket (and the server is down), 
            the system will raise socket error 10045 => connection closed by remote host
            if skip the first sending, the error won't raise
            
            on linux, everything is just fine
        """

        message = '1234567890qwertyuiopasdfghjklzxcvbnm'
        # print 'sending "%s"' % message
        dlen = sock.sendto(message, server_address)
        print dlen, 'sent'
        time.sleep(1)
        data, addr = sock.recvfrom(2048)
        print data, 'from', addr

finally:
    print 'client closed'
    sock.close()
