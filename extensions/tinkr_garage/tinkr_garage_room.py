from core.room_server_base import *


@app_client_game_event
class EventClientShoot(ClientGameEvent):
    def __init__(self):
        ClientGameEvent.__init__(self)
        self.start_pos = [1, 0, 1]


class TinkrGarageRoom(RoomServerBase):

    class ClientState:
        def __init__(self):
            self.pos = [0, 0, 0]
            self.rot = [0, 0, 0]

    def __init__(self, gate_server_ref, room_id, server_name='tinkr_room'):
        RoomServerBase.__init__(self, gate_server_ref, room_id, server_name)

    @on_client_game_event(EventClientShoot)
    def on_client_shoot(self, evt):
        print evt

    #def pack_client_state(self, cid):
    #    print 'my pack'

if __name__ == '__main__':
    rs = TinkrGarageRoom(None, 3, 'hh')
    rs.start_server()
    from core.network.net_package import NetPackage
    pkg = NetPackage('?', '3.3.3.3', 10000)
    rs.run_command('handle_package', pkg)
    rs.run_command('add_client', 4)

    shoot_evt = EventClientShoot()
    rs.game_event_manager.handle_event(shoot_evt)