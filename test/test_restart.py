from ipctest import IpcTest
import i3ipc


class TestRestart(IpcTest):
    def test_restart_doesnt_crash(self, i3):
        i3.command('restart')
