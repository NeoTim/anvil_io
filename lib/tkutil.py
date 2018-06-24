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
    int_sec = int(cur_stamp)
    frac, whole = math.modf(cur_stamp)
    cur_ms = 0
    for i in range(6):
        cur_ms += 10 ** i * (int_sec % 10)
        int_sec /= 10
    cur_ms = cur_ms * 1000 + int(frac * 1000)
    return cur_ms

