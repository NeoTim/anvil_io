import time


class Command:
    def __init__(self, command_name, *args, **kwargs):
        self.command_name = command_name
        self.command_triggered_time = time.time()
        self.args = args
        self.kwargs = kwargs

if __name__ == '__main__':
    cmd = Command('test_command', 11, cid=2)
    for attr in cmd.__dict__:
        print 'attribute', attr
        print cmd.__dict__[attr]
