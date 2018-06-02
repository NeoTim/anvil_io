import event_def
import inspect

def my_event_handle(e):
    print e.event_name, 'was handled!'

evet_handle = {
    'my_event': my_event_handle
}

class Event:
    def __init__(self, event_name, event_data=None):
        self.event_name = event_name
        self.event_data = event_data

if __name__ == '__main__':
    EVENT_DEF = event_def.EVENT
    for cls in EVENT_DEF.__dict__:
        print cls
        if inspect.isclass(EVENT_DEF.__dict__[cls]):
            evt_class = EVENT_DEF.__dict__[cls]
            evt = evt_class()
            getattr(event_def, 'handle_Event1')(evt)

