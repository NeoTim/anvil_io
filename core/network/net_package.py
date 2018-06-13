class NetPackage:

    class PackageType:
        ADMIN = 0
        GAME = 1
        SYS = 2

    def __init__(self, data, ip, port):
        self.ip = ip
        self.port = port
        self.data = data
