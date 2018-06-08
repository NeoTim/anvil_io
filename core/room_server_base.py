from command_server import *
import copy


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

    game_model_class = None
    client_state_class = None

    def __init__(self, gate_server_ref, room_id, server_name='room_server'):
        CommandServer.__init__(self, server_name)
        self.room_id = room_id
        self.gate_server_ref = gate_server_ref
        # self.game_model_dict = {}    # read only
        # self.client_state_dict = {}  # read only
        # self.game_event_dict = {}
        self.client_states = {}     # current client states. client id => app client state

    # @on_command('add_client')
    # def add_client(self, cid):
    #     pass
    #
    # @on_command('remove_client')
    # def remove_client(self, cid):
    #     pass

    def tick_client_update(self):
        """
        update clients to all
        :return:
        """
        pass

    def loop(self):
        while True:
            self.tick_command()
            self.tick_client_update()

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
    # rs_class = RoomServerFactory.make_room_server_class(0, 0, 0)
    # rs = rs_class(example_game_model_config, example_client_state_config)
    # rs.start_server()
    # rs.run_command('handle_package', 3)

    import time

    def get7(num):
        res = 0
        for i in range(6):
            res += 10**i * (num % 10)
            num /= 10
        return res

    n = time.time()
    nn = int(n)
    print nn
    nn = get7(nn)
    import math
    frc, whole = math.modf(n)
    print nn*1000 + int(frc * 1000)
