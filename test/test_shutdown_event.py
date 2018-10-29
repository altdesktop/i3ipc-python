from threading import Timer
from ipctest import IpcTest
import i3ipc


class TestShutdownEvent(IpcTest):
    event = None

    def restart_func(t, i3):
        i3.command('restart')

    def on_shutdown(self, i3, e):
        self.event = e
        i3.main_quit()

    def test_shutdown_event(self, i3):
        i3.on('shutdown::restart', self.on_shutdown)
        Timer(0.001, self.restart_func, args=(i3, )).start()
        i3.main(timeout=1)
        assert self.event
