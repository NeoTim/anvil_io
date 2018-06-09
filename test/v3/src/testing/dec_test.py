from functools import wraps

SERVER_COMMAND_FUNCS = {}   # command register


def on_command(command_name):
    def reg_decorator(func):
        # TODO: verify the server_class
        SERVER_COMMAND_FUNCS[command_name] = func
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapped_func
    return reg_decorator


MY_STATE = {}


def my_state(cls):
    MY_STATE['my_state'] = cls
    return cls


class BaseClass:
    COMMAND_FUNCS = SERVER_COMMAND_FUNCS
    def __init__(self):
        pass

    def new_state(self):
        return MY_STATE['my_state']()


class MyClass(BaseClass):
    def __init__(self):
        BaseClass.__init__(self)

    @my_state
    class MyState:
        def __init__(self):
            self.pos = [0, 0, 0]

if __name__ == '__main__':
    mc = MyClass()
    ms = mc.new_state()
    print ms.pos
