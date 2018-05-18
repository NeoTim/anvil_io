import sys
import socket
import json
import threading
from client_thread import ClientThread
from room_manager import RoomManager


class ClientState:
    def __init__(self, sock_c):
        self.sock_c = sock_c    # client socket
        self.room_num = -1    # -1 == not playing, else == room number


class Room:
    def __init__(self, rid, manager):
        self.room_id = rid
        self.manager = manager


class LobbyServer(threading.Thread):

    latest_id = 0

    def __init__(self):
        super(LobbyServer, self).__init__()
        self.client_states = {}     # client id : client state
        self.rooms = {}     # room id : room

    def accept_client(self, sock_c):
        # create thread to serve client
        new_client_thread = ClientThread(sock_c, None)
        while self.client_states[self.latest_id]:
            self.latest_id += 1
        cid = self.latest_id
        new_client_state = ClientState(sock_c)
        self.client_states[cid] = new_client_state
        # assign client to room
        self.assign_client_room(cid, new_client_thread)
        # start client thread
        new_client_thread.start()

    def assign_client_room(self, cid, thread_c):
        if len(self.rooms) == 0:
            r_manager = RoomManager()
            new_room = Room(0, r_manager)
            self.rooms[0] = new_room
            # run room manager
            r_manager.start()
        a_room = self.rooms[0]
        # must set responder
        thread_c.set_responder(a_room.manager)
        a_room.manager.add_client(cid, thread_c)

    def quit_client_room(self, cid):
        pass

    def create_room(self):
        pass

    def destroy_room(self, rid):
        pass

    def run(self):
        while True:
            try:
                pass
            finally:
                pass

