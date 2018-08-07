from command.command import Command
from functools import wraps
import threading
import Queue
import time

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
        self.command_q = Queue.Queue(5000)
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
        try:
            # TESTING
            while not self.command_q.empty():
                cmd = self.command_q.get(timeout=0)
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
                self.command_q.task_done()
        except Queue.Empty, e:
            pass

    def loop(self):
        while True:
            self.tick_command()

    def start_server(self):
        try:
            self.server_thread = threading.Thread(target=self.loop)
            # self.server_thread.daemon = True
            self.server_thread.start()
        finally:
            pass


if __name__ == '__main__':
    import time
    cs = CommandServer()
    cs.start_server()
    time.sleep(2)
    cs.run_command('login_client', 2)



