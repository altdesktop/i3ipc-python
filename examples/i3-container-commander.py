#!/usr/bin/env python3

# This example shows how to implement a simple, but highly configurable window
# switcher (like a much improved "alt-tab") with iterative dmenu calls. This
# script works well for most use cases with no arguments.
#
# https://faq.i3wm.org/question/228/how-do-i-find-an-app-buried-in-some-workspace-by-its-title/

from argparse import ArgumentParser
from subprocess import check_output
from os.path import basename
import i3ipc

i3 = i3ipc.Connection()

parser = ArgumentParser(prog='i3-container-commander.py',
                        description='''
        i3-container-commander.py is a simple but highly configurable
        dmenu-based script for creating dynamic context-based commands for
        controlling top-level windows. With no arguments, it is an efficient
        and ergonomical window switcher.
        ''',
                        epilog='''
        Additional arguments found after "--" will be passed to dmenu.
        ''')

parser.add_argument('--group-by',
                    metavar='PROPERTY',
                    default='window_class',
                    help='''A container property to initially group windows for selection or
        "none" to skip the grouping step. This works best for properties of
        type string. See <http://i3wm.org/docs/ipc.html#_tree_reply> for a list
        of properties. (default: "window_class")''')

parser.add_argument('--command',
                    metavar='COMMAND',
                    default='focus',
                    help='''The command to execute on the container that you end up
        selecting. The command should be a single command or comma-separated
        list such as what is passed to i3-msg. The command will only affect the
        selected container (it will be selected by criteria). (default: "focus")''')

parser.add_argument('--item-format',
                    metavar='FORMAT_STRING',
                    default='{workspace.name}: {container.name}',
                    help='''A Python format string to use to display the menu items. The
        format string will have the container and workspace available as
        template variables. (default: '{workspace.name}: {container.name}')
        ''')

parser.add_argument('--menu', default='dmenu', help='The menu command to run (ex: --menu=rofi)')

(args, menu_args) = parser.parse_known_args()

if len(menu_args) and menu_args[0] == '--':
    menu_args = menu_args[1:]

# set default menu args for supported menus
if basename(args.menu) == 'dmenu':
    menu_args += ['-i', '-f']
elif basename(args.menu) == 'rofi':
    menu_args += ['-show', '-dmenu']


def find_group(container):
    return str(getattr(container, args.group_by)) if args.group_by != 'none' else ''


def show_menu(items, prompt):
    menu_input = bytes(str.join('\n', items), 'UTF-8')
    menu_cmd = [args.menu] + ['-l', str(len(items)), '-p', prompt] + menu_args
    menu_result = check_output(menu_cmd, input=menu_input)
    return menu_result.decode('UTF-8').strip()


def show_container_menu(containers):
    def do_format(c):
        return args.item_format.format(workspace=c.workspace(), container=c)

    items = [do_format(c) for c in containers]
    items.sort()

    menu_result = show_menu(items, args.command)
    for c in containers:
        if do_format(c) == menu_result:
            return c


containers = i3.get_tree().leaves()

if args.group_by:
    groups = dict()

    for c in containers:
        g = find_group(c)
        if g:
            groups[g] = groups[g] + 1 if g in groups else 1

    if len(groups) > 1:
        chosen_group = show_menu(['{} ({})'.format(k, v) for k, v in groups.items()], args.group_by)
        chosen_group = chosen_group[:chosen_group.rindex(' ')]
        containers = list(filter(lambda c: find_group(c) == chosen_group, containers))

if len(containers):
    chosen_container = containers[0] if len(containers) == 1 else show_container_menu(containers)

    if chosen_container:
        chosen_container.command(args.command)
