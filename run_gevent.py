# running script to start gevent version of tinkr garage server

import time

from extensions.tinkr_garage.gevent_tinkr_garage_room import TinkrGarageRoom
from extensions.tinkr_garage.gevent_tinkr_garage_gate import TinkrGateServer


def main():

    rs_class = TinkrGarageRoom
    gs = TinkrGateServer(rs_class, ('0.0.0.0', 10000), 'tinkr_garage_gate')

    gs.create_room(666)
    gs.room_servers[666].run_command('set_storm_enabling', 0)

    time.sleep(0.5)

    gs.start_server()
'''
    # add fake clients to room 666
    while True:
        if 666 in gs.room_servers and len(gs.room_servers[666].client_infos) > 0:
            time.sleep(10)
            gs.room_servers[0].run_command('spawn_fake_clients', 50)
            break
'''

if __name__ == '__main__':
    main()
