from .ipctest import IpcTest

import pytest


class TestScratchpad(IpcTest):
    @pytest.mark.asyncio
    async def test_scratchpad(self, i3):
        scratchpad = (await i3.get_tree()).scratchpad()
        assert scratchpad is not None
        assert scratchpad.name == '__i3_scratch'
        assert scratchpad.type == 'workspace'
        assert not scratchpad.floating_nodes
        win = self.open_window()
        await i3.command('move scratchpad')
        scratchpad = (await i3.get_tree()).scratchpad()
        assert scratchpad is not None
        assert scratchpad.floating_nodes
