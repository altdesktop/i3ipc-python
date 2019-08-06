from ipctest import IpcTest
from threading import Timer


class TestWindow(IpcTest):
    event = None

    def on_window(self, i3, e):
        TestWindow.event = e
        i3.main_quit()

    def test_window_event(self, i3):
        self.fresh_workspace()
        i3.get_workspaces()
        i3.on('window', self.on_window)
        Timer(0.1, self.open_window).start()
        i3.main(timeout=2)
        assert self.event is not None

    def test_marks(self, i3):
        self.fresh_workspace()
        self.open_window()
        i3.command('mark foo')
        assert 'foo' in i3.get_tree().find_focused().marks
