from ipctest import IpcTest
import i3ipc
import io


class TestGetConfig(IpcTest):
    def test_get_config(self, i3):
        config = i3.get_config()
        assert isinstance(config, i3ipc.ConfigReply)
        with io.open('test/i3.config', 'r', encoding='utf-8') as f:
            assert config.config == f.read()
