#!/usr/bin/env python3

import sys
import errno
import struct
import json
import socket
import os
import re
import subprocess
from enum import Enum
from collections import deque
from threading import Timer, Lock
import time

python2 = sys.version_info[0] < 3


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


class Event(object):
    WORKSPACE = (1 << 0)
    OUTPUT = (1 << 1)
    MODE = (1 << 2)
    WINDOW = (1 << 3)
    BARCONFIG_UPDATE = (1 << 4)
    BINDING = (1 << 5)
    SHUTDOWN = (1 << 6)
    TICK = (1 << 7)


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


class WorkspaceReply(_ReplyType):
    pass


class TickReply(_ReplyType):
    pass


class WorkspaceEvent(object):
    def __init__(self, data, conn):
        self.change = data['change']
        self.current = None
        self.old = None

        if 'current' in data and data['current']:
            self.current = Con(data['current'], None, conn)

        if 'old' in data and data['old']:
            self.old = Con(data['old'], None, conn)


class GenericEvent(object):
    def __init__(self, data):
        self.change = data['change']


class WindowEvent(object):
    def __init__(self, data, conn):
        self.change = data['change']
        self.container = Con(data['container'], None, conn)


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


class _PubSub(object):
    def __init__(self, conn):
        self.conn = conn
        self._subscriptions = []

    def subscribe(self, detailed_event, handler):
        event = detailed_event.replace('-', '_')
        detail = ''

        if detailed_event.count('::') > 0:
            [event, detail] = detailed_event.split('::')

        self._subscriptions.append({
            'event': event,
            'detail': detail,
            'handler': handler
        })

    def unsubscribe(self, handler):
        self._subscriptions = list(
            filter(lambda s: s['handler'] != handler, self._subscriptions))

    def emit(self, event, data):
        detail = ''

        if data and hasattr(data, 'change'):
            detail = data.change

        for s in self._subscriptions:
            if s['event'] == event:
                if not s['detail'] or s['detail'] == detail:
                    if data:
                        s['handler'](self.conn, data)
                    else:
                        s['handler'](self.conn)


# this is for compatability with i3ipc-glib


