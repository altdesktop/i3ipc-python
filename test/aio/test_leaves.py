from .ipctest import IpcTest

import pytest


class TestLeaves(IpcTest):
    @pytest.mark.asyncio
    async def test_workspace_leaves(self, i3):
        ws_name = await self.fresh_workspace()
        con1 = await self.open_window()
        await self.command_checked(f'[id={con1}] floating enable')
        await self.open_window()
        await self.open_window()

        tree = await i3.get_tree()
        ws = [w for w in tree.workspaces() if w.name == ws_name][0]

        assert (len(ws.leaves()) == 3)
