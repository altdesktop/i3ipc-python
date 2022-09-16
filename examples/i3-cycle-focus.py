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
        self.window_list = {} if KEYED_CONF else []
        self.update_task = None
        self.window_index = {} if KEYED_CONF else [1]

    async def connect(self):
        self.i3 = await Connection().connect()
        self.i3.on('window::focus', self.on_window_focus)
        self.i3.on('shutdown', on_shutdown)

    async def update_window_list(self, container):
        if UPDATE_DELAY != 0.0:
            await asyncio.sleep(UPDATE_DELAY)

        logging.info('updating window list')

        if KEYED_CONF:
            key = (container.ipc_data['output'] if PER_OUTPUT
                    else (await self.i3.get_tree()).find_focused().workspace().id)
            wlist = self.window_list.get(key)
            if wlist is None:
                wlist = self.window_list[key] = []

            self.window_index[key] = [1]
        else:
            wlist = self.window_list
            self.window_index[0] = 1

        window_id = container.id
        if window_id in wlist:
            wlist.remove(window_id)

        wlist.insert(0, window_id)

        if len(wlist) > MAX_WIN_HISTORY:
            del wlist[MAX_WIN_HISTORY:]

        logging.info('new window list: {}'.format(wlist))

    async def get_valid_windows(self, tree, focused_ws):
        if args.active_workspace or args.focused_workspace:
            return set(w.id for w in focused_ws.leaves())
        elif args.visible_workspaces:
            ws_list = []
            w_set = set()
            outputs = await self.i3.get_outputs()
            for output in outputs:
                if output.active:
                    ws_list.append(output.current_workspace)
            for ws in tree.workspaces():
                if str(ws.name) in ws_list:
                    for w in ws.leaves():
                        w_set.add(w.id)
            return w_set
        elif args.focused_output:
            w_set = set()
            focused_output = focused_ws.ipc_data['output']
            for ws in tree.workspaces():
                if ws.ipc_data['output'] == focused_output:
                    for w in ws.leaves():
                        w_set.add(w.id)
            return w_set
        else:
            return set(w.id for w in tree.leaves())

    async def on_window_focus(self, i3conn, event):
        logging.info('got window focus event')
        if args.ignore_float and (event.container.floating == 'user_on'
                                  or event.container.floating == 'auto_on'):
            logging.info('not handling this floating window')
            return

        if self.update_task is not None:
            self.update_task.cancel()

        logging.info('scheduling task to update window list')
        self.update_task = asyncio.create_task(self.update_window_list(event.container))

    async def run(self):
        async def handle_switch(reader, writer):
            data = await reader.read(1024)
            logging.info('received data: {}'.format(data))
            if data == b'switch':
                logging.info('switching window')
                tree = await self.i3.get_tree()
                focused_ws = tree.find_focused().workspace()

                wlist = self.window_list
                widx = self.window_index
                if KEYED_CONF:
                    key = focused_ws.ipc_data['output'] if PER_OUTPUT else focused_ws.id
                    wlist = wlist.get(key)
                    if wlist is None:
                        return
                    widx = widx.get(key)

                windows = await self.get_valid_windows(tree, focused_ws)
                logging.info('valid windows = {}'.format(windows))

                for window_id in wlist[widx[0]:]:
                    if window_id not in windows:
                        wlist.remove(window_id)
                    else:
                        if widx[0] < (len(wlist) - 1):
                            widx[0] += 1
                        else:
                            widx[0] = 0
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
    mutex_group = parser.add_mutually_exclusive_group()

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
    mutex_group.add_argument('--visible-workspaces',
                        dest='visible_workspaces',
                        action='store_true',
                        help='Include windows on visible '
                        'workspaces only when cycling the focus history')
    mutex_group.add_argument('--active-workspace',
                        dest='active_workspace',
                        action='store_true',
                        help='Include windows on the '
                        'active workspace only when cycling the focus history')
    mutex_group.add_argument('--focused-workspace',
                        dest='focused_workspace',
                        action='store_true',
                        help='Include windows on the '
                        'focused workspace only when cycling the focus history')
    mutex_group.add_argument('--focused-output',
                        dest='focused_output',
                        action='store_true',
                        help='Include windows on the '
                        'focused output/screen only when cycling the focus history')
    mutex_group.add_argument('--switch',
                        dest='switch',
                        action='store_true',
                        help='Switch to the previous window',
                        default=False)
    parser.add_argument('--debug', dest='debug', action='store_true', help='Turn on debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.switch:
        asyncio.run(send_switch())
    else:
        if args.history:
            MAX_WIN_HISTORY = args.history

        if args.delay or args.delay == 0.0:
            UPDATE_DELAY = args.delay

        PER_OUTPUT = args.focused_output
        PER_WS = args.focused_workspace
        KEYED_CONF = PER_OUTPUT or PER_WS

        asyncio.run(run_server())
