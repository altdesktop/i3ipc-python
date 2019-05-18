from .ipctest import IpcTest

import pytest
import asyncio


class TestTicks(IpcTest):
    events = []

    async def on_tick(self, i3, e):
        self.events.append(e)
        if len(self.events) == 3:
            i3.main_quit()

    @pytest.mark.asyncio
    async def test_tick_event(self, i3):
        i3.on('tick', self.on_tick)

        def send_ticks():
            asyncio.ensure_future(i3.send_tick())
            asyncio.ensure_future(i3.send_tick('hello world'))

        i3._loop.call_later(0.1, send_ticks)

        await i3.main()

        assert len(self.events) == 3
        assert self.events[0].first
        assert self.events[0].payload == ''
        assert not self.events[1].first
        assert self.events[1].payload == ''
        assert not self.events[2].first
        assert self.events[2].payload == 'hello world'
