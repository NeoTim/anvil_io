import threading


class Message:
    def __init__(self, content, msg_from):
        self.content = content   # actual data
        self.msg_from = msg_from  # from messenger name


class Messenger:

    class ResultCode:
        OK = 0
        MESSAGE_FULL = 1

        def __init__(self):
            pass

    def __init__(self, messenger_name):
        self.message_limit = 500
        self.messages = []  # message inbox
        self.messages_lock = threading.RLock()
        self.messenger_name = messenger_name

    def get_message(self):

        msg = None

        self.messages_lock.acquire()
        if len(self.messages) != 0:
            msg = self.messages.pop(0)
        self.messages_lock.release()

        return msg

    def send_message_content(self, content, target_messenger):
        msg = Message(content, self.messenger_name)
        target_messenger.put_message(msg)

    def put_message(self, msg):

        res = Messenger.ResultCode.OK

        self.messages_lock.acquire()
        if len(self.messages) >= self.message_limit:
            print self.messenger_name
            print 'message box full'
            res = Messenger.ResultCode.MESSAGE_FULL
        else:
            self.messages.append(msg)
        self.messages_lock.release()

        return res

