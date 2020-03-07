from . import con
from .replies import BarConfigReply, InputReply
from enum import Enum


class IpcBaseEvent:
    """An abstract base event that all events inherit from.
    """
    pass


class Event(Enum):
    """An enumeration of events that can be subscribed to with
    :func:`Connection.on()`.
    """
    WORKSPACE = 'workspace'
    OUTPUT = 'output'
    MODE = 'mode'
    WINDOW = 'window'
    BARCONFIG_UPDATE = 'barconfig_update'
    BINDING = 'binding'
    SHUTDOWN = 'shutdown'
    TICK = 'tick'
    INPUT = 'input'
    WORKSPACE_FOCUS = 'workspace::focus'
    WORKSPACE_INIT = 'workspace::init'
    WORKSPACE_EMPTY = 'workspace::empty'
    WORKSPACE_URGENT = 'workspace::urgent'
    WORKSPACE_RELOAD = 'workspace::reload'
    WORKSPACE_RENAME = 'workspace::rename'
    WORKSPACE_RESTORED = 'workspace::restored'
    WORKSPACE_MOVE = 'workspace::move'
    WINDOW_NEW = 'window::new'
    WINDOW_CLOSE = 'window::close'
    WINDOW_FOCUS = 'window::focus'
    WINDOW_TITLE = 'window::title'
    WINDOW_FULLSCREEN_MODE = 'window::fullscreen_mode'
    WINDOW_MOVE = 'window::move'
    WINDOW_FLOATING = 'window::floating'
    WINDOW_URGENT = 'window::urgent'
    WINDOW_MARK = 'window::mark'
    SHUTDOWN_RESTART = 'shutdown::restart'
    SHUTDOWN_EXIT = 'shutdown::exit'
    INPUT_ADDED = 'input::added'
    INPUT_REMOVED = 'input::removed'


Event._subscribable_events = [e for e in Event if '::' not in e.value]


class WorkspaceEvent(IpcBaseEvent):
    """Sent when the user switches to a different workspace, when a new
    workspace is initialized or when a workspace is removed (because the last
    client vanished).

    .. seealso:: https://i3wm.org/docs/ipc.html#_workspace_event

    :ivar change: The type of change.
    :vartype change: str
    :ivar current: The affected workspace.
    :vartype current: :class:`Con`
    :ivar old: When the change is "focus", an old (object) property will be
        present with the previous workspace if it exists.
    :vartype old: :class:`Con` or :class:`None`
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data, conn, _Con=con.Con):
        self.ipc_data = data
        self.change = data['change']
        self.current = None
        self.old = None

        if 'current' in data and data['current']:
            self.current = _Con(data['current'], None, conn)

        if 'old' in data and data['old']:
            self.old = _Con(data['old'], None, conn)


class OutputEvent(IpcBaseEvent):
    """Sent when RandR issues a change notification (of either screens,
    outputs, CRTCs or output properties).

    .. seealso:: https://i3wm.org/docs/ipc.html#_output_event

    :ivar change: The type of change (currently only "unspecified").
    :vartype change: str
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data):
        self.ipc_data = data
        self.change = data['change']


class ModeEvent(IpcBaseEvent):
    """Sent whenever i3 changes its binding mode.

    .. seealso:: https://i3wm.org/docs/ipc.html#_mode_event

    :ivar change: The name of the current mode in use.
    :vartype change: str
    :ivar pango_markup: Whether pango markup should be used for displaying this
        mode.
    :vartype pango_markup: bool
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data):
        self.ipc_data = data
        self.change = data['change']
        self.pango_markup = data.get('pango_markup', False)


class WindowEvent(IpcBaseEvent):
    """Sent when a client’s window is successfully reparented (that is when i3
    has finished fitting it into a container), when a window received input
    focus or when certain properties of the window have changed.

    .. seealso:: https://i3wm.org/docs/ipc.html#_window_event

    :ivar change: The type of change.
    :vartype change: str
    :ivar container: The window's parent container.
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data, conn, _Con=con.Con):
        self.ipc_data = data
        self.change = data['change']
        self.container = _Con(data['container'], None, conn)


