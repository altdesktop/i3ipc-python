from i3ipc import Event

import time
from ipctest import IpcTest
from threading import Timer


class TestWindow(IpcTest):
    def test_window_event(self, i3):
        event = None

        def on_window(i3, e):
            nonlocal event
            event = e
            i3.main_quit()

        i3.on('window', on_window)
        Timer(0.001, self.open_window).start()
        i3.main(timeout=2)

        assert event is not None
        i3.off(on_window)

    def test_marks(self, i3):
        self.fresh_workspace()
        self.open_window()
        i3.command('mark foo')
        assert 'foo' in i3.get_tree().find_focused().marks

    def test_detailed_window_event(self, i3):
        events = []

        def generate_events():
            win1 = self.open_window()
            win2 = self.open_window()
            i3.command(f'[id={win1}] kill; [id={win2}] kill')
            # TODO sync protocol
            time.sleep(0.01)
            i3.main_quit()

        def on_window(i3, e):
            nonlocal events
            events.append(e)

        i3.on(Event.WINDOW_NEW, on_window)
        Timer(0.01, generate_events).start()
        i3.main(timeout=2)

        assert len(events)
        for e in events:
            assert e.change == 'new'

        events.clear()
        i3.off(on_window)

        i3.on(Event.WINDOW_FOCUS, on_window)
        Timer(0.01, generate_events).start()
        i3.main(timeout=2)

        assert len(events)
        for e in events:
            assert e.change == 'focus'
