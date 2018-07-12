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

