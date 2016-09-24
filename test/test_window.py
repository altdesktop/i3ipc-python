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
        self.fresh_workspace()
        workspaces = self.i3.get_workspaces()
        self.i3.on('window', self.on_window)
        self.open_window()
        self.main()
        assert self.event

    def test_marks(self):
        ws = self.fresh_workspace()
        self.open_window()
        self.i3.command('mark foo')
        assert 'foo' in self.i3.get_tree().find_focused().marks
