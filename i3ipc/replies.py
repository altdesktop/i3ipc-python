from .model import Rect, OutputMode


class _BaseReply:
    def __init__(self, data):
        self.ipc_data = data
        for member in self.__class__._members:
            value = data.get(member[0], None)
            if value is not None:
                setattr(self, member[0], member[1](value))
            else:
                setattr(self, member[0], None)

    @classmethod
    def _parse_list(cls, data):
        return [cls(d) for d in data]


class CommandReply(_BaseReply):
    """A reply to the ``RUN_COMMAND`` message.

    .. seealso:: https://i3wm.org/docs/ipc.html#_command_reply

    :ivar success: Whether the command succeeded.
    :vartype success: bool
    :ivar error: A human-readable error message.
    :vartype error: str or :class:`None` if no error message was set.
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('success', bool),
        ('error', str),
    ]


class WorkspaceReply(_BaseReply):
    """A reply to the ``GET_WORKSPACES`` message.

    .. seealso:: https://i3wm.org/docs/ipc.html#_workspaces_reply

    :ivar num: The logical number of the workspace. Corresponds to the command
        to switch to this workspace. For named workspaces, this will be -1.
    :vartype num: int
    :ivar name: The name of this workspace (by default num+1), as changed by
        the user.
    :vartype name: str
    :ivar visible: Whether this workspace is currently visible on an output
        (multiple workspaces can be visible at the same time).
    :vartype visible: bool
    :ivar focused: Whether this workspace currently has the focus (only one
        workspace can have the focus at the same time).
    :vartype focused: bool
    :ivar urgent: Whether a window on this workspace has the "urgent" flag set.
    :vartype urgent: bool
    :ivar rect: The rectangle of this workspace (equals the rect of the output
        it is on)
    :vartype rect: :class:`Rect`
    :ivar output: The video output this workspace is on (LVDS1, VGA1, ...).
    :vartype output: str
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('num', int),
        ('name', str),
        ('visible', bool),
        ('focused', bool),
        ('urgent', bool),
        ('rect', Rect),
        ('output', str),
    ]


class OutputReply(_BaseReply):
    """A reply to the ``GET_OUTPUTS`` message.

    .. seealso:: https://i3wm.org/docs/ipc.html#_outputs_reply

    :ivar name: The name of this output (as seen in xrandr(1)).
    :vartype name: str
    :ivar active: Whether this output is currently active (has a valid mode).
    :vartype active: bool
    :ivar primary: Whether this output is currently the primary output.
    :vartype primary: bool
    :ivar current_workspace: The name of the current workspace that is visible
        on this output. :class:`None` if the output is not active.
    :vartype current_workspace: str or :class:`None` if the output is not active.
    :ivar rect: The rectangle of this output (equals the rect of the output it
        is on).
    :vartype rect: :class:`Rect`
    :ivar make: (sway only)
    :vartype make: str
    :ivar model: (sway only)
    :vartype model: str
    :ivar serial: (sway only)
    :vartype serial: str
    :ivar scale: (sway only)
    :vartype scale: float
    :ivar transform: (sway only)
    :vartype transform: str
    :ivar max_render_time: (sway only)
    :vartype max_render_time: int
    :ivar focused: (sway only)
    :vartype focused: bool
    :ivar dpms: (sway only)
    :vartype dpms: bool
    :ivar subpixel_hinting: (sway only)
    :vartype subpixel_hinting: str
    :ivar modes: (sway only)
    :vartype modes: list(:class:`OutputMode`)
    :ivar current_mode: (sway only)
    :vartype current_mode: :class:`OutputMode`
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('name', str),
        ('active', bool),
        ('primary', bool),
        ('current_workspace', str),
        ('rect', Rect),
        # Sway only output fields:
        ('make', str),
        ('model', str),
        ('serial', str),
        ('scale', float),
        ('transform', str),
        ('max_render_time', int),
        ('focused', bool),
        ('dpms', bool),
        ('subpixel_hinting', str),
        ('modes', OutputMode._parse_list),
        ('current_mode', OutputMode),
    ]


class BarConfigGaps:
    """(sway only) The useless gaps for the bar.

    :ivar left: The gap to the left.
    :vartype left: int
    :ivar right: The gap to the right.
    :vartype right: int
    :ivar top: The gap on the top.
    :vartype top: int
    :ivar bottom: The gap on the bottom.
    :vartype bottom: int
    """
    def __init__(self, data):
        self.left = data['left']
        self.right = data['right']
        self.top = data['top']
        self.bottom = data['bottom']


class BarConfigReply(_BaseReply):
    """A reply to the ``GET_BAR_CONFIG`` message with a specified bar id.

    .. seealso:: https://i3wm.org/docs/ipc.html#_bar_config_reply

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
    :ivar tray_padding:
    :vartype tray_padding: int
    :ivar hidden_state:
    :vartype hidden_state: str
    :ivar modifier:
    :vartype modifier: int
    :ivar workspace_min_width:
    :vartype workspace_min_width: int
    :ivar strip_workspace_numbers:
    :vartype strip_workspace_numbers: bool
    :ivar strip_workspace_name:
    :vartype strip_workspace_name: bool
    :ivar gaps: (sway only)
    :vartype gaps: :class:`BarConfigGaps`
    :ivar bar_height: (sway only)
    :vartype bar_height: int
    :ivar status_padding: (sway only)
    :vartype status_padding: int
    :ivar status_edge_padding: (sway only)
    :vartype status_edge_padding: int
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('id', str),
        ('tray_padding', int),
        ('hidden_state', str),
        ('mode', str),
        ('modifier', int),
        ('position', str),
        ('status_command', str),
        ('font', str),
        ('workspace_buttons', bool),
        ('workspace_min_width', int),
        ('strip_workspace_numbers', bool),
        ('strip_workspace_name', bool),
        ('binding_mode_indicator', bool),
        ('verbose', bool),
        ('colors', dict),
        ('gaps', BarConfigGaps),
        ('bar_height', int),
        ('status_padding', int),
        ('status_edge_padding', int),
    ]


