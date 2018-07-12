# running script to test server architect

from extensions.tinkr_garage.tinkr_garage_room import TinkrGarageRoom
from core.gate_server_base import GateServerBase


def main():

    class TinkrGateServer(GateServerBase):
        def __init__(self, room_server_class, bind_addr, server_name):
            GateServerBase.__init__(self, room_server_class, bind_addr, server_name)

    # rs_class = room_server_base.RoomServerFactory.make_room_server_class(0, 0, 0)
    rs_class = TinkrGarageRoom
    gs = GateServerBase(rs_class)
    gs.start_server()


if __name__ == '__main__':
    main()