import socket
from struct import *
import time
import random
from multiprocessing import Process
from threading import Thread


def get_current_millisecond_clamped():
    cur_stamp = time.time()
    cur_ms = int(cur_stamp * 1000) % 604800000
    return cur_ms


class ClientState:
    def __init__(self):
        self.grid_xy = ['\x00', '\x00']
        self.pos = ['\x00', '\x00', 0]
        self.rot = ['\x00', '\x00', '\x00']


class ClientAgent(Thread):

    STATE_SEND_RATE = 10
    PING_RATE = 0.1
    MAX_SERVER_NO_RESPONSE = 30
    LOGIN_REQUEST_WAIT = 10
    JOIN_GAME_REQUEST_WAIT = 10

    # states of this state machine
    class AgentState:
        NOT_LOGGED_IN = 0
        LOGGED_IN = 1
        IN_ROOM = 2
        GAME_RUNNING = 3

    def __init__(self, cid, sever_addr, target_room_id):
        Thread.__init__(self)
        self.agent_state = self.AgentState.NOT_LOGGED_IN
        self.cid = cid
        self.sock = None
        self.server_addr = sever_addr
        self.target_room_id = target_room_id
        self.client_state = ClientState()
        self.init_client_state()

        self.last_send_state_time = 0
        self.last_ping_time = 0
        self.last_server_response_time = time.time()
        self.last_login_request_time = 0
        self.last_join_game_request_time = 0
        self.last_start_game_request_time = 0

    def init_client_state(self):
        for i in range(5):
            rand_val = random.randint(100, 120)
            packed_val = pack('<i', rand_val)[0]
            if i == 0:
                self.client_state.grid_xy[0] = packed_val
            if i == 1:
                self.client_state.grid_xy[1] = packed_val
            if i == 2:
                self.client_state.pos[0] = packed_val
            if i == 3:
                self.client_state.pos[1] = packed_val
            if i == 4:
                self.client_state.pos[2] = 10000

    def login(self):
        print 'client', self.cid, 'login requested'
        self.sock.sendto(
            pack(
                '<ciicii',
                '\x12',
                get_current_millisecond_clamped(),
                self.cid,
                '\x07',
                2,
                999
            ),
            self.server_addr
        )

    def join_game(self, room_id=-1):
        print 'client', self.cid, 'join room', room_id, 'requested'
        self.sock.sendto(
            pack(
                '<ciicii',
                '\x12',
                get_current_millisecond_clamped(),
                self.cid,
                '\x00',
                1,
                room_id
            ),
            self.server_addr
        )

    def start_game(self):
        print 'client', self.cid, 'start game requested'
        self.sock.sendto(
            pack(
                '<ciicicccchccc',
                '\x12',
                get_current_millisecond_clamped(),
                self.cid,
                '\x0c',
                1,
                self.client_state.grid_xy[0], self.client_state.grid_xy[1],
                self.client_state.pos[0], self.client_state.pos[1], self.client_state.pos[2],
                self.client_state.rot[0], self.client_state.rot[1], self.client_state.rot[2]
            ),
            self.server_addr
        )
        pass

    def send_state(self):
        dlen = self.sock.sendto(
            pack(
                '<ciicccchccc',
                '\x11',
                get_current_millisecond_clamped(),
                self.cid,
                self.client_state.grid_xy[0], self.client_state.grid_xy[1],
                self.client_state.pos[0], self.client_state.pos[1], self.client_state.pos[2],
                self.client_state.rot[0], self.client_state.rot[1], self.client_state.rot[2]
            ),
            self.server_addr
        )
        # print dlen, 'sent'

    def ping(self):
        self.sock.sendto(
            pack(
                '<ciic',
                '\x12',
                get_current_millisecond_clamped(),
                self.cid,
                '\x06'
            ),
            self.server_addr
        )

    def tick_game_logic(self):
        grid_x = unpack('<h', self.client_state.grid_xy[0] + '\x00')[0]
        grid_y = unpack('<h', self.client_state.grid_xy[1] + '\x00')[0]
        grid_x += random.randint(-1, 1)
        grid_y += random.randint(-1, 1)
        if grid_x > 140:
            grid_x = 140
        if grid_x < 80:
            grid_x = 80
        if grid_y > 140:
            grid_y = 140
        if grid_y < 80:
            grid_y = 80
        self.client_state.grid_xy[0] = pack('<h', grid_x)[0]
        self.client_state.grid_xy[1] = pack('<h', grid_y)[0]

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        while True:

            # agent state switch
            if self.agent_state == self.AgentState.NOT_LOGGED_IN:
                if time.time() - self.last_login_request_time > self.LOGIN_REQUEST_WAIT:
                    self.last_login_request_time = time.time()
                    self.login()
            if self.agent_state == self.AgentState.LOGGED_IN:
                if time.time() - self.last_join_game_request_time > self.JOIN_GAME_REQUEST_WAIT:
                    self.last_join_game_request_time = time.time()
                    self.join_game(self.target_room_id)
                if time.time() - self.last_ping_time > 1.0 / self.PING_RATE:
                    self.ping()
                    self.last_ping_time = time.time()
            if self.agent_state == self.AgentState.IN_ROOM:
                if time.time() - self.last_start_game_request_time > 5:
                    self.last_start_game_request_time = time.time()
                    self.start_game()
            if self.agent_state == self.AgentState.GAME_RUNNING:
                if time.time() - self.last_send_state_time > 1.0 / self.STATE_SEND_RATE:
                    self.send_state()
                    self.last_send_state_time = time.time()
                self.tick_game_logic()

            # recv data
            try:
                data, addr = self.sock.recvfrom(1024)
                if data:
                    self.last_server_response_time = time.time()
                    op_code = unpack('<c', data[0])[0]
                    if op_code == '\x11':   # state package
                        pass
                    if op_code == '\x12':   # event package
                        event_id = unpack('<c', data[9])[0]
                        if event_id == '\x0a':  # login response
                            login_res = unpack('<c', data[10])[0]
                            if True:  # login_res == '\x00':
                                self.agent_state = self.AgentState.LOGGED_IN
                                print 'client', self.cid, 'logged in'
                        if event_id == '\x0e':  # game matched
                            self.agent_state = self.AgentState.IN_ROOM
                            print 'client', self.cid, 'joined game'
                        if event_id == '\x04':  # start game
                            self.agent_state = self.AgentState.GAME_RUNNING
                            print 'client', self.cid, 'starts game'
            except Exception, e:
                pass

            # logout self if server no response
            if self.agent_state != self.AgentState.NOT_LOGGED_IN:
                if time.time() - self.last_server_response_time > self.MAX_SERVER_NO_RESPONSE:
                    self.agent_state = self.AgentState.NOT_LOGGED_IN
                    print 'server timed out. logged out.'


def main():
    import threading
    import multiprocessing

    SERVER_IP = '192.168.145.39'  # '167.99.169.64'
    SERVER_PORT = 10000
    server_addr = (SERVER_IP, SERVER_PORT)

    NUM_CLIENT = 70  # number of AI to spawn
    TARGET_ROOM_ID = 666    # target room id, -1 == auto
    for i in range(NUM_CLIENT):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_agent = ClientAgent(0 + i, server_addr, TARGET_ROOM_ID)
        client_agent.start()
        time.sleep(0.01)

if __name__ == '__main__':
    main()
