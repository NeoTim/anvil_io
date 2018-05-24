from messenger import Messenger


class MessageServer:
    """
    parent class of all the servers with messenger
    """
    def __init__(self, messenger_name):
        self.server_messenger = Messenger(messenger_name)

    def get_message(self):
        return self.server_messenger.get_message()

    def put_message(self, msg):
        self.server_messenger.put_message(msg)

    def send_message_content(self, content, target_message_server):
        self.server_messenger.send_message_content(content, target_message_server.server_messenger)

    def handle_message(self, msg):
        raise NotImplementedError('please implement function "handle_message"')


