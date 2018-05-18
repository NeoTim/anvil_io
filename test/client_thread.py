import threading
import socket


class ClientThread(threading.Thread):
    def __init__(self, sock_c, responder):
        super(ClientThread, self).__init__()
        self.sock_c = sock_c
        self.responder = responder
        self.to_send = []   # message to send
        self.to_send_lock = threading.RLock()

    def read_message(self):
        self.sock_c.settimeout(1)
        data = None
        try:
            data = self.sock_c.recv(1024)
            if not data:
                raise socket.error
        except socket.timeout:
            print 'time out'
        return data

    def send_message(self, msg):
        try:
            self.sock_c.sendall(msg)
        finally:
            pass

    def handle_send(self, msg):
        self.to_send_lock.acquire()
        if len(self.to_send) < 200:
            self.to_send.append(msg)
        self.to_send_lock.release()

    def set_responder(self, responder):
        self.responder = responder

    def run(self):
        while True:
            try:
                # receive
                msg = self.read_message()
                if msg and self.responder is not None:
                    self.responder.handle_recv(msg)
                # send
                self.to_send_lock.acquire()
                while len(self.to_send) > 0:
                    self.send_message(self.to_send[0])
                    self.to_send.pop(0)
                self.to_send_lock.release()
            finally:
                pass
