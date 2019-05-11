from .ipctest import IpcTest

import pytest


class TestGetMarks(IpcTest):
    @pytest.mark.asyncio
    async def test_get_marks(self, i3):
        await self.open_window()
        await self.command_checked('mark a')
        await self.command_checked('mark --add b')
        await self.open_window()
        await self.command_checked('mark "(╯°□°）╯︵ ┻━┻"')

        marks = await i3.get_marks()
        assert isinstance(marks, list)
        assert len(marks) == 3
        assert 'a' in marks
        assert 'b' in marks
        assert '(╯°□°）╯︵ ┻━┻' in marks
