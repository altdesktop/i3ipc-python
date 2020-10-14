from ipctest import IpcTest


class TestLeaves(IpcTest):
    def test_workspace_leaves(self, i3):
        ws_name = self.fresh_workspace()
        con1 = self.open_window()
        assert not i3.get_tree().find_focused().is_floating()
        i3.command('[id=%s] floating enable' % con1)
        assert i3.get_tree().find_focused().is_floating()
        self.open_window()
        self.open_window()

        ws = [w for w in i3.get_tree().workspaces() if w.name == ws_name][0]

        assert (len(ws.leaves()) == 3)
