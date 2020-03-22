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
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.height = data['height']
        self.width = data['width']


class OutputMode:
    """(sway only) A mode for an output

    :ivar width: The width of the output in this mode.
    :vartype width: int
    :ivar height: The height of the output in this mode.
    :vartype height: int
    :vartype refresh: The refresh rate of the output in this mode.
    :vartype refresh: int
    """
    def __init__(self, data):
        self.width = data['width']
        self.height = data['height']
        self.refresh = data['refresh']

    def __getitem__(self, item):
        # for backwards compatability because this used to be a dict
        if not hasattr(self, item):
            raise KeyError(item)
        return getattr(self, item)

    @classmethod
    def _parse_list(cls, data):
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
    def __init__(self, data):
        self.inner = data['inner']
        self.outer = data['outer']
        self.left = data.get('left', None)
        self.right = data.get('right', None)
        self.top = data.get('top', None)
        self.bottom = data.get('bottom', None)
