import socket
import sys
import threading

# config
CONFIG = {
    'SERVER_IP': '0.0.0.0',
    'PORT': 10000
}


def main():
    # server socket
    udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server_ip = CONFIG['SERVER_IP']
        if len(sys.argv) > 1:
            server_ip = sys.argv[1]
        udpsocket.bind((server_ip, CONFIG['PORT']))
        # udpsocket.listen(1024)
        print 'server listening at: ', udpsocket.getsockname()
        if True:
            # data, addr = udpsocket.recvfrom(1024)
            # print 'client socket from ', addr
            # print 'respond to client'
            # sock_client.settimeout(2)
            time.sleep(0.02)
            while True:
                try:
                    data, addr = udpsocket.recvfrom(1024)
                    print 'received from client: ' + data
                except socket.timeout:
                    print 'time out'
                except Exception, e:
                    print e
    finally:
        print 'server closed'
        udpsocket.close()


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
    sock.bind(('0.0.0.0', 10000))
    import time
    addr = None
    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if data:
                    print 'message \'', data, '\'from', addr
                    sock.sendto('Hi Tinkr!', addr)
            except Exception, e:
                print e
    finally:
        print 'socket closed'
        sock.close()
