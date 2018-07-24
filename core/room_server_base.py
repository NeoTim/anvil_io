from command_server import *
import time
import copy
import inspect
from struct import *


# room server structs dict
ROOM_SERVER_STRUCTS = {
    'client_game_event_regs': {},  # client game event id => event class, handler function
    'server_game_event_regs': {}   # server game event id => event class, handler function
}


# register client game event
def app_client_game_event(evt_class):
    if (not evt_class) or (not evt_class.event_id) or (evt_class.event_id in ROOM_SERVER_STRUCTS['client_game_event_regs']):
        print 'client game event register error'
        return evt_class
    ROOM_SERVER_STRUCTS['client_game_event_regs'][evt_class.event_id] = [evt_class, None]
    return evt_class


# register server game event
def app_server_game_event(evt_class):
    if (not evt_class) or (not evt_class.event_id) or (evt_class.event_id in ROOM_SERVER_STRUCTS['server_game_event_regs']):
        print 'server game event register error'
        return evt_class
    ROOM_SERVER_STRUCTS['server_game_event_regs'][evt_class.event_id] = [evt_class, None]
    return evt_class


# decorator to register client game event
def on_client_game_event(evt_class):
    def reg_decorator(func):
        if evt_class.event_id not in ROOM_SERVER_STRUCTS['client_game_event_regs']:
            print 'client game event "' + evt_class.__name__ + '" not found. handler register failed'
            raise KeyError
        ROOM_SERVER_STRUCTS['client_game_event_regs'][evt_class.event_id][1] = func
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapped_func
    return reg_decorator


# decorator to register client game event
def on_server_game_event(evt_class):
    def reg_decorator(func):
        if evt_class.event_id not in ROOM_SERVER_STRUCTS['server_game_event_regs']:
            print 'server game event "' + evt_class.__name__ + '" not found. handler register failed'
            raise KeyError
        ROOM_SERVER_STRUCTS['server_game_event_regs'][evt_class.event_id][1] = func
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapped_func
    return reg_decorator


class GameModelBase:
    def __init__(self, game_mode):
        self.game_mode = game_mode


class Packable:
    """
    class that can be serialized (transmitted through network)
    """
    def __init__(self):
        pass

    def pack(self):
        """
        struct => bytes
        :return:
        """
        raise NotImplementedError

    @classmethod
    def unpack(cls, packed_data):
        """
        bytes => struct
        read packed_data info into event instance
        :return:
        """
        raise NotImplementedError


class GameEvent(Packable):

    event_id = '\x00'
    """
        supported types:
            i = int (4 bytes)
            h = short (2 bytes)
            c = char (1 byte)
        representation format:
            'i' => int,
            'iii' => [int, int, int]
    """
    var_struct = []    # [(var name, var type), ..], ** the order matters **

    def __init__(self):
        Packable.__init__(self)
        self.time_stamp = 0     # time stamp of the event
        self.var = {}   # var name => var value, the dict to store event attributes
        for var_name, var_type in self.var_struct:
            if len(var_type) == 1:
                self.var[var_name] = None
            elif len(var_type) > 1:
                self.var[var_name] = [0] * len(var_type)

    def pack(self):
        """
        event_id not included ( same as unpack() )
        :return:
        """
        packed_data = ''
        for var_name, var_type in self.var_struct:
            if len(var_type) == 1:
                packed_data += pack('<' + var_type, self.var[var_name])
            elif len(var_type) > 1:
                for i in range(len(var_type)):
                    single_format = var_type[i]
                    packed_data += pack('<' + single_format, self.var[var_name][i])
        return packed_data

    def read_packed_data(self, var_type, read_iter, packed_data):
        """
        read var value with given read iterator and packed data
        return read value and read length
        :param var_type:
        :param read_iter:
        :param packed_data:
        :return:
        """
        value = None
        read_len = 0
        if var_type == 'i':
            value = unpack('<i', packed_data[read_iter:read_iter + 4])[0]
            read_len = 4
        elif var_type == 'h':
            value = unpack('<h', packed_data[read_iter:read_iter + 2])[0]
            read_len = 2
        elif var_type == 'c':
            value = unpack('<c', packed_data[read_iter:read_iter + 1])[0]
            read_len = 1
        return value, read_len

    @classmethod
    def unpack(cls, packed_data):
        evt = cls()
        read_iter = 0
        for var_name, var_type in cls.var_struct:
            if len(var_type) == 1:
                value, read_len = evt.read_packed_data(var_type, read_iter, packed_data)
                evt.var[var_name] = value
                read_iter += read_len
            elif len(var_type) > 1:
                print evt.var[var_name]
                for i in range(len(var_type)):
                    single_format = var_type[i]
                    value, read_len = evt.read_packed_data(single_format, read_iter, packed_data)
                    evt.var[var_name][i] = value
                    read_iter += read_len
        return evt


class ClientGameEvent(GameEvent):

    event_id = '\x00'

    def __init__(self):
        GameEvent.__init__(self)
        self.from_cid = None    # TODO: better with exception check


