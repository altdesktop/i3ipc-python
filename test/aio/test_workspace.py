from .ipctest import IpcTest

import pytest
import asyncio
from i3ipc import Event

events = asyncio.Queue()

class TestWorkspace(IpcTest):

    async def on_workspace(self, i3, e):
        await events.put(e)

    @pytest.mark.asyncio
    async def test_workspace(self, i3):
        await i3.command('workspace 0')
        await i3.subscribe([Event.WORKSPACE])
        i3.on(Event.WORKSPACE_FOCUS, self.on_workspace)
        await i3.command('workspace 12')
        e = await events.get()

        workspaces = await i3.get_workspaces()

        assert len(workspaces) == 1
        ws = workspaces[0]
        assert ws.name == '12'

        assert e is not None
        assert e.current.name == '12'
