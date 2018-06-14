from command_server import *
import time
from core.network.net_package import NetPackage
import copy


# room server structs dict( game_model, client_state )
ROOM_SERVER_STRUCTS = {
    'client_state': None,
    'game_model': None,
    'game_event_funcs': {}  # event_name => handler function
}


# decorator to register client state
def app_client_state(cls):
    ROOM_SERVER_STRUCTS['client_state'] = cls
    return cls


# decorator to register game model
def app_game_model(cls):
    ROOM_SERVER_STRUCTS['game_model'] = cls
    return cls


# decorator to register game event
def on_game_event(evt_name):
    def reg_decorator(func):
        # TODO: verify the server_class
        ROOM_SERVER_STRUCTS['game_event_funcs'][evt_name] = func
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


class GameEventManagerBase:
    def __init__(self):
        pass


class RoomServerBase(CommandServer):

    CLIENT_UPDATE_RATE = 30     # 30fps

    def __init__(self, gate_server_ref, room_id, server_name='room_server'):
        CommandServer.__init__(self, server_name)
        self.room_id = room_id
        self.gate_server_ref = gate_server_ref
        self.last_client_sync = time.time()
        self.client_states = {}     # current client states. client id => app client state

    @on_command('add_client')
    def add_client(self, cid):
        if cid not in self.client_states:
            new_client_state = ROOM_SERVER_STRUCTS['client_state']()
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

    def handle_client_state_package_data(self, pkg_data):
        pass

    def handle_game_event_package_data(self, pkg_data):
        pass

    @on_command('handle_package')
    def handle_package(self, pkg):
        """
        | op_code | seq | other data ...
             1       4        n
        op_code structure:
            00xxxxxx = admin
            01xxxxxx = game (state / event)
                010xxxxx = state
                011xxxxx = event
            10xxxxxx = sys info
        :param pkg:
        :return:
        """
        data = pkg.data
        if not data or len(data) < 5:
            print 'too small package size. package discarded.'
        op_code = data[0]
        if op_code <= '\x3f':   # admin package
            pass
        elif op_code <= '\x7f':     # game package
            # TODO: update client state or handle game event
            if op_code <= '\x4f':   # state update
                self.handle_client_state_package_data(data)
            else:   # game event
                self.handle_game_event_package_data(data)
        elif op_code <= '\xbf':     # sys info package
            pass

    def loop(self):
        try:
            while True:
                self.tick_command()
                self.tick_client_state_sync()
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

example_net_funcs = {

}


def room_server_class(cls):
    return cls


class RoomServerFactory:

    def __init__(self):
        pass

    @classmethod
    def make_game_model_class(cls, game_model_config):
        class AppGameModel(GameModelBase):
            def __init__(self):
                game_mode = game_model_config['MODE']
                GameModelBase.__init__(self, game_mode)
                for var in game_model_config['VAR']:
                    self.__dict__[var] = game_model_config['VAR'][var]
        return AppGameModel

    @classmethod
    def make_client_state_class(cls, client_state_config):
        class AppClientState(ClientStateBase):
            def __init__(self):
                ClientStateBase.__init__(self)
                for var in client_state_config['VAR']:
                    self.__dict__[var] = client_state_config['VAR'][var]
        return AppClientState

    @classmethod
    def make_room_server_class(cls, game_model_config, client_state_config, game_event_config):
        """
        Factory method to make room server instance given game_model, client_state and game_event
        :param game_model_config:
        :param client_state_config:
        :param game_event_config:
        :return:
        """
        class AppRoomServer(RoomServerBase):
            game_model_class = RoomServerFactory.make_game_model_class(game_model_config)
            client_state_class = RoomServerFactory.make_client_state_class(client_state_config)
            # TODO: game event manager / handler

            def __init__(self, gate_server_ref, room_id, server_name='app_room_server'):
                RoomServerBase.__init__(self, gate_server_ref, room_id, server_name)
        return AppRoomServer


if __name__ == '__main__':
    rs_class = RoomServerFactory.make_room_server_class(0, 0, 0)
    rs = rs_class(example_game_model_config, example_client_state_config)
    rs.start_server()
    rs.run_command('handle_package', 3)

    # import time
    #
    # def get7(num):
    #     res = 0
    #     for i in range(6):
    #         res += 10**i * (num % 10)
    #         num /= 10
    #     return res
    #
    # n = time.time()
    # nn = int(n)
    # print nn
    # nn = get7(nn)
    # import math
    # frc, whole = math.modf(n)
    # print nn*1000 + int(frc * 1000)