class ServerGameEvent(GameEvent):

    event_id = '\x00'

    def __init__(self):
        GameEvent.__init__(self)
        self.from_cid = None


class GameEventManager:

    # event id => event class, event handler (function)
    CLIENT_GAME_EVENTS = ROOM_SERVER_STRUCTS['client_game_event_regs']
    SERVER_GAME_EVENTS = ROOM_SERVER_STRUCTS['server_game_event_regs']

    def __init__(self, room_server_ref):
        self.room_server_ref = room_server_ref
        self.game_event_q = Queue.Queue(5000)

    def send_server_event(self, to_cid, evt):
        """ raise server event to client """
        data_to_send = pack('<ic', evt.from_cid, evt.event_id) + evt.pack()
        gate_server_ref = self.room_server_ref.gate_server_ref
        gate_server_ref.run_command(
            'send_package',
            [to_cid],
            data_to_send,
            '\x12'
        )

    def broadcast_server_event(self, evt, exclude=list()):
        """ broadcast server event to clients """
        target_cids = []
        for target_cid in self.room_server_ref.client_infos:
            if target_cid not in exclude:
                target_cids.append(target_cid)
        data_to_send = pack('<ic', evt.from_cid, evt.event_id) + evt.pack()
        if evt.event_id == '\x09':
            print 'radius sent:', unpack('<i', data_to_send[9:13])[0]   # TESTING
        self.room_server_ref.gate_server_ref.run_command(
            'send_package',
            target_cids,
            data_to_send,
            '\x12'
        )
        pass

    def handle_event(self, evt):
        # interface to handle events
        if isinstance(evt, ClientGameEvent):
            evt_class = evt.__class__
            if evt_class.event_id in self.CLIENT_GAME_EVENTS:
                print 'handle client event "' + evt_class.__name__ + '"'
                self.CLIENT_GAME_EVENTS[evt_class.event_id][1](self.room_server_ref, evt)
            else:
                print 'event "' + evt_class.__name__ + '" not found'
        elif isinstance(evt, ServerGameEvent):
            evt_class = evt.__class__
            if evt_class.event_id in self.SERVER_GAME_EVENTS:
                print 'handle server event "' + evt_class.__name__ + '"'
                self.SERVER_GAME_EVENTS[evt_class.event_id][1](self.room_server_ref, evt)
            else:
                print 'event "' + evt_class.__name__ + '" not found'
        pass


