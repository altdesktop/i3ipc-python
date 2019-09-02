from ipctest import IpcTest

from threading import Timer
import pytest


class HandlerException(Exception):
    pass


class TestEventExceptions(IpcTest):
    def exception_throwing_handler(self, i3, e):
        raise HandlerException()

    def test_event_exceptions(self, i3):
        i3.on('tick', self.exception_throwing_handler)

        Timer(0.001, i3.send_tick).start()

        with pytest.raises(HandlerException):
            i3.main()
