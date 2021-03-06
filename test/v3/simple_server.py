import socket
from struct import *
# import lib.tkutil as tkutil
import time
import math
import sys
import select
import threading
import Queue


class ClientState:
    def __init__(self, cid):
        self.cid = cid
        self.grid_x = '\x15'
        self.grid_y = '\x33'
        self.pos = ['\xa0', '\xa0', 2200]
        self.rot = ['\x00', '\x00', '\x00']
        self.HP = 100
        self.vid = 0
        self.spawn_slot = 0  # spawn slot of the client in the map
        self.need_update = False  # mask of updating
        self.latest_stamp = 0
        self.addr = ('', 0)
        self.last_package_stamp = time.time()


class GAME_STATUS:
    NOT_START = 0
    RUNNING = 1


class GAME_OBJ_TYPE:
    WEAPON = 0
    MEDKIT = 1
    DESTRUCTIBLE_OBJECT = 2
    GAS_TANK = 3


class GAME_WEAPON_TYPE:
    TURRET_BASIC = 1
    RPG_ROCKET = 2
    BIG_GUN = 3


class GameModel:
    def __init__(self):
        self.game_status = GAME_STATUS.NOT_START


def get_current_millisecond_clamped():
    cur_stamp = time.time()
    cur_ms = int(cur_stamp * 1000) % 604800000
    return cur_ms


def send_data_to_client(data_sent, target_cid):
    try:
        if not clients[target_cid].addr:
            # AI as no addr
            return
        d_len = sock_server.sendto(data_sent, clients[target_cid].addr)
        if d_len > 40:
            print d_len, ' sent'
        # print d_len, 'bytes sent'
    except socket.timeout, e:
        print 'send timeout'


def broadcast_data(data, sock, clients, excludes=[]):
    for target_cid in clients:
        if target_cid not in excludes:
            try:
                if not clients[target_cid].addr:
                    # AI as no addr
                    continue
                d_len = sock.sendto(data, clients[target_cid].addr)
                # print d_len, 'bytes sent'
            except socket.timeout, e:
                print 'send timeout'


def on_client_join_game(data, addr, cid, clients):
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
        if addr:
            new_client_state.addr = (addr[0], addr[1])
        else:
            # AI has no addr
            new_client_state.addr = None

        new_client_state.vid = vid
        new_client_state.spawn_slot = len(clients)  # cur_spawn_slot
        if cid < 100:
            # AI pos
            new_client_state.grid_x = pack('<h', unpack('<h', '\x15\x00')[0] + cid)[0]
        # cur_spawn_slot += 1

        # add new client to map
        clients[cid] = new_client_state

        # notify new client of existing clients
        print 'notify new client of existing clients'
        for existing_cid in clients:
            if existing_cid != cid:
                data_sent = pack(
                    '<ciicii',
                    '\x12',  # 1 == game package, 2 == game event
                    get_current_millisecond_clamped(),
                    existing_cid,
                    '\x00',  # event id == 0
                    clients[existing_cid].vid,
                    clients[existing_cid].spawn_slot
                )
                send_data_to_client(data_sent, cid)

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
            send_data_to_client(data_sent, target_cid)

    if not game_model.game_status == GAME_STATUS.RUNNING:
        # game start
        data_sent = pack(
            '<ciic',
            '\x12',
            get_current_millisecond_clamped(),
            0,
            '\x04'
        )
        broadcast_data(data_sent, sock_server, clients, [])
        # game_model.game_status = GAME_STATUS.RUNNING    # change game status


class ConsoleThread(threading.Thread):
    def __init__(self, console_buffer):
        threading.Thread.__init__(self)
        self.console_buffer = console_buffer

    def run(self):
        while True:
            input_data = raw_input()
            print 'get input', input_data
            self.console_buffer.put(input_data)


