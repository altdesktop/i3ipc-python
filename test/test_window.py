from ipctest import IpcTest
import i3ipc


class TestWindow(IpcTest):
    event = None

    def on_window(self, i3, e):
        self.event = e
        i3.main_quit()

    def test_window_event(self, i3):
        self.fresh_workspace()
        workspaces = i3.get_workspaces()
        i3.on('window', self.on_window)
        self.open_window()
        i3.main(timeout=1)
        assert self.event

    def test_marks(self, i3):
        ws = self.fresh_workspace()
        self.open_window()
        i3.command('mark foo')
        assert 'foo' in i3.get_tree().find_focused().marks
