import socket
from struct import *
import lib.tkutil as tkutil
import time


class ClientState:
    def __init__(self, cid):
        self.cid = cid
        self.pos = [0, 0, 0]
        self.rot = [0, 0, 0]
        self.vid = 0
        self.spawn_slot = 0  # spawn slot of the client in the map
        self.need_update = False  # mask of updating
        self.latest_stamp = 0
        self.addr = ('', 0)
        self.last_package_stamp = time.time()


if __name__ == '__main__':

    MAX_NO_RESPONSE = 10
    STATE_SYNC_RATE = 20

    sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_server.bind(('0.0.0.0', 10000))
    sock_server.setblocking(0)

    clients = {}    # cid => client state

    cur_spawn_slot = 0

    last_state_sync = time.time()

    print 'gate server listening at', sock_server.getsockname()

    while True:

        (data, addr) = (None, '')

        try:
            (data, addr) = sock_server.recvfrom(1024)
        except Exception, e:
            pass

        if data:
            op_code = unpack('<c', data[0:0+1])[0]
            if op_code == '\x11':
                # game state
                (op_code, seq, cid, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<ciiiiiiii', data)
                if cid in clients:
                    clients[cid].last_package_stamp = time.time()
                    if clients[cid].pos != [pos_x, pos_y, pos_z]:
                        clients[cid].pos = [pos_x, pos_y, pos_z]
                        clients[cid].need_update = True
                    if clients[cid].rot != [rot_x, rot_y, rot_z]:
                        clients[cid].rot = [rot_x, rot_y, rot_z]
                        clients[cid].need_update = True
                else:
                    print 'client', cid, 'not logged in. state not sync'
            elif op_code == '\x12':
                # game event
                event_id = unpack('<c', data[5])[0]
                cid = unpack('<i', data[6:6 + 4])[0]
                print 'event id ' + event_id
                print 'cid ', cid
                if event_id == '\x00':  # login event
                    print 'login event'
                    vid = unpack('<i', data[10:10 + 4])[0]
                    print 'vehicle id', vid
                    token = 0
                    login_success = False
                    if cid in clients:
                        print 'client', cid, 'already logged in'
                    else:
                        login_success = True
                    if login_success:
                        # add client
                        new_client_state = ClientState(cid)
                        new_client_state.addr = (addr[0], addr[1])
                        new_client_state.vid = vid
                        new_client_state.spawn_slot = len(clients) # cur_spawn_slot
                        cur_spawn_slot += 1

                        # notify new client of existing clients
                        print 'notify new client of existing clients'
                        for existing_cid in clients:
                            data_sent = pack(
                                '<ciciii',
                                '\x12',     # 1 == game package, 2 == game event
                                tkutil.get_current_millisecond_clamped(),
                                '\x00',     # event id == 0
                                existing_cid,
                                clients[existing_cid].vid,
                                clients[existing_cid].spawn_slot
                            )
                            try:
                                d_len = sock_server.sendto(data_sent, new_client_state.addr)
                                print d_len, 'bytes sent'
                            except socket.timeout, e:
                                print 'send timeout'

                        # add new client to map
                        clients[cid] = new_client_state

                        # notify all clients to add new client
                        print 'notify all clients to add new client'
                        for target_cid in clients:
                            data_sent = pack(
                                '<ciciii',
                                '\x12',  # 1 == game package, 2 == game event
                                tkutil.get_current_millisecond_clamped(),
                                '\x00',  # event id == 0
                                cid,
                                clients[cid].vid,
                                clients[cid].spawn_slot
                            )
                            try:
                                d_len = sock_server.sendto(data_sent, clients[target_cid].addr)
                                print d_len, 'bytes sent'
                            except socket.timeout, e:
                                print 'send timeout'

        # update client states to all
        if time.time() - last_state_sync > 1.0 / STATE_SYNC_RATE:
            last_state_sync = time.time()
            data_sent = ''
            state_count = 0
            for cid in clients:
                if clients[cid].need_update:
                    state_count += 1
                    pos = clients[cid].pos
                    rot = clients[cid].rot
                    data_sent += pack(
                                '<iiiiiii',
                                cid,
                                pos[0], pos[1], pos[2],
                                rot[0], rot[1], rot[2]
                            )
                clients[cid].need_update = False
            if state_count > 0:
                data_sent = pack('<cii', '\x11', tkutil.get_current_millisecond_clamped(), state_count) + data_sent
                for target_cid in clients:
                    try:
                        d_len = sock_server.sendto(data_sent, clients[target_cid].addr)
                        print d_len, 'bytes sent'
                    except Exception, e:
                        pass

        # check connection timeout
        for cid in [ccid for ccid in clients]:
            if time.time() - clients[cid].last_package_stamp > MAX_NO_RESPONSE:
                print 'timeout. client', cid, 'connection closed'
                clients.pop(cid, None)


