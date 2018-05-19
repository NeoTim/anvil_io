# -*- coding: utf-8 -*-
import threading


class ClientResponder(threading.Thread):
    def __init__(self):
        super(ClientResponder, self).__init__()
        self.client_threads = {}    # id : client_thread
        self.client_threads_lock = threading.RLock()
        self.to_recv = []   # message to receive
        self.to_recv_lock = threading.RLock()

    def handle_recv(self, msg):
        self.to_recv_lock.acquire()
        if len(self.to_recv) < 200:
            self.to_recv.append(msg)
        self.to_recv_lock.release()

    def add_client_thread(self, cid, thread_c):
        self.client_threads_lock.acquire()
        if cid not in self.client_threads:
            self.client_threads[cid] = thread_c
        self.client_threads_lock.release()

    def remove_client_thread(self, cid):
        pass




