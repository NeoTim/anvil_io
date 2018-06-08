
class TinkrGarageRoomServer:

    def __init__(self):
        pass

    def myfunc(self, arg1, arg2=0):
        print self
        print arg1

    # @client_state
    # class MyClientState:
    #     def __init__(self):
    #         pass
    #
    # @game_model
    # class MyGameModel:
    #     def __init__(self):
    #         pass
    #
    # @on_command('handle_package')
    # def handle_package(self, pkg):
    #     pass

MY_REG = {}


def my_dec(func):
    MY_REG[func.__name__] = func
    return func


class BaseClass:
    def __init__(self):
        pass


def make_my_class(my_config):
    class MyClass:
        def __init__(self):
            pass
        def myfunc(self, *args, **kwargs):
            TinkrGarageRoomServer.myfunc(self, *args, **kwargs)

    return MyClass

my_class = make_my_class({})
my_ins = my_class()
my_ins.myfunc()