if __name__ == '__main__':

    MAX_NO_RESPONSE = 10
    STATE_SYNC_RATE = 20

    sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_server.bind(('0.0.0.0', 20000))
    sock_server.setblocking(0)

    clients = {}    # cid => client state

    cur_spawn_slot = 0

    last_state_sync = time.time()

    game_model = GameModel()    # game model

    console_input = Queue.Queue()  # buffer of console input
    console_thread = ConsoleThread(console_input)
    console_thread.daemon = True
    console_thread.start()

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
                # (op_code, seq, cid, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<ciiiiiiii', data)
                (op_code, seq, cid, grid_ind_x, grid_ind_y, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<ciicccchccc', data)
                # print ord(grid_ind_x), ord(grid_ind_y), ord(pos_x), ord(pos_y), pos_z, ord(rot_x), ord(rot_y), ord(rot_z)
                if cid in clients:
                    clients[cid].last_package_stamp = time.time()
                    need_update = True
                    if clients[cid].grid_x != grid_ind_x or clients[cid].grid_y != grid_ind_y:
                        clients[cid].grid_x = grid_ind_x
                        clients[cid].grid_y = grid_ind_y
                        need_update = True
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
                    # # login event
                    # print 'login event'
                    # vid = unpack('<i', data[10:10 + 4])[0]
                    # print 'vehicle id', vid
                    # token = 0
                    # login_success = False
                    # if cid in clients:
                    #     print 'client', cid, 'already logged in'
                    # else:
                    #     login_success = True
                    # if login_success:
                    #     # add client
                    #     new_client_state = ClientState(cid)
                    #     new_client_state.addr = (addr[0], addr[1])
                    #     new_client_state.vid = vid
                    #     new_client_state.spawn_slot = len(clients) # cur_spawn_slot
                    #     cur_spawn_slot += 1
                    #
                    #     # notify new client of existing clients
                    #     print 'notify new client of existing clients'
                    #     for existing_cid in clients:
                    #         data_sent = pack(
                    #             '<ciicii',
                    #             '\x12',     # 1 == game package, 2 == game event
                    #             get_current_millisecond_clamped(),
                    #             existing_cid,
                    #             '\x00',     # event id == 0
                    #             clients[existing_cid].vid,
                    #             clients[existing_cid].spawn_slot
                    #         )
                    #         try:
                    #             d_len = sock_server.sendto(data_sent, new_client_state.addr)
                    #             # print d_len, 'bytes sent'
                    #         except socket.timeout, e:
                    #             print 'send timeout'
                    #
                    #     # add new client to map
                    #     clients[cid] = new_client_state
                    #
                    #     # notify all clients to add new client
                    #     print 'notify all clients to add new client'
                    #     for target_cid in clients:
                    #         data_sent = pack(
                    #             '<ciicii',
                    #             '\x12',  # 1 == game package, 2 == game event
                    #             get_current_millisecond_clamped(),
                    #             cid,
                    #             '\x00',  # event id == 0
                    #             clients[cid].vid,
                    #             clients[cid].spawn_slot
                    #         )
                    #         try:
                    #             d_len = sock_server.sendto(data_sent, clients[target_cid].addr)
                    #             # print d_len, 'bytes sent'
                    #         except socket.timeout, e:
                    #             print 'send timeout'
                    #
                    # if not game_model.game_status == GAME_STATUS.RUNNING:
                    #     # game start
                    #     data_sent = pack(
                    #         '<ciic',
                    #         '\x12',
                    #         get_current_millisecond_clamped(),
                    #         0,
                    #         '\x04'
                    #     )
                    #     broadcast_data(data_sent, sock_server, clients, [])
                    #     # game_model.game_status = GAME_STATUS.RUNNING    # change game status

                    on_client_join_game(data, addr, cid, clients)

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
                    damage *= 0.96
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
                    broadcast_data(data_sent, sock_server, clients, [])
                elif event_id == '\x04':
                    # pick up weapon event
                    print 'pick up weapon event'
                    weapon_id = unpack('<i', data[10:10 + 4])[0]

                    pick_success = True

                    if pick_success:
                        # destroy weapon event
                        data_sent = pack(
                            '<ciici',
                            '\x12',
                            get_current_millisecond_clamped(),
                            cid,
                            '\x06',
                            weapon_id
                        )
                        broadcast_data(data_sent, sock_server, clients, [])

                        # equip weapon event
                        data_sent = pack(
                            '<ciiciii',
                            '\x12',
                            get_current_millisecond_clamped(),
                            cid,
                            '\x07',
                            weapon_id,
                            unpack('<i', data[14:14 + 4])[0],
                            unpack('<i', data[18:18 + 4])[0]
                        )
                        broadcast_data(data_sent, sock_server, clients, [])
                elif event_id == '\x06':    # ping event
                    data_sent = pack(
                        '<ciic',
                        '\x12',
                        get_current_millisecond_clamped(),
                        cid,
                        '\x08'
                    )
                    send_data_to_client(data_sent, cid)
                else:
                    print 'unknown event'

        # update client states to all
        if time.time() - last_state_sync > 1.0 / STATE_SYNC_RATE:
            last_state_sync = time.time()
            data_sent = ''
            state_count = 0
            for cid in clients:
                # testing condition for partial sync state
                if state_count > 20:
                    # break
                    pass
                if True:  # clients[cid].need_update:
                    state_count += 1
                    pos = clients[cid].pos
                    rot = clients[cid].rot
                    data_sent += pack(
                                # '<iiiiiii',
                                '<icccchccc',
                                cid,
                                clients[cid].grid_x,
                                clients[cid].grid_y,
                                pos[0], pos[1], pos[2],
                                rot[0], rot[1], rot[2]
                            )
                clients[cid].need_update = False
            if state_count > 0:
                data_sent = pack('<cii', '\x11', get_current_millisecond_clamped(), state_count) + data_sent
                for target_cid in clients:
                    send_data_to_client(data_sent, target_cid)

        # check connection timeout
        if False:  # game_model.game_status == GAME_STATUS.RUNNING:
            for cid in [ccid for ccid in clients]:
                if clients[cid].addr and time.time() - clients[cid].last_package_stamp > MAX_NO_RESPONSE:
                    print 'timeout. client', cid, 'connection closed'
                    clients.pop(cid, None)
                    if len(clients) == 0:
                        print 'all clients logged out'

        # check console input
        try:
            console_str = console_input.get(block=False)
            if console_str == 's':
                # start game
                print 'game start'
                data_sent = pack(
                    '<ciic',
                    '\x12',
                    get_current_millisecond_clamped(),
                    0,
                    '\x04'
                )
                broadcast_data(data_sent, sock_server, clients, [])
                game_model.game_status = GAME_STATUS.RUNNING
                pass
            elif console_str == 'e':
                # end game
                print 'end game'
                game_model.game_status = GAME_STATUS.NOT_START
            elif console_str == 'fake':
                # spawn fake clients
                for i in range(40):
                    to_spawn_cid = i
                    pack_data = pack(
                        '<ciici',
                        '\x12',
                        get_current_millisecond_clamped(),
                        to_spawn_cid,
                        '\x00',
                        1
                    )
                    on_client_join_game(pack_data, ('192.168.145.222', 1000 + i), to_spawn_cid, clients)
            elif console_str == 'show_clients':
                for cid in clients:
                    if clients[cid].addr:
                        print 'cid', cid
                    else:
                        print 'cid', cid, ', faked'
        except Queue.Empty, e:
            pass




