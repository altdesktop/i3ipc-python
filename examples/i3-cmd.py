#!/usr/bin/python3

import i3ipc
from argparse import ArgumentParser
from subprocess import check_output, Popen, CalledProcessError
from sys import exit
from os.path import basename

history = []

parser = ArgumentParser(prog='i3-cmd',
                        description='''
                        i3-cmd is a dmenu-based script that sends the given
                        command to i3.
                        ''',
                        epilog='''
                        Additional arguments after "--" will be passed to
                        the menu command.
                        ''')

parser.add_argument('--menu', default='dmenu', help='The menu command to run (ex: --menu=rofi)')

try:
    with open('/tmp/i3-cmd-history') as f:
        history = f.read().split('\n')
except FileNotFoundError:
    pass

i3 = i3ipc.Connection()

(args, menu_args) = parser.parse_known_args()

if len(menu_args) and menu_args[0] == '--':
    menu_args = menu_args[1:]

# set default menu args for supported menus
if basename(args.menu) == 'dmenu':
    menu_args += ['-i', '-f']
elif basename(args.menu) == 'rofi':
    menu_args += ['-show', '-dmenu', '-p', 'i3-cmd: ']

cmd = ''

try:
    cmd = check_output([args.menu] + menu_args, input=bytes('\n'.join(history),
                                                            'UTF-8')).decode('UTF-8').strip()
except CalledProcessError as e:
    exit(e.returncode)

if not cmd:
    # nothing to do
    exit(0)

result = i3.command(cmd)

cmd_success = True

for r in result:
    if not r.success:
        cmd_success = False
        Popen(['notify-send', 'i3-cmd error', r.error])

if cmd_success:
    with open('/tmp/i3-cmd-history', 'w') as f:
        try:
            history.remove(cmd)
        except ValueError:
            pass
        history.insert(0, cmd)
        f.write('\n'.join(history))
