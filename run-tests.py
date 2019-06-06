#!/usr/bin/env python3

import subprocess
from subprocess import Popen
import os
from os import listdir, path
from os.path import isfile, join
import sys
import re
import time
import random
from shutil import which

here = os.path.abspath(os.path.dirname(__file__))

XVFB = 'Xvfb'
I3_BINARY = 'i3'
SOCKETDIR = '/tmp/.X11-unix'


def check_dependencies():
    if not which(XVFB):
        # TODO make this optional
        print('Xvfb is required to run tests')
        print('Command "%s" not found in PATH' % XVFB)
        sys.exit(127)

    if not which(I3_BINARY):
        print('i3 binary is required to run tests')
        print('Command "%s" not found in PATH' % I3_BINARY)
        sys.exit(127)


def get_open_display():
    if not os.path.isdir(SOCKETDIR):
        sys.stderr.write(
            'warning: could not find the X11 socket directory at {}. Using display 0.\n'
            .format(SOCKETDIR))
        sys.stderr.flush()
        return 0
    socket_re = re.compile(r'^X([0-9]+)$')
    socket_files = [f for f in listdir(SOCKETDIR) if socket_re.match(f)]
    displays = [int(socket_re.search(f).group(1)) for f in socket_files]
    open_display = min(
        [i for i in range(0,
                          max(displays or [0]) + 2) if i not in displays])
    return open_display


def start_server(display):
    xvfb = Popen([XVFB, ':%d' % display])
    # wait for the socket to make sure the server is running
    socketfile = path.join(SOCKETDIR, 'X%d' % display)
    tries = 0
    while True:
        if path.exists(socketfile):
            break
        else:
            tries += 1

            if tries > 100:
                print('could not start x server')
                xvfb.kill()
                sys.exit(1)

            time.sleep(0.1)

    return xvfb


def run_pytest(display):
    env = os.environ.copy()
    env['DISPLAY'] = ':%d' % display
    env['PYTHONPATH'] = here
    env['I3SOCK'] = f'/tmp/i3ipc-test-sock-{display}'
    return subprocess.run(['python3', '-m', 'pytest', '-s'] + sys.argv[1:], env=env)


def main():
    check_dependencies()
    display = get_open_display()

    with start_server(display) as server:
        result = run_pytest(display)
        server.terminate()

    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
