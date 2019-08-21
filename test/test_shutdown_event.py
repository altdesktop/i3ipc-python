from threading import Timer
from ipctest import IpcTest


class TestShutdownEvent(IpcTest):
    events = []

    def restart_func(self, i3):
        i3.command('restart')

    def on_shutdown(self, i3, e):
        self.events.append(e)
        assert i3._wait_for_socket()
        if len(self.events) == 1:
            Timer(0.1, self.restart_func, args=(i3, )).start()
        elif len(self.events) == 2:
            i3.main_quit()

    def test_shutdown_event_reconnect(self, i3):
        i3._auto_reconnect = True
        self.events = []
        i3.on('shutdown::restart', self.on_shutdown)
        Timer(0.2, self.restart_func, args=(i3, )).start()
        i3.main(timeout=1)
        assert len(self.events) == 2
