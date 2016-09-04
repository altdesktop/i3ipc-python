from subprocess import Popen, run
import pytest
import time
import i3ipc

class IpcTest:
    i3_process = None
    i3 = None

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

    def __del__(self):
        i3_process.kill()
