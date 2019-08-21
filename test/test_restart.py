from ipctest import IpcTest


class TestRestart(IpcTest):
    def test_auto_reconnect(self, i3):
        i3._auto_reconnect = True
        i3.command('restart')
        assert i3.command('nop')
