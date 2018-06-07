from command_server import *


class RoomServerBase(CommandServer):

    def __init__(self, server_name='room_server'):
        CommandServer.__init__(self, server_name)
        self.game_model_dict = {}    # read only
        self.client_state_dict = {}  # read only
        self.game_event_dict = {}
        self.client_states = {} # current clients in the room


class RoomServerFactory:

    def __init__(self):
        pass

    @classmethod
    def make_room_server(cls, game_model_config, client_state_config, game_event_config):
        """
        Factory method to make room server instance given game_model, client_state and game_event
        :param game_model_config:
        :param client_state_config:
        :param game_event_config:
        :return:
        """
        pass


if __name__ == '__main__':
    rs = RoomServerBase()
    rs.start_server()
