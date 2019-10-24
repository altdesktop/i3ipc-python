#!/usr/bin/env python3

# This example shows how to make any window that opens on a workspace floating

# All workspaces that start with a string in this list will have their windows
# open floating
FLOATING_WORKSPACES = ['3']


def is_ws_floating(name):
    for floating_ws in FLOATING_WORKSPACES:
        if name.startswith(floating_ws):
            return True

    return False


import i3ipc

i3 = i3ipc.Connection()


def on_window_open(i3, e):
    ws = i3.get_tree().find_focused().workspace()
    if is_ws_floating(ws.name):
        e.container.command('floating toggle')


i3.on('window::new', on_window_open)

i3.main()
