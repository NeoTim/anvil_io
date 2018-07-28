import socket
import time
import threading


def client_send(sock, pkg_num):
    for i in range(pkg_num):
        sock.sendto(str(time.time()), ('192.168.145.97', 20000))


def client_recv(sock, start_time, pkg_num):
    count = 0
    last_time = time.time()
    avg_response_time = 0
    while True:
        data = None
        try:
            data, addr = sock.recvfrom(1024)
            if data:
                count += 1
                last_time = time.time()
                response_time = time.time() - float(data)
                if response_time < 5:
                    avg_response_time = (avg_response_time * (count - 1) + response_time) / count
        except Exception, e:
            pass
        if time.time() - start_time > 10 or count == pkg_num:
            print 'total time:', last_time - start_time
            print 'loss rate:', float(pkg_num - count) / pkg_num
            print 'average response time:', avg_response_time
            break


def client_turns(sock, start_time, pkg_num):
    count = 0
    last_time = time.time()
    avg_response_time = 0
    for i in range(pkg_num):
        sock.sendto(str(time.time()), ('192.168.145.97', 20000))
        data = None
        try:
            data, addr = sock.recvfrom(1024)
            if data:
                count += 1
                last_time = time.time()
                response_time = time.time() - float(data)
                if response_time < 5:
                    avg_response_time = (avg_response_time * (count - 1) + response_time) / count
        except Exception, e:
            pass
    print 'total time:', last_time - start_time
    print 'loss rate:', float(pkg_num - count) / pkg_num
    print 'average response time:', avg_response_time


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start_time = time.time()
    sock.settimeout(0.01)
    # sock.bind(('0.0.0.0', 12345))

    pkg_num = 60000

    t1 = threading.Thread(target=client_send, args=(sock, pkg_num)).start()
    t2 = threading.Thread(target=client_recv, args=(sock, start_time, pkg_num)).start()

    time.sleep(10)

    start_time = time.time()

    # client_send(sock, pkg_num)
    # client_recv(sock, start_time, pkg_num)

    client_turns(sock, start_time, pkg_num)

    # time.sleep(10)


if __name__ == '__main__':
    main()
