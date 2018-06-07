class ServerEvent:
    """
    base of server event
    """
    def __init__(self):
        pass


class ClientLoginEvent(ServerEvent):
    def __init__(self, client_id):
        ServerEvent.__init__(self)
        self.client_id = client_id


class ClientLogoutEvent(ServerEvent):
    def __init__(self, client_id):
        ServerEvent.__init__(self)
        self.client_id = client_id


class ClientTimeOutEvent(ServerEvent):
    def __init__(self, client_id):
        ServerEvent.__init__(self)
        self.client_id = client_id


class ClientJoinRoomEvent(ServerEvent):
    def __init__(self, client_id, room_id):
        ServerEvent.__init__(self)
        self.client_id = client_id
        self.room_id = room_id


class ClientQuitRoomEvent(ServerEvent):
    def __init__(self, client_id, room_id):
        ServerEvent.__init__(self)
        self.client_id = client_id
        self.room_id = room_id


class ClientStateUpdateEvent(ServerEvent):
    def __init__(self, client_id):
        ServerEvent.__init__(self)
        self.client_id = client_id