import re
from collections import deque


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


class Con(object):
    """
    The container class. Has all internal information about the windows,
    outputs, workspaces and containers that :command:`i3` manages.

    .. attribute:: id

        The internal ID (actually a C pointer value within i3) of the container.
        You can use it to (re-)identify and address containers when talking to
        i3.

    .. attribute:: name

        The internal name of the container.  ``None`` for containers which
        are not leaves.  The string `_NET_WM_NAME <://specifications.freedesktop.org/wm-spec/1.3/ar01s05.html#idm140238712347280>`_
        for windows. Read-only value.

    .. attribute:: type

        The type of the container. Can be one of ``root``, ``output``, ``con``,
        ``floating_con``, ``workspace`` or ``dockarea``.

    .. attribute:: window_title

        The window title.

    .. attribute:: window_class

        The window class.

    .. attribute:: instance

        The instance name of the window class.

    .. attribute:: gaps

        The inner and outer gaps devation from default values.

    .. attribute:: border

        The type of border style for the selected container. Can be either
        ``normal``, ``none`` or ``1pixel``.

    .. attribute:: current_border_width

       Returns amount of pixels for the border. Readonly value. See `i3's user
       manual <https://i3wm.org/docs/userguide.html#_border_style_for_new_windows>_
       for more info.

    .. attribute:: layout

        Can be either ``splith``, ``splitv``, ``stacked``, ``tabbed``, ``dockarea`` or
        ``output``.
        :rtype: string

    .. attribute:: percent

        The percentage which this container takes in its parent. A value of
        null means that the percent property does not make sense for this
        container, for example for the root container.
        :rtype: float

    .. attribute:: rect

        The absolute display coordinates for this container. Display
        coordinates means that when you have two 1600x1200 monitors on a single
        X11 Display (the standard way), the coordinates of the first window on
        the second monitor are ``{ "x": 1600, "y": 0, "width": 1600, "height":
        1200 }``.

    .. attribute:: window_rect

        The coordinates of the *actual client window* inside the container,
        without the window decorations that may also occupy space.

    .. attribute:: deco_rect

        The coordinates of the window decorations within a container. The
        coordinates are relative to the container and do not include the client
        window.

    .. attribute:: geometry

        The original geometry the window specified when i3 mapped it. Used when
        switching a window to floating mode, for example.

    .. attribute:: window

        The X11 window ID of the client window.

    .. attribute:: focus

        A list of container ids describing the focus situation within the current
        container. The first element refers to the container with (in)active focus.

    .. attribute:: focused

        Whether or not the current container is focused. There is only
        one focused container.

    .. attribute:: visible

        Whether or not the current container is visible.

    .. attribute:: num

        Optional attribute that only makes sense for workspaces. This allows
        for arbitrary and changeable names, even though the keyboard
        shortcuts remain the same.  See `the i3wm docs <https://i3wm.org/docs/userguide.html#_named_workspaces>`_
        for more information

    .. attribute:: urgent

        Whether the window or workspace has the `urgent` state.

        :returns: :bool:`True` or :bool:`False`.

    .. attribute:: floating

        Whether the container is floating or not. Possible values are
        "auto_on", "auto_off", "user_on" and "user_off"

    .. attribute:: pid

        The id of the process who owns the client window
        sway only, version >= 1.0-alpha.6

    ..
        command <-- method
        command_children <-- method
        deco_rect IPC
        descendents
        find_by_id
        find_by_role
        find_by_window
        find_classed
        find_focused
        find_fullscreen
        find_marked
        find_named
        find_titled
        floating
        floating_nodes
        fullscreen_mode
        gaps
        leaves
        marks
        nodes
        orientation
        parent
        props
        root
        scratchpad
        scratchpad_state
        window_class
        window_instance
        window_rect
        window_role
        workspace
        workspaces


    """

    def __init__(self, data, parent, conn):
        self._conn = conn
        self.parent = parent

        # set simple properties
        ipc_properties = [
            'border', 'current_border_width', 'floating', 'focus', 'focused', 'fullscreen_mode',
            'id', 'layout', 'marks', 'name', 'num', 'orientation', 'percent', 'scratchpad_state',
            'sticky', 'type', 'urgent', 'window', 'pid'
        ]
        for attr in ipc_properties:
            if attr in data:
                setattr(self, attr, data[attr])
            else:
                setattr(self, attr, None)

        # XXX in 4.12, marks is an array (old property was a string "mark")
        if not self.marks:
            self.marks = []
            if 'mark' in data and data['mark']:
                self.marks.append(data['mark'])

        # XXX this is for compatability with 4.8
        if isinstance(self.type, int):
            if self.type == 0:
                self.type = "root"
            elif self.type == 1:
                self.type = "output"
            elif self.type == 2 or self.type == 3:
                self.type = "con"
            elif self.type == 4:
                self.type = "workspace"
            elif self.type == 5:
                self.type = "dockarea"

        # set complex properties
        self.nodes = []
        if 'nodes' in data:
            for n in data['nodes']:
                self.nodes.append(self.__class__(n, self, conn))

        self.floating_nodes = []
        if 'floating_nodes' in data:
            for n in data['floating_nodes']:
                self.floating_nodes.append(self.__class__(n, self, conn))

        self.window_class = None
        self.window_instance = None
        self.window_role = None
        self.window_title = None
        if 'window_properties' in data:
            if 'class' in data['window_properties']:
                self.window_class = data['window_properties']['class']
            if 'instance' in data['window_properties']:
                self.window_instance = data['window_properties']['instance']
            if 'window_role' in data['window_properties']:
                self.window_role = data['window_properties']['window_role']
            if 'title' in data['window_properties']:
                self.window_title = data['window_properties']['title']

        if 'app_id' in data:
            self.app_id = data['app_id']

        self.rect = Rect(data['rect'])
        if 'window_rect' in data:
            self.window_rect = Rect(data['window_rect'])
        if 'deco_rect' in data:
            self.deco_rect = Rect(data['deco_rect'])

        self.gaps = None
        if 'gaps' in data:
            self.gaps = Gaps(data['gaps'])

    def __iter__(self):
        """
        Iterate through the descendents of this node (breadth-first tree traversal)
        """
        queue = deque(self.nodes)
        queue.extend(self.floating_nodes)

        while queue:
            con = queue.popleft()
            yield con
            queue.extend(con.nodes)
            queue.extend(con.floating_nodes)

    def root(self):
        """
        Retrieves the root container.

        :rtype: :class:`Con`.
        """

        if not self.parent:
            return self

        con = self.parent

        while con.parent:
            con = con.parent

        return con

    def descendents(self):
        """
        Retrieve a list of all containers that delineate from the currently
        selected container.  Includes any kind of container.

        :rtype: List of :class:`Con`.
        """
        return [c for c in self]

    def leaves(self):
        """
        Retrieve a list of windows that delineate from the currently
        selected container.  Only lists client windows, no intermediate
        containers.

        :rtype: List of :class:`Con`.
        """
        leaves = []

        for c in self:
            if not c.nodes and c.type == "con" and c.parent.type != "dockarea":
                leaves.append(c)

        return leaves

    def command(self, command):
        """
        Run a command on the currently active container.

        :rtype: CommandReply
        """
        return self._conn.command('[con_id="{}"] {}'.format(self.id, command))

    def command_children(self, command):
        """
        Run a command on the direct children of the currently selected
        container.

        :rtype: List of CommandReply????
        """
        if not len(self.nodes):
            return

        commands = []
        for c in self.nodes:
            commands.append('[con_id="{}"] {};'.format(c.id, command))

        self._conn.command(' '.join(commands))

    def workspaces(self):
        """
        Retrieve a list of currently active workspaces.

        :rtype: List of :class:`Con`.
        """
        workspaces = []

        def collect_workspaces(con):
            if con.type == "workspace" and not con.name.startswith('__'):
                workspaces.append(con)
                return

            for c in con.nodes:
                collect_workspaces(c)

        collect_workspaces(self.root())
        return workspaces

    def find_focused(self):
        """
        Finds the focused container.

        :rtype class Con:
        """
        try:
            return next(c for c in self if c.focused)
        except StopIteration:
            return None

    def find_by_id(self, id):
        try:
            return next(c for c in self if c.id == id)
        except StopIteration:
            return None

    def find_by_window(self, window):
        try:
            return next(c for c in self if c.window == window)
        except StopIteration:
            return None

    def find_by_role(self, pattern):
        return [c for c in self if c.window_role and re.search(pattern, c.window_role)]

    def find_named(self, pattern):
        return [c for c in self if c.name and re.search(pattern, c.name)]

    def find_titled(self, pattern):
        return [c for c in self if c.window_title and re.search(pattern, c.window_title)]

    def find_classed(self, pattern):
        return [c for c in self if c.window_class and re.search(pattern, c.window_class)]

    def find_instanced(self, pattern):
        return [c for c in self if c.window_instance and re.search(pattern, c.window_instance)]

    def find_marked(self, pattern=".*"):
        pattern = re.compile(pattern)
        return [c for c in self if any(pattern.search(mark) for mark in c.marks)]

    def find_fullscreen(self):
        return [c for c in self if c.type == 'con' and c.fullscreen_mode]

    def workspace(self):
        if self.type == 'workspace':
            return self

        ret = self.parent

        while ret:
            if ret.type == 'workspace':
                break
            ret = ret.parent

        return ret

    def scratchpad(self):
        root = self.root()

        i3con = None
        for c in root.nodes:
            if c.name == "__i3":
                i3con = c
                break

        if not i3con:
            return None

        i3con_content = None
        for c in i3con.nodes:
            if c.name == "content":
                i3con_content = c
                break

        if not i3con_content:
            return None

        scratch = None
        for c in i3con_content.nodes:
            if c.name == "__i3_scratch":
                scratch = c
                break

        return scratch
