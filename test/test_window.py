from ipctest import IpcTest
import i3ipc
import time
import subprocess
from subprocess import check_output
from threading import Thread
import sys

class TestWindow(IpcTest):
    event = None

    def on_window(self, i3, e):
        self.event = e
        i3.main_quit()

    def test_window_event(self):
        self.i3.on('window', self.on_window)
        self.i3.command('open')
        self.main()
        assert self.event
