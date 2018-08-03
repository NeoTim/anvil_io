from command_server import *
from network.net_communicator import NetCommunicator
from network.net_package import NetPackage
import socket
from struct import *
import time
import tkutil


class ClientConnection:
    """
    client connection model
    """
    MAX_NO_RESPONSE = 20    # max seconds with no response from client before disconnect it

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
        # self.package_client_routing = {}    # ip address => client id
        self.room_server_class = room_server_class
        self.room_servers = {}  # room servers ref
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(bind_addr)
        self.bind_addr = bind_addr
        self.net_communicator = NetCommunicator(sock=sock, time_out=0.1)

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
        new_room_server.start_server()  # run room server
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
                if d_len == 22:  # TESTING
                    continue
                # print d_len, 'bytes sent to', remote_ip, remote_port
            else:
                # print 'client', to_cid, 'not connected. no data sent'
                pass

    def parse_token(self, pkg_data):
        # TODO: should be overwritten. return the client token from the package data
        return ''

    def solve_package(self, pkg):
        data = pkg.data
        addr = (pkg.ip, pkg.port)
        op_code = unpack('<c', data[0])[0]
        # int_op_code = tkutil.get_int_from_byte(op_code)
        target_cid = unpack('<i', data[5:5 + 4])[0]

        if op_code <= '\x0f':  # admin package
            if op_code == '\x01':  # login
                token = self.parse_token(data)
                self.login_client(target_cid, token, addr[0], addr[1])
            elif op_code == '\x02':  # logout
                self.logout_client(target_cid)
        elif op_code <= '\x1f':  # game package

            # TODO: move login handling to admin package
            if op_code == '\x12':
                event_id = unpack('<c', data[9:10])[0]
                if event_id == '\x00':
                    print 'login event'
                    token = self.parse_token(data)
                    self.login_client(target_cid, token, addr[0], addr[1])

                    # TODO: move join room to separate package
                    print 'join room event'
                    self.assign_room(target_cid, pkg)

                elif event_id == '\x06':
                    print 'ping event'
                    ping_start = unpack('<i', data[1:5])[0]
                    pkg_data = pack(
                        '<ciici',
                        '\x12',
                        tkutil.get_current_millisecond_clamped(),
                        target_cid,
                        '\x08',
                        ping_start
                    )
                    dlen = self.net_communicator.send_data(pkg_data, addr[0], addr[1])
                    print dlen, 'sent'
                    return

            if target_cid in self.client_connections:
                at_room = self.client_connections[target_cid].at_room
                if at_room >= 0:
                    self.room_servers[at_room].run_command('handle_package', pkg)

        elif op_code <= '\x2f':  # sys info package
            pass

    def tick_package(self):
        """
        tick function to process incoming packages
        | op_code | seq | cid | game data ...
             1       4     4        n
        :return:
        """
        pkg = None
        [data, addr] = self.net_communicator.receive_data()
        if data:
            pkg = NetPackage(data, addr[0], addr[1])
            # update client last response time
            target_cid = unpack('<i', data[5:5 + 4])[0]
            if target_cid in self.client_connections:
                self.client_connections[target_cid].last_package_time = time.time()
        if pkg:
            try:
                # op_code = unpack('<c', data[0])[0]
                # # int_op_code = tkutil.get_int_from_byte(op_code)
                # target_cid = unpack('<i', data[5:5+4])[0]
                #
                # # TESTING !!
                # if op_code == '\x12':
                #     eid = unpack('<c', data[9:10])[0]
                #     if eid == '\x06':
                #         print 'ping event'
                #         ping_start = unpack('<i', data[1:5])[0]
                #         pkg_data = pack(
                #             '<ciici',
                #             '\x12',
                #             tkutil.get_current_millisecond_clamped(),
                #             target_cid,
                #             '\x08',
                #             ping_start
                #         )
                #         dlen = self.net_communicator.send_data(pkg_data, addr[0], addr[1])
                #         print dlen, 'sent'
                #         return
                #
                # if op_code <= '\x0f':  # admin package
                #     if op_code == '\x01':   # login
                #         token = self.parse_token(data)
                #         self.login_client(target_cid, token, addr[0], addr[1])
                #     elif op_code == '\x02':  # logout
                #         self.logout_client(target_cid)
                # elif op_code <= '\x1f':  # game package
                #
                #     # TODO: move login handling to admin package
                #     if op_code == '\x12':
                #         event_id = unpack('<c', data[9:10])[0]
                #         if event_id == '\x00':
                #             print 'login event'
                #             token = self.parse_token(data)
                #             self.login_client(target_cid, token, addr[0], addr[1])
                #
                #             # TODO: move join room to separate package
                #             print 'join room event'
                #             self.assign_room(target_cid, pkg)
                #
                #     if target_cid in self.client_connections:
                #         at_room = self.client_connections[target_cid].at_room
                #         if at_room >= 0:
                #             self.room_servers[at_room].run_command('handle_package', pkg)
                # elif op_code <= '\x2f':  # sys info package
                #     pass
                self.solve_package(pkg)
                pass
            except KeyError, e:
                print e
                print 'unknown package'

    def tick_connection_check(self):
        if time.time() - self.last_connection_check_stamp > self.CONNECTION_CHECK_INTERVAL:
            self.last_connection_check_stamp = time.time()
            # detect if the client connection is timed out
            for cid in [ccid for ccid in self.client_connections]:
                if time.time() - self.client_connections[cid].last_package_time > ClientConnection.MAX_NO_RESPONSE:
                    print 'timeout. client', cid, 'connection closed'
                    self.quit_room(cid)
                    self.logout_client(cid)

    def loop(self):
        try:
            while True:
                self.tick_command()
                self.tick_package()
                self.tick_connection_check()
        finally:
            print 'gate server closed'

    def start_server(self):
        try:
            self.server_thread = threading.Thread(target=self.loop)
            print 'gate server listening at', self.bind_addr
            self.server_thread.start()
        except Exception, e:
            print e


if __name__ == '__main__':
    import room_server_base
    # CONFIG.get_room_server_class()

    from extensions.tinkr_garage.tinkr_garage_room import TinkrGarageRoom

    class TinkrGateServer(GateServerBase):
        def __init__(self, room_server_class, bind_addr, server_name):
            GateServerBase.__init__(self, room_server_class, bind_addr, server_name)

    # rs_class = room_server_base.RoomServerFactory.make_room_server_class(0, 0, 0)
    rs_class = TinkrGarageRoom
    gs = GateServerBase(rs_class)
    gs.start_server()

    # spawn fake clients
    round = 1
    while round == 0:
        if 0 in gs.room_servers and round == 0 and len(gs.room_servers[0].client_infos) > 0:
            time.sleep(15)
            gs.room_servers[0].run_command('spawn_fake_clients', 1)
            round += 1
    print 'done'
