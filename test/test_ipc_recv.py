"""Reading IPC messages that arrive in pieces or are cut off.

These tests do not need i3: a small Unix socket server stands in for the
window manager and sends its replies in whatever pieces the test asks for.
"""
import json
import os
import socket
import struct
import tempfile
import threading
import time

import pytest

from i3ipc import Connection
from i3ipc._private import MessageType

MAGIC = b'i3-ipc'


def frame(msg_type, payload):
    body = json.dumps(payload).encode('utf-8')
    return MAGIC + struct.pack('=II', len(body), msg_type) + body


class FakeServer:
    """Stands in for the window manager. For each client connection, in
    order, it takes the next entry of ``scripts``: a ``(chunks, close)``
    pair. It reads one request, sends each chunk with a short pause between
    them, then closes the connection if ``close`` is set. Connections
    without a script are accepted and left idle."""

    def __init__(self, scripts):
        self.scripts = list(scripts)
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, 'ipc.sock')
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(4)
        self.thread = threading.Thread(target=self._accept, daemon=True)
        self.thread.start()

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
            script = self.scripts.pop(0) if self.scripts else None
            threading.Thread(target=self._serve, args=(conn, script), daemon=True).start()

    def _serve(self, conn, script):
        if script is None:
            time.sleep(5)
            conn.close()
            return
        chunks, close = script
        header = self._read_exact(conn, 14)
        _, length, _ = struct.unpack('=6sII', header)
        self._read_exact(conn, length)
        for chunk in chunks:
            conn.sendall(chunk)
            time.sleep(0.05)
        if not close:
            # keep the connection open until the test is done
            time.sleep(5)
        conn.close()

    def cleanup(self):
        self.listener.close()
        os.unlink(self.path)
        os.rmdir(self.dir)


def run_with_timeout(fn, timeout=3):
    """Runs fn in a thread; returns ('ok', value), ('error', exc) or
    ('hung', None) if it has not returned after ``timeout`` seconds."""
    result = {}

    def target():
        try:
            result['ok'] = fn()
        except Exception as e:
            result['error'] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return 'hung', None
    if 'error' in result:
        return 'error', result['error']
    return 'ok', result['ok']


VERSION = {
    'major': 4,
    'minor': 24,
    'patch': 0,
    'human_readable': '4.24',
    'loaded_config_file_name': '/dev/null'
}


@pytest.fixture
def server():
    servers = []

    def make(*scripts):
        s = FakeServer(scripts)
        servers.append(s)
        return s

    yield make
    for s in servers:
        s.cleanup()


def test_header_split_across_reads(server):
    msg = frame(7, VERSION)
    s = server(([msg[:3], msg[3:9], msg[9:]], False))
    conn = Connection(socket_path=s.path)

    status, reply = run_with_timeout(conn.get_version)

    assert status == 'ok', reply
    assert reply.human_readable == '4.24'


def test_payload_split_does_not_swallow_next_message(server):
    first = frame(7, VERSION)
    second = frame(7, dict(VERSION, human_readable='second'))
    # the first reply's payload arrives in two pieces, and the second piece
    # comes together with the whole next message
    s = server(([first[:20], first[20:] + second], False))
    conn = Connection(socket_path=s.path)

    conn._cmd_socket.sendall(conn._pack(MessageType.GET_VERSION, ''))

    status, first_reply = run_with_timeout(lambda: conn._ipc_recv(conn._cmd_socket))
    assert status == 'ok', first_reply
    assert json.loads(first_reply[0])['human_readable'] == '4.24'

    status, second_reply = run_with_timeout(lambda: conn._ipc_recv(conn._cmd_socket))
    assert status == 'ok', second_reply
    assert json.loads(second_reply[0])['human_readable'] == 'second'


def test_connection_closed_mid_payload_raises(server):
    msg = frame(7, VERSION)
    s = server(([msg[:15]], True))
    conn = Connection(socket_path=s.path)

    status, err = run_with_timeout(conn.get_version)

    assert status == 'error', 'get_version() did not return' if status == 'hung' else err
    assert isinstance(err, ConnectionError)


def test_connection_closed_mid_header_raises(server):
    msg = frame(7, VERSION)
    s = server(([msg[:5]], True))
    conn = Connection(socket_path=s.path)

    status, err = run_with_timeout(conn.get_version)

    assert status == 'error', 'get_version() did not return' if status == 'hung' else err
    assert isinstance(err, ConnectionError)


def test_event_loop_returns_when_closed_mid_event(server):
    subscribed = frame(2, {'success': True})
    event = frame(0x80000000 | 7, {'first': False, 'payload': 'x'})
    # first connection: the command socket, idle; second: the event socket
    s = server(None, ([subscribed, event[:16]], True))
    conn = Connection(socket_path=s.path)
    conn.on('tick', lambda i3, e: None)

    status, err = run_with_timeout(conn.main)

    assert status == 'error', 'main() did not return' if status == 'hung' else err
    assert isinstance(err, ConnectionError)
