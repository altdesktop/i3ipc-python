from . import con
from enum import Enum


class Event(Enum):
    WORKSPACE = 'workspace'
    WORKSPACE_FOCUS = 'workspace::focus'
    WORKSPACE_INIT = 'workspace::init'
    WORKSPACE_EMPTY = 'workspace::empty'
    WORKSPACE_URGENT = 'workspace::urgent'
    WORKSPACE_RELOAD = 'workspace::reload'
    WORKSPACE_RENAME = 'workspace::rename'
    WORKSPACE_RESTORED = 'workspace::restored'
    WORKSPACE_MOVE = 'workspace::move'
    OUTPUT = 'output'
    MODE = 'mode'
    WINDOW = 'window'
    WINDOW_NEW = 'window::new'
    WINDOW_CLOSE = 'window::close'
    WINDOW_FOCUS = 'window::focus'
    WINDOW_TITLE = 'window::title'
    WINDOW_FULLSCREEN_MODE = 'window::fullscreen_mode'
    WINDOW_MOVE = 'window::move'
    WINDOW_FLOATING = 'window::floating'
    WINDOW_URGENT = 'window::urgent'
    WINDOW_MARK = 'window::mark'
    BINDING = 'binding'
    SHUTDOWN = 'shutdown'
    SHUTDOWN_RESTART = 'shutdown::restart'
    SHUTDOWN_EXIT = 'shutdown::exit'
    TICK = 'tick'


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
        self.event_state_mask = data.get('event_state_mask', [])
        self.input_code = data['input_code']
        self.symbol = data['symbol']
        self.input_type = data['input_type']
        # sway only
        self.symbols = data.get('symbols', [])
        # not included in sway
        self.mods = data.get('mods', [])


class BindingEvent:
    def __init__(self, data):
        self.change = data['change']
        self.binding = BindingInfo(data['binding'])


class TickEvent:
    def __init__(self, data):
        # i3 didn't include the 'first' field in 4.15. See i3/i3#3271.
        self.first = data.get('first', None)
        self.payload = data['payload']
