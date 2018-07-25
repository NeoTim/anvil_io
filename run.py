# running script to test server architect

from extensions.tinkr_garage.tinkr_garage_room import TinkrGarageRoom
from extensions.tinkr_garage.tinkr_garage_gate import TinkrGateServer


def main():

    rs_class = TinkrGarageRoom
    gs = TinkrGateServer(rs_class, ('0.0.0.0', 10000), 'tinkr_garage_gate')
    gs.start_server()


if __name__ == '__main__':
    main()