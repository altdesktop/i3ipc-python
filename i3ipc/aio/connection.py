from .._private import PubSub, MessageType, EventType, Synchronizer
from ..replies import (BarConfigReply, CommandReply, ConfigReply, OutputReply, TickReply,
                       VersionReply, WorkspaceReply, SeatReply, InputReply)
from ..events import (IpcBaseEvent, BarconfigUpdateEvent, BindingEvent, OutputEvent, ShutdownEvent,
                      WindowEvent, TickEvent, ModeEvent, WorkspaceEvent, InputEvent, Event)
from .. import con
import os
import json
from typing import Optional, List, Tuple, Callable, Union
from Xlib import display, X
from Xlib.error import DisplayError
import struct
import socket

import asyncio
from asyncio.subprocess import PIPE
from asyncio import Future

_MAGIC = b'i3-ipc'  # safety string for i3-ipc
_chunk_size = 1024  # in bytes
_timeout = 0.5  # in seconds
_struct_header = f'={len(_MAGIC)}sII'
_struct_header_size = struct.calcsize(_struct_header)


class _AIOPubSub(PubSub):
    def queue_handler(self, handler, data=None):
        conn = self.conn

        async def handler_coroutine():
            try:
                if data:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(conn, data)
                    else:
                        handler(conn, data)
                else:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(conn)
                    else:
                        handler(conn)
            except Exception as e:
                conn.main_quit(_error=e)

        asyncio.ensure_future(handler_coroutine())

    def emit(self, event, data):
        detail = ''

        if data and hasattr(data, 'change'):
            detail = data.change

        for s in self._subscriptions:
            if s['event'] == event:
                if not s['detail'] or s['detail'] == detail:
                    self.queue_handler(s['handler'], data)


