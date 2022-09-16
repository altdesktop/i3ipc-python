#!/usr/bin/env python3
# coding=utf-8

"""
Moves windows from workspace 1 to workspace 10 unless marked "_dontmove".

Listens to i3 new/move events, and tells i3 to move windows from workspace 1 to
workspace 10 unless they have a mark that starts with "_dontmove".(It looks for
a prefix because marks need to be unique, and we might want to mark multiple
windows as not needing to be moved.)

Tips:

 - You can have marks in an i3 workspace.json file by having an array named
   "marks" in the nodes dictionary. For example:

        "marks": ["_dontmove3"],
        "swallows": [ ...

 - This script does *not* move windows on startup, so you probably want to run
   it early on. I run it from my .i3/config before starting any apps:

        exec --no-startup-id ~/src/i3ipc-python/examples/avoid-ws.py

See also https://redd.it/4fitpu
"""

import i3ipc

def on_window_event(i3, e):
    w = e.container

    # This is necessary to find the workspace. The container in the event is
    # not wired up to its parents, and the root is where the workspace info is
    # kept.
    w = i3.get_tree().find_by_id(e.container.id)

    ws = w.workspace()
    if ws and ws.name == '1'and not any(
            mark.startswith('_dontmove') for mark in w.marks):
        i3.command('[con_id=%d] move window to workspace 10' % w.id)
        i3.command('workspace 10')


def main():
    i3 = i3ipc.Connection()
    i3.on("window::move", on_window_event)
    i3.on("window::new", on_window_event)
    i3.main()

if __name__ == '__main__':
    main()
