from dec_test import *
from class_a import ClassA


class ClassB(ClassBase):

    @reg_func
    def func_b(self):
        print 'func b'

if __name__ == '__main__':
    pass
    ins_a = ClassA()
    print ins_a.get_reg()
    ins_b = ClassB()
    print ins_b.get_reg()
    while True:
        pass
