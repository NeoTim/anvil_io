import socket
from multiprocessing import Process
from threading import Thread
import threading
import Queue
import time
from struct import *
from client import ClientState, socket_recv_data, socket_send_data, get_current_millisecond_clamped


SERVER_IP = '0.0.0.0'
SERVER_PORT = 10000


class ClientConnection:
    def __init__(self, cid, sock, remote_addr):
        self.cid = cid
        self.sock = sock
        self.remote_addr = remote_addr
        self.last_package_time = time.time()


class ClientRoomInfo:
    def __init__(self, cid, sock, addr):
        self.state = ClientState()
        self.connection = ClientConnection(cid, sock, addr)


class BufferedPackage:
    def __init__(self, data, cid):
        self.data = data
        self.cid = cid


class RoomDirect(Thread):

    STATE_SYNC_RATE = 20

    class RecvThread(Thread):

        def __init__(self, socks, buffer_q, buffer_limit):
            Thread.__init__(self)
            self.socks = socks
            self.buffer_q = buffer_q
            self.buffer_limit = buffer_limit

        def run(self):
            try:
                while True:
                    for sock in self.socks:
                        try:
                            data, addr = sock.recvfrom(1024)
                            if data and self.buffer_q.qsize() < self.buffer_limit:
                                cid = unpack('<i', data[5:9])[0]
                                pkg_in = BufferedPackage(data, cid)
                                self.buffer_q.put(pkg_in)
                        finally:
                            pass
            finally:
                print 'recv thread ends'

    class SendThread(Thread):

        def __init__(self, clients, buffer_q):
            Thread.__init__(self)
            self.clients = clients
            self.buffer_q = buffer_q

        def run(self):
            try:
                while True:
                    try:
                        pkg_out = self.buffer_q.get(block=False)
                        data = pkg_out.data
                        cid = pkg_out.cid
                        if data:
                            socket_send_data(self.clients[cid].connection.sock, data, self.clients[cid].remote_addr)
                    except Queue.Empty, e:
                        pass
                    finally:
                        pass
            finally:
                print 'send thread ends'

    def __init__(self, rid, gate_ref):
        Thread.__init__(self)
        self.rid = rid
        self.clients = {}   # cid => client info
        self.clients_lock = threading.RLock()
        self.socks = []
        self.gate_ref = gate_ref
        self.last_sync_time = time.time()
        self.q_in = Queue.Queue()
        self.q_out = Queue.Queue()

    def add_client(self, client_info):
        self.clients_lock.acquire()
        cid = client_info.connection.cid
        if cid not in self.clients:
            print 'client', cid, 'entered room', self.rid
            self.clients[cid] = client_info
        self.clients_lock.release()

    def tick_sync_states(self):
        if time.time() - self.last_sync_time > 1.0 / self.STATE_SYNC_RATE:
            self.last_sync_time = time.time()
            for cid in self.clients:
                pass

    def run(self):
        recv_thread = self.RecvThread(self.socks, self.q_in, 500)
        send_thread = self.SendThread(self.clients, self.q_out)
        recv_thread.start()
        send_thread.start()
        try:
            print 'room', self.rid, 'starts'
            while True:
                self.tick_sync_states()
        finally:
            print 'room', self.rid, 'ends'


class ServerDirectMultiIOProcess(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.sock_gate = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_gate.bind((SERVER_IP, SERVER_PORT))
        self.socks = []  # sockets to recv and send packages
        for i in range(10):
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_sock.bind((SERVER_IP, 20000 + i))
            self.socks.append(new_sock)
        self.client_connections = {}    # cid => client connection

    def run(self):
        try:
            print 'server starts. listening at ', (SERVER_IP, SERVER_PORT)
            new_room = RoomDirect(0, self)  # only one room for test
            new_room.start()
            while True:
                data, addr = socket_recv_data(self.sock_gate)
                if data:
                    op_code = unpack('<c', data[0])[0]
                    cid = unpack('<i', data[5:9])[0]
                    if op_code == '\x00':
                        # login request
                        assigned_sock = self.socks[cid % len(self.socks)]
                        # echo login success
                        socket_send_data(assigned_sock, pack(
                            '<cii',
                            '\x00',
                            get_current_millisecond_clamped(),
                            assigned_sock.getsockname()[1]
                        ), addr)
                        new_client_info = ClientRoomInfo(cid, assigned_sock, addr)
                        new_room.add_client(new_client_info)
                        pass
        finally:
            print 'server ends.'


def main():
    gs = ServerDirectMultiIOProcess()
    gs.start()


def test(q):
    q.put('hi multi process')


if __name__ == '__main__':
    # main()
    from multiprocessing import Process, Queue
    q = Queue()
    p = Process(target=test, args=(q,))

    p.start()
    p.join()
    content = q.get()
    print content
