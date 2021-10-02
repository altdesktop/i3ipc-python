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

    def test_detailed_window_event_decorator(self, i3):
        events = []

        def generate_events():
            win1 = self.open_window()
            win2 = self.open_window()
            i3.command(f'[id={win1}] kill; [id={win2}] kill')
            # TODO sync protocol
            time.sleep(0.01)
            i3.main_quit()

        @i3.on(Event.WINDOW_NEW)
        @i3.on(Event.WINDOW_FOCUS)
        def on_window(i3, e):
            nonlocal events
            events.append(e)

        Timer(0.01, generate_events).start()
        i3.main(timeout=2)

        assert len(events)
        for e in events:
            assert e.change in ['new', 'focus']
        assert len([e for e in events if e.change == 'new'])
        assert len([e for e in events if e.change == 'focus'])

        i3.off(on_window)

    def test_resize(self, i3):
        self.fresh_workspace()
        self.open_window()
        i3.command('floating enable')

        self.command_checked('resize set height 200 px; resize set width 250 px')
        con = i3.get_tree().find_focused()

        self.command_checked('resize set width 300 px; resize set height 350 px')
        con2 = i3.get_tree().find_focused()

        def height_width(c):
            return (c.rect.height + c.deco_rect.height, c.rect.width)

        assert height_width(con) == (200, 250)
        assert height_width(con2) == (350, 300)
