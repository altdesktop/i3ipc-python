#!/usr/bin/env python3

import re
from argparse import ArgumentParser
from functools import reduce
import i3ipc
from tools import App, Lists, Menu, Sockets

parser = ArgumentParser(prog='i3-app-focus.py',
                        description='''
        i3-app-focus.py is dmenu-based script for creating dynamic app switcher.
        ''',
                        epilog='''
        Additional arguments found after "--" will be passed to dmenu.
        ''')
parser.add_argument('--menu', default='dmenu', help='The menu command to run (ex: --menu=rofi)')
parser.add_argument('--socket-file', default='/tmp/i3-app-focus.socket', help='Socket file path')
(args, menu_args) = parser.parse_known_args()

sockets = Sockets(args.socket_file)
containers_info = sockets.get_containers_history()

apps = list(map(App, containers_info))
apps_uniq = reduce(Lists.accum_uniq_apps, apps, [])

i3 = i3ipc.Connection()
menu = Menu(i3, args.menu, menu_args)
menu.show_menu_app(apps_uniq)
