from command_server import *
from net_package import NetPackage
from net_communicator import NetCommunicator
import socket
from struct import *
import time
import core.tkutil as tkutil
import threading

import gevent
from gevent import monkey
monkey.patch_socket()   # should be careful to use


class ClientConnection:
    """
    client connection model
    """
    MAX_NO_RESPONSE = 30    # max seconds with no response from client before disconnect it

    def __init__(self, r_ip, r_port, sock_c=None):
        self.sock_c = sock_c
        self.seq = 0
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.last_package_time = time.time()
        self.at_room = -1


class GateServerBase(CommandServer):

    CONNECTION_CHECK_INTERVAL = 5   # check connection every 5 secs

    def __init__(self, room_server_class, bind_addr=('0.0.0.0', 10000), server_name='gate_server'):
        CommandServer.__init__(self, server_name)
        self.client_connections = {}    # TODO: this dict might need to be synchronized among threads
        self.room_server_class = room_server_class
        self.room_servers = {}  # room servers ref
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(bind_addr)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
        bufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        print 'send buffer size', bufsize
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
        bufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        print 'recv buffer size', bufsize
        self.bind_addr = bind_addr
        self.net_communicator = NetCommunicator('UDP', sock=sock, time_out=0)   # timeout == 0 => return immediately

        self.last_connection_check_stamp = time.time()

    def post_login_client(self, cid):
        pass

    def login_client(self, cid, token, remote_ip, remote_port):
        if cid not in self.client_connections:
            login_success = True    # TODO: the login state should be returned by login server
            if login_success:
                new_connection = ClientConnection(remote_ip, remote_port)
                self.client_connections[cid] = new_connection
                print 'client', cid, 'login success'
                self.post_login_client(cid)  # after login action
            else:
                print 'client', cid, 'info not correct. login failed'
        else:
            print 'client', cid, 'already logged in'

    def pre_logout_client(self, cid):
        pass

    @on_command('logout_client')
    def logout_client(self, cid):
        self.pre_logout_client(cid)  # before logout actions
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
        # run room server
        room_thread = threading.Thread(target=new_room_server.start_server)
        room_thread.start()
        return new_room_server

    def assign_room(self, cid, pkg, rid=-1):
        room_id = 0     # always 0 for now
        if rid >= 0:    # if room id specified, use it
            room_id = rid
        target_room = None
        if room_id not in self.room_servers:        # create room if not exists
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
                target_room.run_command('add_client', cid)
                self.client_connections[cid].at_room = room_id

    @on_command('quit_room')
    def quit_room(self, cid):
        if cid in self.client_connections:
            at_room = self.client_connections[cid].at_room
            if at_room >= 0:
                print 'client', cid, 'requests to quit room', at_room
                self.room_servers[at_room].run_command('remove_client', cid)
                self.client_connections[cid].at_room = -1
            else:
                print 'client', cid, 'not in any room. quit room failed'
        else:
            print 'client', cid, 'not logged in. quit room failed'

    @on_command('send_package')
    def send_package(self, to_cids, pkg_data, op_code):
        """
        send package to to_cid client
        header:
            | op_code | seq |
                 1       4
        :param to_cids:
        :param pkg_data:
        :param op_code:
        :return:
        """
        # add op_code and time stamp
        pkg_data = pack('<ci', op_code, tkutil.get_current_millisecond_clamped()) + pkg_data
        for to_cid in to_cids:
            if to_cid in self.client_connections:
                remote_ip = self.client_connections[to_cid].remote_ip
                remote_port = self.client_connections[to_cid].remote_port
                d_len = self.net_communicator.send_data(pkg_data, remote_ip, remote_port)
                # TESTING
                if op_code != '\x11':   # if not state
                    print d_len, 'bytes sent to', remote_ip, remote_port
            else:
                # print 'client', to_cid, 'not connected. no data sent'
                pass

    def parse_token(self, pkg_data):
        # TODO: should be overwritten. return the client token from the package data
        return ''

    def solve_package(self, pkg):
        raise NotImplementedError

    def tick_package(self):
        """
        coroutine = tick function to process incoming packages
        """
        while True:
            pkg = None
            # TODO: avoid copy value from socket responses
            [data, addr] = self.net_communicator.receive_data()
            if data:
                pkg = NetPackage(data, addr[0], addr[1])
                # update client last response time
                target_cid = unpack('<i', data[5:5 + 4])[0]
                if target_cid in self.client_connections:
                    self.client_connections[target_cid].last_package_time = time.time()
            if pkg:
                try:
                    self.solve_package(pkg)
                except KeyError, e:
                    print e
                    print 'unknown package'
            gevent.sleep(0)

    def tick_connection_check(self):
        """
        coroutine = check client timeout
        """
        while True:
            # detect if the client connection is timed out
            for cid in [ccid for ccid in self.client_connections]:
                if time.time() - self.client_connections[cid].last_package_time > ClientConnection.MAX_NO_RESPONSE:
                    print 'timeout. client', cid, 'connection closed'
                    self.logout_client(cid)
            # TESTING
            for rid in self.room_servers:
                print 'room', rid, 'has', len(self.room_servers[rid].client_infos), 'clients'
            gevent.sleep(self.CONNECTION_CHECK_INTERVAL)

    def start_server(self):
        try:
            threads = [
                gevent.spawn(self.tick_command),
                gevent.spawn(self.tick_package),
                gevent.spawn(self.tick_connection_check)
            ]
            print 'gate server listening at', self.bind_addr
            gevent.joinall(threads)
        except Exception, e:
            print e
        print 'gate server closed'


if __name__ == '__main__':

    from extensions.tinkr_garage.tinkr_garage_room import TinkrGarageRoom

    class TinkrGateServer(GateServerBase):
        def __init__(self, room_server_class, bind_addr, server_name):
            GateServerBase.__init__(self, room_server_class, bind_addr, server_name)

    rs_class = TinkrGarageRoom
    gs = GateServerBase(rs_class)
    gs.start_server()

    # spawn fake clients
    spawn_fake_clients = False
    if spawn_fake_clients:
        if 0 in gs.room_servers and round == 0 and len(gs.room_servers[0].client_infos) > 0:
            time.sleep(15)
            gs.room_servers[0].run_command('spawn_fake_clients', 1)
            round += 1
