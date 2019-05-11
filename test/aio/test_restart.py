from .ipctest import IpcTest

import pytest


class TestRestart(IpcTest):
    @pytest.mark.asyncio
    async def test_auto_reconnect(self, i3):
        i3._auto_reconnect = True
        await i3.command('restart')
        assert await i3.command('nop')
