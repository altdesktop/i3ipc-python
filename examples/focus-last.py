#!/usr/bin/env python3

import os
import socket
import selectors
from argparse import ArgumentParser
from multiprocessing import Process, Value
from gi.repository import i3ipc

SOCKET_FILE = '/tmp/i3_focus_last'


class FocusWatcher:

    def __init__(self):
        self.window_id = Value('i', 0)
        self.old_window_id = Value('i', 0)
        self.i3 = i3ipc.Connection()
        self.i3.on('window::focus', self.on_window_focus)
        self.listening_socket = socket.socket(socket.AF_UNIX,
            socket.SOCK_STREAM)
        if os.path.exists(SOCKET_FILE):
            os.remove(SOCKET_FILE)
        self.listening_socket.bind(SOCKET_FILE)
        self.listening_socket.listen(1)

    def on_window_focus(self, i3conn, event):
        self.old_window_id.value = self.window_id.value
        self.window_id.value = event.container.props.id

    def launch_i3(self):
        self.i3.main()

    def launch_server(self):
        selector = selectors.DefaultSelector()

        def accept(sock):
            conn, addr = sock.accept()
            selector.register(conn, selectors.EVENT_READ, read)

        def read(conn):
            data = conn.recv(1024)
            if data == b'switch':
                window_id = self.old_window_id.value
                if window_id:
                    self.i3.command('[con_id=%s] focus' %
                        self.old_window_id.value)
            elif not data:
                selector.unregister(conn)
                conn.close()

        selector.register(self.listening_socket, selectors.EVENT_READ, accept)

        while True:
            for key, event in selector.select():
                callback = key.data
                callback(key.fileobj)

    def run(self):
        p_i3 = Process(target=self.launch_i3)
        p_server = Process(target=self.launch_server)
        for p in (p_i3, p_server):
            p.start()

if __name__ == '__main__':
    parser = ArgumentParser(prog='focus-last.py',
        description='''
        Focus last focused window.

        This script should be launch from the .xsessionrc without argument.

        Then you can bind this script with the `--switch` option to one of your
        i3 keybinding.
        ''')
    parser.add_argument('--switch', dest='switch', action='store_true',
        help='Switch to the previous window', default=False)
    args = parser.parse_args()

    if not args.switch:
        focus_watcher = FocusWatcher()
        focus_watcher.run()
    else:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_FILE)
        client_socket.send('switch'.encode('utf-8'))
        client_socket.close()
