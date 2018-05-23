from message_server import MessageServer
from client_communicator import ClientCommunicator
import threading
import socket
import config
from struct import *


class ClientConnection:
    def __init__(self, sock_c=None, r_ip='', r_port=0):
        self.sock_c = sock_c
        self.remote_ip = r_ip
        self.remote_port = r_port


class NetPackage:
    def __init__(self, data, ip, port):
        self.data = data
        self.ip = ip
        self.port = port


class GateServer(MessageServer):

    """
    gate server to accept client initial requests
    """

    class CommunicatorThread(threading.Thread):
        def __init__(self, gate_server_ref):
            super(GateServer.CommunicatorThread, self).__init__()
            self.gate_server_ref = gate_server_ref

        def run(self):
            print 'communicator thread ' + self.getName() + ' start'

    def __init__(self, m_name):
        MessageServer.__init__(self, m_name)

        # socket to accept new connection
        self.sock_accepting = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.init_accepting_socket()

        # NOT SURE IF EACH CONNECTION SHOULD HAVE SEPARATE SOCKET
        # communicator threads to receive packages
        # self.communicator_threads = [GateServer.CommunicatorThread(self) for ti in range(10)]

        # communicator
        self.gate_communicator = ClientCommunicator(sock=self.sock_accepting)

        # current client connections
        self.client_connections = {}   # client id : client connection
        self.client_connections_lock = threading.RLock()

        # ensure the handle message function is implemented
        try:
            self.handle_message(None)
        finally:
            pass

    def init_accepting_socket(self):
        # bind accepting socket to (gate ip : port)
        self.sock_accepting.bind((config.GATE_IP, config.GATE_PORT))
        self.sock_accepting.settimeout(0.1)

    def login_client(self, cid, token):
        pass

    def logout_client(self, cid):
        pass

    def handle_message(self, msg):
        """
        handle received packages
        routing packages to other servers / managers
        :param msg:
        :return:
        """
        print 'handling message: ', msg
        # send package here

    # get package from client
    def get_package(self):
        pkg = None
        try:
            pkg = NetPackage(0, '', 0)
            data, addr = self.gate_communicator.receive_data()
            pkg.data = data
            pkg.ip = addr[0]
            pkg.port = addr[1]
        finally:
            return pkg

    def handle_package(self, pkg):
        # parse package
        op_code = 0
        if op_code == 1:
            # connect request
            cid = unpack('i', pkg.data[5:5+4])
            token = 0
            self.login_client(cid, token)
        if op_code == 2:
            # game data
            pass

    def start_server(self):
        """

        package => UDP/TCP data from client

        message => message from other servers (also messenger)

        :return:
        """
        print 'gate server listening at: ', self.sock_accepting.getsockname()
        try:
            while True:

                # process incoming packages, max 10 a time
                for p_count in range(10):
                    new_pkg = self.get_package()
                    if new_pkg:
                        self.handle_package(new_pkg)
                    else:
                        break

                # process new messages, max 10 a time
                for m_count in range(10):
                    new_message = self.get_message()
                    if new_message:
                        self.handle_message(new_message)
                    else:
                        break
        finally:
            self.sock_accepting.close()
            print 'gate server closed'


if __name__ == '__main__':
    gs = GateServer('gate_server')
    gs.start_server()
