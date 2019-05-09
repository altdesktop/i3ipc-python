#!/usr/bin/env python3

from argparse import ArgumentParser
from subprocess import call
import i3ipc

i3 = i3ipc.Connection()

parser = ArgumentParser(prog='disable-standby-fs',
                        description='''
        Disable standby (dpms) and screensaver when a window becomes fullscreen
        or exits fullscreen-mode. Requires `xorg-xset`.
        ''')

args = parser.parse_args()


def find_fullscreen(con):
    # XXX remove me when this method is available on the con in a release
    return [c for c in con.descendents() if c.type == 'con' and c.fullscreen_mode]


def set_dpms(state):
    if state:
        print('setting dpms on')
        call(['xset', 's', 'on'])
        call(['xset', '+dpms'])
    else:
        print('setting dpms off')
        call(['xset', 's', 'off'])
        call(['xset', '-dpms'])


def on_fullscreen_mode(i3, e):
    set_dpms(not len(find_fullscreen(i3.get_tree())))


def on_window_close(i3, e):
    if not len(find_fullscreen(i3.get_tree())):
        set_dpms(True)


i3.on('window::fullscreen_mode', on_fullscreen_mode)
i3.on('window::close', on_window_close)

i3.main()
