from __future__ import annotations

from .._private import PubSub
from ..model import (MessageType, ReplyType, CommandReply, Event, GenericEvent, WorkspaceEvent,
                     WindowEvent, BarconfigUpdateEvent, BindingEvent, TickEvent, VersionReply,
                     BarConfigReply, OutputReply, WorkspaceReply, ConfigReply, TickReply)
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

    # first try environment variables
    socket_path = os.environ.get('I3SOCK')
    if socket_path:
        return socket_path

    socket_path = os.environ.get('SWAYSOCK')
    if socket_path:
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

    if socket_path:
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
            return stdout.decode().strip()

    # could not find the socket path
    return None


class Connection:
    def __init__(self, socket_path: Optional[str] = None, auto_reconnect: bool = False):
        self.socket_path = socket_path
        self._auto_reconnect = auto_reconnect
        self._pubsub = PubSub(self)
        self._subscriptions = 0
        self._restarting = False
        self._main_future = None

    def _message_reader(self):
        try:
            self._read_message()
        except Exception as e:
            self.main_quit(_error=e)

    def _read_message(self):
        buf = self._sub_socket.recv(_struct_header_size)

        if not buf:
            self._loop.remove_reader(self._sub_fd)

            if self._auto_reconnect:
                asyncio.ensure_future(self._reconnect())

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
            if event.change == 'restart':
                self._restarting = True
        elif event_type == Event.TICK:
            event = TickEvent(message)
        else:
            # we have not implemented this event
            return

        self._pubsub.emit(event_type.to_string(), event)

    async def connect(self) -> Connection:
        if not self.socket_path:
            self.socket_path = await _find_socket_path()

        if not self.socket_path:
            raise Exception('Failed to retrieve the i3 or sway IPC socket path')

        (cmd_reader, cmd_writer) = await asyncio.open_unix_connection(self.socket_path)

        self._sub_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sub_socket.connect(self.socket_path)

        self._loop = asyncio.get_event_loop()
        self._sub_fd = self._sub_socket.fileno()
        self._loop.add_reader(self._sub_fd, self._message_reader)

        self._cmd_reader = cmd_reader
        self._cmd_writer = cmd_writer

        if self._auto_reconnect:
            await self.subscribe(Event.SHUTDOWN)

        return self

    async def _reconnect(self):
        for tries in range(0, 500):
            try:
                await self.connect()
                await self.subscribe(self._subscriptions)
                break
            except FileNotFoundError:
                await asyncio.sleep(0.001)

    async def message(self, message_type: MessageType, payload: str) -> Tuple[ReplyType, bytes]:
        if message_type is MessageType.SUBSCRIBE:
            raise Exception('cannot subscribe on the command socket')

        self._cmd_writer.write(_pack(message_type, payload))
        buf = await self._cmd_reader.read(_struct_header_size)
        magic, message_length, reply_type = _unpack_header(buf)
        assert magic == _MAGIC
        message = await self._cmd_reader.read(message_length)
        return (ReplyType(reply_type), message)

    async def subscribe(self, events: Event):
        new_subscriptions = self._subscriptions ^ events

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
        asyncio.ensure_future(self.subscribe(event_type))

    def off(self, handler: Callable):
        self._pubsub.unsubscribe(handler)

    async def command(self, cmd: str) -> List[CommandReply]:
        reply_type, data = await self.message(MessageType.COMMAND, cmd)
        assert reply_type is ReplyType.COMMAND

        if data:
            return json.loads(data, object_hook=CommandReply)
        else:
            return []

    async def get_version(self) -> VersionReply:
        reply_type, data = await self.message(MessageType.GET_VERSION, '')
        assert reply_type is ReplyType.VERSION

        return json.loads(data, object_hook=VersionReply)

    async def get_bar_config_list(self) -> List[str]:
        reply_type, data = await self.message(MessageType.GET_BAR_CONFIG, '')
        assert reply_type is ReplyType.BAR_CONFIG
        return json.loads(data)

    async def get_bar_config(self, bar_id=None) -> BarConfigReply:
        if not bar_id:
            bar_config_list = await self.get_bar_config_list()
            if not bar_config_list:
                return None
            bar_id = bar_config_list[0]

        reply_type, data = await self.message(MessageType.GET_BAR_CONFIG, bar_id)
        assert reply_type is ReplyType.BAR_CONFIG

        return json.loads(data, object_hook=BarConfigReply)

    async def get_outputs(self) -> List[OutputReply]:
        reply_type, data = await self.message(MessageType.GET_OUTPUTS, '')
        assert reply_type is ReplyType.OUTPUTS

        return json.loads(data, object_hook=OutputReply)

    async def get_workspaces(self) -> List[WorkspaceReply]:
        reply_type, data = await self.message(MessageType.GET_WORKSPACES, '')
        assert reply_type is ReplyType.WORKSPACES

        return json.loads(data, object_hook=WorkspaceReply)

    async def get_tree(self) -> Con:
        reply_type, data = await self.message(MessageType.GET_TREE, '')
        assert reply_type is ReplyType.TREE

        return Con(json.loads(data), None, self)

    async def get_marks(self) -> List[str]:
        reply_type, data = await self.message(MessageType.GET_MARKS, '')
        assert reply_type is ReplyType.MARKS

        return json.loads(data)

    async def get_binding_modes(self) -> List[str]:
        reply_type, data = await self.message(MessageType.GET_BINDING_MODES, '')
        assert reply_type is ReplyType.BINDING_MODES

        return json.loads(data)

    async def get_config(self) -> ConfigReply:
        reply_type, data = await self.message(MessageType.GET_CONFIG, '')
        assert reply_type is ReplyType.GET_CONFIG

        return json.loads(data, object_hook=ConfigReply)

    async def send_tick(self, payload: str = "") -> TickReply:
        reply_type, data = await self.message(MessageType.SEND_TICK, payload)
        assert reply_type is ReplyType.TICK

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
