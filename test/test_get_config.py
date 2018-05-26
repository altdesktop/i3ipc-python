from ipctest import IpcTest
import i3ipc


class TestGetConfig(IpcTest):
    def test_get_config(self, i3):
        config = i3.get_config()
        assert isinstance(config, i3ipc.ConfigReply)
        with open('test/i3.config') as f:
            assert config.config == f.read()
