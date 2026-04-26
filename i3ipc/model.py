from typing import Any, Optional


class Rect:
    """Used by other classes to represent rectangular position and dimensions.

    :ivar x: The x coordinate.
    :vartype x: int
    :ivar y: The y coordinate.
    :vartype y: int
    :ivar height: The height of the rectangle.
    :vartype height: int
    :ivar width: The width of the rectangle.
    :vartype width: int
    """
    def __init__(self, data: dict[str, Any]):
        self.x: int = data['x']
        self.y: int = data['y']
        self.height: int = data['height']
        self.width: int = data['width']


class OutputMode:
    """(sway only) A mode for an output

    :ivar width: The width of the output in this mode.
    :vartype width: int
    :ivar height: The height of the output in this mode.
    :vartype height: int
    :vartype refresh: The refresh rate of the output in this mode.
    :vartype refresh: int
    """
    def __init__(self, data: dict[str, Any]):
        self.width: int = data['width']
        self.height: int = data['height']
        self.refresh: int = data['refresh']

    def __getitem__(self, item: str):
        # for backwards compatability because this used to be a dict
        if not hasattr(self, item):
            raise KeyError(item)
        return getattr(self, item)

    @classmethod
    def _parse_list(cls, data: list[dict[str, Any]]) -> list['OutputMode']:
        return [cls(d) for d in data]


class Gaps:
    """For forks that have useless gaps, the dimension of the gaps.

    :ivar inner: The inner gaps.
    :vartype inner: int
    :ivar outer: The outer gaps.
    :vartype outer: int
    :ivar left: The left outer gaps.
    :vartype left: int or :class:`None` if not supported.
    :ivar right: The right outer gaps.
    :vartype right: int or :class:`None` if not supported.
    :ivar top: The top outer gaps.
    :vartype top: int or :class:`None` if not supported.
    :ivar bottom: The bottom outer gaps.
    :vartype bottom: int or :class:`None` if not supported.
    """
    def __init__(self, data: dict[str, Any]):
        self.inner: int = data['inner']
        self.outer: int = data['outer']
        self.left: Optional[int] = data.get('left', None)
        self.right: Optional[int] = data.get('right', None)
        self.top: Optional[int] = data.get('top', None)
        self.bottom: Optional[int] = data.get('bottom', None)
