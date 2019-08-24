class Rect:
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.height = data['height']
        self.width = data['width']


class Gaps:
    def __init__(self, data):
        self.inner = data['inner']
        self.outer = data['outer']
