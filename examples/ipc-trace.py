#!/usr/bin/env python3

import i3ipc
from time import strftime, gmtime

i3 = i3ipc.Connection()


def print_separator():
    print('-----')


def print_time():
    print(strftime(strftime("%Y-%m-%d %H:%M:%S", gmtime())))


def print_con_info(con):
    if con:
        print('Id: %s' % con.id)
        print('Name: %s' % con.name)
    else:
        print('(none)')


def on_window(i3, e):
    print_separator()
    print('Got window event:')
    print_time()
    print('Change: %s' % e.change)
    print_con_info(e.container)


def on_workspace(i3, e):
    print_separator()
    print('Got workspace event:')
    print_time()
    print('Change: %s' % e.change)
    print('Current:')
    print_con_info(e.current)
    print('Old:')
    print_con_info(e.old)


# TODO subscribe to all events

i3.on('window', on_window)
i3.on('workspace', on_workspace)

i3.main()
