from subprocess import Popen, run
import pytest
import time
import i3ipc
import threading
from threading import Thread, Condition

class IpcTest:
    i3_process = None
    i3 = None
    timeout_thread = None

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup(self):
        self.i3_process = Popen(['i3', '-c', 'test/i3.config'])
        # wait for i3 to start up
        tries = 0

        while True:
            try:
                self.i3 = i3ipc.Connection()
                break
            except Exception:
                tries += 1

                if tries > 100:
                    raise Exception('could not start i3')


    def main(self):
        """Start the main thread and wait for events with a timeout"""

        def timeout_function(quit_cv: Condition):
            with quit_cv:
                quit_cv.wait(3)
                self.i3.main_quit()

        quit_cv = Condition()
        self.timeout_thread = Thread(target=timeout_function, args=(quit_cv,))
        self.timeout_thread.start()
        self.i3.main()

        with quit_cv:
            quit_cv.notify()

    def __del__(self):
        i3_process.kill()
