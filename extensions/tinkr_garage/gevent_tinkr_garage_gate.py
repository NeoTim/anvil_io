from core_v2.gate_server_base import GateServerBase, ClientConnection
from struct import *
from lib.tkutil import get_current_millisecond_clamped
import requests
import json
import threading
from garage_web_api import GarageWebApi
import garage_util


class TinkrGateServer(GateServerBase):
    def __init__(self, room_server_class, bind_addr, server_name):
        GateServerBase.__init__(self, room_server_class, bind_addr, server_name)
        self.log_server_name = 'gameserver'     # server name registerd in log server

    def login_client(self, cid, token, remote_ip, remote_port):
        res_code = '\x00'
        if cid not in self.client_connections:
            # TESTING
            login_success = GarageWebApi.check_session(cid, token)
            if login_success:
                new_connection = ClientConnection(remote_ip, remote_port)
                self.client_connections[cid] = new_connection
                res_code = '\x00'   # 00 == login success
                garage_util.log_garage('Player ' + str(cid) + ' login success', True)
                # self.post_login_client(cid)  # after login action
            else:
                res_code = '\x01'   # 01 == authorization failed
                garage_util.log_garage('Player ' + str(cid) + ' info not correct. login failed', True)
        else:
            res_code = '\x02'   # 02 == login conflict
            garage_util.log_garage('Player ' + str(cid) + ' already logged in')
        pkg_data = pack(
            '<ciicc',
            '\x12',
            get_current_millisecond_clamped(),
            cid,
            '\x0a',  # \x0a == server login result event
            res_code,
        )
        dlen = self.net_communicator.send_data(pkg_data, remote_ip, remote_port)
        garage_util.log_garage(str(dlen) + ' sent')

    def logout_client(self, cid):
        self.pre_logout_client(cid)  # before logout actions
        if cid in self.client_connections:
            at_room = self.client_connections[cid].at_room
            if at_room >= 0:
                self.quit_room(cid)
            self.client_connections.pop(cid, None)
            garage_util.log_garage('client ' + str(cid) + ' logged out', True)
        else:
            garage_util.log_garage('client ' + str(cid) + ' not logged in. logout failed')

    def create_room(self, rid=None):
        res_rid = 0
        if rid and rid >= 0:
            res_rid = rid
        while res_rid in self.room_servers:
            res_rid += 1
        new_room_server = self.room_server_class(self, res_rid)
        self.room_servers[rid] = new_room_server
        garage_util.log_garage('room ' + str(res_rid) + ' created', True)
        # run room server
        room_thread = threading.Thread(target=new_room_server.start_server)
        room_thread.start()
        return new_room_server

    def assign_room(self, cid, pkg, rid=-1):
        room_id = 0     # default room id
        if rid >= 0:    # if room id specified, use it
            room_id = rid
        else:
            # TESTING
            while room_id in self.room_servers and len(self.room_servers[room_id].client_infos) >= 80:
                room_id += 1
        target_room = None
        if room_id not in self.room_servers:        # create room if not exists
            target_room = self.create_room(room_id)
        else:
            target_room = self.room_servers[room_id]
        if not target_room:
            garage_util.log_garage('room error. no room available')
        else:
            if cid not in self.client_connections:
                garage_util.log_garage('client ' + str(cid) + ' not logged in')
            elif self.client_connections[cid].at_room >= 0:
                garage_util.log_garage('client ' + str(cid) + ' already in room ' + str(self.client_connections[cid].at_room), True)
            else:
                garage_util.log_garage('pass client ' + str(cid) + ' to room ' + str(room_id))
                target_room.run_command('add_client', cid)
                self.client_connections[cid].at_room = room_id

    def quit_room(self, cid):
        if cid in self.client_connections:
            at_room = self.client_connections[cid].at_room
            if at_room >= 0:
                garage_util.log_garage('client ' + str(cid) + ' requests to quit room ' + str(at_room))
                self.room_servers[at_room].run_command('remove_client', cid)
                self.client_connections[cid].at_room = -1
            else:
                garage_util.log_garage('client ' + str(cid) + ' not in any room. quit room failed')
        else:
            garage_util.log_garage('client ' + str(cid) + ' not logged in. quit room failed')

    def parse_token(self, pkg_data):
        token = unpack('<i', pkg_data[14:18])[0]
        garage_util.log_garage('get session ' + str(token))
        return token

    def solve_package(self, pkg):
        data = pkg.data
        addr = (pkg.ip, pkg.port)
        op_code = unpack('<c', data[0])[0]
        target_cid = unpack('<i', data[5:5 + 4])[0]

        if op_code <= '\x0f':  # admin package
            if op_code == '\x01':  # login
                token = self.parse_token(data)
                self.login_client(target_cid, token, addr[0], addr[1])
            elif op_code == '\x02':  # logout
                self.logout_client(target_cid)
        elif op_code <= '\x1f':  # game package
            # TODO: move login handling to admin package
            if op_code == '\x12':   # event
                event_id = unpack('<c', data[9:10])[0]
                if event_id == '\x06':  # ping
                    # TESTING
                    if target_cid in self.client_connections:
                        ping_start = unpack('<i', data[1:5])[0]
                        pkg_data = pack(
                            '<ciici',
                            '\x12',
                            get_current_millisecond_clamped(),
                            target_cid,
                            '\x08',
                            ping_start
                        )
                        dlen = self.net_communicator.send_data(pkg_data, addr[0], addr[1])
                    else:
                        garage_util.log_garage('no echo for not logged in client' + str(target_cid))
                    return
                if event_id == '\x07':   # login
                    garage_util.log_garage('login event')
                    token = self.parse_token(data)
                    self.login_client(target_cid, token, addr[0], addr[1])
                    return
                if event_id == '\x0b':  # re-login
                    garage_util.log_garage('re-login event')
                    relogin_res = '\x00'    # 00 == ok
                    if target_cid in self.client_connections:
                        pkg_data = pack(
                            '<ciicc',
                            '\x12',
                            get_current_millisecond_clamped(),
                            target_cid,
                            '\x0d',
                            relogin_res
                        )
                        dlen = self.net_communicator.send_data(pkg_data, addr[0], addr[1])
                    return
                if event_id == '\x08':  # logout
                    # TODO: logout
                    garage_util.log_garage('logout event')
                    self.logout_client(target_cid)
                    return
                if event_id == '\x00':  # match game request
                    # TODO: move join room to separate package
                    garage_util.log_garage('join room event')
                    desired_rid = unpack('<i', data[14:18])[0]
                    garage_util.log_garage('desired room id' + str(desired_rid))
                    self.assign_room(target_cid, pkg, desired_rid)

            # pass to room if necessary (game event)
            if target_cid in self.client_connections:
                at_room = self.client_connections[target_cid].at_room
                if at_room >= 0:
                    self.room_servers[at_room].run_command('handle_package', pkg)

        elif op_code <= '\x2f':  # sys info package
            pass
'''
if __name__ == '__main__':

    from gevent_tinkr_garage_room import TinkrGarageRoom
    import time

    rs_class = TinkrGarageRoom
    gs = TinkrGateServer(rs_class, ('0.0.0.0', 10000), 'tinkr_garage_gate')

    gs.create_room(666)
    gs.room_servers[666].run_command('set_storm_enabling', 0)

    threading.Thread(target=gs.start_server).start()

    # spawn fake clients
    spawn_fake_clients = False
    while spawn_fake_clients:
        if 666 in gs.room_servers:  # and len(gs.room_servers[666].client_infos) > 0:
            time.sleep(10)
            gs.room_servers[666].run_command('spawn_fake_clients', 10)
            break
'''