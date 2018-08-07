from core.gate_server_base import GateServerBase
from core.gate_server_base import ClientConnection
from struct import *
import core.tkutil as tkutil
import requests
import json


class TinkrGateServer(GateServerBase):
    def __init__(self, room_server_class, bind_addr, server_name):
        GateServerBase.__init__(self, room_server_class, bind_addr, server_name)

    def authenticate_client(self, cid, token):
        try:
            # TODO: make request through api
            response = requests.get(
                'https://tinkrinc.com/api/checksession?pid=' + str(cid) + '&sessionid=' + str(token),
                timeout=5
            )
            res = json.loads(response.text)
            if res['result'] == 'succeed':
                return True
            return False
        except requests.exceptions.Timeout, e:
            print 'web server timed out.'
        return False

    def login_client(self, cid, token, remote_ip, remote_port):
        res_code = '\x00'
        if cid not in self.client_connections:
            # TESTING
            login_success = True  # self.authenticate_client(cid, token)
            if login_success:
                new_connection = ClientConnection(remote_ip, remote_port)
                self.client_connections[cid] = new_connection
                res_code = '\x00'   # 00 == login success
                print 'client', cid, 'login success'
                # self.post_login_client(cid)  # after login action
            else:
                res_code = '\x01'   # 01 == authorization failed
                print 'client', cid, 'info not correct. login failed'
        else:
            res_code = '\x02'   # 02 == login conflict
            print 'client', cid, 'already logged in'
        pkg_data = pack(
            '<ciicc',
            '\x12',
            tkutil.get_current_millisecond_clamped(),
            cid,
            '\x0a',  # \x0a == server login result event
            res_code,
        )
        dlen = self.net_communicator.send_data(pkg_data, remote_ip, remote_port)
        print dlen, 'sent'

    def assign_room(self, cid, pkg, rid=-1):
        room_id = 0     # default room id
        if rid >= 0:    # if room id specified, use it
            room_id = rid
        else:
            # TESTING
            while room_id in self.room_servers and len(self.room_servers[room_id].client_infos) > 80:
                room_id += 1
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

    def parse_token(self, pkg_data):
        token = unpack('<i', pkg_data[14:18])[0]
        print 'get session', token
        return token

    def solve_package(self, pkg):
        data = pkg.data
        addr = (pkg.ip, pkg.port)
        op_code = unpack('<c', data[0])[0]
        # int_op_code = tkutil.get_int_from_byte(op_code)
        target_cid = unpack('<i', data[5:5 + 4])[0]

        # TESTING
        # if op_code == '\x12':   # ping event
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
                    print 'ping event'
                    # TESTING
                    if target_cid in self.client_connections:
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
                    else:
                        print 'no echo for not logged in clients'
                    return
                if event_id == '\x07':   # login
                    print 'login event'
                    token = self.parse_token(data)
                    self.login_client(target_cid, token, addr[0], addr[1])
                    return
                if event_id == '\x08':  # logout
                    # print 'logout event'
                    # self.logout_client(target_cid)
                    return
                if event_id == '\x00':  # match game request
                    # TODO: move join room to separate package
                    print 'join room event'
                    desired_rid = unpack('<i', data[14:18])[0]
                    print 'desired room id', desired_rid
                    self.assign_room(target_cid, pkg, desired_rid)

            # pass to room if necessary (game event)
            if target_cid in self.client_connections:
                at_room = self.client_connections[target_cid].at_room
                if at_room >= 0:
                    self.room_servers[at_room].run_command('handle_package', pkg)

        elif op_code <= '\x2f':  # sys info package
            pass

if __name__ == '__main__':

    from tinkr_garage_room import TinkrGarageRoom
    import time

    rs_class = TinkrGarageRoom
    gs = TinkrGateServer(rs_class, ('0.0.0.0', 10001), 'tinkr_garage_gate')

    # gs.create_room(666)
    # gs.room_servers[666].run_command('set_storm_enabling', 0)

    time.sleep(0.5)

    gs.start_server()

    time.sleep(2)

    # spawn fake clients
    round = 1
    while round == 0:
        if 0 in gs.room_servers and round == 0 and len(gs.room_servers[0].client_infos) > 0:
            time.sleep(10)
            gs.room_servers[0].run_command('spawn_fake_clients', 80)
            round += 1
