import socket
import sys
import threading

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
            # sock_client.settimeout(2)
            while True:
                try:
                    data = sock_client.recv(1024)
                    print 'received from client: ' + data
                    sock_client.sendall(data)
                except socket.timeout:
                    print 'time out'
                else:
                    sock_client.close()
    finally:
        print 'server closed'
        tcpsock.close()


class TestThread:
    def __init__(self, aa):
        self.test_a = aa

    def test_f(self):
        print 'test_a = ', self.test_a

if __name__ == '__main__':
    # t1 = TestThread(4)
    # t2 = TestThread(77)
    # threading.Thread(target=t1.test_f).start()
    # threading.Thread(target=t2.test_f).start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('192.168.145.205', 10000))
    import time
    addr = None
    while True:
        if not addr:
            try:
                data, addr = sock.recvfrom(1024)
                print addr
            except:
                pass
        if addr:
            time.sleep(1)
            d = sock.sendto('hihi', addr)
            print d
