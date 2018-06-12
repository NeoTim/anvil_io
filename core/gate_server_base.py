from command_server import *
from room_server_base import RoomServerBase
from network.net_communicator import NetCommunicator
from network.net_package import NetPackage
import socket
from struct import *


class ClientConnection:
    """
    client connection model
    """
    MAX_NO_RESPONSE = 10    # max seconds with no response from client before disconnect it

    def __init__(self, r_ip, r_port, sock_c=None):
        self.sock_c = sock_c
        self.seq = 0
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.at_room = -1


class GateServerBase(CommandServer):

    def __init__(self, room_server_class, bind_addr=('0,0,0,0', 10000), server_name='gate_server'):
        CommandServer.__init__(self, server_name)
        self.client_connections = {}
        # self.package_client_routing = {}    # ip address => client id
        self.room_server_class = room_server_class
        self.room_servers = {}  # room servers ref
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(bind_addr)
        self.net_communicator = NetCommunicator(sock=sock, time_out=0.01)

    def login_client(self, cid, token, remote_ip, remote_port):
        if cid not in self.client_connections:
            login_success = True    # TODO: the login state should be returned by login server
            if login_success:
                new_connection = ClientConnection(remote_ip, remote_port)
                self.client_connections[cid] = new_connection
                print 'client', cid, 'login success'
            else:
                print 'client', cid, 'info not correct. login failed'
        else:
            print 'client', cid, 'already logged in'

    @on_command('logout_client')
    def logout_client(self, cid):
        if cid in self.client_connections:
            at_room = self.client_connections[cid].at_room
            if at_room >= 0:
                self.quit_room(cid)
            self.client_connections.pop(cid, None)
            print 'client', cid, 'logged out'
        else:
            print 'client', cid, ' not logged in. logout failed'

    def create_room(self, rid=None):
        res_rid = 0
        if rid and rid >= 0:
            res_rid = rid
        while res_rid in self.room_servers:
            res_rid += 1
        new_room_server = self.room_server_class(self, res_rid)
        self.room_servers[rid] = new_room_server
        print 'room', res_rid, 'created'
        new_room_server.start_server()  # run room server
        return new_room_server

    def assign_room(self, cid, pkg, rid=-1):
        room_id = 0     # always 0 for now
        if rid >= 0:
            room_id = rid
        target_room = None
        if room_id not in self.room_servers:
            target_room = self.create_room(room_id)
        else:
            target_room = self.room_servers[room_id]
        if not target_room:
            print 'room error. no room available'
        else:
            if cid not in self.client_connections:
                print 'client not logged in'
            elif self.client_connections[cid].at_room >= 0:
                print 'client already in room ', self.client_connections[cid].at_room
            else:
                print 'pass client', cid, 'to room', room_id
                target_room.run_command('add_client', cid, pkg.data)
                self.client_connections[cid].at_room = room_id

    def quit_room(self, cid):
        if cid in self.client_connections:
            at_room = self.client_connections[cid].at_room
            if at_room >= 0:
                print 'client', cid, 'requests to quit room', at_room
                self.room_servers[at_room].run_command('remove_client', cid)
            else:
                print 'client', cid, 'not in any room. quit room failed'
        else:
            print 'client', cid, 'not logged in. quit room failed'

    @on_command('send_package')
    def send_package(self, to_cid, pkg_data):
        if to_cid in self.client_connections:
            remote_ip = self.client_connections[to_cid].remote_ip
            remote_port = self.client_connections[to_cid].remote_port
            d_len = self.net_communicator.send_data(pkg_data, remote_ip, remote_port)
            print d_len, 'bytes sent'
        else:
            print 'client', to_cid, 'not connected. no data sent'

    def parse_token(self, pkg_data):
        # TODO: should be overwritten. return the client token from the package data
        return ''

    def tick_package(self):
        """
        tick function to process incoming packages
        | op_code | seq | cid | game data ...
             1       4     4        n
        :return:
        """
        pkg = None
        data, addr = self.net_communicator.receive_data()
        if data:
            pkg = NetPackage(data, addr[0], addr[1])
        if pkg:
            try:
                op_code = unpack('<c', data[0])
                target_cid = unpack('<i', data[5:5+4])
                if op_code == '\x01':   # login request
                    token = self.parse_token(data)
                    self.login_client(target_cid, token, addr[0], addr[1])
                elif op_code == '\x02':     # game update
                    at_room = self.client_connections[target_cid]
                    if at_room >= 0:
                        self.room_servers[at_room].run_command('handle_package', pkg)
                elif op_code == '\x03':  # logout request
                    self.logout_client(target_cid)
            except KeyError, e:
                print e
                print 'unknown package'

    def tick_connection_check(self):
        pass

    def loop(self):
        while True:
            self.tick_command()
            self.tick_package()
            self.tick_connection_check()


if __name__ == '__main__':
    import room_server_base
    # CONFIG.get_room_server_class()
    rs_class = room_server_base.RoomServerFactory.make_room_server_class(0, 0, 0)
    gs = GateServerBase(rs_class)
    gs.start_server()
