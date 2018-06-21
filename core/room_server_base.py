from command_server import *
import time
from core.network.net_package import NetPackage
import copy
import inspect


# room server structs dict( game_model, client_state )
ROOM_SERVER_STRUCTS = {
    'client_state': None,
    'game_model': None,
    'client_game_event_funcs': {},  # client game event class => handler function
    'server_game_event_funcs': {}   # server game event class => handler function
}


# # decorator to register client state
# def app_client_state(cls):
#     ROOM_SERVER_STRUCTS['client_state'] = cls
#     return cls
#
#
# # decorator to register game model
# def app_game_model(cls):
#     ROOM_SERVER_STRUCTS['game_model'] = cls
#     return cls


# register client game event
def app_client_game_event(evt_class):
    ROOM_SERVER_STRUCTS['client_game_event_funcs'][evt_class] = None
    return evt_class


# register server game event
def app_server_game_event(evt_class):
    ROOM_SERVER_STRUCTS['server_game_event_funcs'][evt_class] = None
    return evt_class


# decorator to register client game event
def on_client_game_event(evt_class):
    def reg_decorator(func):
        if evt_class not in ROOM_SERVER_STRUCTS['client_game_event_funcs']:
            print 'client game event "' + evt_class.__name__ + '" not found. handler register failed'
            raise KeyError
        ROOM_SERVER_STRUCTS['client_game_event_funcs'][evt_class] = func
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapped_func
    return reg_decorator


# decorator to register client game event
def on_server_game_event(evt_class):
    def reg_decorator(func):
        if evt_class not in ROOM_SERVER_STRUCTS['server_game_event_funcs']:
            print 'server game event "' + evt_class.__name__ + '" not found. handler register failed'
            raise KeyError
        ROOM_SERVER_STRUCTS['server_game_event_funcs'][evt_class] = func
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapped_func
    return reg_decorator


class GameModelBase:
    def __init__(self, game_mode):
        self.game_mode = game_mode


class ClientStateBase:
    def __init__(self):
        pass


class GameEvent:
    def __init__(self):
        pass


class ClientGameEvent(GameEvent):
    def __init__(self):
        GameEvent.__init__(self)


class ServerGameEvent(GameEvent):
    def __init__(self):
        GameEvent.__init__(self)


class GameEventManager:

    CLIENT_GAME_EVENTS = ROOM_SERVER_STRUCTS['client_game_event_funcs']
    SERVER_GAME_EVENTS = ROOM_SERVER_STRUCTS['server_game_event_funcs']

    def __init__(self, room_server_ref):
        self.room_server_ref = room_server_ref
        self.game_event_q = Queue.Queue()

    def broadcast_event(self, evt, exclude=list()):
        """ broadcast server event to clients """
        pass

    def handle_event(self, evt):
        # TODO: handle game event
        if isinstance(evt, ClientGameEvent):
            evt_class = evt.__class__
            if evt_class in self.CLIENT_GAME_EVENTS:
                self.CLIENT_GAME_EVENTS[evt_class](self.room_server_ref, evt)
            else:
                print 'event "' + evt_class.__name__ + '" not found'
        elif isinstance(evt, ServerGameEvent):
            evt_class = evt.__class__
            if evt_class in self.SERVER_GAME_EVENTS:
                self.SERVER_GAME_EVENTS[evt_class](self.room_server_ref, evt)
            else:
                print 'event "' + evt_class.__name__ + '" not found'
        pass


class RoomServerBase(CommandServer):

    CLIENT_UPDATE_RATE = 30     # 30fps

    class ClientState:
        """ class of client state """
        def __init__(self):
            pass

    class GameModel:
        """ class of game model """
        def __init__(self):
            pass

    def __init__(self, gate_server_ref, room_id, server_name='room_server'):
        CommandServer.__init__(self, server_name)
        self.room_id = room_id
        self.gate_server_ref = gate_server_ref
        self.last_client_sync = time.time()
        self.client_states = {}     # current client states. client id => app client state
        self.game_event_manager = GameEventManager(self)

    @on_command('add_client')
    def add_client(self, cid):
        if cid not in self.client_states:
            new_client_state = self.ClientState()   # ROOM_SERVER_STRUCTS['client_state']()
            self.client_states[cid] = new_client_state
            print 'client', cid, 'entered room', self.room_id
        else:
            print 'client', cid, 'already in room', self.room_id

    @on_command('remove_client')
    def remove_client(self, cid):
        if cid in self.client_states:
            self.client_states.pop(cid, None)
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
        :return:
        """
        try:
            if time.time() - self.last_client_sync > self.CLIENT_UPDATE_RATE:
                self.last_client_sync = time.time()
                for cid in self.client_states:
                    pkg_data = self.pack_client_state(cid)
                    for target_cid in self.client_states:
                        if target_cid != cid:
                            self.gate_server_ref.run_command(
                                'send_package',
                                target_cid,
                                pkg_data,
                                NetPackage.PackageType.GAME
                            )
        except Exception, e:
            print e

    def handle_client_state_package_data(self, pkg_data):
        pass

    def unpack_client_game_event(self, pkg_data):
        pass

    def handle_game_event_package_data(self, pkg_data):
        c_game_event = self.unpack_client_game_event(pkg_data)
        # TODO: push client game event to event manager's event queue

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
                0001 0010 = event
            0010xxxx = sys info
        :param pkg:
        :return:
        """
        data = pkg.data
        if not data or len(data) < 5:
            print 'too small package size. package discarded.'
        op_code = data[0]
        if op_code <= '\x0f':   # admin package
            pass
        elif op_code <= '\x1f':     # game package
            # TODO: update client state or handle game event
            if op_code == '\x11':   # state update
                self.handle_client_state_package_data(data)
            elif op_code == '\x12':   # game event
                self.handle_game_event_package_data(data)
        elif op_code <= '\x2f':     # sys info package
            pass

    def tick_game_event(self):
        # solve and clear the game event queue
        try:
            while not self.game_event_manager.game_event_q.empty():
                evt = self.game_event_manager.game_event_q.get(block=False)
                self.game_event_manager.handle_event(evt)
        except Exception, e:
            print e

    def loop(self):
        try:
            while True:
                self.tick_command()
                self.tick_game_event()
                self.tick_client_state_sync()
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
