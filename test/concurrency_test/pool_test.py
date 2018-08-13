# def consumer():
#     r = ''
#     while True:
#         n = yield r
#         if not n:
#             return
#         print('[CONSUMER] Consuming %s...' % n)
#         r = '200 OK'
#
# def produce(c):
#     c.send(None)
#     n = 0
#     while n < 5:
#         n = n + 1
#         print('[PRODUCER] Producing %s...' % n)
#         r = c.send(n)
#         print('[PRODUCER] Consumer return: %s' % r)
#     c.close()
#
# c = consumer()
# produce(c)
#import gevent
#from gevent import Greenlet
# from gevent.event import AsyncResult
# import gevent.socket
#
# a = AsyncResult()
#
# def setter():
#     gevent.sleep(3)
#     a.set('?')
#
# def waiter():
#     print (a.get())
#
# gevent.joinall([
#     gevent.spawn(setter),
#     gevent.spawn(waiter),
#     gevent.spawn(waiter)
# ])

# from multiprocessing import Process, Queue
# import time
# q = Queue()
#
# def room_process(q, gate_ref):
#     print 'room starts'
#     while True:
#         try:
#             msg = q.get()
#             if msg:
#                 if msg == 'stop':
#                     break
#                 else:
#                     print 'room get msg', msg
#         except Exception, e:
#             pass
#     print 'room ends'
#
# def gate_process(q):
#     room_ref = Process(target=room_process, args=(q,))
#     room_ref.start()
#     for i in range(10):
#         try:
#             time.sleep(1)
#             q.put(i, timeout=2)
#             print 'gate send', i, 'to room'
#         except Exception, e:
#             pass
#     q.put('stop')
#
# if __name__ == '__main__':
#     gate = Process(target=gate_process, args=(q,))
#     gate.start()

import threading
import time

class ThreadA(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            print 'test 1'
            time.sleep(0.1)