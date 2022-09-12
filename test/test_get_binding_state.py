from ipctest import IpcTest
import i3ipc


class TestBindingState(IpcTest):
    def test_binding_state(self, i3):
        binding_state = i3.get_binding_state()
        assert isinstance(binding_state, i3ipc.BindingStateReply)

        i3.command('mode "default"')
        binding_state = i3.get_binding_state()
        assert binding_state.name == 'default'
        i3.command('mode "resize"')
        binding_state = i3.get_binding_state()
        assert binding_state.name == 'resize'
