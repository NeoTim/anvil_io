import socket
from multiprocessing import Process
from threading import Thread
import time
from struct import *

SERVER_IP = '10.123.160.189'
SERVER_GATE_PORT = 10000


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
        return d_len
    except Exception, e:
        print 'send error'
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

    def run(self):
        print self.name, 'starts'
        package_count = 0
        lag_total = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind(('0.0.0.0', 5000 + self.cid))
        try:
            while True:
                data, addr = socket_recv_data(sock)
                """
                header of recv package:
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
                
                header of send package:
                | op_code | stamp | cid |
                     1        4      4
                login_request:
                | \x00 | ... |
                client_state:
                | \x01 | ... | state_data |
                                   6
                """
                if data:
                    op_code = unpack('<c', data)[0]
                    stamp = unpack('<i', data[1:5])[0]

                    # stat of network
                    lag_total += (time.time() * 1000 % 1000000000 - stamp)
                    package_count += 1

                    if self.running_state == self.RunningState.NOT_LOGGED_IN:
                        if op_code == '\x00':
                            print self.name, 'logged in'
                            self.running_state = self.RunningState.LOGGED_IN
                            com_port = unpack('<i', data[5:9])[0]
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
            print 'average lag:', lag_total / package_count


def main():
    for i in range(5):
        p = ClientProcess(i)
        p.start()
        # p.join()

if __name__ == '__main__':
    main()