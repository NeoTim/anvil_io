from core.room_server_base import *


class TinkrGarageRoom(RoomServerBase):

    @app_client_state
    class GarageClientState:
        def __init__(self):
            self.pos = [0, 0, 0]
            self.rot = [0, 0, 0]

    def __init__(self, gate_server_ref, room_id, server_name):
        RoomServerBase.__init__(self, gate_server_ref, room_id, server_name)

    @on_command('handle_package')
    def handle_package(self, pkg):
        """
        server game logic
        :param pkg:
        :return:
        """
        # game logic here
        pass

    # def tick_client_update(self):
    #     pass

if __name__ == '__main__':
    rs = TinkrGarageRoom(None, 3, 'hh')
    rs.start_server()
    rs.run_command('add_client', 4)