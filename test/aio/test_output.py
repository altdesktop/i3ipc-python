from .ipctest import IpcTest

import pytest


class TestOutput(IpcTest):
    @pytest.mark.asyncio
    async def test_output(self, i3):
        await i3.command('workspace 12')
        outputs = await i3.get_outputs()

        xroot = next(filter(lambda o: o.name == 'xroot-0', outputs))
        screen = next(filter(lambda o: o.name == 'screen', outputs))

        assert screen.current_workspace == '12'
        assert screen.primary is False
        assert xroot.current_workspace is None
        assert xroot.primary is False
