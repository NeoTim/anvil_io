from gate_server import GateServer
from lobby_server import LobbyServer

if __name__ == '__main__':
    try:
        lobby = LobbyServer()
        gate_server = GateServer(lobby)
        gate_server.start()
    except Exception, e:
        print e
