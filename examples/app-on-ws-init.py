#!/usr/bin/env python3

# https://faq.i3wm.org/question/3699/how-can-i-open-an-application-when-i-open-a-certain-workspace-for-the-first-time/

from argparse import ArgumentParser
import i3ipc

i3 = i3ipc.Connection()

parser = ArgumentParser(description="""Open the given application each time the
    given workspace is created. For instance, running 'app-on-ws-init.py 6
    i3-sensible-terminal' should open your terminal as soon as you create the
    workspace 6.
    """)

parser.add_argument('--workspace',
                    metavar='WS_NAME',
                    nargs='+',
                    required=True,
                    help='The name of the workspaces to run the command on')
parser.add_argument('--command',
                    metavar='CMD',
                    required=True,
                    help='The command to run on the newly initted workspace')

args = parser.parse_args()


def on_workspace(i3, e):
    if e.current.name in args.workspace and not len(e.current.leaves()):
        i3.command('exec {}'.format(args.command))


i3.on('workspace::focus', on_workspace)

i3.main()
