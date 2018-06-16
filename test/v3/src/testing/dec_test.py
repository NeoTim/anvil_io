import inspect
# REG = []


# def reg_func(func):
#     REG.append(func)
#     print REG
#     return func


class ClassBase:

    REG = {}

    @classmethod
    def reg_func(cls, func_name):
        def dec(func):
            cls.REG[func_name] = func
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return dec

    def __init__(self):
        pass

if __name__ == '__main__':
    pass
