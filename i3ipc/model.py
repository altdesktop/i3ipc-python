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


class Gaps:
    """For forks that have useless gaps, the dimension of the gaps.

    :ivar inner: The inner gaps.
    :vartype inner: int
    :ivar outer: The outer gaps.
    :vartype outer: int
    """

    def __init__(self, data):
        self.inner = data['inner']
        self.outer = data['outer']
