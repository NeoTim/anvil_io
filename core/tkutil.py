# util functions
from struct import *
import time
import math


def get_int_from_byte(bt):
    if len(bt) != 1:
        print 'not a byte!'
        return None
    return unpack('<i', bt)


def get_current_millisecond_clamped():
    cur_stamp = time.time()
    cur_ms = int(cur_stamp * 1000) % 604800000
    return cur_ms


def log(log_content):
    local_time = time.localtime(time.time())
    cur_time = '%d-%02d-%02d %02d:%02d:%02d' % (local_time.tm_year, local_time.tm_mon, local_time.tm_mday, local_time.tm_hour, local_time.tm_min, local_time.tm_sec)
    print cur_time + ' - ' + log_content