class Con(con.Con):
    """A container of a window and child containers gotten from :func:`i3ipc.Connection.get_tree()` or events.

    .. seealso:: https://i3wm.org/docs/ipc.html#_tree_reply

    :ivar border:
    :vartype border: str
    :ivar current_border_width:
    :vartype current_border_with: int
    :ivar floating:
    :vartype floating: bool
    :ivar focus: The focus stack for this container as a list of container ids.
        The "focused inactive" is at the top of the list which is the container
        that would be focused if this container recieves focus.
    :vartype focus: list(int)
    :ivar focused:
    :vartype focused: bool
    :ivar fullscreen_mode:
    :vartype fullscreen_mode: int
    :ivar ~.id:
    :vartype ~.id: int
    :ivar layout:
    :vartype layout: str
    :ivar marks:
    :vartype marks: list(str)
    :ivar name:
    :vartype name: str
    :ivar num:
    :vartype num: int
    :ivar orientation:
    :vartype orientation: str
    :ivar percent:
    :vartype percent: float
    :ivar scratchpad_state:
    :vartype scratchpad_state: str
    :ivar sticky:
    :vartype sticky: bool
    :ivar type:
    :vartype type: str
    :ivar urgent:
    :vartype urgent: bool
    :ivar window:
    :vartype window: int
    :ivar nodes:
    :vartype nodes: list(:class:`Con <i3ipc.Con>`)
    :ivar floating_nodes:
    :vartype floating_nodes: list(:class:`Con <i3ipc.Con>`)
    :ivar window_class:
    :vartype window_class: str
    :ivar window_instance:
    :vartype window_instance: str
    :ivar window_role:
    :vartype window_role: str
    :ivar window_title:
    :vartype window_title: str
    :ivar rect:
    :vartype rect: :class:`Rect <i3ipc.Rect>`
    :ivar window_rect:
    :vartype window_rect: :class:`Rect <i3ipc.Rect>`
    :ivar deco_rect:
    :vartype deco_rect: :class:`Rect <i3ipc.Rect>`
    :ivar app_id: (sway only)
    :vartype app_id: str
    :ivar pid: (sway only)
    :vartype pid: int
    :ivar gaps: (gaps only)
    :vartype gaps: :class:`Gaps <i3ipc.Gaps>`

    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    async def command(self, command: str) -> List[CommandReply]:
        """Runs a command on this container.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :returns: A list of replies for each command in the given command
            string.
        :rtype: list(CommandReply)
        """
        return await self._conn.command('[con_id="{}"] {}'.format(self.id, command))

    async def command_children(self, command: str) -> List[CommandReply]:
        """Runs a command on the immediate children of the currently selected
        container.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :returns: A list of replies for each command that was executed.
        :rtype: list(CommandReply)
        """
        if not len(self.nodes):
            return []

        commands = []
        for c in self.nodes:
            commands.append('[con_id="{}"] {};'.format(c.id, command))

        return await self._conn.command(' '.join(commands))


def _pack(msg_type: MessageType, payload: str) -> bytes:
    pb = payload.encode()
    s = struct.pack('=II', len(pb), msg_type.value)
    return b''.join((_MAGIC, s, pb))


def _unpack_header(data: bytes) -> Tuple[bytes, int, int]:
    return struct.unpack(_struct_header, data[:_struct_header_size])


async def _find_socket_path() -> Optional[str]:
    socket_path = None

    def exists(path):
        if not path:
            return False
        return os.path.exists(path)

    # first try environment variables
    socket_path = os.environ.get('I3SOCK')
    if exists(socket_path):
        return socket_path

    socket_path = os.environ.get('SWAYSOCK')
    if exists(socket_path):
        return socket_path

    # next try the root window property
    try:
        d = display.Display()
        atom = d.get_atom('I3_SOCKET_PATH')
        root = d.screen().root
        prop = root.get_full_property(atom, X.AnyPropertyType)
        if prop and prop.value:
            socket_path = prop.value.decode()
    except DisplayError:
        pass

    if exists(socket_path):
        return socket_path

    # finally try the binaries
    for binary in ('i3', 'sway'):
        try:
            process = await asyncio.create_subprocess_exec(binary,
                                                           '--get-socketpath',
                                                           stdout=PIPE,
                                                           stderr=PIPE)
        except Exception:
            continue

        stdout, stderr = await process.communicate()

        if process.returncode == 0 and stdout:
            socket_path = stdout.decode().strip()
            if exists(socket_path):
                return socket_path

    # could not find the socket path
    return None


class Connection:
    """A connection to the i3 ipc used for querying window manager state and
    listening to events.

    The ``Connection`` class is the entry point into all features of the
    library.  You must call :func:`connect() <i3ipc.aio.Connection.connect>`
    before using this ``Connection``.

    :Example:

    .. code-block:: python3

        i3 = await Connection().connect()
        workspaces = await i3.get_workspaces()
        await i3.command('focus left')

    :param socket_path: A path to the i3 ipc socket path to connect to. If not
        given, find the socket path through the default search path.
    :type socket_path: str
    :param auto_reconnect: Whether to attempt to reconnect if the connection to
        the socket is broken when i3 restarts.
    :type auto_reconnect: bool

    :raises Exception: If the connection to i3 cannot be established.
    """
    def __init__(self, socket_path: Optional[str] = None, auto_reconnect: bool = False):
        self._socket_path = socket_path
        self._auto_reconnect = auto_reconnect
        self._pubsub = _AIOPubSub(self)
        self._subscriptions = set()
        self._main_future = None
        self._reconnect_future = None
        self._synchronizer = None

    def _sync(self):
        if self._synchronizer is None:
            self._synchronizer = Synchronizer()

        self._synchronizer.sync()

    @property
    def socket_path(self) -> str:
        """The path of the socket this ``Connection`` is connected to.

        :rtype: str
        """
        return self._socket_path

    @property
    def auto_reconect(self) -> bool:
        """Whether this ``Connection`` will attempt to reconnect when the
        connection to the socket is broken.

        :rtype: bool
        """
        return self._auto_reconnect

    async def _ipc_recv(self, sock):
        pass

    def _message_reader(self):
        try:
            self._read_message()
        except Exception as e:
            self.main_quit(_error=e)

    def _read_message(self):

        error = None
        buf = b''
        try:
            buf = self._sub_socket.recv(_struct_header_size)
        except ConnectionError as e:
            error = e

        if not buf or error is not None:
            self._loop.remove_reader(self._sub_fd)

            if self._auto_reconnect:
                asyncio.ensure_future(self._reconnect())
            else:
                if error is not None:
                    raise error
                else:
                    raise EOFError()

            return

        magic, message_length, event_type = _unpack_header(buf)
        assert magic == _MAGIC
        message = json.loads(self._sub_socket.recv(message_length))

        # events have the highest bit set
        if not event_type & (1 << 31):
            # a reply
            return

        event_type = EventType(1 << (event_type & 0x7f))

        if event_type == EventType.WORKSPACE:
            event = WorkspaceEvent(message, self, _Con=Con)
        elif event_type == EventType.OUTPUT:
            event = OutputEvent(message)
        elif event_type == EventType.MODE:
            event = ModeEvent(message)
        elif event_type == EventType.WINDOW:
            event = WindowEvent(message, self, _Con=Con)
        elif event_type == EventType.BARCONFIG_UPDATE:
            event = BarconfigUpdateEvent(message)
        elif event_type == EventType.BINDING:
            event = BindingEvent(message)
        elif event_type == EventType.SHUTDOWN:
            event = ShutdownEvent(message)
        elif event_type == EventType.TICK:
            event = TickEvent(message)
        elif event_type == EventType.INPUT:
            event = InputEvent(message)
        else:
            # we have not implemented this event
            return

        self._pubsub.emit(event_type.to_string(), event)

    async def connect(self) -> 'Connection':
        """Connects to the i3 ipc socket. You must await this method to use this
        Connection.

        :returns: The ``Connection``.
        :rtype: :class:`~.Connection`
        """
        if not self._socket_path:
            self._socket_path = await _find_socket_path()

        if not self.socket_path:
            raise Exception('Failed to retrieve the i3 or sway IPC socket path')

        self._cmd_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._cmd_socket.connect(self.socket_path)

        self._sub_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sub_socket.connect(self.socket_path)

        self._loop = asyncio.get_event_loop()
        self._sub_fd = self._sub_socket.fileno()
        self._loop.add_reader(self._sub_fd, self._message_reader)

        await self.subscribe(list(self._subscriptions), force=True)

        return self

    def _reconnect(self) -> Future:
        if self._reconnect_future is not None:
            return self._reconnect_future

        self._reconnect_future = self._loop.create_future()

        async def do_reconnect():
            error = None

            for tries in range(0, 1000):
                try:
                    await self.connect()
                    error = None
                    break
                except Exception as e:
                    error = e
                    await asyncio.sleep(0.001)

            if error:
                self._reconnect_future.set_exception(error)
            else:
                self._reconnect_future.set_result(None)

            self._reconnect_future = None

        asyncio.ensure_future(do_reconnect())

        return self._reconnect_future

    async def _message(self, message_type: MessageType, payload: str = '') -> bytes:
        if message_type is MessageType.SUBSCRIBE:
            raise Exception('cannot subscribe on the command socket')

        for tries in range(0, 5):
            try:
                await self._loop.sock_sendall(self._cmd_socket, _pack(message_type, payload))
                buf = await self._loop.sock_recv(self._cmd_socket, _struct_header_size)
                break
            except ConnectionError as e:
                if not self._auto_reconnect:
                    raise e

                await self._reconnect()

        if not buf:
            return b''

        magic, message_length, reply_type = _unpack_header(buf)
        assert reply_type == message_type.value
        assert magic == _MAGIC

        try:
            message = await self._loop.sock_recv(self._cmd_socket, message_length)
        except ConnectionError as e:
            if self._auto_reconnect:
                asyncio.ensure_future(self._reconnect())
            raise e

        return message

    async def subscribe(self, events: Union[List[Event], List[str]], force: bool = False):
        """Send a ``SUBSCRIBE`` command to the ipc subscription connection and
        await the result. To attach event handlers, use :func:`Connection.on()
        <i3ipc.aio.Connection.on()>`. Calling this is only needed if you want
        to be notified when events will start coming in.

        :ivar events: A list of events to subscribe to. Currently you cannot
            subscribe to detailed events.
        :vartype events: list(:class:`Event <i3ipc.Event>`) or list(str)
        :ivar force: If ``False``, the message will not be sent if this
            connection is already subscribed to the event.
        :vartype force: bool
        """
        if not events:
            return

        if type(events) is not list:
            raise TypeError('events must be a list of events')

        subscriptions = set()

        for e in events:
            e = Event(e)
            if e not in Event._subscribable_events:
                correct_event = str.split(e.value, '::')[0].upper()
                raise ValueError(
                    f'only nondetailed events are subscribable (use Event.{correct_event})')
            subscriptions.add(e)

        if not force:
            subscriptions = subscriptions.difference(self._subscriptions)
            if not subscriptions:
                return

        self._subscriptions.update(subscriptions)

        payload = json.dumps([s.value for s in subscriptions])

        await self._loop.sock_sendall(self._sub_socket, _pack(MessageType.SUBSCRIBE, payload))

    def on(self, event: Union[Event, str], handler: Callable[['Connection', IpcBaseEvent], None]):
        """Subscribe to the event and call the handler when it is emitted by
        the i3 ipc.

        :param event: The event to subscribe to.
        :type event: :class:`Event <i3ipc.Event>` or str
        :param handler: The event handler to call.
        :type handler: :class:`Callable`
        """
        if type(event) is Event:
            event = event.value

        event = event.replace('-', '_')

        if event.count('::') > 0:
            [base_event, __] = event.split('::')
        else:
            base_event = event

        self._pubsub.subscribe(event, handler)
        asyncio.ensure_future(self.subscribe([base_event]))

    def off(self, handler: Callable[['Connection', IpcBaseEvent], None]):
        """Unsubscribe the handler from being called on ipc events.

        :param handler: The handler that was previously attached with
            :func:`on()`.
        :type handler: :class:`Callable`
        """
        self._pubsub.unsubscribe(handler)

    async def command(self, cmd: str) -> List[CommandReply]:
        """Sends a command to i3.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :param cmd: The command to send to i3.
        :type cmd: str
        :returns: A list of replies that contain info for the result of each
            command given.
        :rtype: list(:class:`CommandReply <i3ipc.CommandReply>`)
        """
        data = await self._message(MessageType.COMMAND, cmd)

        if data:
            data = json.loads(data)
            return CommandReply._parse_list(data)
        else:
            return []

    async def get_version(self) -> VersionReply:
        """Gets the i3 version.

        :returns: The i3 version.
        :rtype: :class:`i3ipc.VersionReply`
        """
        data = await self._message(MessageType.GET_VERSION)
        data = json.loads(data)
        return VersionReply(data)

    async def get_bar_config_list(self) -> List[str]:
        """Gets the names of all bar configurations.

        :returns: A list of all bar configurations.
        :rtype: list(str)
        """
        data = await self._message(MessageType.GET_BAR_CONFIG)
        return json.loads(data)

    async def get_bar_config(self, bar_id=None) -> Optional[BarConfigReply]:
        """Gets the bar configuration specified by the id.

        :param bar_id: The bar id to get the configuration for. If not given,
            get the configuration for the first bar id.
        :type bar_id: str

        :returns: The bar configuration for the bar id.
        :rtype: :class:`BarConfigReply <i3ipc.BarConfigReply>` or :class:`None`
            if no bar configuration is found.
        """
        if not bar_id:
            bar_config_list = await self.get_bar_config_list()
            if not bar_config_list:
                return None
            bar_id = bar_config_list[0]

        data = await self._message(MessageType.GET_BAR_CONFIG, bar_id)
        data = json.loads(data)
        return BarConfigReply(data)

    async def get_outputs(self) -> List[OutputReply]:
        """Gets the list of current outputs.

        :returns: A list of current outputs.
        :rtype: list(:class:`i3ipc.OutputReply`)
        """
        data = await self._message(MessageType.GET_OUTPUTS)
        data = json.loads(data)
        return OutputReply._parse_list(data)

    async def get_workspaces(self) -> List[WorkspaceReply]:
        """Gets the list of current workspaces.

        :returns: A list of current workspaces
        :rtype: list(:class:`i3ipc.WorkspaceReply`)
        """
        data = await self._message(MessageType.GET_WORKSPACES)
        data = json.loads(data)
        return WorkspaceReply._parse_list(data)

    async def get_tree(self) -> Con:
        """Gets the root container of the i3 layout tree.

        :returns: The root container of the i3 layout tree.
        :rtype: :class:`i3ipc.Con`
        """
        data = await self._message(MessageType.GET_TREE)
        return Con(json.loads(data), None, self)

    async def get_marks(self) -> List[str]:
        """Gets the names of all currently set marks.

        :returns: A list of currently set marks.
        :rtype: list(str)
        """
        data = await self._message(MessageType.GET_MARKS)
        return json.loads(data)

    async def get_binding_modes(self) -> List[str]:
        """Gets the names of all currently configured binding modes

        :returns: A list of binding modes
        :rtype: list(str)
        """
        data = await self._message(MessageType.GET_BINDING_MODES)
        return json.loads(data)

    async def get_config(self) -> ConfigReply:
        """Returns the last loaded i3 config.

        :returns: A class containing the config.
        :rtype: :class:`i3ipc.ConfigReply`
        """
        data = await self._message(MessageType.GET_CONFIG)
        data = json.loads(data)
        return ConfigReply(data)

    async def send_tick(self, payload: str = "") -> TickReply:
        """Sends a tick with the specified payload.

        :returns: The reply to the tick command
        :rtype: :class:`i3ipc.TickReply`
        """
        data = await self._message(MessageType.SEND_TICK, payload)
        data = json.loads(data)
        return TickReply(data)

    async def get_inputs(self) -> List[InputReply]:
        """(sway only) Gets the inputs connected to the compositor.

        :returns: The reply to the inputs command
        :rtype: list(:class:`i3ipc.InputReply`)
        """
        data = await self._message(MessageType.GET_INPUTS)
        data = json.loads(data)
        return InputReply._parse_list(data)

    async def get_seats(self) -> List[SeatReply]:
        """(sway only) Gets the seats configured on the compositor

        :returns: The reply to the seats command
        :rtype: list(:class:`i3ipc.SeatReply`)
        """
        data = await self._message(MessageType.GET_SEATS)
        data = json.loads(data)
        return SeatReply._parse_list(data)

    def main_quit(self, _error=None):
        """Quits the running main loop for this connection."""
        if self._main_future is not None:
            if _error:
                self._main_future.set_exception(_error)
            else:
                self._main_future.set_result(None)

            self._main_future = None

    async def main(self):
        """Starts the main loop for this connection to start handling events."""
        if self._main_future is not None:
            raise Exception('the main loop is already running')
        self._main_future = self._loop.create_future()
        await self._main_future
