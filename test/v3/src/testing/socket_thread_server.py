import socket
import time
import threading
import logging

TOTAL_PACKS = 10000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('192.168.145.88', 666))
msg = 'THIS IS S STRING OF TESTING DATA. TESTING TESTING TESTING'


def get_send_data():
    def send_data():
        sock.sendto(msg, ('192.168.145.88', 777))
        # print 'sending'
    return send_data

send_func = get_send_data()

packs = [0] * TOTAL_PACKS
thread_lock = threading.RLock()


class SendThread(threading.Thread):
    def run(self):
        #logging.warning(self.name + ' runing')
        while True:
            thread_lock.acquire()
            if len(packs) > 0:
                # logging.warning('seding. packs left' + str(len(packs)))
                send_func()
                packs.pop()
                thread_lock.release()
            else:
                thread_lock.release()
                break
        #logging.warning(self.name + ' ends')




threads = []
for i in range(30):
    threads.append(SendThread())
for j in range(30):
    pass
    threads[j].start()


time.sleep(5)


for ind in range(TOTAL_PACKS):
    send_func()
