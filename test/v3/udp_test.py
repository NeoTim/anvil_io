import socket
from struct import *

SERVER_IP = '192.168.147.64'
SERVER_PORT = 10000


class ClientInfo:
    def __init__(self, ip, port, cid):
        self.cid = cid
        self.ip = ip
        self.port = port
        self.seq = 0
        self.pos = [0, 0, 0]
        self.rot = [0, 0, 0]

    def to_binary(self):
        data = pack('<ic', self.seq, '1')
        data += pack('<iiiiiii', self.cid, self.pos[0], self.pos[1], self.pos[2], self.rot[0], self.rot[1], self.rot[2])
        return data


def solve(pkg, clients, addr):
    (seq, op_code) = unpack('<ic', pkg[0:5])
    (cid, pos_x, pos_y, pos_z, rot_x, rot_y, rot_z) = unpack('<iiiiiii', pkg[5:5+28])
    if cid not in clients:
        # add client
        new_client_info = ClientInfo(addr[0], addr[1], cid)
        clients[cid] = new_client_info
        print 'client ', cid, ' login from ', addr
    else:
        # update client
        clients[cid].pos = [pos_x, pos_y, pos_z]
        clients[cid].rot = [rot_x, rot_y, rot_z]


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        clients = {}    # cid : client info
        sock.bind((SERVER_IP, SERVER_PORT))
        sock.settimeout(0.1)
        print 'server listening at: ', sock.getsockname()
        while True:
            try:
                pkg, addr = sock.recvfrom(1024)
                if pkg:
                    solve(pkg, clients, addr)
            except socket.timeout, e:
                pass
            for cid in clients:     # send to cid
                for ccid in clients:
                    if cid == ccid:     # skip self
                        continue
                    # send client info
                    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        send_sock.settimeout(1)
                        data = clients[ccid].to_binary()
                        send_sock.sendto(data, (clients[cid].ip, clients[cid].port))
                        # remember to add seq num
                        clients[cid].seq += 1
                    finally:
                        send_sock.close()
    finally:
        sock.close()
        print 'server closed'

if __name__ == '__main__':
    # main()
    d = pack('<i', -1)
    for i in range(4):
        try:
            print int(d[i])
        except Exception, e:
            print e
    dd = unpack('<i', d)
    print dd
