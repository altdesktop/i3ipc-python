from subprocess import Popen
try:
    from subprocess import run
except ImportError:
    from subprocess import call as run
import pytest
import time
import i3ipc
import threading
from threading import Thread, Condition
import math
from random import random


class IpcTest:
    timeout_thread = None
    i3_conn = None

    @pytest.fixture(scope='class')
    def i3(self):
        process = Popen(['i3', '-c', 'test/i3.config'])
        # wait for i3 to start up
        tries = 0

        while True:
            try:
                IpcTest.i3_conn = i3ipc.Connection()
                break
            except Exception:
                tries += 1

                if tries > 100:
                    raise Exception('could not start i3')
        yield IpcTest.i3_conn
        process.kill()
        IpcTest.i3_conn = None

    def main(self):
        """Start the main thread and wait for events with a timeout"""

        i3 = IpcTest.i3_conn
        assert i3

        def timeout_function(Condition):
            with quit_cv:
                quit_cv.wait(3)
                i3.main_quit()

        quit_cv = Condition()
        self.timeout_thread = Thread(target=timeout_function, args=(quit_cv, ))
        self.timeout_thread.start()
        i3.main()

        with quit_cv:
            quit_cv.notify()

    def open_window(self):
        i3 = IpcTest.i3_conn
        assert i3

        # TODO: use gtk to open windows
        result = i3.command('open')
        return result[0].id

    def fresh_workspace(self):
        i3 = IpcTest.i3_conn
        assert i3

        workspaces = i3.get_workspaces()
        while True:
            new_name = str(math.floor(random() * 100000))
            if not any(w for w in workspaces if w['name'] == new_name):
                i3.command('workspace %s' % new_name)
                return new_name
