from __future__ import annotations

from .._private import PubSub
from ..model import (MessageType, CommandReply, Event, GenericEvent, WorkspaceEvent, WindowEvent,
                     BarconfigUpdateEvent, BindingEvent, TickEvent, VersionReply, BarConfigReply,
                     OutputReply, WorkspaceReply, ConfigReply, TickReply)
from .. import con
import os
import json
from typing import Optional, List, Tuple, Callable
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


class Con(con.Con):
    async def command(self, command: str) -> List[CommandReply]:
        return await self._conn.command('[con_id="{}"] {}'.format(self.id, command))

    async def command_children(self, command: str) -> List[CommandReply]:
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
    def __init__(self, socket_path: Optional[str] = None, auto_reconnect: bool = True):
        self._socket_path = socket_path
        self._auto_reconnect = auto_reconnect
        self._pubsub = PubSub(self)
        self._subscriptions = 0
        self._main_future = None
        self._reconnect_future = None

    @property
    def socket_path(self) -> str:
        return self._socket_path

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

        event_type = Event(1 << (event_type & 0x7f))

        if event_type == Event.WORKSPACE:
            event = WorkspaceEvent(message, self, _Con=Con)
        elif event_type == Event.OUTPUT:
            event = GenericEvent(message)
        elif event_type == Event.MODE:
            event = GenericEvent(message)
        elif event_type == Event.WINDOW:
            event = WindowEvent(message, self, _Con=Con)
        elif event_type == Event.BARCONFIG_UPDATE:
            event = BarconfigUpdateEvent(message)
        elif event_type == Event.BINDING:
            event = BindingEvent(message)
        elif event_type == Event.SHUTDOWN:
            event = GenericEvent(message)
        elif event_type == Event.TICK:
            event = TickEvent(message)
        else:
            # we have not implemented this event
            return

        self._pubsub.emit(event_type.to_string(), event)

    async def connect(self) -> Connection:
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

        await self._subscribe(self._subscriptions, force=True)

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

    async def message(self, message_type: MessageType, payload: str) -> bytes:
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

    async def _subscribe(self, events: Event, force=False):
        if not force:
            new_subscriptions = self._subscriptions ^ events
        else:
            new_subscriptions = events

        if not new_subscriptions:
            return

        self._subscriptions |= new_subscriptions
        event_list = new_subscriptions.to_list()
        await self._loop.sock_sendall(self._sub_socket,
                                      _pack(MessageType.SUBSCRIBE, json.dumps(event_list)))

    def on(self, detailed_event: str, handler: Callable):
        event = detailed_event.replace('-', '_')

        if detailed_event.count('::') > 0:
            [event, __] = detailed_event.split('::')

        event_type = Event.from_string(event)
        self._pubsub.subscribe(detailed_event, handler)
        asyncio.ensure_future(self._subscribe(event_type))

    def off(self, handler: Callable):
        self._pubsub.unsubscribe(handler)

    async def command(self, cmd: str) -> List[CommandReply]:
        data = await self.message(MessageType.COMMAND, cmd)

        if data:
            return json.loads(data, object_hook=CommandReply)
        else:
            return []

    async def get_version(self) -> VersionReply:
        data = await self.message(MessageType.GET_VERSION, '')
        return json.loads(data, object_hook=VersionReply)

    async def get_bar_config_list(self) -> List[str]:
        data = await self.message(MessageType.GET_BAR_CONFIG, '')
        return json.loads(data)

    async def get_bar_config(self, bar_id=None) -> BarConfigReply:
        if not bar_id:
            bar_config_list = await self.get_bar_config_list()
            if not bar_config_list:
                return None
            bar_id = bar_config_list[0]

        data = await self.message(MessageType.GET_BAR_CONFIG, bar_id)
        return json.loads(data, object_hook=BarConfigReply)

    async def get_outputs(self) -> List[OutputReply]:
        data = await self.message(MessageType.GET_OUTPUTS, '')
        return json.loads(data, object_hook=OutputReply)

    async def get_workspaces(self) -> List[WorkspaceReply]:
        data = await self.message(MessageType.GET_WORKSPACES, '')
        return json.loads(data, object_hook=WorkspaceReply)

    async def get_tree(self) -> Con:
        data = await self.message(MessageType.GET_TREE, '')
        return Con(json.loads(data), None, self)

    async def get_marks(self) -> List[str]:
        data = await self.message(MessageType.GET_MARKS, '')
        return json.loads(data)

    async def get_binding_modes(self) -> List[str]:
        data = await self.message(MessageType.GET_BINDING_MODES, '')
        return json.loads(data)

    async def get_config(self) -> ConfigReply:
        data = await self.message(MessageType.GET_CONFIG, '')
        return json.loads(data, object_hook=ConfigReply)

    async def send_tick(self, payload: str = "") -> TickReply:
        data = await self.message(MessageType.SEND_TICK, payload)
        return json.loads(data, object_hook=TickReply)

    def main_quit(self, _error=None):
        if self._main_future is not None:
            if _error:
                self._main_future.set_exception(_error)
            else:
                self._main_future.set_result(None)

            self._main_future = None

    async def main(self):
        if self._main_future is not None:
            raise Exception('the main loop is already running')
        self._main_future = self._loop.create_future()
        await self._main_future
