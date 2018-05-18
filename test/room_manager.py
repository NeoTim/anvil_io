import socket
import json
import copy
import threading
from client_responder import ClientResponder


class ClientInfo:
    def __init__(self, cid):
        self.id = cid
        self.pos = [0, 0, 0]
        self.rot = [0, 0, 0]


class RoomManager(threading.Thread, ClientResponder):

    def __init__(self):
        super(RoomManager, self).__init__()
        self.clients = {}      # client id : client info
        self.clients_lock = threading.RLock()

    def add_client(self, cid, thread_c):
        self.add_client_thread(cid, thread_c)
        info_c = ClientInfo(cid)

        self.clients_lock.acquire()
        self.clients[cid] = info_c
        self.clients_lock.release()

    def remove_client(self, cid):
        pass

    def run(self):
        while True:
            try:
                # receive
                self.to_recv_lock.acquire()
                while len(self.to_recv) > 0:
                    # update clients
                    new_info_json = self.to_recv[0]
                    new_info = json.loads(new_info_json)
                    cid = new_info['id']
                    self.clients[cid] = new_info
                    # don't forget to pop queue
                    self.to_recv.pop(0)
                self.to_recv_lock.release()
                # send
                self.clients_lock.acquire()
                for cid in self.clients:
                    # sync clients
                    self.client_threads[cid].handle_send(json.dumps(self.clients[cid]))
                self.clients_lock.release()
            finally:
                pass
