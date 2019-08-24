from .ipctest import IpcTest

import pytest
from i3ipc import Event


class TestWindow(IpcTest):
    event = None

    def on_window(self, i3, e):
        TestWindow.event = e
        i3.main_quit()

    @pytest.mark.asyncio
    async def test_window_event(self, i3):
        await self.fresh_workspace()
        await i3.subscribe([Event.WINDOW])
        i3.on(Event.WINDOW, self.on_window)

        self.open_window()

        await i3.main()

        assert TestWindow.event

    @pytest.mark.asyncio
    async def test_marks(self, i3):
        await self.fresh_workspace()
        self.open_window()
        await i3.command('mark foo')
        tree = await i3.get_tree()
        assert 'foo' in tree.find_focused().marks