class _PropsObject(object):
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)

    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, "_obj"), name)

    def __delattr__(self, name):
        delattr(object.__getattribute__(self, "_obj"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_obj"), name, value)


class Connection(object):
    """
    This class controls a connection to the i3 ipc socket. It is capable of
    executing commands, subscribing to window manager events, and querying the
    window manager for information about the current state of windows,
    workspaces, outputs, and the i3bar. For more information, see the `ipc
    documentation <http://i3wm.org/docs/ipc.html>`_

    :param str socket_path: The path for the socket to the current i3 session.
        In most situations, you will not have to supply this yourself. Guessing
        first happens by the environment variable :envvar:`I3SOCK`, and, if this is
        empty, by executing :command:`i3 --get-socketpath`.
    :raises Exception: If the connection to ``i3`` cannot be established, or when
        the connection terminates.
    """
    MAGIC = 'i3-ipc'  # safety string for i3-ipc
    _chunk_size = 1024  # in bytes
    _timeout = 0.5  # in seconds
    _struct_header = '=%dsII' % len(MAGIC.encode('utf-8'))
    _struct_header_size = struct.calcsize(_struct_header)

    def __init__(self, socket_path=None, auto_reconnect=False):
        if not socket_path and os.environ.get("_I3IPC_TEST") is None:
            socket_path = os.environ.get("I3SOCK")

        if not socket_path:
            socket_path = os.environ.get("SWAYSOCK")

        if not socket_path:
            try:
                socket_path = subprocess.check_output(
                    ['i3', '--get-socketpath'],
                    close_fds=True,
                    universal_newlines=True).strip()
            except Exception:
                pass

        if not socket_path:
            try:
                socket_path = subprocess.check_output(
                    ['sway', '--get-socketpath'],
                    close_fds=True,
                    universal_newlines=True).strip()
            except Exception:
                pass

        if not socket_path:
            raise Exception(
                'Failed to retrieve the i3 or sway IPC socket path')

        if auto_reconnect:
            self.subscriptions = Event.SHUTDOWN
        else:
            self.subscriptions = 0

        self._pubsub = _PubSub(self)
        self.props = _PropsObject(self)
        self.socket_path = socket_path
        self.cmd_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.cmd_socket.connect(self.socket_path)
        self.cmd_lock = Lock()
        self.sub_socket = None
        self.sub_lock = Lock()
        self.auto_reconnect = auto_reconnect
        self._restarting = False
        self._quitting = False

    def _pack(self, msg_type, payload):
        """
        Packs the given message type and payload. Turns the resulting
        message into a byte string.
        """
        pb = payload.encode('utf-8')
        s = struct.pack('=II', len(pb), msg_type.value)
        return self.MAGIC.encode('utf-8') + s + pb

    def _unpack(self, data):
        """
        Unpacks the given byte string and parses the result from JSON.
        Returns None on failure and saves data into "self.buffer".
        """
        msg_magic, msg_length, msg_type = self._unpack_header(data)
        msg_size = self._struct_header_size + msg_length
        # XXX: Message shouldn't be any longer than the data
        payload = data[self._struct_header_size:msg_size]
        return payload.decode('utf-8', 'replace')

    def _unpack_header(self, data):
        """
        Unpacks the header of given byte string.
        """
        return struct.unpack(self._struct_header,
                             data[:self._struct_header_size])

    def _recv_robust(self, sock, size):
        """
        Receive size from sock, and retry if the recv() call was interrupted.
        (this is only required for python2 compatability)
        """
        while True:
            try:
                return sock.recv(size)
            except socket.error as e:
                if e.errno != errno.EINTR:
                    raise

    def _ipc_recv(self, sock):
        data = self._recv_robust(sock, 14)

        if len(data) == 0:
            # EOF
            return '', 0

        msg_magic, msg_length, msg_type = self._unpack_header(data)
        msg_size = self._struct_header_size + msg_length
        while len(data) < msg_size:
            data += self._recv_robust(sock, msg_length)
        return self._unpack(data), msg_type

    def _ipc_send(self, sock, message_type, payload):
        '''
        Send and receive a message from the ipc.
        NOTE: this is not thread safe
        '''
        sock.sendall(self._pack(message_type, payload))
        data, msg_type = self._ipc_recv(sock)
        return data

    def _wait_for_socket(self):
        # for the auto_reconnect feature only
        socket_path_exists = False
        for tries in range(0, 500):
            socket_path_exists = os.path.exists(self.socket_path)
            if socket_path_exists:
                break
            time.sleep(0.001)

        return socket_path_exists

    def message(self, message_type, payload):
        if python2:
            ErrorType = IOError
        else:
            ErrorType = ConnectionError

        try:
            self.cmd_lock.acquire()
            return self._ipc_send(self.cmd_socket, message_type, payload)
        except ErrorType as e:
            if not self.auto_reconnect:
                raise (e)

            if not self._wait_for_socket():
                raise (e)

            self.cmd_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.cmd_socket.connect(self.socket_path)
            return self._ipc_send(self.cmd_socket, message_type, payload)
        finally:
            self.cmd_lock.release()

    def command(self, payload):
        """
        Send a command to i3. See the `list of commands
        <http://i3wm.org/docs/userguide.html#_list_of_commands>`_ in the user
        guide for available commands. Pass the text of the command to execute
        as the first arguments. This is essentially the same as using
        ``i3-msg`` or an ``exec`` block in your i3 config to control the
        window manager.

        :rtype: List of :class:`CommandReply`.
        """
        data = self.message(MessageType.COMMAND, payload)
        if data:
            return json.loads(data, object_hook=CommandReply)
        else:
            return []

    def get_version(self):
        """
        Get json encoded information about the running i3 instance.  The
        equivalent of :command:`i3-msg -t get_version`. The return
        object exposes the following attributes :attr:`~VersionReply.major`,
        :attr:`~VersionReply.minor`, :attr:`~VersionReply.patch`,
        :attr:`~VersionReply.human_readable`, and
        :attr:`~VersionReply.loaded_config_file_name`.

        Example output:

        .. code:: json

            {'patch': 0,
             'human_readable': '4.12 (2016-03-06, branch "4.12")',
             'major': 4,
             'minor': 12,
             'loaded_config_file_name': '/home/joep/.config/i3/config'}


        :rtype: VersionReply

        """
        data = self.message(MessageType.GET_VERSION, '')
        return json.loads(data, object_hook=VersionReply)

    def get_bar_config(self, bar_id=None):
        """
        Get the configuration of a single bar. Defaults to the first if none is
        specified. Use :meth:`get_bar_config_list` to obtain a list of valid
        IDs.

        :rtype: BarConfigReply
        """
        if not bar_id:
            bar_config_list = self.get_bar_config_list()
            if not bar_config_list:
                return None
            bar_id = bar_config_list[0]

        data = self.message(MessageType.GET_BAR_CONFIG, bar_id)
        return json.loads(data, object_hook=BarConfigReply)

    def get_bar_config_list(self):
        """
        Get list of bar IDs as active in the connected i3 session.

        :rtype: List of strings that can be fed as ``bar_id`` into
            :meth:`get_bar_config`.
        """
        data = self.message(MessageType.GET_BAR_CONFIG, '')
        return json.loads(data)

    def get_outputs(self):
        """
        Get a list of outputs.  The equivalent of :command:`i3-msg -t get_outputs`.

        :rtype: List of :class:`OutputReply`.

        Example output:

        .. code:: python

            >>> i3ipc.Connection().get_outputs()
            [{'name': 'eDP1',
              'primary': True,
              'active': True,
              'rect': {'width': 1920, 'height': 1080, 'y': 0, 'x': 0},
              'current_workspace': '2'},
             {'name': 'xroot-0',
              'primary': False,
              'active': False,
              'rect': {'width': 1920, 'height': 1080, 'y': 0, 'x': 0},
              'current_workspace': None}]
        """
        data = self.message(MessageType.GET_OUTPUTS, '')
        return json.loads(data, object_hook=OutputReply)

    def get_workspaces(self):
        """
        Get a list of workspaces. Returns JSON-like data, not a Con instance.

        You might want to try the :meth:`Con.workspaces` instead if the info
        contained here is too little.

        :rtype: List of :class:`WorkspaceReply`.

        """
        data = self.message(MessageType.GET_WORKSPACES, '')
        return json.loads(data, object_hook=WorkspaceReply)

    def get_tree(self):
        """
        Returns a :class:`Con` instance with all kinds of methods and selectors.
        Start here with exploration. Read up on the :class:`Con` stuffs.

        :rtype: Con
        """
        data = self.message(MessageType.GET_TREE, '')
        return Con(json.loads(data), None, self)

    def get_marks(self):
        """
        Get a list of the names of all currently set marks.

        :rtype: list
        """
        data = self.message(MessageType.GET_MARKS, '')
        return json.loads(data)

    def get_binding_modes(self):
        """
        Returns all currently configured binding modes.

        :rtype: list
        """
        data = self.message(MessageType.GET_BINDING_MODES, '')
        return json.loads(data)

    def get_config(self):
        """
        Currently only contains the "config" member, which is a string
        containing the config file as loaded by i3 most recently.

        :rtype: ConfigReply
        """
        data = self.message(MessageType.GET_CONFIG, '')
        return json.loads(data, object_hook=ConfigReply)

    def send_tick(self, payload=""):
        """
        Sends a tick event with the specified payload. After the reply was
        received, the tick event has been written to all IPC connections which
        subscribe to tick events.

        :rtype: TickReply
        """
        data = self.message(MessageType.SEND_TICK, payload)
        return json.loads(data, object_hook=TickReply)

    def subscribe(self, events):
        events_obj = []
        if events & Event.WORKSPACE:
            events_obj.append("workspace")
        if events & Event.OUTPUT:
            events_obj.append("output")
        if events & Event.MODE:
            events_obj.append("mode")
        if events & Event.WINDOW:
            events_obj.append("window")
        if events & Event.BARCONFIG_UPDATE:
            events_obj.append("barconfig_update")
        if events & Event.BINDING:
            events_obj.append("binding")
        if events & Event.SHUTDOWN:
            events_obj.append("shutdown")
        if events & Event.TICK:
            events_obj.append("tick")

        try:
            self.sub_lock.acquire()
            data = self._ipc_send(self.sub_socket, MessageType.SUBSCRIBE,
                                  json.dumps(events_obj))
        finally:
            self.sub_lock.release()
        result = json.loads(data, object_hook=CommandReply)
        self.subscriptions |= events
        return result

    def off(self, handler):
        self._pubsub.unsubscribe(handler)

    def on(self, detailed_event, handler):
        event = detailed_event.replace('-', '_')

        if detailed_event.count('::') > 0:
            [event, __] = detailed_event.split('::')

        # special case: ipc-shutdown is not in the protocol
        if event == 'ipc_shutdown':
            # TODO deprecate this
            self._pubsub.subscribe(event, handler)
            return

        event_type = 0
        if event == "workspace":
            event_type = Event.WORKSPACE
        elif event == "output":
            event_type = Event.OUTPUT
        elif event == "mode":
            event_type = Event.MODE
        elif event == "window":
            event_type = Event.WINDOW
        elif event == "barconfig_update":
            event_type = Event.BARCONFIG_UPDATE
        elif event == "binding":
            event_type = Event.BINDING
        elif event == "shutdown":
            event_type = Event.SHUTDOWN
        elif event == "tick":
            event_type = Event.TICK

        if not event_type:
            raise Exception('event not implemented')

        self.subscriptions |= event_type

        self._pubsub.subscribe(detailed_event, handler)

    def event_socket_setup(self):
        self.sub_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sub_socket.connect(self.socket_path)

        self.subscribe(self.subscriptions)

    def event_socket_teardown(self):
        if self.sub_socket:
            self.sub_socket.shutdown(socket.SHUT_RDWR)
        self.sub_socket = None

    def event_socket_poll(self):
        if self.sub_socket is None:
            return True

        data, msg_type = self._ipc_recv(self.sub_socket)

        if len(data) == 0:
            # EOF
            self._pubsub.emit('ipc_shutdown', None)
            return True

        data = json.loads(data)
        msg_type = 1 << (msg_type & 0x7f)
        event_name = ''
        event = None

        if msg_type == Event.WORKSPACE:
            event_name = 'workspace'
            event = WorkspaceEvent(data, self)
        elif msg_type == Event.OUTPUT:
            event_name = 'output'
            event = GenericEvent(data)
        elif msg_type == Event.MODE:
            event_name = 'mode'
            event = GenericEvent(data)
        elif msg_type == Event.WINDOW:
            event_name = 'window'
            event = WindowEvent(data, self)
        elif msg_type == Event.BARCONFIG_UPDATE:
            event_name = 'barconfig_update'
            event = BarconfigUpdateEvent(data)
        elif msg_type == Event.BINDING:
            event_name = 'binding'
            event = BindingEvent(data)
        elif msg_type == Event.SHUTDOWN:
            event_name = 'shutdown'
            event = GenericEvent(data)
            if event.change == 'restart':
                self._restarting = True
        elif msg_type == Event.TICK:
            event_name = 'tick'
            event = TickEvent(data)
        else:
            # we have not implemented this event
            return

        self._pubsub.emit(event_name, event)

    def main(self, timeout=0):
        self._quitting = False
        while True:
            try:
                self.event_socket_setup()

                timer = None

                if timeout:
                    timer = Timer(timeout, self.main_quit)
                    timer.start()

                while not self.event_socket_poll():
                    pass

                if timer:
                    timer.cancel()
            finally:
                self.event_socket_teardown()

                if self._quitting or not self._restarting or not self.auto_reconnect:
                    return

                self._restarting = False
                # The ipc told us it's restarting and the user wants to survive
                # restarts. Wait for the socket path to reappear and reconnect
                # to it.
                if not self._wait_for_socket():
                    break

    def main_quit(self):
        self._quitting = True
        self.event_socket_teardown()


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


class Con(object):
    """
    The container class. Has all internal information about the windows,
    outputs, workspaces and containers that :command:`i3` manages.

    .. attribute:: id

        The internal ID (actually a C pointer value within i3) of the container.
        You can use it to (re-)identify and address containers when talking to
        i3.

    .. attribute:: name

        The internal name of the container.  ``None`` for containers which
        are not leaves.  The string `_NET_WM_NAME <://specifications.freedesktop.org/wm-spec/1.3/ar01s05.html#idm140238712347280>`_
        for windows. Read-only value.

    .. attribute:: type

        The type of the container. Can be one of ``root``, ``output``, ``con``,
        ``floating_con``, ``workspace`` or ``dockarea``.

    .. attribute:: window_title

        The window title.

    .. attribute:: window_class

        The window class.

    .. attribute:: instance

        The instance name of the window class.

    .. attribute:: gaps

        The inner and outer gaps devation from default values.

    .. attribute:: border

        The type of border style for the selected container. Can be either
        ``normal``, ``none`` or ``1pixel``.

    .. attribute:: current_border_width

       Returns amount of pixels for the border. Readonly value. See `i3's user
       manual <https://i3wm.org/docs/userguide.html#_border_style_for_new_windows>_
       for more info.

    .. attribute:: layout

        Can be either ``splith``, ``splitv``, ``stacked``, ``tabbed``, ``dockarea`` or
        ``output``.
        :rtype: string

    .. attribute:: percent

        The percentage which this container takes in its parent. A value of
        null means that the percent property does not make sense for this
        container, for example for the root container.
        :rtype: float

    .. attribute:: rect

        The absolute display coordinates for this container. Display
        coordinates means that when you have two 1600x1200 monitors on a single
        X11 Display (the standard way), the coordinates of the first window on
        the second monitor are ``{ "x": 1600, "y": 0, "width": 1600, "height":
        1200 }``.

    .. attribute:: window_rect

        The coordinates of the *actual client window* inside the container,
        without the window decorations that may also occupy space.

    .. attribute:: deco_rect

        The coordinates of the window decorations within a container. The
        coordinates are relative to the container and do not include the client
        window.

    .. attribute:: geometry

        The original geometry the window specified when i3 mapped it. Used when
        switching a window to floating mode, for example.

    .. attribute:: window

        The X11 window ID of the client window.

    .. attribute:: focus

        A list of container ids describing the focus situation within the current
        container. The first element refers to the container with (in)active focus.

    .. attribute:: focused

        Whether or not the current container is focused. There is only
        one focused container.

    .. attribute:: visible

        Whether or not the current container is visible.

    .. attribute:: num

        Optional attribute that only makes sense for workspaces. This allows
        for arbitrary and changeable names, even though the keyboard
        shortcuts remain the same.  See `the i3wm docs <https://i3wm.org/docs/userguide.html#_named_workspaces>`_
        for more information

    .. attribute:: urgent

        Whether the window or workspace has the `urgent` state.

        :returns: :bool:`True` or :bool:`False`.

    .. attribute:: floating

        Whether the container is floating or not. Possible values are
        "auto_on", "auto_off", "user_on" and "user_off"

    .. attribute:: pid

        The id of the process who owns the client window
        sway only, version >= 1.0-alpha.6

    ..
        command <-- method
        command_children <-- method
        deco_rect IPC
        descendents
        find_by_id
        find_by_role
        find_by_window
        find_classed
        find_focused
        find_fullscreen
        find_marked
        find_named
        find_titled
        floating
        floating_nodes
        fullscreen_mode
        gaps
        leaves
        marks
        nodes
        orientation
        parent
        props
        root
        scratchpad
        scratchpad_state
        window_class
        window_instance
        window_rect
        window_role
        workspace
        workspaces


    """

    def __init__(self, data, parent, conn):
        self.props = _PropsObject(self)
        self._conn = conn
        self.parent = parent

        # set simple properties
        ipc_properties = [
            'border', 'current_border_width', 'floating', 'focus', 'focused',
            'fullscreen_mode', 'id', 'layout', 'marks', 'name', 'num',
            'orientation', 'percent', 'scratchpad_state', 'sticky', 'type',
            'urgent', 'window', 'pid'
        ]
        for attr in ipc_properties:
            if attr in data:
                setattr(self, attr, data[attr])
            else:
                setattr(self, attr, None)

        # XXX in 4.12, marks is an array (old property was a string "mark")
        if not self.marks:
            self.marks = []
            if 'mark' in data and data['mark']:
                self.marks.append(data['mark'])

        # XXX this is for compatability with 4.8
        if isinstance(self.type, int):
            if self.type == 0:
                self.type = "root"
            elif self.type == 1:
                self.type = "output"
            elif self.type == 2 or self.type == 3:
                self.type = "con"
            elif self.type == 4:
                self.type = "workspace"
            elif self.type == 5:
                self.type = "dockarea"

        # set complex properties
        self.nodes = []
        if 'nodes' in data:
            for n in data['nodes']:
                self.nodes.append(Con(n, self, conn))

        self.floating_nodes = []
        if 'floating_nodes' in data:
            for n in data['floating_nodes']:
                self.floating_nodes.append(Con(n, self, conn))

        self.window_class = None
        self.window_instance = None
        self.window_role = None
        self.window_title = None
        if 'window_properties' in data:
            if 'class' in data['window_properties']:
                self.window_class = data['window_properties']['class']
            if 'instance' in data['window_properties']:
                self.window_instance = data['window_properties']['instance']
            if 'window_role' in data['window_properties']:
                self.window_role = data['window_properties']['window_role']
            if 'title' in data['window_properties']:
                self.window_title = data['window_properties']['title']

        self.rect = Rect(data['rect'])
        if 'window_rect' in data:
            self.window_rect = Rect(data['window_rect'])
        if 'deco_rect' in data:
            self.deco_rect = Rect(data['deco_rect'])

        self.gaps = None
        if 'gaps' in data:
            self.gaps = Gaps(data['gaps'])

    def __iter__(self):
        """
        Iterate through the descendents of this node (breadth-first tree traversal)
        """
        queue = deque(self.nodes)
        queue.extend(self.floating_nodes)

        while queue:
            con = queue.popleft()
            yield con
            queue.extend(con.nodes)
            queue.extend(con.floating_nodes)

    def root(self):
        """
        Retrieves the root container.

        :rtype: :class:`Con`.
        """

        if not self.parent:
            return self

        con = self.parent

        while con.parent:
            con = con.parent

        return con

    def descendents(self):
        """
        Retrieve a list of all containers that delineate from the currently
        selected container.  Includes any kind of container.

        :rtype: List of :class:`Con`.
        """
        return [c for c in self]

    def leaves(self):
        """
        Retrieve a list of windows that delineate from the currently
        selected container.  Only lists client windows, no intermediate
        containers.

        :rtype: List of :class:`Con`.
        """
        leaves = []

        for c in self:
            if not c.nodes and c.type == "con" and c.parent.type != "dockarea":
                leaves.append(c)

        return leaves

    def command(self, command):
        """
        Run a command on the currently active container.

        :rtype: CommandReply
        """
        return self._conn.command('[con_id="{}"] {}'.format(self.id, command))

    def command_children(self, command):
        """
        Run a command on the direct children of the currently selected
        container.

        :rtype: List of CommandReply????
        """
        if not len(self.nodes):
            return

        commands = []
        for c in self.nodes:
            commands.append('[con_id="{}"] {};'.format(c.id, command))

        self._conn.command(' '.join(commands))

    def workspaces(self):
        """
        Retrieve a list of currently active workspaces.

        :rtype: List of :class:`Con`.
        """
        workspaces = []

        def collect_workspaces(con):
            if con.type == "workspace" and not con.name.startswith('__'):
                workspaces.append(con)
                return

            for c in con.nodes:
                collect_workspaces(c)

        collect_workspaces(self.root())
        return workspaces

    def find_focused(self):
        """
        Finds the focused container.

        :rtype class Con:
        """
        try:
            return next(c for c in self if c.focused)
        except StopIteration:
            return None

    def find_by_id(self, id):
        try:
            return next(c for c in self if c.id == id)
        except StopIteration:
            return None

    def find_by_window(self, window):
        try:
            return next(c for c in self if c.window == window)
        except StopIteration:
            return None

    def find_by_role(self, pattern):
        return [
            c for c in self
            if c.window_role and re.search(pattern, c.window_role)
        ]

    def find_named(self, pattern):
        return [c for c in self if c.name and re.search(pattern, c.name)]

    def find_titled(self, pattern):
        return [c for c in self if c.window_title and re.search(pattern, c.window_title)]

    def find_classed(self, pattern):
        return [
            c for c in self
            if c.window_class and re.search(pattern, c.window_class)
        ]

    def find_instanced(self, pattern):
        return [
            c for c in self
            if c.window_instance and re.search(pattern, c.window_instance)
        ]

    def find_marked(self, pattern=".*"):
        pattern = re.compile(pattern)
        return [
            c for c in self if any(pattern.search(mark) for mark in c.marks)
        ]

    def find_fullscreen(self):
        return [c for c in self if c.type == 'con' and c.fullscreen_mode]

    def workspace(self):
        if self.type == 'workspace':
            return self

        ret = self.parent

        while ret:
            if ret.type == 'workspace':
                break
            ret = ret.parent

        return ret

    def scratchpad(self):
        root = self.root()

        i3con = None
        for c in root.nodes:
            if c.name == "__i3":
                i3con = c
                break

        if not i3con:
            return None

        i3con_content = None
        for c in i3con.nodes:
            if c.name == "content":
                i3con_content = c
                break

        if not i3con_content:
            return None

        scratch = None
        for c in i3con_content.nodes:
            if c.name == "__i3_scratch":
                scratch = c
                break

        return scratch
