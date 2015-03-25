#!/usr/bin/python3

import i3ipc
from argparse import ArgumentParser
from subprocess import check_output, Popen

history = []

parser = ArgumentParser(prog='i3-cmd',
                        description='''
                        i3-cmd is a dmenu-based script that sends the given
                        command to i3.
                        ''',
                        epilog='''
                        Additional arguments after "--" will be passed to
                        dmenu.
                        ''')

try:
    with open('/tmp/i3-cmd-history') as f:
        history = f.read().split('\n')
except FileNotFoundError:
    pass

i3 = i3ipc.Connection()

(args, menu_args) = parser.parse_known_args()

if len(menu_args) and menu_args[0] == '--':
    menu_args = menu_args[1:]
else:
    menu_args = ['-i', '-f']

menu_cmd = ['dmenu'] + menu_args
cmd = check_output(menu_cmd, input=bytes('\n'.join(history), 'UTF-8'))
cmd = cmd.decode('UTF-8').strip()

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