class RoomServerBase(CommandServer):

    CLIENT_UPDATE_RATE = 15     # 20fps

    class ClientState:
        """ class of client state """
        def __init__(self):
            pass

    class GameModel:
        """ class of game model """
        def __init__(self):
            pass

    class ClientInfo:
        """ info to record each client communication condition """
        def __init__(self, client_state):
            self.state = client_state   # instance of ClientState
            self.state_latest_stamp = 0    # timestamp of latest state package

    def __init__(self, gate_server_ref, room_id, server_name='room_server'):
        CommandServer.__init__(self, server_name)
        self.room_id = room_id
        self.gate_server_ref = gate_server_ref
        self.last_client_sync = time.time()
        self.client_infos = {}     # current client states. client id => client info
        self.game_event_manager = GameEventManager(self)

    @on_command('add_client')
    def add_client(self, cid):
        if cid not in self.client_infos:
            new_client_state = self.ClientState()   # ROOM_SERVER_STRUCTS['client_state']()
            new_client_info = self.ClientInfo(new_client_state)
            self.client_infos[cid] = new_client_info
            print 'client', cid, 'entered room', self.room_id
        else:
            print 'client', cid, 'already in room', self.room_id

    @on_command('remove_client')
    def remove_client(self, cid):
        if cid in self.client_infos:
            self.client_infos.pop(cid, None)
            print 'client', cid, 'leaves room', self.room_id
        else:
            print 'client', cid, 'not in room', self.room_id, '. no client removed from room'

    def pack_client_state(self, cid):
        raise NotImplementedError

    def unpack_client_state(self, pkg_data):
        raise NotImplementedError

    def tick_client_state_sync(self):
        """
        sync client states to all
        | op_code | seq | state_count | state(s)
             1       4         4           n
        state = | cid | packed client state |
        :return:
        """
        try:
            if time.time() - self.last_client_sync > 1.0 / self.CLIENT_UPDATE_RATE:
                self.last_client_sync = time.time()
                client_state_count = 0
                data_to_send = ''
                for cid in self.client_infos:
                    if client_state_count > 50:
                        # TODO: remove this check
                        break
                    data_to_send += pack('<i', cid) + self.pack_client_state(cid)
                    client_state_count += 1
                data_to_send = pack('<i', client_state_count) + data_to_send
                if client_state_count > 0:
                    # broadcast client states
                    target_cids = []
                    for target_cid in self.client_infos:
                        if self.client_infos[target_cid].state.is_faked:
                            # print 'no data sent to AI'
                            # continue
                            pass
                        target_cids.append(target_cid)
                    self.gate_server_ref.run_command(
                        'send_package',
                        target_cids,
                        data_to_send,
                        '\x11'
                    )
        except Exception, e:
            print e
            print 'sync states error'

    def update_client_state(self, cid, new_state):
        """ method to update client state given new state data"""
        # TODO: try not new client state
        self.client_infos[cid].state = new_state

    def handle_client_state_package(self, pkg):
        """ | op_code | seq | cid | state """
        # (op_code, seq, cid) = unpack('<cii', pkg.data[0:9])
        cid = unpack('<i', pkg.data[5:9])[0]
        new_state = self.unpack_client_state(pkg.data)
        # update client state
        self.update_client_state(cid, new_state)

    def handle_game_event_package(self, pkg):
        """ | op_code | seq | cid | eid | event data """
        (op_code, seq, cid, event_id) = unpack('<ciic', pkg.data[0:10])
        evt_class = self.game_event_manager.CLIENT_GAME_EVENTS[event_id][0]
        evt = evt_class.unpack(pkg.data[10:])
        evt.from_cid = cid  # from client id
        evt.time_stamp = seq    # timestamp of the event
        # put event into queue
        self.game_event_manager.game_event_q.put(evt)

    @on_command('handle_package')
    def handle_package(self, pkg):
        """
        | op_code | seq | other data ...
             1       4        n
        op_code structure:
            0000xxxx = admin
                0000 0001 = login
                0000 0010 = logout
            0001xxxx = game (state / event)
                0001 0001 = state
                    op_code | seq | cid | ...
                       1       4     4
                0001 0010 = event
                    op_code | seq | cid | event_id | ...
                       1       4     4       1
                    event_id: 0 == login, 1 == logout, 2 == game start
            0010xxxx = sys info
        :param pkg:
        :return:
        """
        data = pkg.data
        if not data or len(data) < 9:
            print 'too small package size. package discarded.'
        op_code = data[0]
        if op_code <= '\x0f':   # admin package
            pass
        elif op_code <= '\x1f':     # game package
            # TODO: update client state or handle game event
            if op_code == '\x11':   # state update
                self.handle_client_state_package(pkg)
            elif op_code == '\x12':   # game event
                self.handle_game_event_package(pkg)
        elif op_code <= '\x2f':     # sys info package
            pass

    def tick_game_event(self):
        # solve and clear the game event queue
        try:
            while not self.game_event_manager.game_event_q.empty():
                evt = self.game_event_manager.game_event_q.get(timeout=0.01)
                self.game_event_manager.handle_event(evt)
                self.game_event_manager.game_event_q.task_done()
        except Exception, e:
            print e

    def tick_extra(self):
        pass

    def loop(self):
        try:
            while True:
                self.tick_command()
                self.tick_game_event()
                self.tick_client_state_sync()
                self.tick_extra()
                pass
        except Exception, e:
            print e
        finally:
            print 'room -', self.room_id, 'ends'

    def start_server(self):
        try:
            self.server_thread = threading.Thread(target=self.loop)
            print 'room -', self.room_id, 'starts'
            self.server_thread.start()
        except Exception, e:
            print e

example_game_model_config = {
    'MODE': 'NORMAL',
    'VAR': {
        'var1': 0,
        'var2': 'var2',
        'var3': 2.0
    }
}
example_client_state_config = {
    'VAR': {
        'var1': 0,
        'var2': 'var2',
        'var3': [2.0, 2.0, 2.0]
    }
}


def room_server_class(cls):
    return cls


# class RoomServerFactory:
#
#     def __init__(self):
#         pass
#
#     @classmethod
#     def make_game_model_class(cls, game_model_config):
#         class AppGameModel(GameModelBase):
#             def __init__(self):
#                 game_mode = game_model_config['MODE']
#                 GameModelBase.__init__(self, game_mode)
#                 for var in game_model_config['VAR']:
#                     self.__dict__[var] = game_model_config['VAR'][var]
#         return AppGameModel
#
#     @classmethod
#     def make_client_state_class(cls, client_state_config):
#         class AppClientState(ClientStateBase):
#             def __init__(self):
#                 ClientStateBase.__init__(self)
#                 for var in client_state_config['VAR']:
#                     self.__dict__[var] = client_state_config['VAR'][var]
#         return AppClientState
#
#     @classmethod
#     def make_room_server_class(cls, game_model_config, client_state_config, game_event_config):
#         """
#         Factory method to make room server instance given game_model, client_state and game_event
#         :param game_model_config:
#         :param client_state_config:
#         :param game_event_config:
#         :return:
#         """
#         class AppRoomServer(RoomServerBase):
#             game_model_class = RoomServerFactory.make_game_model_class(game_model_config)
#             client_state_class = RoomServerFactory.make_client_state_class(client_state_config)
#             # TODO: game event manager / handler
#
#             def __init__(self, gate_server_ref, room_id, server_name='app_room_server'):
#                 RoomServerBase.__init__(self, gate_server_ref, room_id, server_name)
#         return AppRoomServer


if __name__ == '__main__':
    # rs_class = RoomServerFactory.make_room_server_class(0, 0, 0)
    # rs = rs_class(example_game_model_config, example_client_state_config)
    # rs.start_server()
    # rs.run_command('handle_package', 3)
    pass
