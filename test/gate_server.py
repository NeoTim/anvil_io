import socket
import sys
import threading
from lobby_server import LobbyServer

# config
CONFIG = {
    'SERVER_IP': '192.168.137.1',
    'GATE_PORT': 10000
}


class GateServer(threading.Thread):

    def __init__(self, lobby):
        super(GateServer, self).__init__()
        self.lobby_ref = lobby

    def pass_to_lobby(self, sock_c):
        self.lobby_ref.accept_client(sock_c)

    def run(self):
        # server socket
        tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_ip = CONFIG['SERVER_IP']
            if len(sys.argv) > 1:
                server_ip = sys.argv[1]
            tcpsock.bind((server_ip, CONFIG['GATE_PORT']))
            tcpsock.listen(1024)
            print 'car gate server listening at: ', tcpsock.getsockname()
            while True:
                (sock_client, addr_clinet) = tcpsock.accept()
                print 'client socket from ', addr_clinet
                print 'pass to lobby'
                # pass to lobby server
                self.pass_to_lobby(sock_client)
        finally:
            print 'car gate server closed'
            tcpsock.close()
