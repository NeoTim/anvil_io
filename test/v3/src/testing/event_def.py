class Event:
    def __init__(self):
        self.id = self.__class__


class EVENT:

    class Event1:
        def __init__(self):
            self.name = 'event1'

    class Event2:
        def __init__(self):
            self.name = 'event2'

def handle_Event1(e):
    print e.name