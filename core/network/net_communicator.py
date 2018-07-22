import socket


class CommunicateState:

    OK = 0
    TIME_OUT = 1
    # TODO: more types of result code

    def __init__(self):
        self.code = self.OK


class NetCommunicator:
    """
    send and receive data through network
    """
    def __init__(self, protocol='UDP', sock=None, time_out=1):
        if protocol != 'TCP' and protocol != 'UDP':
            raise ValueError('no suitable protocol for "' + protocol + '"')
        self.protocol = protocol
        self.communicate_state = CommunicateState()
        self.sock = None
        self.remote_addr = ''
        self.remote_port = 0
        if sock:
            self.sock = sock
        sock.settimeout(time_out)  # set default timeout to 1 sec

    def send_data(self, msg, addr=None, port=None):
        d_len = 0
        if self.protocol == 'TCP':
            if addr:
                raise ValueError('dynamic remote address ' + addr + 'not allowed for TCP!')
            try:
                d_len = self.sock.send(msg)
            except socket.timeout, e:
                print 'time out'
        if self.protocol == 'UDP':
            remote_addr = self.remote_addr
            remote_port = self.remote_port
            if addr:
                remote_addr = addr
                remote_port = port
            try:
                d_len = self.sock.sendto(msg, (remote_addr, remote_port))
            except socket.timeout, e:
                print 'time out'
            except Exception, e:
                print 'send error', e
        return d_len

    def receive_data(self):
        data = None
        addr = ('', 0)
        if self.protocol == 'TCP':
            try:
                data = self.sock.recv(1024)
                addr = self.sock.getsocketname()
            except socket.timeout:
                print 'time out'
        if self.protocol == 'UDP':
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                pass
            except Exception, e:
                print e
        if data:
            return [data, addr]
        return [None, None]

if __name__ == '__main__':
    pass
