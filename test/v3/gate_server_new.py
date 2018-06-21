from message_server import MessageServer
from client_communicator import ClientCommunicator
from room_manager_new import RoomManager
from messenger import Message
import threading
import socket
import config
import json
import time
from struct import *
import math


class ClientConnection:

    MAX_NO_RESPONSE = 30    # max seconds with no response from client before disconnect it

    def __init__(self, sock_c=None, r_ip='', r_port=0):
        self.sock_c = sock_c
        self.seq = 0
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.at_room = -1
        self.last_package_time = time.time()


class RoomInfo:
    def __init__(self, rid, room_manager):
        self.rid = rid
        self.manager = room_manager
        self.room_thead = threading.Thread(name='RoomManager-'+str(rid), target=room_manager.start)


class NetPackage:
    def __init__(self, data, ip, port):
        self.data = data
        self.ip = ip
        self.port = port


class GateServer(MessageServer):
    """
    servers server to accept client initial requests
    """
    class CommunicatorThread(threading.Thread):
        def __init__(self, gate_server_ref):
            super(GateServer.CommunicatorThread, self).__init__()
            self.gate_server_ref = gate_server_ref

        def run(self):
            print 'communicator thread ' + self.getName() + ' start'

    def __init__(self, m_name):
        MessageServer.__init__(self, m_name)

        self.sock_accepting = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket to accept packages
        # bind accepting socket to (servers ip : port)
        self.sock_accepting.bind((config.GATE_IP, config.GATE_PORT))
        self.sock_accepting.settimeout(0.1)
        # NOT SURE IF EACH CONNECTION SHOULD HAVE SEPARATE SOCKET
        self.gate_communicator = ClientCommunicator(sock=self.sock_accepting)   # communicator
        self.client_connections = {}   # client id : client connection
        self.client_connections_lock = threading.RLock()
        self.rooms = {}     # room id : room info

    def login_client(self, cid, token, pkg):
        login_success = True
        if login_success:
            self.client_connections_lock.acquire()

            new_connection = ClientConnection(r_ip=pkg.ip, r_port=pkg.port)
            self.client_connections[cid] = new_connection

            self.client_connections_lock.release()
            print 'client', cid, 'login success'
        else:
            print 'login failed. connection request denied.'
        return login_success

    def logout_client(self, cid):
        self.client_connections_lock.acquire()

        self.client_connections.pop(cid, None)
        print 'client', cid, 'logout'

        self.client_connections_lock.release()

    def create_room(self, rid=None):
        res_rid = 0
        if rid and rid >= 0:
            res_rid = rid
        while res_rid in self.rooms:
            res_rid += 1
        new_room_manager = RoomManager(res_rid, self)
        new_room_info = RoomInfo(res_rid, new_room_manager)
        self.rooms[rid] = new_room_info
        # run room manager
        new_room_info.room_thead.start()
        return new_room_info

    def assign_room(self, cid, pkg, rid=-1):
        room_id = 0     # always 0 for now
        if rid >= 0:
            room_id = rid
        target_room = None
        if room_id not in self.rooms:
            target_room = self.create_room(room_id)
        else:
            target_room = self.rooms[room_id]
        if not target_room:
            print 'room error. no room available'
        else:
            self.client_connections_lock.acquire()

            if cid not in self.client_connections:
                print 'client not logged in'
            elif self.client_connections[cid].at_room >= 0:
                print 'client already in room ', self.client_connections[cid].at_room
            else:
                # self.client_connections[cid].at_room = room_id
                print 'pass client', cid, 'to room', room_id
                self.send_message_content(
                    {
                        'add_client': cid,
                        'data': pkg.data
                    },
                    target_room.manager
                )
                self.client_connections[cid].at_room = room_id

            self.client_connections_lock.release()

    def quit_room(self, cid):
        self.client_connections_lock.acquire()
        if cid not in self.client_connections:
            print 'client', cid, 'not exists'
        elif self.client_connections[cid].at_room < 0:
            print 'client', cid, 'was not assigned to any room'
        else:
            print 'client', cid, 'requests to quit room', self.client_connections[cid].at_room
            self.send_message_content(
                {
                    'remove_client': cid,
                    'data': ''
                },
                self.rooms[self.client_connections[cid].at_room].manager
            )
            self.client_connections[cid].at_room = -1
        self.client_connections_lock.release()

    def handle_message(self, msg):
        """
        routing packages to other servers / managers
        message content structure from 'room_manager':
            {
                "send_to_cid": cid,
                "data": "op_code | cid | pos | rot"
            }
            {
                "room_close": rid,
                "data": [cid]
            }
        :param msg:
        :type msg: Message
        :return:
        """
        msg_struct = msg.content
        if 'send_to_cid' in msg_struct:
            # print 'get message to sent'
            # print msg_struct
            # send package here
            cid = msg_struct['send_to_cid']
            # send_data = msg_struct['data'][0] + pack('<i', self.client_connections[cid].seq) + msg_struct['data'][1:]
            cur_stamp = time.time()
            int_sec = int(cur_stamp)
            frac, whole = math.modf(cur_stamp)
            cur_ms = 0
            for i in range(6):
                cur_ms += 10**i * (int_sec % 10)
                int_sec /= 10
            cur_ms = cur_ms * 1000 + int(frac * 1000)
            send_data = msg_struct['data'][0] + pack('<i', cur_ms) + msg_struct['data'][1:]
            self.client_connections_lock.acquire()
            if cid not in self.client_connections:
                print 'client not connected. package not sent'
            else:
                # TODO: should use communicator here
                d_len = self.gate_communicator.send_data(send_data, self.client_connections[cid].remote_ip, self.client_connections[cid].remote_port)
                print d_len
                # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # try:
                #     d_len = sock.sendto(send_data,
                #                         (self.client_connections[cid].remote_ip, self.client_connections[cid].remote_port)
                #                         )
                #     # add sequential number
                #     self.client_connections[cid].seq += 1
                #     print d_len, 'bytes data sent to', self.client_connections[cid].remote_ip, self.client_connections[cid].remote_port
                # finally:
                #     sock.close()
            self.client_connections_lock.release()
        elif 'room_close' in msg_struct:
            to_quit_clients = msg_struct['data']
            for cid in to_quit_clients:
                self.quit_room(cid)

    # get package from client
    def get_package(self):
        pkg = None
        try:
            data_addr = self.gate_communicator.receive_data()
            if data_addr:
                # print data_addr
                pkg = NetPackage(0, '', 0)
                pkg.data = data_addr[0]
                pkg.ip = data_addr[1][0]
                pkg.port = data_addr[1][1]
        finally:
            return pkg

    def handle_package(self, pkg):
        """
        cid == client id, vid == vehicle id
        op_code == '\x01' (join room):
            | *seq | op_code | cid | vid |
               4       1        4     4
        op_code == '\x02' (update):
            | *seq | op_code | cid | pos | rot |
               4       1        4    12    12
        op_code == '\x03' (quit room):
            | *seq | op_code | cid |
               4       1        4
        :param: pkg
        :type: pkg: NetPackage
        :return:
        """
        # parse package
        (op_code, seq) = unpack('<ci', pkg.data[0:0+5])
        if op_code <= '\x0f':    # connect request
            # if op_code == '\x01':
            #     # cid = unpack('<i', pkg.data[5:5+4])
            #     vid = unpack('<i', pkg.data[9:9+4])
            #     print 'vehicle id', vid
            #     token = 0
            #     login_success = self.login_client(cid, token, pkg)
            #     # TODO: assign room should be done by client request
            #     if login_success:
            #         self.assign_room(cid, pkg)
            pass
        elif op_code <= '\x1f':    # game data
            if op_code == '\x11':      # client state
                (op_code, seq, cid, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<ciiiiiiii', pkg.data)
                # TODO: check seq here
                self.client_connections_lock.acquire()
                if cid in self.client_connections:
                    self.client_connections[cid].last_package_time = time.time()    # update client last package time
                    rid = self.client_connections[cid].at_room
                    if rid >= 0:
                        # route package to room
                        if rid not in self.rooms:
                            print 'room not exists, package discarded'
                        else:
                            # self.send_message_content(pkg.data, self.rooms[rid].manager)
                            self.send_message_content(
                                {
                                    'update_client': cid,
                                    'data': pkg.data
                                },
                                self.rooms[rid].manager
                            )
                            # print 'notify room to update client'
                    else:
                        print 'client', cid, 'not in room', rid, ', package discarded'
                else:
                    print cid
                    print self.client_connections
                    print 'client not logged in, package discarded'
                self.client_connections_lock.release()
            elif op_code == '\x12': # game event
                print 'game event'
                (event_id) = unpack('<c', pkg.data[5])
                (cid) = unpack('<i', pkg.data[6:6+4])
                event_id = event_id[0]
                cid = cid[0]
                print 'event id', event_id
                print 'cid ', cid
                if event_id == '\x00':   # login event
                    print 'login event'
                    # cid = unpack('<i', pkg.data[5:5+4])
                    vid = unpack('<i', pkg.data[10:10 + 4])
                    print 'vehicle id', vid
                    token = 0
                    login_success = self.login_client(cid, token, pkg)
                    # TODO: assign room should be done by client request
                    if login_success:
                        self.assign_room(cid, pkg)
        elif op_code == '\x03':     # quit request
            pass

    def keep_sending(self):
        while True:
            new_message = self.get_message()
            if new_message:
                self.handle_message(new_message)

    def start_server(self):
        """
        package => UDP/TCP data from client
        message => message from other servers (also messenger)
        :return:
        """

        print 'servers server listening at: ', self.sock_accepting.getsockname()

        sending_thread = threading.Thread(target=self.keep_sending)
        sending_thread.start()

        try:
            while True:

                # process incoming packages, max 1 a time
                for ind in range(1):
                    new_pkg = self.get_package()
                    if new_pkg:
                        self.handle_package(new_pkg)

                # # process new messages, max 1 a time
                # for ind in range(1):
                #     new_message = self.get_message()
                #     if new_message:
                #         self.handle_message(new_message)
                #     else:
                #         break

                # loop each client connection
                self.client_connections_lock.acquire()
                for cid in [ccid for ccid in self.client_connections]:
                    if time.time() - self.client_connections[cid].last_package_time > ClientConnection.MAX_NO_RESPONSE:
                        print 'timeout. client', cid, 'connection closed'
                        self.quit_room(cid)
                        self.logout_client(cid)
                self.client_connections_lock.release()

        finally:
            self.sock_accepting.close()
            print 'servers server closed'


if __name__ == '__main__':
    gs = GateServer('gate_server')
    gs.start_server()
    # for i in range(100):
    #     time.sleep(1)
    #     cur_ms = int(time.time() * 1000) % 60000
    #     print cur_ms
