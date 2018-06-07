from command_server import *
from room_server_base import RoomServerBase


class ClientConnection:
    """
    Client connection model
    """
    MAX_NO_RESPONSE = 10    # max seconds with no response from client before disconnect it

    def __init__(self, sock_c=None, r_ip='', r_port=0):
        self.sock_c = sock_c
        self.seq = 0
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.at_room = -1


class RoomInfo:
    """
    Room information to watch room
    """
    def __init__(self, rid, room_server_ref):
        self.rid = rid
        self.room_server_ref = room_server_ref


class GateServerBase(CommandServer):

    def __init__(self, server_name='gate_server'):
        CommandServer.__init__(self, server_name)
        pass


if __name__ == '__main__':
    gs = GateServerBase()
    gs.start_server()
