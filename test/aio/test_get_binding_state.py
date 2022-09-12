from .ipctest import IpcTest
import i3ipc

import pytest


class TestBindingState(IpcTest):
    @pytest.mark.asyncio
    async def test_binding_state(self, i3):
        binding_state = await i3.get_binding_state()
        assert isinstance(binding_state, i3ipc.BindingStateReply)

        await i3.command('mode default')
        binding_state = await i3.get_binding_state()
        assert binding_state.name == 'default'
        await i3.command('mode resize')
        binding_state = await i3.get_binding_state()
        assert binding_state.name == 'resize'
