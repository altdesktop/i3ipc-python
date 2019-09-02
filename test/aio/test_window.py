from .ipctest import IpcTest
from i3ipc import Event

import pytest
import asyncio


class TestWindow(IpcTest):
    @pytest.mark.asyncio
    async def test_window_event(self, i3):
        event = None

        def on_window(i3, e):
            nonlocal event
            event = e
            i3.main_quit()

        await i3.subscribe([Event.WINDOW])
        i3.on(Event.WINDOW, on_window)

        self.open_window()

        await i3.main()

        assert event

        i3.off(on_window)

    @pytest.mark.asyncio
    async def test_detailed_window_event(self, i3):
        events = []

        def on_window(i3, e):
            events.append(e)

        async def generate_events():
            win1 = self.open_window()
            win2 = self.open_window()
            await i3.command(f'[id={win1}] kill; [id={win2}] kill')
            # TODO sync protocol
            await asyncio.sleep(0.01)
            i3.main_quit()

        await i3.subscribe([Event.WINDOW])

        i3.on(Event.WINDOW_NEW, on_window)

        asyncio.ensure_future(generate_events())
        await i3.main()
        i3.off(on_window)

        assert len(events)
        for e in events:
            assert e.change == 'new'

        events.clear()

        i3.on(Event.WINDOW_FOCUS, on_window)

        asyncio.ensure_future(generate_events())
        await i3.main()
        i3.off(on_window)

        assert len(events)
        for e in events:
            assert e.change == 'focus'

    @pytest.mark.asyncio
    async def test_marks(self, i3):
        await self.fresh_workspace()
        self.open_window()
        await i3.command('mark foo')
        tree = await i3.get_tree()
        assert 'foo' in tree.find_focused().marks
