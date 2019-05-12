from .ipctest import IpcTest

import pytest
import asyncio


class HandlerException(Exception):
    pass


class TestEventExceptions(IpcTest):
    def exception_throwing_handler(self, i3, e):
        raise HandlerException()

    @pytest.mark.asyncio
    async def test_event_exceptions(self, i3):
        i3.on('window', self.exception_throwing_handler)

        def open_window():
            asyncio.ensure_future(self.open_window())

        i3._loop.call_later(0.1, open_window)

        with pytest.raises(HandlerException):
            await i3.main()
