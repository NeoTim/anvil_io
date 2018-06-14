# util functions
from struct import *


def get_int_from_byte(bt):
    if len(bt) != 1:
        print 'not a byte!'
        return None
    return unpack('<i', bt)
