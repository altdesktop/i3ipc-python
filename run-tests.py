#!/usr/bin/env python3

import subprocess
from subprocess import Popen
import os
from os import listdir, path
from os.path import isfile, join
from shutil import which
import sys
import re
import time

PYTEST = 'py.test-3.5'
XEPHYR = 'Xephyr'
XVFB_RUN = 'xvfb-run'
I3_BINARY = 'i3'
LOCKDIR = '/tmp'

def check_dependencies():
    if not which(XEPHYR):
        print('Xephyr is required to run tests')
        print('Command "%s" not found in PATH' % XEPHYR)
        sys.exit(127)

    if not which(XVFB_RUN):
        # TODO make this optional
        print('Xvfb is required to run tests')
        print('Command "%s" not found in PATH' % XVFB_RUN)
        sys.exit(127)

    if not which(I3_BINARY):
        print('i3 binary is required to run tests')
        print('Command "%s" not found in PATH' % I3_BINARY)
        sys.exit(127)

def get_open_display():
    # TODO find the general lock directory
    lock_re = re.compile(r'^\.X([0-9]+)-lock$')
    lock_files = [f for f in listdir(LOCKDIR) if lock_re.match(f)]
    displays = [int(lock_re.search(f).group(1)) for f in lock_files]
    open_display = min([i for i in range(0, max(displays) + 2) if i not in displays])
    return open_display

def start_xephyr(display):
    process = Popen([XVFB_RUN, XEPHYR, ':%d' % display])
    # wait for the lock file to make sure xephyr is running
    lockfile = path.join(LOCKDIR, '.X%d-lock' % display)
    tries = 0
    while True:
        if path.exists(lockfile):
            break
        else:
            tries += 1

            if tries > 100:
                print('could not start Xephyr server')
                process.kill()
                sys.exit(1)

            time.sleep(0.1)

    return process

def run_pytest(display):
    env = os.environ.copy()
    env['DISPLAY'] = ':%d' % display
    env['PYTHONPATH'] = './i3ipc'
    subprocess.run([PYTEST], env=env)

def main():
    display = get_open_display()

    with start_xephyr(display) as xephyr:
        run_pytest(display)
        xephyr.kill()

if __name__ == '__main__':
    main()
