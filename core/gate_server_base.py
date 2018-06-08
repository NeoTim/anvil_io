from command_server import *
from room_server_base import RoomServerBase


class ClientConnection:
    """
    client connection model
    """
    MAX_NO_RESPONSE = 10    # max seconds with no response from client before disconnect it

    def __init__(self, sock_c=None, r_ip='', r_port=0):
        self.sock_c = sock_c
        self.seq = 0
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.at_room = -1


# class RoomInfo:
#     """
#     Room information to watch room
#     """
#     def __init__(self, rid, room_server_ref):
#         self.rid = rid
#         self.room_server_ref = room_server_ref


class GateServerBase(CommandServer):

    def __init__(self, room_server_class, server_name='gate_server'):
        CommandServer.__init__(self, server_name)
        self.client_connections = {}
        self.room_server_class = room_server_class
        self.room_servers = {}  # room servers ref

    def create_room(self, rid=None):
        res_rid = 0
        if rid and rid >= 0:
            res_rid = rid
        while res_rid in self.room_servers:
            res_rid += 1
        new_room_server = self.room_server_class(self, res_rid)
        self.room_servers[rid] = new_room_server
        # run room manager
        new_room_server.start_server()
        return new_room_server

    def assign_room(self, cid, pkg, rid=-1):
        room_id = 0     # always 0 for now
        if rid >= 0:
            room_id = rid
        target_room = None
        if room_id not in self.room_servers:
            target_room = self.create_room(room_id)
        else:
            target_room = self.room_servers[room_id]
        if not target_room:
            print 'room error. no room available'
        else:
            if cid not in self.client_connections:
                print 'client not logged in'
            elif self.client_connections[cid].at_room >= 0:
                print 'client already in room ', self.client_connections[cid].at_room
            else:
                print 'pass client', cid, 'to room', room_id
                target_room.run_command('add_client', cid, pkg.data)
                # self.send_message_content(
                #     {
                #         'add_client': cid,
                #         'data': pkg.data
                #     },
                #     target_room.manager
                # )
                self.client_connections[cid].at_room = room_id


if __name__ == '__main__':
    import room_server_base
    # CONFIG.get_room_server_class()
    rs_class = room_server_base.RoomServerFactory.make_room_server_class(0, 0, 0)
    gs = GateServerBase(rs_class)
    gs.start_server()
