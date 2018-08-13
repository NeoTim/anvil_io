import socket
from multiprocessing import Process
from threading import Thread
import time
from struct import *

SERVER_IP = '10.123.163.239'
SERVER_GATE_PORT = 10000


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

    class RunningState:
        NOT_LOGGED_IN = 0
        LOGGED_IN = 1
        RUNNING_GAME = 2
        STOP = 3

    def __init__(self, cid):
        Process.__init__(self)
        self.cid = cid
        self.state = ClientState()
        self.running_state = self.RunningState.NOT_LOGGED_IN
        self.com_addr = [SERVER_IP, 0]
        self.time_to_live = 10  # in seconds
        self.start_time = 0

    def run(self):
        print self.name, 'starts'
        # record start time
        self.start_time = time.time()
        package_count = 0
        lag_total = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind(('0.0.0.0', 5000 + self.cid))
        try:
            while True:
                if time.time() - self.start_time > self.time_to_live:
                    print 'client times up.'
                    break
                data, addr = socket_recv_data(sock)
                """
                header of server (recv) package:
                | op_code | stamp |
                     1        4
                login_success:
                | \x00 | ... | com_port |
                                   4
                start_game:
                | \x01 | ... |
                end_game:
                | \x02 | ... |
                client_state:
                | \x03 | ... | state_count | state_data |
                                   4        (4 + 6) * n
                
                header of client (send) package:
                | op_code | stamp | cid |
                     1        4      4
                login_request:
                | \x00 | ... |
                client_state:
                | \x01 | ... | state_data |
                                   6
                """
                if data:
                    op_code = unpack('<c', data[0])[0]
                    stamp = unpack('<i', data[1:5])[0]

                    # stat of network
                    lag_total += get_current_millisecond_clamped() - stamp
                    package_count += 1

                    if self.running_state == self.RunningState.NOT_LOGGED_IN:
                        if op_code == '\x00':
                            print self.name, 'logged in'
                            self.running_state = self.RunningState.LOGGED_IN
                            com_port = unpack('<i', data[5:9])[0]
                            print com_port
                            self.com_addr[1] = com_port
                    if self.running_state == self.RunningState.LOGGED_IN:
                        if op_code == '\x01':
                            print self.name, 'join game'
                            self.running_state = self.RunningState.RUNNING_GAME
                    if self.running_state == self.RunningState.RUNNING_GAME:
                        if op_code == '\x02':
                            print self.name, 'quit game'
                            self.running_state = self.RunningState.STOP
                        elif op_code == '\x03':
                            pass
                    if self.running_state == self.RunningState.STOP:
                        break

                if self.running_state != self.RunningState.LOGGED_IN:
                    # send login request
                    d_len = socket_send_data(
                        sock,
                        pack('<cii', '\00', int(time.time()), self.cid),
                        (SERVER_IP, SERVER_GATE_PORT)
                    )
        finally:
            print self.name, 'ends'
            if package_count == 0:
                print 'average lag: infinite'
            else:
                print 'average lag:', lag_total / package_count


def main():
    # for i in range(10):
    #     p = ClientProcess(i)
    #     p.start()
    #     # p.join()
    c_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        c_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c_sock.bind(('10.23.13.108', 30000))
        print 'client sock', c_sock.getsockname()
        c_sock.sendto('login', ('10.23.13.108', 20000))
        data, addr = c_sock.recvfrom(1024)
        if data:
            print data
            if data == 'ok':
                print 'login success'
                c_sock.connect(('10.23.13.108', 20000))
                while True:
                    c_sock.sendto('hi', addr)
                    time.sleep(1)
    finally:
        c_sock.close()

if __name__ == '__main__':
    main()