class BarconfigUpdateEvent(IpcBaseEvent, BarConfigReply):
    """Sent when the hidden_state or mode field in the barconfig of any bar
    instance was updated and when the config is reloaded.

    .. seealso:: https://i3wm.org/docs/ipc.html#_barconfig_update_event

    :ivar id: The ID for this bar.
    :vartype id: str
    :ivar mode: Either dock (the bar sets the dock window type) or hide (the
        bar does not show unless a specific key is pressed).
    :vartype mode: str
    :ivar position: Either bottom or top at the moment.
    :vartype position: str
    :ivar status_command: Command which will be run to generate a statusline.
    :vartype status_command: str
    :ivar font: The font to use for text on the bar.
    :vartype font: str
    :ivar workspace_buttons: Display workspace buttons or not.
    :vartype workspace_buttons: bool
    :ivar binding_mode_indicator: Display the mode indicator or not.
    :vartype binding_mode_indicator: bool
    :ivar verbose: Should the bar enable verbose output for debugging.
    :vartype verbose: bool
    :ivar colors: Contains key/value pairs of colors. Each value is a color
        code in hex, formatted #rrggbb (like in HTML).
    :vartype colors: dict
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    pass


class BindingInfo:
    """Info about a binding associated with a :class:`BindingEvent`.

    :ivar ~.command: The i3 command that is configured to run for this binding.
    :vartype ~.command: str
    :ivar event_state_mask: The group and modifier keys that were configured
        with this binding.
    :vartype event_state_mask: list(str)
    :ivar input_code: If the binding was configured with bindcode, this will be
        the key code that was given for the binding.
    :vartype input_code: int
    :ivar symbol: If this is a keyboard binding that was configured with
        bindsym, this field will contain the given symbol.
    :vartype symbol: str or :class:`None` if this binding was not configured
        with a symbol.
    :ivar input_type: This will be "keyboard" or "mouse" depending on whether
        or not this was a keyboard or a mouse binding.
    :vartype input_type: str
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data):
        self.ipc_data = data
        self.command = data['command']
        self.event_state_mask = data.get('event_state_mask', [])
        self.input_code = data['input_code']
        self.symbol = data.get('symbol', None)
        self.input_type = data['input_type']
        # sway only
        self.symbols = data.get('symbols', [])
        # not included in sway
        self.mods = data.get('mods', [])


class BindingEvent(IpcBaseEvent):
    """Sent when a configured command binding is triggered with the keyboard or
    mouse.

    .. seealso:: https://i3wm.org/docs/ipc.html#_binding_event

    :ivar change: The type of change.
    :vartype change: str
    :ivar binding: Contains details about the binding that was run.
    :vartype binding: :class:`BindingInfo <i3ipc.BindingInfo>`
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data):
        self.ipc_data = data
        self.change = data['change']
        self.binding = BindingInfo(data['binding'])


class ShutdownEvent(IpcBaseEvent):
    """Sent when the ipc shuts down because of a restart or exit by user
    command.

    .. seealso:: https://i3wm.org/docs/ipc.html#_shutdown_event

    :ivar change: The type of change.
    :vartype change: str
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data):
        self.ipc_data = data
        self.change = data['change']


class TickEvent(IpcBaseEvent):
    """Sent when the ipc client subscribes to the tick event (with "first":
    true) or when any ipc client sends a SEND_TICK message (with "first":
    false).

    .. seealso:: https://i3wm.org/docs/ipc.html#_tick_event

    :ivar first: True when the ipc first subscribes to the tick event.
    :vartype first: bool or :class:`None` if not supported by this version of
        i3 (<=4.15).
    :ivar payload: The payload that was sent with the tick.
    :vartype payload: str
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data):
        self.ipc_data = data
        # i3 didn't include the 'first' field in 4.15. See i3/i3#3271.
        self.first = data.get('first', None)
        self.payload = data['payload']


class InputEvent(IpcBaseEvent):
    """(sway only) Sent when something related to the input devices changes.

    :ivar change: The type of change ("added" or "removed")
    :vartype change: str
    :ivar input: Information about the input that changed.
    :vartype input: :class:`InputReply <i3ipc.InputReply>`
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data):
        self.ipc_data = data
        self.change = data['change']
        self.input = InputReply(data['input'])
