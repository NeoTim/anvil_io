from message_server import MessageServer
from messenger import Message
import threading
from struct import *
import time
import json


class ClientInfo:
    def __init__(self, cid):
        self.cid = cid
        self.pos = [0, 0, 0]
        self.rot = [0, 0, 0]
        self.vid = 0
        self.spawn_slot = 0     # spawn slot of the client in the map
        self.need_update = False    # mask of updating


class RoomManager(MessageServer):

    update_rate = 30   # 30 FPS

    def __init__(self, rid, gate_server_ref, cap=20):
        MessageServer.__init__(self, 'room_manager')
        self.rid = rid
        self.gate_server_ref = gate_server_ref  # must have a ref to servers server
        self.capacity = cap
        self.clients = {}   # client id : client info
        self.last_update = time.time()  # last update time in milliseconds

    def add_client(self, cid, pkg_data):
        if len(self.clients) >= self.capacity:
            print 'room full'
        elif cid in self.clients:
            print 'client already in room'
        else:
            new_client_info = ClientInfo(cid)
            vids = unpack('<i', pkg_data[9:9+4])
            new_client_info.vid = vids[0]
            new_client_info.spawn_slot = int(len(self.clients))

            print new_client_info.cid
            print new_client_info.vid
            print new_client_info.spawn_slot

            # add client to list
            self.clients[cid] = new_client_info

            # notify other clients to add new client
            self.broadcast_data(
                pack(
                    '<ciii',
                    '\x01',
                    cid,
                    new_client_info.vid,
                    new_client_info.spawn_slot
                ),
                [cid]
            )
            # notify new client of existing clients
            for existing_cid in self.clients:
                self.send_message_content(
                    {
                        'send_to_cid': cid,
                        'data': pack(
                            '<ciii',
                            '\x01',
                            existing_cid,
                            self.clients[existing_cid].vid,
                            self.clients[existing_cid].spawn_slot
                        )
                    },
                    self.gate_server_ref
                )

    def remove_client(self, cid):
        if cid not in self.clients:
            print 'client not exists'
        else:
            self.clients.pop(cid)
            print 'client', cid, 'leaves room', self.rid

    def broadcast_data(self, data, exclude_cids=[]):

        for target_cid in self.clients:
            if target_cid in exclude_cids:
                continue
            # print 'notify servers server to send data'
            self.send_message_content(
                {
                    'send_to_cid': target_cid,
                    'data': data
                },
                self.gate_server_ref
            )

    def handle_message(self, msg):
        """
        message content structure: package binary data
        | seq | op_code | cid | pos | rot |
           4       1       4    12    12
        :param msg: Message
        message content structure from 'gate_server':
            {
                "add_client": cid,
                "data": "seq | op_code | cid | vid"
            }
            {
                "remove_client": cid,
                "data": ""
            }
            {
                "update_client": cid,
                "data": "seq | op_code | cid | pos | rot"
            }
        :return:
        """
        msg_struct = msg.content
        if 'add_client' in msg_struct:
            cid = msg_struct['add_client']
            self.add_client(cid, msg_struct['data'])
        elif 'update_client' in msg_struct:
            # print 'room update client'
            # sync client data
            (op_code, seq, cid, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<ciiiiiiii', msg_struct['data'])
            if cid in self.clients:
                if self.clients[cid].pos != [pos_x, pos_y, pos_z]:
                    self.clients[cid].pos = [pos_x, pos_y, pos_z]
                    self.clients[cid].need_update = True
                if self.clients[cid].rot != [rot_x, rot_y, rot_z]:
                    self.clients[cid].rot = [rot_x, rot_y, rot_z]
                    self.clients[cid].need_update = True
        elif 'remove_client' in msg_struct:
            cid = msg_struct['remove_client']
            self.remove_client(cid)

    def start(self):
        print 'RoomManager-' + str(self.rid) + ' starts'
        try:
            while True:

                # process new messages, max 1 a time
                for i in range(1):
                    new_message = self.get_message()
                    if not new_message:
                        break
                    self.handle_message(new_message)

                # send updated clients to gate_server
                # TODO: better with tick() function
                if time.time() - self.last_update > (1.0 / self.update_rate):
                    for cid in self.clients:
                        if self.clients[cid].need_update:
                            # broadcast to other clients
                            pos = self.clients[cid].pos
                            rot = self.clients[cid].rot
                            client_data = pack(
                                '<ciiiiiii',
                                '\x02',
                                cid,
                                pos[0], pos[1], pos[2],
                                rot[0], rot[1], rot[2]
                            )
                            self.broadcast_data(client_data, [cid])
                            # print 'broadcast client ', cid
                        # clear update flag
                        self.clients[cid].need_update = False

        finally:
            print 'RoomManager-' + str(self.rid) + ' ends'
            # notify servers server
            self.send_message_content({
                    'room_close': self.rid,
                    'data': [self.clients[ck].cid for ck in self.clients]
                },
                self.gate_server_ref
            )
