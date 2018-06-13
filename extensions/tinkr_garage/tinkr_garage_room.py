from core.room_server_base import *


class TinkrGarageRoom(RoomServerBase):

    @app_client_state
    class GarageClientState:
        def __init__(self):
            self.pos = [0, 0, 0]
            self.rot = [0, 0, 0]

    def __init__(self, gate_server_ref, room_id, server_name):
        RoomServerBase.__init__(self, gate_server_ref, room_id, server_name)

    #def pack_client_state(self, cid):
    #    print 'my pack'

if __name__ == '__main__':
    rs = TinkrGarageRoom(None, 3, 'hh')
    rs.start_server()
    from core.network.net_package import NetPackage
    pkg = NetPackage('?', '3.3.3.3', 10000)
    rs.run_command('handle_package', pkg)