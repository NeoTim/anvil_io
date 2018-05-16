import socket
import sys

# config
CONFIG = {
    'SERVER_IP': '192.168.137.1',
    'PORT': 10000
}


def main():
    # server socket
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_ip = CONFIG['SERVER_IP']
        if len(sys.argv) > 1:
            server_ip = sys.argv[1]
        tcpsock.bind((server_ip, CONFIG['PORT']))
        tcpsock.listen(1024)
        print 'server listening at: ', tcpsock.getsockname()
        while True:
            (sock_client, addr_clinet) = tcpsock.accept()
            print 'client socket from ', addr_clinet
            print 'respond to client'
            sock_client.send('Hi Tinkr!')
    finally:
        print 'server closed'
        tcpsock.close()


if __name__ == '__main__':
    main()
