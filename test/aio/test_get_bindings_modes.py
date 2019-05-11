from .ipctest import IpcTest

import pytest


class TestBindingModes(IpcTest):
    @pytest.mark.asyncio
    async def test_binding_modes(self, i3):
        binding_modes = await i3.get_binding_modes()
        assert isinstance(binding_modes, list)
        assert len(binding_modes) == 2
        assert 'default' in binding_modes
        assert 'resize' in binding_modes
