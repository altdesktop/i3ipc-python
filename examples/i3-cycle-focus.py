#!/usr/bin/env python3
#
# provides alt+tab functionality between windows, switching
# between n windows; example i3 conf to use:
#     exec_always --no-startup-id i3-cycle-focus.py --history 2
#     bindsym $mod1+Tab exec --no-startup-id i3-cycle-focus.py --switch

import os
import asyncio
from argparse import ArgumentParser
import logging

from i3ipc.aio import Connection

SOCKET_FILE = '/tmp/.i3-cycle-focus.sock'
MAX_WIN_HISTORY = 16
UPDATE_DELAY = 2.0


def on_shutdown(i3_conn, e):
    os._exit(0)


class FocusWatcher:
    def __init__(self):
        self.i3 = None
        self.window_list = []
        self.update_task = None
        self.window_index = 1

    async def connect(self):
        self.i3 = await Connection().connect()
        self.i3.on('window::focus', self.on_window_focus)
        self.i3.on('shutdown', on_shutdown)

    async def update_window_list(self, window_id):
        if UPDATE_DELAY != 0.0:
            await asyncio.sleep(UPDATE_DELAY)

        logging.info('updating window list')
        if window_id in self.window_list:
            self.window_list.remove(window_id)

        self.window_list.insert(0, window_id)

        if len(self.window_list) > MAX_WIN_HISTORY:
            del self.window_list[MAX_WIN_HISTORY:]

        self.window_index = 1
        logging.info('new window list: {}'.format(self.window_list))

    async def get_valid_windows(self):
        tree = await self.i3.get_tree()
        if args.active_workspace:
            return set(w.id for w in tree.find_focused().workspace().leaves())
        elif args.visible_workspaces:
            ws_list = []
            w_set = set()
            outputs = await self.i3.get_outputs()
            for item in outputs:
                if item.active:
                    ws_list.append(item.current_workspace)
            for ws in tree.workspaces():
                if str(ws.name) in ws_list:
                    for w in ws.leaves():
                        w_set.add(w.id)
            return w_set
        else:
            return set(w.id for w in tree.leaves())

    async def on_window_focus(self, i3conn, event):
        logging.info('got window focus event')
        if args.ignore_float and (event.container.floating == "user_on"
                                  or event.container.floating == "auto_on"):
            logging.info('not handling this floating window')
            return

        if self.update_task is not None:
            self.update_task.cancel()

        logging.info('scheduling task to update window list')
        self.update_task = asyncio.create_task(self.update_window_list(event.container.id))

    async def run(self):
        async def handle_switch(reader, writer):
            data = await reader.read(1024)
            logging.info('received data: {}'.format(data))
            if data == b'switch':
                logging.info('switching window')
                windows = await self.get_valid_windows()
                logging.info('valid windows = {}'.format(windows))
                for window_id in self.window_list[self.window_index:]:
                    if window_id not in windows:
                        self.window_list.remove(window_id)
                    else:
                        if self.window_index < (len(self.window_list) - 1):
                            self.window_index += 1
                        else:
                            self.window_index = 0
                        logging.info('focusing window id={}'.format(window_id))
                        await self.i3.command('[con_id={}] focus'.format(window_id))
                        break

        server = await asyncio.start_unix_server(handle_switch, SOCKET_FILE)
        await server.serve_forever()


async def send_switch():
    reader, writer = await asyncio.open_unix_connection(SOCKET_FILE)

    logging.info('sending switch message')
    writer.write('switch'.encode())
    await writer.drain()

    logging.info('closing the connection')
    writer.close()
    await writer.wait_closed()


async def run_server():
    focus_watcher = FocusWatcher()
    await focus_watcher.connect()
    await focus_watcher.run()


if __name__ == '__main__':
    parser = ArgumentParser(prog='i3-cycle-focus.py',
                            description="""
        Cycle backwards through the history of focused windows (aka Alt-Tab).
        This script should be launched from ~/.xsession or ~/.xinitrc.
        Use the `--history` option to set the maximum number of windows to be
        stored in the focus history (Default 16 windows).
        Use the `--delay` option to set the delay between focusing the
        selected window and updating the focus history (Default 2.0 seconds).
        Use a value of 0.0 seconds to toggle focus only between the current
        and the previously focused window. Use the `--ignore-floating` option
        to exclude all floating windows when cycling and updating the focus
        history. Use the `--visible-workspaces` option to include windows on
        visible workspaces only when cycling the focus history. Use the
        `--active-workspace` option to include windows on the active workspace
        only when cycling the focus history.

        To trigger focus switching, execute the script from a keybinding with
        the `--switch` option.""")
    parser.add_argument('--history',
                        dest='history',
                        help='Maximum number of windows in the focus history',
                        type=int)
    parser.add_argument('--delay',
                        dest='delay',
                        help='Delay before updating focus history',
                        type=float)
    parser.add_argument('--ignore-floating',
                        dest='ignore_float',
                        action='store_true',
                        help='Ignore floating windows '
                        'when cycling and updating the focus history')
    parser.add_argument('--visible-workspaces',
                        dest='visible_workspaces',
                        action='store_true',
                        help='Include windows on visible '
                        'workspaces only when cycling the focus history')
    parser.add_argument('--active-workspace',
                        dest='active_workspace',
                        action='store_true',
                        help='Include windows on the '
                        'active workspace only when cycling the focus history')
    parser.add_argument('--switch',
                        dest='switch',
                        action='store_true',
                        help='Switch to the previous window',
                        default=False)
    parser.add_argument('--debug', dest='debug', action='store_true', help='Turn on debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.history:
        MAX_WIN_HISTORY = args.history
    if args.delay:
        UPDATE_DELAY = args.delay
    else:
        if args.delay == 0.0:
            UPDATE_DELAY = args.delay
    if args.switch:
        asyncio.run(send_switch())
    else:
        asyncio.run(run_server())
