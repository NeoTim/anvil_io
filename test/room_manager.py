# -*- coding: utf-8 -*-
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


class RoomManager(ClientResponder):

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

                has_updates = False

                # receive
                self.to_recv_lock.acquire()
                while len(self.to_recv) > 0:
                    has_updates = True
                    # update clients
                    new_info_json = self.to_recv[0]
                    try:
                        new_info_dict = json.loads(new_info_json)
                        new_info = ClientInfo(0)
                        new_info.id = new_info_dict['id']
                        new_info.pos = new_info_dict['pos']
                        new_info.rot = new_info_dict['rot']
                        cid = new_info.id
                        self.clients[cid] = new_info
                    except Exception, e:
                        pass
                    # don't forget to pop queue
                    self.to_recv.pop(0)
                self.to_recv_lock.release()

                if not has_updates:
                    continue

                # send
                self.clients_lock.acquire()
                for cid in self.clients:
                    # sync clients
                    for ccid in self.clients:
                        if cid == ccid:
                            pass
                        try:
                            to_send_dict = {}
                            to_send_dict['id'] = self.clients[ccid].id
                            to_send_dict['pos'] = self.clients[ccid].pos
                            to_send_dict['rot'] = self.clients[ccid].rot
                            print 'sending: ' + str(ccid)
                            print to_send_dict
                            msg = json.dumps(to_send_dict)
                            self.client_threads[cid].handle_send(msg)
                        except Exception, e:
                            pass # print e
                self.clients_lock.release()
            finally:
                pass
