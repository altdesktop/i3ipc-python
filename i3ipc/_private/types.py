from enum import Enum


class MessageType(Enum):
    COMMAND = 0
    GET_WORKSPACES = 1
    SUBSCRIBE = 2
    GET_OUTPUTS = 3
    GET_TREE = 4
    GET_MARKS = 5
    GET_BAR_CONFIG = 6
    GET_VERSION = 7
    GET_BINDING_MODES = 8
    GET_CONFIG = 9
    SEND_TICK = 10
    # sway-specific command types
    GET_INPUTS = 100
    GET_SEATS = 101


class ReplyType(Enum):
    COMMAND = 0
    WORKSPACES = 1
    SUBSCRIBE = 2
    OUTPUTS = 3
    TREE = 4
    MARKS = 5
    BAR_CONFIG = 6
    VERSION = 7
    BINDING_MODES = 8
    GET_CONFIG = 9
    TICK = 10


class Event(Enum):
    WORKSPACE = (1 << 0)
    OUTPUT = (1 << 1)
    MODE = (1 << 2)
    WINDOW = (1 << 3)
    BARCONFIG_UPDATE = (1 << 4)
    BINDING = (1 << 5)
    SHUTDOWN = (1 << 6)
    TICK = (1 << 7)

    def to_string(self):
        return str.lower(self.name)

    @staticmethod
    def from_string(val):
        match = [e for e in Event if e.to_string() == val]

        if not match:
            raise ValueError('event not implemented: ' + val)

        return match[0]

    def to_list(self):
        events_list = []
        if self.value & Event.WORKSPACE.value:
            events_list.append(Event.WORKSPACE.to_string())
        if self.value & Event.OUTPUT.value:
            events_list.append(Event.OUTPUT.to_string())
        if self.value & Event.MODE.value:
            events_list.append(Event.MODE.to_string())
        if self.value & Event.WINDOW.value:
            events_list.append(Event.WINDOW.to_string())
        if self.value & Event.BARCONFIG_UPDATE.value:
            events_list.append(Event.BARCONFIG_UPDATE.to_string())
        if self.value & Event.BINDING.value:
            events_list.append(Event.BINDING.to_string())
        if self.value & Event.SHUTDOWN.value:
            events_list.append(Event.SHUTDOWN.to_string())
        if self.value & Event.TICK.value:
            events_list.append(Event.TICK.to_string())

        return events_list
