#!/usr/bin/env python3

# This example shows how to run a command when i3 exits
#
# https://faq.i3wm.org/question/3468/run-a-command-when-i3-exits/

# This is the command to run
COMMAND = [ 'echo', 'hello, world' ]

from gi.repository import i3ipc
from subprocess import Popen

def on_shutdown(i3):
    Popen(COMMAND)

i3 = i3ipc.Connection()

i3.on('ipc-shutdown', on_shutdown)

i3.main()
