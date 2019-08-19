from . import con


class WorkspaceEvent:
    def __init__(self, data, conn, _Con=con.Con):
        self.change = data['change']
        self.current = None
        self.old = None

        if 'current' in data and data['current']:
            self.current = _Con(data['current'], None, conn)

        if 'old' in data and data['old']:
            self.old = _Con(data['old'], None, conn)


class OutputEvent:
    def __init__(self, data):
        self.change = data['change']


class ModeEvent:
    def __init__(self, data):
        self.change = data['change']


class ShutdownEvent:
    def __init__(self, data):
        self.change = data['change']


class WindowEvent:
    def __init__(self, data, conn, _Con=con.Con):
        self.change = data['change']
        self.container = _Con(data['container'], None, conn)


class BarconfigUpdateEvent:
    def __init__(self, data):
        self.id = data['id']
        self.hidden_state = data['hidden_state']
        self.mode = data['mode']


class BindingInfo:
    def __init__(self, data):
        self.command = data['command']
        # not included in sway
        self.mods = data.get('mods', [])
        self.event_state_mask = data.get('event_state_mask', [])
        self.input_code = data['input_code']
        self.symbol = data['symbol']
        # sway only
        self.symbols = data.get('symbols', [])
        self.input_type = data['input_type']


class BindingEvent:
    def __init__(self, data):
        self.change = data['change']
        self.binding = BindingInfo(data['binding'])


class TickEvent:
    def __init__(self, data):
        # i3 didn't include the 'first' field in 4.15. See i3/i3#3271.
        self.first = ('first' in data) and data['first']
        self.payload = data['payload']
