#!/usr/bin/env python

import subprocess
from subprocess import Popen
import os
from os import listdir, path
from os.path import isfile, join
import sys
import re
import time
try:
    from shutil import which
except ImportError:
    def which(cmd):
        path = os.getenv('PATH')
        for p in path.split(os.path.pathsep):
            p = os.path.join(p, cmd)
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p

if not hasattr(subprocess, 'run'):
    subprocess.run = subprocess.call

if not hasattr(Popen, '__enter__'):

    def backported_enter(self):
        return self

    def backported_exit(self, type, value, traceback):
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()
        try:  # Flushing a BufferedWriter may raise an error
            if self.stdin:
                self.stdin.close()
        finally:
            # Wait for the process to terminate, to avoid zombies.
            return
            self.wait()

    Popen.__enter__ = backported_enter
    Popen.__exit__ = backported_exit

PYTEST = 'pytest'
XVFB = 'Xvfb'
I3_BINARY = 'i3'
LOCKDIR = '/tmp'

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

    if not which(PYTEST):
        print('pytest is required to run tests')
        print('Command %s not found in PATH' % PYTEST)
        sys.exit(127)

def get_open_display():
    # TODO find the general lock directory
    lock_re = re.compile(r'^\.X([0-9]+)-lock$')
    lock_files = [f for f in listdir(LOCKDIR) if lock_re.match(f)]
    displays = [int(lock_re.search(f).group(1)) for f in lock_files]
    open_display = min([i for i in range(0, max(displays or [0]) + 2) if i not in displays])
    return open_display

def start_server(display):
    xvfb = Popen([XVFB, ':%d' % display])
    # wait for the lock file to make sure the server is running
    lockfile = path.join(LOCKDIR, '.X%d-lock' % display)
    tries = 0
    while True:
        if path.exists(lockfile):
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
    env['PYTHONPATH'] = './i3ipc'
    subprocess.run([PYTEST], env=env)

def main():
    check_dependencies()
    display = get_open_display()

    with start_server(display) as server:
        run_pytest(display)
        server.terminate()

if __name__ == '__main__':
    main()
