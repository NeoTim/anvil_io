from command import Command
from functools import wraps

import gevent
from gevent.queue import Queue
from gevent import monkey
monkey.patch_all()


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


class CommandServer:

    """

    Example method to register member function to command:

    @on_command(command_name='my_command')
    def my_command_handler(self, *args, **kwargs):
        # do something according to command 'my_command'
        pass

    Method to execute command:

    my_server = CommandServer()
    my_server.start_server()

    my_server.run_command('my_command', *args, **kwargs)

    """

    COMMAND_FUNCS = SERVER_COMMAND_FUNCS

    def __init__(self, server_name='command_server'):
        self.command_q = Queue(5000)
        self.server_thread = None
        self.server_name = server_name

    def run_command(self, command_name, *args, **kwargs):
        """
        method to trigger command call
        :param command_name:
        :param args:
        :param kwargs:
        :return:
        """
        cmd = Command(command_name, self, *args, **kwargs)
        self.command_q.put(cmd)

    def tick_command(self):
        while True:
            try:
                if True:
                    cmd = self.command_q.get()
                    if cmd:
                        if cmd.command_name not in self.COMMAND_FUNCS:
                            print 'command \'' + cmd.command_name + '\' not found'
                        else:
                            try:
                                # TODO: verify arguments
                                self.COMMAND_FUNCS[cmd.command_name](*cmd.args, **cmd.kwargs)
                                # print cmd.command_name, 'execute delay:', time.time() - cmd.command_triggered_time
                            except Exception, e:
                                print 'run command "' + cmd.command_name + '" error'
                                print e
            except Exception, e:
                print e

    def test(self):
        started = False
        while True:
            print 'test coroutine'
            gevent.sleep(0.5)
            if not started:
                gevent.spawn(self.sub_thread)
                t_sub = threading.Thread(target=self.sub_thread)
                t_sub.start()
                started = True

    def sub_thread_green(self):
        while True:
            print 'green'
            gevent.sleep(1)

    def sub_thread_green2(self):
        while True:
            print 'green2'
            gevent.sleep(0.5)

    def sub_thread(self):
        g = gevent.spawn(self.sub_thread_green)
        g2 = gevent.spawn(self.sub_thread_green2)
        g.join()
        g2.join()

    def start_server(self):
        try:
            threads = [gevent.spawn(self.tick_command), gevent.spawn(self.test)]
            gevent.joinall(threads)
        finally:
            pass

    @on_command('test_command')
    def test_command(self, num):
        print 'get command', num


if __name__ == '__main__':
    import time
    import threading
    cs = CommandServer()
    # cs.start_server()
    t = threading.Thread(target=cs.start_server)
    t.start()
    time.sleep(3)
    cs.run_command('test_command', 2)
    time.sleep(5)
    cs.run_command('test_command', 3)



