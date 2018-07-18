import socket
from multiprocessing import Process
from threading import Thread
import time
from struct import *

SERVER_IP = '192.168.145.64'
SERVER_GATE_PORT = 10000

TOTAL_LAG = 0


def get_current_millisecond_clamped():
    cur_stamp = time.time()
    cur_ms = int(cur_stamp * 1000) % 604800000
    return cur_ms


class ClientState:
    def __init__(self):
        self.pos = [1, 1, 1]


def socket_recv_data(sock):
    try:
        data, addr = sock.recvfrom(1024)
        if data:
            return data, addr
        return None, None
    except Exception, e:
        return None, None


def socket_send_data(sock, data, addr):
    try:
        d_len = sock.sendto(data, addr)
        # print d_len, ' sent'
        return d_len
    except Exception, e:
        return 0


class ClientProcess(Process):

    SEND_RATE = 20

    def __init__(self, cid):
        Process.__init__(self)
        self.cid = cid
        self.com_addr = [SERVER_IP, 0]
        self.time_to_send = 5  # in seconds
        self.time_to_live = 10
        self.start_time = 0
        self.last_send_time = time.time()

    def run(self):
        print self.name, 'starts'
        # record start time
        self.start_time = time.time()
        package_count = 0
        lag_total = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind(('0.0.0.0', 3000 + self.cid))
        try:
            login_requested = False
            while True:

                # times up
                if time.time() - self.start_time > self.time_to_live:
                    # print 'client times up.'
                    break

                # recv
                data, addr = socket_recv_data(sock)
                if data:
                    lag_total += get_current_millisecond_clamped() - unpack('<i', data[1:5])[0]
                    package_count += 1

                    op_code = unpack('<c', data[0])[0]

                    if op_code == '\x00':
                        # logged in
                        com_port = unpack('<i', data[5:9])[0]
                        self.com_addr[1] = com_port
                        # print 'new port', com_port

                    elif op_code == '\x01':
                        # state update
                        # print 'get new state'
                        pass

                # send
                if time.time() - self.last_send_time > 1.0 / self.SEND_RATE:
                    # if time.time() - self.start_time > self.time_to_send:
                    #     continue
                    self.last_send_time = time.time()
                    target_addr = self.com_addr
                    if self.com_addr[1] == 0:
                        # not logged in
                        target_addr = (SERVER_IP, SERVER_GATE_PORT)
                        socket_send_data(
                            sock,
                            pack(
                                '<ciiiii',
                                '\x00',
                                get_current_millisecond_clamped(),
                                self.cid,
                                0, 0, 0
                            ),
                            target_addr
                        )
                    else:
                        socket_send_data(
                            sock,
                            pack(
                                '<ciiiii',
                                '\x00',
                                get_current_millisecond_clamped(),
                                self.cid,
                                0, 0, 0
                            ),
                            target_addr
                        )
                    # login_requested = True
        finally:
            # print self.name, 'ends'
            if package_count == 0:
                print self.name, 'infinite'
            else:
                avg_lag = lag_total * 1.0 / package_count
                print avg_lag, package_count


def main():
    for i in range(100):
        t = ClientProcess(i)
        t.start()


if __name__ == '__main__':
    main()
