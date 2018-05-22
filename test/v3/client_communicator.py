import socket


class COMMUNICATE_STATE:

    OK = 0
    TIME_OUT = 1

    def __init__(self):
        self.code = self.OK


class ClientCommunicator:
    """
    send and receive message from client
    """
    def __init__(self, protocol='UDP', sock=None):
        if protocol != 'TCP' and protocol != 'UDP':
            raise ValueError('no suitable protocol for "' + protocol + '"')
        self.protocol = protocol
        self.communicate_state = COMMUNICATE_STATE()
        self.sock = None
        self.remote_addr = ''
        self.remote_port = 0
        if sock:
            self.sock = sock
        sock.settimeout(5)  # set timeout to 5 sec

    def send_message(self, msg, addr=None, port=None):
        if self.protocol == 'TCP':
            if addr:
                raise ValueError('dynamic remote address ' + addr + 'not allowed for TCP!')
            try:
                self.sock.send(1024)
            except socket.timeout, e:
                print 'time out'
        if self.protocol == 'UDP':
            remote_addr = self.remote_addr
            remote_port = self.remote_port
            if addr:
                remote_addr = addr
                remote_port = port
            try:
                self.sock.sendto(msg, (remote_addr, remote_port))
            except socket.timeout, e:
                print 'time out'

    def receive_message(self):
        msg = None
        if self.protocol == 'TCP':
            try:
                msg = self.sock.recv(1024)
            except socket.timeout:
                print 'time out'
        if self.protocol == 'UDP':
            try:
                msg = self.sock.recv(1024)
            except socket.timeout:
                print 'time out'
        return msg

if __name__ == '__main__':
    pass