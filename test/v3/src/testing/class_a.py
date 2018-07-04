from dec_test import *


class ClassA(ClassBase):

    # @ClassBase.reg_func('func_a')
    # def func_a(self):
    #     print 'func a'

    my_dict = ['a']

    def __init__(self):
        ClassBase.__init__(self)
        self.aaa = 0

    @classmethod
    def get_ins(cls):
        # ins = ClassA()
        ins = cls()
        return ins


class ClassB(ClassA):

    my_dict = ['b']

    pass


if __name__ == '__main__':
    ins = ClassB.get_ins()
    print ins.my_dict
