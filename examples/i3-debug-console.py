#!/usr/bin/env python3

import i3ipc
from curses import wrapper


def con_type_to_text(con):
    if con.type != 'con':
        return con.type
    if len(con.nodes):
        return 'container'
    else:
        return 'view'


def layout_txt(con):
    if con.layout == 'splith':
        return 'HORIZ'
    elif con.layout == 'splitv':
        return 'VERT'
    else:
        return ''


def container_to_text(con, indent):
    t = con_type_to_text(con)
    txt = (' ' * indent) + '('
    txt += t + ' ' + layout_txt(con)

    if con.focused:
        txt += ' focus'

    has_children = len(con.nodes)

    for c in con.nodes:
        txt += '\n'
        txt += container_to_text(c, indent + 4)

    if has_children:
        txt += '\n' + (' ' * indent)

    txt += ')'

    return txt


last_txt = ''


def main(stdscr):
    ipc = i3ipc.Connection()

    def on_event(ipc, e):
        txt = ''
        for ws in ipc.get_tree().workspaces():
            txt += container_to_text(ws, 0) + '\n'

        global last_txt
        if txt == last_txt:
            return

        stdscr.clear()
        for l in txt:
            try:
                stdscr.addstr(l)
            except Exception:
                break
        stdscr.refresh()
        last_txt = txt

    on_event(ipc, None)

    ipc.on('window', on_event)
    ipc.on('binding', on_event)
    ipc.on('workspace', on_event)

    ipc.main()


wrapper(main)
