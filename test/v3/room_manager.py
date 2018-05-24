from message_server import MessageServer
import threading


# SHOULD BE LOADED FROM SERVER INSTANCE
class ClientInfo:
    def __init__(self, cid):
        self.cid = cid
        self.pos = [0, 0, 0]
        self.rot = [0, 0, 0]


class RoomManager(MessageServer):
    def __init__(self, rid, gate_server_ref, cap=20):
        MessageServer.__init__(self, 'room_manager')
        self.rid = rid
        self.gate_server_ref = gate_server_ref  # must have a ref to gate server
        self.capacity = cap
        self.clients = {}   # client id : client info

    def add_client(self, cid):
        if len(self.clients) >= self.capacity:
            print 'room full'
        elif cid in self.clients:
            print 'client already in room'
        else:
            self.clients[cid] = ClientInfo(cid)

    def remove_client(self, cid):
        pass

    def handle_message(self, msg):
        pass

    def start(self):
        print 'RoomManager-' + str(self.rid) + ' starts'
        while True:
            pass
