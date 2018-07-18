import socket
# from multiprocessing import Process
from threading import Thread
import threading
import Queue
import time
from struct import *


def get_current_millisecond_clamped():
    cur_stamp = time.time()
    cur_ms = int(cur_stamp * 1000) % 604800000
    return cur_ms


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


class ClientInfo:
    def __init__(self, cid, io_port):
        self.cid = cid
        self.io_port = io_port


class RWLock:
    def __init__(self):
        self.r_lock = threading.RLock()
        self.w_lock = threading.RLock()
        self.read_count = 0

    def read_acquire(self):
        self.r_lock.acquire()
        self.read_count += 1
        if self.read_count == 1:
            self.w_lock.acquire()
        self.r_lock.release()

    def read_release(self):
        self.r_lock.acquire()
        self.read_count -= 1
        if self.read_count == 0:
            self.w_lock.release()
        self.r_lock.release()

    def write_acquire(self):
        self.w_lock.acquire()

    def write_release(self):
        self.w_lock.release()


class ServerProcess(Thread):

    SYNC_RATE = 20

    class IOPort(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.socks = []
            self.socks_lock = RWLock()
            self.client_sockets = {}  # cid => socket, remote addr
            self.client_sockets_lock = RWLock()
            """ buffer_in (client package): [data, from_cid]"""
            self.buffer_in = Queue.Queue(1000)
            """ buffer_out (server package): [data, to_cid] """
            self.buffer_out = Queue.Queue(1000)

        def register_client(self, cid, sock, addr):
            """ add client routing info here """
            self.client_sockets_lock.write_acquire()
            self.client_sockets[cid] = [sock, addr]
            self.client_sockets_lock.write_release()
            pass

        def keep_recv(self):
            while True:
                for sock in self.socks:
                    try:
                        data, addr = sock.recvfrom(1024)
                        if data:
                            cid = unpack('<i', data[5:9])[0]
                            try:
                                self.buffer_in.put([data, cid])
                            finally:
                                pass
                    except Exception, e:
                        pass
                    finally:
                        pass

        def keep_send(self):
            while True:
                try:
                    pkg = self.buffer_out.get()
                    if pkg:
                        to_cid = pkg[1]
                        sock = None
                        self.client_sockets_lock.read_acquire()
                        sock, addr = self.client_sockets[to_cid]
                        self.client_sockets_lock.read_release()
                        if sock:
                            dlen = socket_send_data(sock, pkg[0], addr)
                            # print dlen, 'sent'
                except Queue.Empty, e:
                    pass
                finally:
                    pass

        def run(self):
            print self.name, 'starts'
            try:
                t_recv = Thread(target=self.keep_recv)
                t_recv.start()
                t_send = Thread(target=self.keep_send)
                t_send.start()
                t_recv.join()
                t_recv.join()
                # while True:
                #     self.keep_recv()
                #     self.keep_send()
            finally:
                print self.name, 'ends'

    def __init__(self, port_num):
        Thread.__init__(self)
        self.sock_gate = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_gate.bind(('0.0.0.0', 10000))
        self.sock_gate.setblocking(0)

        self.socks = []
        self.io_ports = []
        self.sock_to_io_port = {}    # socket => io port. -1 == not assigned
        """ 
        note that one socket port can be assigned to ONLY ONE io port
        currently ONE socket <=> ONE io port (thread)
        """
        # init ports
        for i in range(port_num):
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_sock.bind(('0.0.0.0', 20000 + i))
            # new_sock.setblocking(0)
            self.socks.append(new_sock)
            new_io_port = self.IOPort()
            new_io_port.name = 'io-port-' + str(i)
            new_io_port.socks.append(new_sock)
            self.io_ports.append(new_io_port)
            self.sock_to_io_port[new_sock] = new_io_port

        # start io ports
        for io_port in self.io_ports:
            io_port.start()

        self.clients = {}  # cid => client info
        self.last_sync_time = time.time()
        pass

    def run(self):
        print 'server listening at', self.sock_gate.getsockname()
        try:
            while True:
                data, addr = socket_recv_data(self.sock_gate)
                if data:
                    op_code = unpack('<c', data[0])[0]
                    cid = unpack('<i', data[5:9])[0]
                    if op_code == '\x00':
                        # login request

                        if cid in self.clients:
                            print 'client', cid, 'already logged in'
                        else:
                            assigned_sock = self.socks[cid % len(self.socks)]
                            print 'client', cid, 'logged in'
                            assigned_io_port = self.sock_to_io_port[assigned_sock]
                            print 'assigned socket port', assigned_sock.getsockname()[1], 'io port', assigned_io_port

                            # add client record
                            new_client_info = ClientInfo(cid, assigned_io_port)
                            self.clients[cid] = new_client_info

                            # register client to io port
                            assigned_io_port.register_client(cid, assigned_sock, addr)

                            # notify client with new port
                            socket_send_data(self.sock_gate, pack('<cii', '\x00', get_current_millisecond_clamped(), assigned_sock.getsockname()[1]), addr)

                # read new packages
                # TODO: async io
                for io_port in self.io_ports:
                    try:
                        pkg = io_port.buffer_in.get(block=False)
                        if pkg:
                            # do some updates here
                            pass
                    except Queue.Empty:
                        pass

                # update clients to all
                if time.time() - self.last_sync_time > 1.0 / self.SYNC_RATE:
                    self.last_sync_time = time.time()

                    packed_data = ''
                    state_count = 0
                    for cid in self.clients:
                        if state_count > 20:
                            break
                        packed_data += pack(
                            '<iiii',
                            cid,
                            0, 0, 0
                        )
                        state_count += 1
                    packed_data = pack('<cii', '\x01', get_current_millisecond_clamped(), state_count) + packed_data
                    # broadcast via io port
                    for cid in self.clients:
                        try:
                            target_io_port = self.clients[cid].io_port
                            target_io_port.buffer_out.put([packed_data, cid])
                        except Exception, e:
                            print e

        finally:
            print 'server ends'


def main():
    gs = ServerProcess(5)
    gs.start()


if __name__ == '__main__':
    main()
