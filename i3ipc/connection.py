#!/usr/bin/env python3

from .con import Con
from .replies import (BarConfigReply, CommandReply, ConfigReply, OutputReply, TickReply,
                      VersionReply, WorkspaceReply, SeatReply, InputReply)
from .events import (IpcBaseEvent, BarconfigUpdateEvent, BindingEvent, OutputEvent, ShutdownEvent,
                     WindowEvent, TickEvent, ModeEvent, WorkspaceEvent, InputEvent, Event)
from ._private import PubSub, MessageType, EventType, Synchronizer

from typing import List, Optional, Union, Callable
import struct
import json
import socket
import os
from threading import Timer, Lock
import time
import Xlib
import Xlib.display


class Connection:
    """A connection to the i3 ipc used for querying window manager state and
    listening to events.

    The ``Connection`` class is the entry point into all features of the
    library.

    :Example:

    .. code-block:: python3

        i3 = Connection()
        workspaces = i3.get_workspaces()
        i3.command('focus left')

    :param socket_path: A path to the i3 ipc socket path to connect to. If not
        given, find the socket path through the default search path.
    :type socket_path: str
    :param auto_reconnect: Whether to attempt to reconnect if the connection to
        the socket is broken when i3 restarts.
    :type auto_reconnect: bool

    :raises Exception: If the connection to i3 cannot be established.
    """
    _MAGIC = 'i3-ipc'  # safety string for i3-ipc
    _chunk_size = 1024  # in bytes
    _timeout = 0.5  # in seconds
    _struct_header = '=%dsII' % len(_MAGIC.encode('utf-8'))
    _struct_header_size = struct.calcsize(_struct_header)

    def __init__(self, socket_path=None, auto_reconnect=False):
        if not socket_path:
            socket_path = os.environ.get("I3SOCK")

        if not socket_path:
            socket_path = os.environ.get("SWAYSOCK")

        if not socket_path:
            try:
                disp = Xlib.display.Display()
                root = disp.screen().root
                i3atom = disp.intern_atom("I3_SOCKET_PATH")
                socket_path = root.get_full_property(i3atom, Xlib.X.AnyPropertyType).value.decode()
            except Exception:
                pass

        if not socket_path:
            raise Exception('Failed to retrieve the i3 or sway IPC socket path')

        self.subscriptions = 0
        self._pubsub = PubSub(self)
        self._socket_path = socket_path
        self._cmd_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._cmd_socket.connect(self._socket_path)
        self._cmd_lock = Lock()
        self._sub_socket = None
        self._sub_lock = Lock()
        self._auto_reconnect = auto_reconnect
        self._quitting = False
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
    def auto_reconnect(self) -> bool:
        """Whether this ``Connection`` will attempt to reconnect when the
        connection to the socket is broken.

        :rtype: bool
        """
        return self._auto_reconnect

    def _pack(self, msg_type, payload):
        """Packs the given message type and payload. Turns the resulting
        message into a byte string.
        """
        pb = payload.encode('utf-8')
        s = struct.pack('=II', len(pb), msg_type.value)
        return self._MAGIC.encode('utf-8') + s + pb

    def _unpack(self, data):
        """Unpacks the given byte string and parses the result from JSON.
        Returns None on failure and saves data into "self.buffer".
        """
        msg_magic, msg_length, msg_type = self._unpack_header(data)
        msg_size = self._struct_header_size + msg_length
        # XXX: Message shouldn't be any longer than the data
        payload = data[self._struct_header_size:msg_size]
        return payload.decode('utf-8', 'replace')

    def _unpack_header(self, data):
        """Unpacks the header of given byte string.
        """
        return struct.unpack(self._struct_header, data[:self._struct_header_size])

    def _ipc_recv(self, sock):
        data = sock.recv(14)

        if len(data) == 0:
            # EOF
            return '', 0

        msg_magic, msg_length, msg_type = self._unpack_header(data)
        msg_size = self._struct_header_size + msg_length
        while len(data) < msg_size:
            data += sock.recv(msg_length)
        return self._unpack(data), msg_type

    def _ipc_send(self, sock, message_type, payload):
        """Send and receive a message from the ipc.  NOTE: this is not thread
        safe
        """
        sock.sendall(self._pack(message_type, payload))
        data, msg_type = self._ipc_recv(sock)
        return data

    def _wait_for_socket(self):
        # for the auto_reconnect feature only
        socket_path_exists = False
        for tries in range(0, 500):
            socket_path_exists = os.path.exists(self._socket_path)
            if socket_path_exists:
                break
            time.sleep(0.001)

        return socket_path_exists

    def _message(self, message_type, payload):
        try:
            self._cmd_lock.acquire()
            return self._ipc_send(self._cmd_socket, message_type, payload)
        except ConnectionError as e:
            if not self.auto_reconnect:
                raise e

            # XXX: can the socket path change between restarts?
            if not self._wait_for_socket():
                raise e

            self._cmd_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._cmd_socket.connect(self._socket_path)
            return self._ipc_send(self._cmd_socket, message_type, payload)
        finally:
            self._cmd_lock.release()

    def command(self, payload: str) -> List[CommandReply]:
        """Sends a command to i3.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :param cmd: The command to send to i3.
        :type cmd: str
        :returns: A list of replies that contain info for the result of each
            command given.
        :rtype: list(:class:`CommandReply <i3ipc.CommandReply>`)
        """
        data = self._message(MessageType.COMMAND, payload)
        if data:
            data = json.loads(data)
            return CommandReply._parse_list(data)
        else:
            return []

    def get_version(self) -> VersionReply:
        """Gets the i3 version.

        :returns: The i3 version.
        :rtype: :class:`i3ipc.VersionReply`
        """
        data = self._message(MessageType.GET_VERSION, '')
        data = json.loads(data)
        return VersionReply(data)

    def get_bar_config(self, bar_id: str = None) -> Optional[BarConfigReply]:
        """Gets the bar configuration specified by the id.

        :param bar_id: The bar id to get the configuration for. If not given,
            get the configuration for the first bar id.
        :type bar_id: str

        :returns: The bar configuration for the bar id.
        :rtype: :class:`BarConfigReply <i3ipc.BarConfigReply>` or :class:`None`
            if no bar configuration is found.
        """
        if not bar_id:
            bar_config_list = self.get_bar_config_list()
            if not bar_config_list:
                return None
            bar_id = bar_config_list[0]

        data = self._message(MessageType.GET_BAR_CONFIG, bar_id)
        data = json.loads(data)
        return BarConfigReply(data)

    def get_bar_config_list(self) -> List[str]:
        """Gets the names of all bar configurations.

        :returns: A list of all bar configurations.
        :rtype: list(str)
        """
        data = self._message(MessageType.GET_BAR_CONFIG, '')
        return json.loads(data)

    def get_outputs(self) -> List[OutputReply]:
        """Gets the list of current outputs.

        :returns: A list of current outputs.
        :rtype: list(:class:`i3ipc.OutputReply`)
        """
        data = self._message(MessageType.GET_OUTPUTS, '')
        data = json.loads(data)
        return OutputReply._parse_list(data)

    def get_inputs(self) -> List[InputReply]:
        """(sway only) Gets the inputs connected to the compositor.

        :returns: The reply to the inputs command
        :rtype: list(:class:`i3ipc.InputReply`)
        """
        data = self._message(MessageType.GET_INPUTS, '')
        data = json.loads(data)
        return InputReply._parse_list(data)

    def get_seats(self) -> List[SeatReply]:
        """(sway only) Gets the seats configured on the compositor

        :returns: The reply to the seats command
        :rtype: list(:class:`i3ipc.SeatReply`)
        """
        data = self._message(MessageType.GET_SEATS, '')
        data = json.loads(data)
        return SeatReply._parse_list(data)

    def get_workspaces(self) -> List[WorkspaceReply]:
        """Gets the list of current workspaces.

        :returns: A list of current workspaces
        :rtype: list(:class:`i3ipc.WorkspaceReply`)
        """
        data = self._message(MessageType.GET_WORKSPACES, '')
        data = json.loads(data)
        return WorkspaceReply._parse_list(data)

    def get_tree(self) -> Con:
        """Gets the root container of the i3 layout tree.

        :returns: The root container of the i3 layout tree.
        :rtype: :class:`i3ipc.Con`
        """
        data = self._message(MessageType.GET_TREE, '')
        return Con(json.loads(data), None, self)

    def get_marks(self) -> List[str]:
        """Gets the names of all currently set marks.

        :returns: A list of currently set marks.
        :rtype: list(str)
        """
        data = self._message(MessageType.GET_MARKS, '')
        return json.loads(data)

    def get_binding_modes(self) -> List[str]:
        """Gets the names of all currently configured binding modes

        :returns: A list of binding modes
        :rtype: list(str)
        """
        data = self._message(MessageType.GET_BINDING_MODES, '')
        return json.loads(data)

    def get_config(self) -> ConfigReply:
        """Returns the last loaded i3 config.

        :returns: A class containing the config.
        :rtype: :class:`i3ipc.ConfigReply`
        """
        data = self._message(MessageType.GET_CONFIG, '')
        data = json.loads(data)
        return ConfigReply(data)

    def send_tick(self, payload: str = "") -> TickReply:
        """Sends a tick with the specified payload.

        :returns: The reply to the tick command
        :rtype: :class:`i3ipc.TickReply`
        """
        data = self._message(MessageType.SEND_TICK, payload)
        data = json.loads(data)
        return TickReply(data)

    def _subscribe(self, events):
        events_obj = []
        if events & EventType.WORKSPACE.value:
            events_obj.append("workspace")
        if events & EventType.OUTPUT.value:
            events_obj.append("output")
        if events & EventType.MODE.value:
            events_obj.append("mode")
        if events & EventType.WINDOW.value:
            events_obj.append("window")
        if events & EventType.BARCONFIG_UPDATE.value:
            events_obj.append("barconfig_update")
        if events & EventType.BINDING.value:
            events_obj.append("binding")
        if events & EventType.SHUTDOWN.value:
            events_obj.append("shutdown")
        if events & EventType.TICK.value:
            events_obj.append("tick")
        if events & EventType.INPUT.value:
            events_obj.append("input")

        try:
            self._sub_lock.acquire()
            data = self._ipc_send(self._sub_socket, MessageType.SUBSCRIBE, json.dumps(events_obj))
        finally:
            self._sub_lock.release()
        data = json.loads(data)
        result = CommandReply(data)
        self.subscriptions |= events
        return result

    def off(self, handler: Callable[['Connection', IpcBaseEvent], None]):
        """Unsubscribe the handler from being called on ipc events.

        :param handler: The handler that was previously attached with
            :func:`on()`.
        :type handler: :class:`Callable`
        """
        self._pubsub.unsubscribe(handler)

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

        # special case: ipc-shutdown is not in the protocol
        if event == 'ipc_shutdown':
            # TODO deprecate this
            self._pubsub.subscribe(event, handler)
            return

        event_type = 0
        if base_event == 'workspace':
            event_type = EventType.WORKSPACE
        elif base_event == 'output':
            event_type = EventType.OUTPUT
        elif base_event == 'mode':
            event_type = EventType.MODE
        elif base_event == 'window':
            event_type = EventType.WINDOW
        elif base_event == 'barconfig_update':
            event_type = EventType.BARCONFIG_UPDATE
        elif base_event == 'binding':
            event_type = EventType.BINDING
        elif base_event == 'shutdown':
            event_type = EventType.SHUTDOWN
        elif base_event == 'tick':
            event_type = EventType.TICK
        elif base_event == 'input':
            event_type = EventType.INPUT

        if not event_type:
            raise Exception('event not implemented')

        self.subscriptions |= event_type.value

        self._pubsub.subscribe(event, handler)

    def _event_socket_setup(self):
        self._sub_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sub_socket.connect(self._socket_path)

        self._subscribe(self.subscriptions)

    def _event_socket_teardown(self):
        if self._sub_socket:
            self._sub_socket.shutdown(socket.SHUT_RDWR)
        self._sub_socket = None

    def _event_socket_poll(self):
        if self._sub_socket is None:
            return True

        data, msg_type = self._ipc_recv(self._sub_socket)

        if len(data) == 0:
            # EOF
            self._pubsub.emit('ipc_shutdown', None)
            return True

        data = json.loads(data)
        msg_type = 1 << (msg_type & 0x7f)
        event_name = ''
        event = None

        if msg_type == EventType.WORKSPACE.value:
            event_name = 'workspace'
            event = WorkspaceEvent(data, self)
        elif msg_type == EventType.OUTPUT.value:
            event_name = 'output'
            event = OutputEvent(data)
        elif msg_type == EventType.MODE.value:
            event_name = 'mode'
            event = ModeEvent(data)
        elif msg_type == EventType.WINDOW.value:
            event_name = 'window'
            event = WindowEvent(data, self)
        elif msg_type == EventType.BARCONFIG_UPDATE.value:
            event_name = 'barconfig_update'
            event = BarconfigUpdateEvent(data)
        elif msg_type == EventType.BINDING.value:
            event_name = 'binding'
            event = BindingEvent(data)
        elif msg_type == EventType.SHUTDOWN.value:
            event_name = 'shutdown'
            event = ShutdownEvent(data)
        elif msg_type == EventType.TICK.value:
            event_name = 'tick'
            event = TickEvent(data)
        elif msg_type == EventType.INPUT.value:
            event_name = 'input'
            event = InputEvent(data)
        else:
            # we have not implemented this event
            return

        try:
            self._pubsub.emit(event_name, event)
        except Exception as e:
            print(e)
            raise e

    def main(self, timeout: float = 0.0):
        """Starts the main loop for this connection to start handling events.

        :param timeout: If given, quit the main loop after ``timeout`` seconds.
        :type timeout: float
        """
        loop_exception = None
        self._quitting = False
        timer = None

        while True:
            try:
                self._event_socket_setup()

                if timeout:
                    timer = Timer(timeout, self.main_quit)
                    timer.start()

                while not self._event_socket_poll():
                    pass
            except Exception as e:
                loop_exception = e
            finally:
                if timer:
                    timer.cancel()

                self._event_socket_teardown()

                if self._quitting or not self.auto_reconnect:
                    break

                if not self._wait_for_socket():
                    break

        if loop_exception:
            raise loop_exception

    def main_quit(self):
        """Quits the running main loop for this connection."""
        self._quitting = True
        self._event_socket_teardown()
