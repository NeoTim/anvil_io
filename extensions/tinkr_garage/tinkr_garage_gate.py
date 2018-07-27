from core.gate_server_base import GateServerBase
from struct import *
import core.tkutil as tkutil


class TinkrGateServer(GateServerBase):
    def __init__(self, room_server_class, bind_addr, server_name):
        GateServerBase.__init__(self, room_server_class, bind_addr, server_name)

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

                if event_id == '\x06':
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
                if event_id == '\x07':   # login
                    print 'login event'
                    token = self.parse_token(data)
                    self.login_client(target_cid, token, addr[0], addr[1])
                    pkg_data = pack(
                        '<ciicc',
                        '\x12',
                        tkutil.get_current_millisecond_clamped(),
                        target_cid,
                        '\x0a',  # \x0a == server login result event
                        '\x00',  # 00 == login success
                    )
                    dlen = self.net_communicator.send_data(pkg_data, addr[0], addr[1])
                    print dlen, 'sent'
                    return
                if event_id == '\x00':  # match game request
                    # TODO: move join room to separate package
                    print 'join room event'
                    self.assign_room(target_cid, pkg)

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
    gs = TinkrGateServer(rs_class, ('0.0.0.0', 10000), 'tinkr_garage_gate')

    gs.create_room(666)
    gs.room_servers[666].run_command('set_storm_enabling', 0)

    time.sleep(0.5)

    gs.start_server()
