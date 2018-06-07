import socket
import time
import logging


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('192.168.145.88', 777))
pack_count = 0
sock.settimeout(0.01)
TOTAL_PACKS = 10000
start_time = 0
while True:
    try:
        data = sock.recvfrom(1024)
        if data:
            # logging.warning(data)
            if pack_count == 0:
                start_time = time.time()
            pack_count += 1
    except:
        pass
    if pack_count == TOTAL_PACKS:
        logging.warning('total time' + str(time.time() - start_time))
        # print 'total time:', time.time() - start_time
        pack_count = 0
