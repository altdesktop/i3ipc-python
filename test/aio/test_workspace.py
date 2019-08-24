from .ipctest import IpcTest

import pytest
from i3ipc import Event


class TestWorkspace(IpcTest):
    event = None

    def on_workspace(self, i3, e):
        TestWorkspace.event = e
        i3.main_quit()

    @pytest.mark.asyncio
    async def test_workspace(self, i3):
        await i3.subscribe([Event.WORKSPACE])
        i3.on(Event.WORKSPACE_INIT, self.on_workspace)
        await i3.command('workspace 12')
        await i3.main()
        workspaces = await i3.get_workspaces()

        assert len(workspaces) == 1
        ws = workspaces[0]
        assert ws.name == '12'

        e = TestWorkspace.event
        assert e is not None
        assert e.current.name == '12'
