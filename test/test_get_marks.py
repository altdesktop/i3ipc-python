# coding=utf-8
from __future__ import unicode_literals

from ipctest import IpcTest


class TestGetMarks(IpcTest):
    def test_get_marks(self, i3):
        self.open_window()
        i3.command('mark a')
        i3.command('mark --add b')
        self.open_window()
        i3.command('mark "(╯°□°）╯︵ ┻━┻"')

        marks = i3.get_marks()
        assert isinstance(marks, list)
        assert len(marks) == 3
        assert 'a' in marks
        assert 'b' in marks
        assert '(╯°□°）╯︵ ┻━┻' in marks
