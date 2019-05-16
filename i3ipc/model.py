from . import con

from enum import Enum, IntFlag


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


class Event(IntFlag):
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
        if self & Event.WORKSPACE:
            events_list.append(Event.WORKSPACE.to_string())
        if self & Event.OUTPUT:
            events_list.append(Event.OUTPUT.to_string())
        if self & Event.MODE:
            events_list.append(Event.MODE.to_string())
        if self & Event.WINDOW:
            events_list.append(Event.WINDOW.to_string())
        if self & Event.BARCONFIG_UPDATE:
            events_list.append(Event.BARCONFIG_UPDATE.to_string())
        if self & Event.BINDING:
            events_list.append(Event.BINDING.to_string())
        if self & Event.SHUTDOWN:
            events_list.append(Event.SHUTDOWN.to_string())
        if self & Event.TICK:
            events_list.append(Event.TICK.to_string())

        return events_list


class _ReplyType(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]


class CommandReply(_ReplyType):
    """
    Info about a command that was executed with :func:`Connection.command`.
    """

    def __init__(self, data):
        super(CommandReply, self).__init__(data)

    @property
    def error(self):
        """
        A human-readable error message

        :type: str
        """
        return self.__getattr__('error')

    @property
    def success(self):
        """
        Whether the command executed successfully

        :type: bool
        """
        return self.__getattr__('success')


class VersionReply(_ReplyType):
    """
    Info about the version of the running i3 instance.
    """

    def __init__(self, data):
        super(VersionReply, self).__init__(data)

    @property
    def major(self):
        """
        The major version of i3.

        :type: int
        """
        return self.__getattr__('major')

    @property
    def minor(self):
        """
        The minor version of i3.

        :type: int
        """
        return self.__getattr__('minor')

    @property
    def patch(self):
        """
        The patch version of i3.

        :type: int
        """
        return self.__getattr__('patch')

    @property
    def human_readable(self):
        """
        A human-readable version of i3 containing the precise git version,
        build date, and branch name.

        :type: str
        """
        return self.__getattr__('human_readable')

    @property
    def loaded_config_file_name(self):
        """
        The current config path.

        :type: str
        """
        return self.__getattr__('loaded_config_file_name')


class BarConfigReply(_ReplyType):
    """
    This can be used by third-party workspace bars (especially i3bar, but
    others are free to implement compatible alternatives) to get the bar block
    configuration from i3.

    Not all properties are documented here. A complete list of properties of
    this reply type can be found `here
    <http://i3wm.org/docs/ipc.html#_bar_config_reply>`_.
    """

    def __init__(self, data):
        super(BarConfigReply, self).__init__(data)

    @property
    def colors(self):
        """
        Contains key/value pairs of colors. Each value is a color code in hex,
        formatted #rrggbb (like in HTML).

        :type: dict
        """
        return self.__getattr__('colors')

    @property
    def id(self):
        """
        The ID for this bar.

        :type: str
        """
        return self.__getattr__('id')

    @property
    def mode(self):
        """
        Either ``dock`` (the bar sets the dock window type) or ``hide`` (the
        bar does not show unless a specific key is pressed).

        :type: str
        """
        return self.__getattr__('mode')

    @property
    def position(self):
        """
        Either ``bottom`` or ``top``.

        :type: str
        """
        return self.__getattr__('position')

    @property
    def status_command(self):
        """
        Command which will be run to generate a statusline. Each line on
        stdout of this command will be displayed in the bar. At the moment, no
        formatting is supported.

        :type: str
        """
        return self.__getattr__('status_command')

    @property
    def font(self):
        """
        The font to use for text on the bar.

        :type: str
        """
        return self.__getattr__('font')


class OutputReply(_ReplyType):
    pass


class InputReply(_ReplyType):
    pass


class SeatReply(_ReplyType):
    pass


class WorkspaceReply(_ReplyType):
    pass


class TickReply(_ReplyType):
    pass


class WorkspaceEvent(object):
    def __init__(self, data, conn, _Con=con.Con):
        self.change = data['change']
        self.current = None
        self.old = None

        if 'current' in data and data['current']:
            self.current = _Con(data['current'], None, conn)

        if 'old' in data and data['old']:
            self.old = _Con(data['old'], None, conn)


class GenericEvent(object):
    def __init__(self, data):
        self.change = data['change']


class WindowEvent(object):
    def __init__(self, data, conn, _Con=con.Con):
        self.change = data['change']
        self.container = _Con(data['container'], None, conn)


class BarconfigUpdateEvent(object):
    def __init__(self, data):
        self.id = data['id']
        self.hidden_state = data['hidden_state']
        self.mode = data['mode']


class BindingInfo(object):
    def __init__(self, data):
        self.command = data['command']
        self.mods = data['mods']
        self.input_code = data['input_code']
        self.symbol = data['symbol']
        self.input_type = data['input_type']


class BindingEvent(object):
    def __init__(self, data):
        self.change = data['change']
        self.binding = BindingInfo(data['binding'])


class ConfigReply(object):
    def __init__(self, data):
        self.config = data['config']


class TickEvent(object):
    def __init__(self, data):
        # i3 didn't include the 'first' field in 4.15. See i3/i3#3271.
        self.first = ('first' in data) and data['first']
        self.payload = data['payload']


class Rect(object):
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.height = data['height']
        self.width = data['width']


class Gaps(object):
    def __init__(self, data):
        self.inner = data['inner']
        self.outer = data['outer']
