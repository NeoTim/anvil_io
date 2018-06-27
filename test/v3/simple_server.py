import socket
from struct import *
# import lib.tkutil as tkutil
import time
import math


class ClientState:
    def __init__(self, cid):
        self.cid = cid
        self.pos = [0, 0, 0]
        self.rot = [0, 0, 0]
        self.HP = 100
        self.vid = 0
        self.spawn_slot = 0  # spawn slot of the client in the map
        self.need_update = False  # mask of updating
        self.latest_stamp = 0
        self.addr = ('', 0)
        self.last_package_stamp = time.time()


def get_current_millisecond_clamped():
    cur_stamp = time.time()
    int_sec = int(cur_stamp)
    frac, whole = math.modf(cur_stamp)
    cur_ms = 0
    for i in range(6):
        cur_ms += 10 ** i * (int_sec % 10)
        int_sec /= 10
    cur_ms = cur_ms * 1000 + int(frac * 1000)
    return cur_ms


def broadcast_data(data, sock, clients, excludes=[]):
    for target_cid in clients:
        if target_cid not in excludes:
            try:
                d_len = sock.sendto(data, clients[target_cid].addr)
                print d_len, 'bytes sent'
            except socket.timeout, e:
                print 'send timeout'


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
            if op_code == '\x11':   # game state
                """
                    | op_code | seq | cid | state |
                         1       4     4      n
                """
                (op_code, seq, cid, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<ciiiiiiii', data)
                if cid in clients:
                    clients[cid].last_package_stamp = time.time()
                    need_update = False
                    if clients[cid].pos != [pos_x, pos_y, pos_z]:
                        clients[cid].pos = [pos_x, pos_y, pos_z]
                        need_update = True
                    if clients[cid].rot != [rot_x, rot_y, rot_z]:
                        clients[cid].rot = [rot_x, rot_y, rot_z]
                        need_update = True
                    clients[cid].need_update = need_update
                else:
                    print 'client', cid, 'not logged in. state not sync'
            elif op_code == '\x12':     # game event
                """
                    | op_code | seq | cid | eid | ...
                         1       4     4     1
                """
                event_id = unpack('<c', data[9])[0]
                cid = unpack('<i', data[5:5 + 4])[0]
                print 'event id ' + event_id
                print 'cid ', cid
                if event_id == '\x00':
                    # login event
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
                                '<ciicii',
                                '\x12',     # 1 == game package, 2 == game event
                                get_current_millisecond_clamped(),
                                existing_cid,
                                '\x00',     # event id == 0
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
                                '<ciicii',
                                '\x12',  # 1 == game package, 2 == game event
                                get_current_millisecond_clamped(),
                                cid,
                                '\x00',  # event id == 0
                                clients[cid].vid,
                                clients[cid].spawn_slot
                            )
                            try:
                                d_len = sock_server.sendto(data_sent, clients[target_cid].addr)
                                print d_len, 'bytes sent'
                            except socket.timeout, e:
                                print 'send timeout'
                elif event_id == '\x02':
                    # fire event
                    """
                        | header | weapon_id |
                            10         4
                    """
                    print 'fire event'
                    weapon_id = unpack('<i', data[10:10 + 4])[0]
                    data_sent = pack(
                        '<ciici',
                        '\x12',
                        get_current_millisecond_clamped(),
                        cid,
                        '\x02',
                        weapon_id
                    )
                    broadcast_data(data_sent, sock_server, clients, [cid])
                elif event_id == '\x03':
                    # hit event
                    """
                        | header | damage | hit_pos | hit_cid |
                            10        4       4x3        4
                    """
                    print 'hit event'
                    fire_cid = cid
                    hit_cid = unpack('<i', data[26:26 + 4])[0]
                    damage = unpack('<i', data[10:10 + 4])[0]
                    print 'client', cid, 'hit', hit_cid, ', damage', damage
                    data_sent = pack(
                        '<ciicii',
                        '\x12',
                        get_current_millisecond_clamped(),
                        hit_cid,
                        '\x03',
                        fire_cid,
                        damage
                    )
                    broadcast_data(data_sent, sock_server, clients, [cid])
                else:
                    print 'unknown event'

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
                data_sent = pack('<cii', '\x11', get_current_millisecond_clamped(), state_count) + data_sent
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


