from typing import List
from i3ipc.aio.connection import Connection

from i3ipc.events import IpcBaseEvent, ShutdownEvent
from .ipctest import IpcTest

import pytest

import asyncio


class TestShutdownEvent(IpcTest):
    events: List[ShutdownEvent] = []

    def restart_func(self, i3: Connection):
        asyncio.ensure_future(i3.command('restart'))

    def on_shutdown(self, i3: Connection, e: IpcBaseEvent):
        assert isinstance(e, ShutdownEvent)
        self.events.append(e)
        if len(self.events) == 1:
            i3._loop.call_later(0.1, self.restart_func, i3)
        elif len(self.events) == 2:
            i3.main_quit()

    @pytest.mark.asyncio
    async def test_shutdown_event_reconnect(self, i3: Connection):
        i3._auto_reconnect = True
        self.events = []
        i3.on('shutdown::restart', self.on_shutdown)
        i3._loop.call_later(0.1, self.restart_func, i3)
        await i3.main()
        assert len(self.events) == 2
