from message_server import MessageServer
from client_communicator import ClientCommunicator
from room_manager import RoomManager
import threading
import socket
import config
from struct import *


class ClientConnection:
    def __init__(self, sock_c=None, r_ip='', r_port=0):
        self.sock_c = sock_c
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.at_room = -1


class RoomInfo:
    def __init__(self, rid, room_manager):
        self.rid = rid
        self.manager = room_manager


class NetPackage:
    def __init__(self, data, ip, port):
        self.data = data
        self.ip = ip
        self.port = port


class GateServer(MessageServer):

    """
    gate server to accept client initial requests
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
        self.init_accepting_socket()
        # NOT SURE IF EACH CONNECTION SHOULD HAVE SEPARATE SOCKET
        self.gate_communicator = ClientCommunicator(sock=self.sock_accepting)   # communicator
        self.client_connections = {}   # client id : client connection
        self.client_connections_lock = threading.RLock()
        self.rooms = {}     # room id : room info

    def init_accepting_socket(self):
        # bind accepting socket to (gate ip : port)
        self.sock_accepting.bind((config.GATE_IP, config.GATE_PORT))
        self.sock_accepting.settimeout(0.1)

    def login_client(self, cid, token, pkg):
        login_success = True
        if login_success:
            self.client_connections_lock.acquire()

            new_connection = ClientConnection(r_ip=pkg.ip, r_port=pkg.port)
            self.client_connections[cid] = new_connection

            self.client_connections_lock.release()
            print 'login success'
        else:
            print 'login failed. connection request denied.'

    def logout_client(self, cid):
        self.client_connections_lock.acquire()

        self.client_connections.pop(cid, None)
        print 'client logout'

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
        threading.Thread(name='RoomManager-'+str(res_rid), target=new_room_manager.start)
        return new_room_info

    def assign_room(self, cid, rid=-1):
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
                self.client_connections[cid].at_room = rid

            self.client_connections_lock.release()

    def handle_message(self, msg):
        """
        routing packages to other servers / managers
        :param msg:
        :return:
        """
        # send package here
        cid = unpack('<i', msg.content[5:5+4])
        self.client_connections_lock.acquire()
        if cid not in self.client_connections:
            print 'client not connected. package not sent'
        else:
            # TODO: should use communicator here
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                d_len = sock.sendto(msg.content,
                                    0,
                                    (self.client_connections[cid].remote_ip,self.client_connections[cid].remote_port)
                                    )
                print d_len, ' bytes data sent'
            finally:
                sock.close()
        self.client_connections_lock.release()

    # get package from client
    def get_package(self):
        pkg = None
        try:
            data, addr = self.gate_communicator.receive_data()
            if data:
                pkg = NetPackage(0, '', 0)
                pkg.data = data
                pkg.ip = addr[0]
                pkg.port = addr[1]
        finally:
            return pkg

    def handle_package(self, pkg):
        """
        | seq | op_code | cid | pos | rot |
           4       1       4    12    12
        :return:
        """
        # parse package
        op_code = unpack('c', pkg.data[4:4+1])
        if op_code == '1':    # connect request
            cid = unpack('<i', pkg.data[5:5+4])
            token = 0
            self.login_client(cid, token, pkg)
        if op_code == '2':    # game data
            (seq, op_code, cid, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<iciiiiiii', pkg.data)
            # TODO: check seq here
            self.client_connections_lock.acquire()
            if cid in self.client_connections:
                rid = self.client_connections[cid].at_room
                if rid >= 0:
                    # route package to room
                    if rid not in self.rooms:
                        print 'room not exists, package discarded'
                    else:
                        self.send_message_content(pkg, self.rooms[rid].manager)
                else:
                    print 'client not in room, package discarded'
            else:
                print 'client not logged in, package discarded'
            self.client_connections_lock.release()

    def start_server(self):
        """
        package => UDP/TCP data from client
        message => message from other servers (also messenger)
        :return:
        """
        print 'gate server listening at: ', self.sock_accepting.getsockname()
        try:
            while True:

                # process incoming packages, max 10 a time
                for p_count in range(10):
                    new_pkg = self.get_package()
                    if new_pkg:
                        self.handle_package(new_pkg)
                    else:
                        break

                # process new messages, max 10 a time
                for m_count in range(10):
                    new_message = self.get_message()
                    if new_message:
                        self.handle_message(new_message)
                    else:
                        break
        finally:
            self.sock_accepting.close()
            print 'gate server closed'


if __name__ == '__main__':
    gs = GateServer('gate_server')
    gs.start_server()
