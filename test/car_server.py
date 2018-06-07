import socket
import sys
import threading
import json
import copy

# config
CONFIG = {
    'SERVER_IP': '192.168.137.1',
    'GATE_PORT': 10000
}

# global variables
client_socks = {}   # id : player socket
client_socks_lock = threading.RLock()


# servers server to accept connection
class GateServer(threading.Thread):

    latest_id = 0

    def __init__(self):
        super(GateServer, self).__init__()

    def add_new_client(self, sock_client):
        client_socks_lock.acquire()
        while client_socks[self.latest_id]:
            self.latest_id += 1
        print 'client ' + str(self.latest_id) + ' joined'
        client_socks[self.latest_id] = sock_client
        client_socks_lock.release()

    def run(self):
        # server socket
        tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_ip = CONFIG['SERVER_IP']
            if len(sys.argv) > 1:
                server_ip = sys.argv[1]
            tcpsock.bind((server_ip, CONFIG['GATE_PORT']))
            tcpsock.listen(1024)
            print 'car servers server listening at: ', tcpsock.getsockname()
            while True:
                (sock_client, addr_clinet) = tcpsock.accept()
                print 'client socket from ', addr_clinet
                print 'accept client connection'
                # add new connection
                self.add_new_client(sock_client)
        finally:
            print 'car servers server closed'
            tcpsock.close()


class RoomServer(threading.Thread):

    # thread to receive and send data to clients
    class ClientThread(threading.Thread):
        def __init__(self, sock_client, room_server):
            super(RoomServer.ClientThread, self).__init__()
            self.sock_c = sock_client
            self.room_server = room_server

        def run(self):
            try:
                self.sock_c.settimeout(0.5)   # set time out
                while True:
                    try:
                        # should use non-blocking read here
                        data = self.sock_c.recv(255)
                        if not data:
                            continue    # should end thread here
                        new_info = json.loads(data)
                        # update client info
                        self.room_server.update_client(self.room_server, new_info)
                    except socket.timeout, e:
                        pass
                    try:
                        # send client info to all clients
                        client_list = copy.deepcopy(self.room_server.get_clients())
                        for cid in client_list:
                            self.sock_c.sendall(json.dumps(client_list[cid]))
                    finally:
                        pass
            finally:
                self.sock_c.close()

    def __init__(self):
        super(RoomServer, self).__init__()
        self.threads_client = []  # client threads
        self.clients = {}   # client id : client info
        self.clients_lock = threading.RLock()

    def update_client(self, client_info):
        client_socks_lock.acquire()
        c_id = client_info['id']
        self.clients[c_id] = client_info
        client_socks_lock.release()

    def get_clients(self):
        return self.clients

    def run(self):
        while True:
            client_socks_lock.acquire()
            for cid in client_socks:
                self.clients_lock.acquire()
                if cid not in self.clients:
                    # open new client thread
                    new_client_thread = self.ClientThread(client_socks[cid], self)
                    self.threads_client.append(new_client_thread)
                    self.clients[cid] = {
                        'id': cid,
                        'pos': [0, 0, 0],
                        'rot': [0, 0, 0]
                    }
                    new_client_thread.start()
                self.clients_lock.release()
            client_socks_lock.release()


def main():
    try:
        gate_server_thread = GateServer()
        room_server_thread = RoomServer()

        gate_server_thread.start()
        room_server_thread.start()
    except Exception, e:
        exit(1)


if __name__ == '__main__':
    main()
