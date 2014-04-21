#!/usr/bin/env python3

# https://faq.i3wm.org/question/3699/how-can-i-open-an-application-when-i-open-a-certain-workspace-for-the-first-time/

from argparse import ArgumentParser
from gi.repository import i3ipc, GLib

i3 = i3ipc.Connection()

parser = ArgumentParser(description='Open an application on a given workspace when it is initialized')

parser.add_argument('--workspace', metavar='NAME', help='The name of the workspace')
parser.add_argument('--command', metavar='CMD', help='The command to run on the newly initted workspace')

args = parser.parse_args()

def on_workspace(i3, e):
    if e.current.props.name == args.workspace and not len(e.current.leaves()):
        i3.command('exec {}'.format(args.command))

i3.on('workspace::focus', on_workspace)

GLib.MainLoop().run()
