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


class EventType(Enum):
    WORKSPACE = (1 << 0)
    OUTPUT = (1 << 1)
    MODE = (1 << 2)
    WINDOW = (1 << 3)
    BARCONFIG_UPDATE = (1 << 4)
    BINDING = (1 << 5)
    SHUTDOWN = (1 << 6)
    TICK = (1 << 7)
    INPUT = (1 << 21)

    def to_string(self):
        return str.lower(self.name)

    @staticmethod
    def from_string(val):
        match = [e for e in EventType if e.to_string() == val]

        if not match:
            raise ValueError('event not implemented: ' + val)

        return match[0]

    def to_list(self):
        events_list = []
        if self.value & EventType.WORKSPACE.value:
            events_list.append(EventType.WORKSPACE.to_string())
        if self.value & EventType.OUTPUT.value:
            events_list.append(EventType.OUTPUT.to_string())
        if self.value & EventType.MODE.value:
            events_list.append(EventType.MODE.to_string())
        if self.value & EventType.WINDOW.value:
            events_list.append(EventType.WINDOW.to_string())
        if self.value & EventType.BARCONFIG_UPDATE.value:
            events_list.append(EventType.BARCONFIG_UPDATE.to_string())
        if self.value & EventType.BINDING.value:
            events_list.append(EventType.BINDING.to_string())
        if self.value & EventType.SHUTDOWN.value:
            events_list.append(EventType.SHUTDOWN.to_string())
        if self.value & EventType.TICK.value:
            events_list.append(EventType.TICK.to_string())
        if self.value & EventType.INPUT.value:
            events_list.append(EventType.INPUT.to_string())

        return events_list