class VersionReply(_BaseReply):
    """A reply to the ``GET_VERSION`` message.

    .. seealso:: https://i3wm.org/docs/ipc.html#_version_reply

    :ivar major: The major version of i3.
    :vartype major: int
    :ivar minor: The minor version of i3.
    :vartype minor: int
    :ivar patch: The patch version of i3.
    :vartype patch: int
    :ivar human_readable: A human-readable version of i3 containing the precise
        git version, build date and branch name.
    :vartype human_readable: str
    :ivar loaded_config_file_name: The current config path.
    :vartype loaded_config_file_name: str
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('major', int),
        ('minor', int),
        ('patch', int),
        ('human_readable', str),
        ('loaded_config_file_name', str),
    ]


class ConfigReply(_BaseReply):
    """A reply to the ``GET_CONFIG`` message.

    .. seealso:: https://i3wm.org/docs/ipc.html#_config_reply

    :ivar config: A string containing the config file as loaded by i3 most
        recently.
    :vartype config: str
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('config', str),
    ]


class TickReply(_BaseReply):
    """A reply to the ``SEND_TICK`` message.

    .. seealso:: https://i3wm.org/docs/ipc.html#_tick_reply

    :ivar success: Whether the tick succeeded.
    :vartype success: bool
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('success', bool),
    ]


class InputReply(_BaseReply):
    """(sway only) A reply to ``GET_INPUTS`` message.

    .. seealso:: https://github.com/swaywm/sway/blob/master/sway/sway-ipc.7.scd

    :ivar identifier: The identifier for the input device.
    :vartype identifier: str
    :ivar name: The human readable name for the device
    :vartype name: str
    :ivar vendor: The vendor code for the input device
    :vartype vendor: int
    :ivar product: The product code for the input device
    :vartype product: int
    :ivar type: The device type. Currently this can be keyboard, pointer,
        touch, tablet_tool, tablet_pad, or switch
    :vartype type: str
    :ivar xkb_active_layout_name: (Only keyboards) The name of the active keyboard layout in use
    :vartype xkb_active_layout_name: str
    :ivar xkb_layout_names: (Only keyboards) A list a layout names configured for the keyboard
    :vartype xkb_layout_names: list(str)
    :ivar xkb_active_layout_index: (Only keyboards) The index of the active keyboard layout in use
    :vartype xkb_active_layout_index: int
    :ivar libinput: (Only libinput devices) An object describing the current device settings.
    :vartype libinput: dict
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [
        ('identifier', str),
        ('name', str),
        ('vendor', int),
        ('product', int),
        ('type', str),
        ('xkb_active_layout_name', str),
        ('xkb_layout_names', list),
        ('xkb_active_layout_index', int),
        ('libinput', dict),
    ]


class SeatReply(_BaseReply):
    """(sway only) A reply to the ``GET_SEATS`` message.

    .. seealso:: https://github.com/swaywm/sway/blob/master/sway/sway-ipc.7.scd

    :ivar name: The unique name for the seat.
    :vartype name: str
    :ivar capabilities: The number of capabilities the seat has.
    :vartype capabilities: int
    :ivar focus: The id of the node currently focused by the seat or _0_ when
        the seat is not currently focused by a node (i.e. a surface layer or
        xwayland unmanaged has focus)
    :vartype focus: int
    :ivar devices: An array of input devices that are attached to the seat.
    :vartype devices: list(:class:`InputReply`)
    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    _members = [('name', str), ('capabilities', int), ('focus', int),
                ('devices', InputReply._parse_list)]
