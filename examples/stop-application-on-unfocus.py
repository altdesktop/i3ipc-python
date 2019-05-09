#!/usr/bin/env python3
"""
Stop an application when unfocused using SIGSTOP
Restart it when focused again using SIGCONT
Useful to save battery / reduce CPU load when running browsers.

Warning: if more than one process with the same name are being run, they
will all be stopped/restarted

Federico Ceratto <federico@firelet.net>
License: GPLv3
"""

import atexit
import i3ipc
import psutil
from argparse import ArgumentParser


class FocusMonitor(object):
    def __init__(self, args):
        self.had_focus = False
        self.class_name = args.class_name
        self.process_name = args.process_name
        self.debug = args.debug
        self.conn = i3ipc.Connection()
        self.conn.on('window::focus', self.focus_change)
        atexit.register(self.continue_at_exit)

    def stop_cont(self, cont=True):
        """Send SIGSTOP/SIGCONT to processes called <name>
        """
        for proc in psutil.process_iter():
            if proc.name() == self.process_name:
                sig = psutil.signal.SIGCONT if cont else psutil.signal.SIGSTOP
                proc.send_signal(sig)
                if self.debug:
                    sig = 'CONT' if cont else 'STOP'
                    print("Sent SIG%s to process %d" % (sig, proc.pid))

    def focus_change(self, i3conn, event):
        """Detect focus change on a process with class class_name.
        On change, stop/continue the process called process_name
        """
        has_focus_now = (event.container.window_class == self.class_name)
        if self.had_focus ^ has_focus_now:
            # The monitored application changed focus state
            self.had_focus = has_focus_now
            self.stop_cont(has_focus_now)

    def continue_at_exit(self):
        """Send SIGCONT on script termination"""
        self.stop_cont(True)

    def run(self):
        try:
            self.conn.main()
        except KeyboardInterrupt:
            print('Exiting on keyboard interrupt')


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('class_name')
    ap.add_argument('process_name')
    ap.add_argument('-d', '--debug', action='store_true')
    return ap.parse_args()


def main():
    args = parse_args()
    fm = FocusMonitor(args)
    fm.run()


if __name__ == '__main__':
    main()
