from .ipctest import IpcTest

from i3ipc import (VersionReply, BarConfigReply, OutputReply, WorkspaceReply, ConfigReply,
                   TickReply)
from i3ipc.aio import Con

import pytest


class TestResquests(IpcTest):
    @pytest.mark.asyncio
    async def test_requests(self, i3):
        resp = await i3.get_version()
        assert type(resp) is VersionReply

        resp = await i3.get_bar_config_list()
        assert type(resp) is list
        assert 'bar-0' in resp

        resp = await i3.get_bar_config('bar-0')
        assert type(resp) is BarConfigReply

        resp = await i3.get_outputs()
        assert type(resp) is list
        assert resp
        assert type(resp[0]) is OutputReply

        resp = await i3.get_workspaces()
        assert type(resp) is list
        assert resp
        assert type(resp[0]) is WorkspaceReply

        resp = await i3.get_tree()
        assert type(resp) is Con

        resp = await i3.get_marks()
        assert type(resp) is list

        resp = await i3.get_binding_modes()
        assert type(resp) is list

        resp = await i3.get_config()
        assert type(resp) is ConfigReply

        resp = await i3.send_tick()
        assert type(resp) is TickReply
