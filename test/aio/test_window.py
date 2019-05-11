from .ipctest import IpcTest

import pytest
import asyncio


class TestWindow(IpcTest):
    event = None

    def on_window(self, i3, e):
        self.event = e
        i3.main_quit()

    @pytest.mark.asyncio
    async def test_window_event(self, i3):
        await self.fresh_workspace()
        i3.on('window', self.on_window)
        asyncio.ensure_future(self.open_window())
        await i3.main()
        assert self.event

    @pytest.mark.asyncio
    async def test_marks(self, i3):
        await self.fresh_workspace()
        await self.open_window()
        await i3.command('mark foo')
        tree = await i3.get_tree()
        assert 'foo' in tree.find_focused().marks
