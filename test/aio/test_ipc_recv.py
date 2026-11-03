"""Reading command replies that arrive in pieces or are cut off.

These tests do not need i3: a small Unix socket server stands in for the
window manager and sends its replies in whatever pieces the test asks for.
"""
import asyncio
import json
import os
import socket
import struct
import tempfile
import threading
import time

import pytest

from i3ipc.aio import Connection
from i3ipc._private import MessageType

MAGIC = b'i3-ipc'

VERSION = {
    'major': 4,
    'minor': 24,
    'patch': 0,
    'human_readable': '4.24',
    'loaded_config_file_name': '/dev/null'
}


def frame(msg_type, payload):
    body = json.dumps(payload).encode('utf-8')
    return MAGIC + struct.pack('=II', len(body), msg_type) + body


class FakeServer:
    """Stands in for the window manager, in a thread of its own: the
    connection's command socket blocks, so the server can't share the
    event loop. The first connection is the command socket: after the
    first request it sends each of ``chunks`` with a short pause between
    them, then closes the connection if ``close`` is set. Other connections
    (the event socket) stay idle."""

    def __init__(self, chunks, close):
        self.chunks = chunks
        self.close = close
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, 'ipc.sock')
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(4)
        self.first = True
        threading.Thread(target=self._accept, daemon=True).start()

    def _read_exact(self, conn, size):
        data = b''
        while len(data) < size:
            chunk = conn.recv(size - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def _accept(self):
        while True:
            try:
                conn, _ = self.listener.accept()
            except OSError:
                return
            first, self.first = self.first, False
            threading.Thread(target=self._serve, args=(conn, first), daemon=True).start()

    def _serve(self, conn, first):
        if first:
            header = self._read_exact(conn, 14)
            _, length, _ = struct.unpack('=6sII', header)
            self._read_exact(conn, length)
            for chunk in self.chunks:
                conn.sendall(chunk)
                time.sleep(0.05)
            if self.close:
                conn.close()
                return
        # keep the connection open until the client closes it
        while self._read_exact(conn, 1):
            pass
        conn.close()

    def cleanup(self):
        self.listener.close()
        os.unlink(self.path)
        os.rmdir(self.dir)


async def connect(chunks, close=False):
    server = FakeServer(chunks, close)
    conn = await Connection(socket_path=server.path).connect()
    return server, conn


async def disconnect(server, conn):
    conn._loop.remove_reader(conn._sub_fd)
    conn._cmd_socket.close()
    conn._sub_socket.close()
    server.cleanup()


@pytest.mark.asyncio
async def test_header_split_across_reads():
    msg = frame(MessageType.GET_VERSION.value, VERSION)
    server, conn = await connect([msg[:3], msg[3:9], msg[9:]])
    try:
        reply = await asyncio.wait_for(conn.get_version(), 3)
        assert reply.human_readable == '4.24'
    finally:
        await disconnect(server, conn)


@pytest.mark.asyncio
async def test_payload_split_does_not_swallow_next_message():
    first = frame(MessageType.GET_VERSION.value, VERSION)
    second = frame(MessageType.GET_VERSION.value, dict(VERSION, human_readable='second'))
    # the first reply's payload arrives in two pieces, and the second piece
    # comes together with the whole next reply
    server, conn = await connect([first[:20], first[20:] + second])
    try:
        reply = await asyncio.wait_for(conn.get_version(), 3)
        assert reply.human_readable == '4.24'
        reply = await asyncio.wait_for(conn.get_version(), 3)
        assert reply.human_readable == 'second'
    finally:
        await disconnect(server, conn)


@pytest.mark.asyncio
async def test_connection_closed_mid_reply_raises():
    msg = frame(MessageType.GET_VERSION.value, VERSION)
    server, conn = await connect([msg[:20]], close=True)
    try:
        with pytest.raises(ConnectionError):
            await asyncio.wait_for(conn.get_version(), 3)
    finally:
        await disconnect(server, conn)


@pytest.mark.asyncio
async def test_connection_closed_mid_header_raises():
    msg = frame(MessageType.GET_VERSION.value, VERSION)
    server, conn = await connect([msg[:5]], close=True)
    try:
        with pytest.raises(ConnectionError):
            await asyncio.wait_for(conn.get_version(), 3)
    finally:
        await disconnect(server, conn)
