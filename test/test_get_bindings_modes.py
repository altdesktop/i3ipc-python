from ipctest import IpcTest


class TestBindingModes(IpcTest):
    def test_binding_modes(self, i3):
        binding_modes = i3.get_binding_modes()
        assert isinstance(binding_modes, list)
        assert len(binding_modes) == 2
        assert 'default' in binding_modes
        assert 'resize' in binding_modes
