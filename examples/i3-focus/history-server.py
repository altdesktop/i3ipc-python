#!/usr/bin/env python3

import os
import socket
import selectors
import threading
import json
from argparse import ArgumentParser
import i3ipc

MAX_WIN_HISTORY = 15

parser = ArgumentParser(prog='i3-app-focus.py', description='''''', epilog='''''')
parser.add_argument('--socket-file', default='/tmp/i3-app-focus.socket', help='Socket file path')
(args, other) = parser.parse_known_args()


class FocusWatcher:
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.i3.on('window::focus', self._on_window_focus)
        self.listening_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(args.socket_file):
            os.remove(args.socket_file)
        self.listening_socket.bind(args.socket_file)
        self.listening_socket.listen(2)
        self.window_list = []
        self.window_list_lock = threading.RLock()

    def run(self):
        t_i3 = threading.Thread(target=self._launch_i3)
        t_server = threading.Thread(target=self._launch_server)
        for t in (t_i3, t_server):
            t.start()

    def _on_window_focus(self, i3conn, event):
        window_id = event.container.id
        con = self.i3.get_tree().find_by_id(window_id)
        if not self._is_window(con):
            return

        with self.window_list_lock:
            if window_id in self.window_list:
                self.window_list.remove(window_id)
            self.window_list.insert(0, window_id)
            if len(self.window_list) > MAX_WIN_HISTORY:
                del self.window_list[MAX_WIN_HISTORY:]

    def _launch_i3(self):
        self.i3.main()

    def _launch_server(self):
        selector = selectors.DefaultSelector()

        def accept(sock):
            conn, addr = sock.accept()
            tree = self.i3.get_tree()
            info = []
            with self.window_list_lock:
                for window_id in self.window_list:
                    con = tree.find_by_id(window_id)
                    if con:
                        info.append({
                            "id": con.id,
                            "window": con.window,
                            "window_title": con.window_title,
                            "window_class": con.window_class,
                            "window_role": con.window_role,
                            "focused": con.focused
                        })

            conn.send(json.dumps(info).encode())
            conn.close()

        selector.register(self.listening_socket, selectors.EVENT_READ, accept)

        while True:
            for key, event in selector.select():
                callback = key.data
                callback(key.fileobj)

    @staticmethod
    def _is_window(con):
        return not con.nodes and con.type == "con" and (con.parent and con.parent.type != "dockarea"
                                                        or True)


focus_watcher = FocusWatcher()
focus_watcher.run()
