from .ipctest import IpcTest

import pytest
import asyncio
from i3ipc import Event, TickEvent


class TestWorkspace(IpcTest):
    async def on_workspace(self, i3, e):
        await self.events.put(e)

    async def on_tick(self, i3, e):
        await self.events.put(e)

    @pytest.mark.asyncio
    async def test_workspace(self, i3):
        self.events = asyncio.Queue()
        await i3.command('workspace 0')
        await i3.subscribe([Event.WORKSPACE, Event.TICK])

        i3.on(Event.WORKSPACE_FOCUS, self.on_workspace)
        i3.on(Event.TICK, self.on_tick)

        await i3.send_tick()
        assert isinstance(await self.events.get(), TickEvent)
        assert isinstance(await self.events.get(), TickEvent)

        await i3.command('workspace 12')
        e = await self.events.get()

        workspaces = await i3.get_workspaces()

        assert len(workspaces) == 1
        ws = workspaces[0]
        assert ws.name == '12'

        assert e is not None
        assert e.current.name == '12'
