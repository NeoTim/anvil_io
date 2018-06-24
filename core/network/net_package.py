class NetPackage:

    class PackageType:
        ADMIN = 0
        GAME_STATE = 1
        GAME_EVENT = 2
        SYS = 3

    def __init__(self, data, ip, port):
        self.ip = ip
        self.port = port
        self.data = data
