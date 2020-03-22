import re
import sys
from .model import Rect, Gaps
from . import replies
from collections import deque
from typing import List, Optional


class Con:
    """A container of a window and child containers gotten from :func:`i3ipc.Connection.get_tree()` or events.

    .. seealso:: https://i3wm.org/docs/ipc.html#_tree_reply

    :ivar border:
    :vartype border: str
    :ivar current_border_width:
    :vartype current_border_with: int
    :ivar floating:
    :vartype floating: bool
    :ivar focus: The focus stack for this container as a list of container ids.
        The "focused inactive" is at the top of the list which is the container
        that would be focused if this container recieves focus.
    :vartype focus: list(int)
    :ivar focused:
    :vartype focused: bool
    :ivar fullscreen_mode:
    :vartype fullscreen_mode: int
    :ivar ~.id:
    :vartype ~.id: int
    :ivar layout:
    :vartype layout: str
    :ivar marks:
    :vartype marks: list(str)
    :ivar name:
    :vartype name: str
    :ivar num:
    :vartype num: int
    :ivar orientation:
    :vartype orientation: str
    :ivar percent:
    :vartype percent: float
    :ivar scratchpad_state:
    :vartype scratchpad_state: str
    :ivar sticky:
    :vartype sticky: bool
    :ivar type:
    :vartype type: str
    :ivar urgent:
    :vartype urgent: bool
    :ivar window:
    :vartype window: int
    :ivar nodes:
    :vartype nodes: list(:class:`Con <i3ipc.Con>`)
    :ivar floating_nodes:
    :vartype floating_nodes: list(:class:`Con <i3ipc.Con>`)
    :ivar window_class:
    :vartype window_class: str
    :ivar window_instance:
    :vartype window_instance: str
    :ivar window_role:
    :vartype window_role: str
    :ivar window_title:
    :vartype window_title: str
    :ivar rect:
    :vartype rect: :class:`Rect <i3ipc.Rect>`
    :ivar window_rect:
    :vartype window_rect: :class:`Rect <i3ipc.Rect>`
    :ivar deco_rect:
    :vartype deco_rect: :class:`Rect <i3ipc.Rect>`
    :ivar geometry:
    :vartype geometry: :class:`Rect <i3ipc.Rect>`
    :ivar app_id: (sway only)
    :vartype app_id: str
    :ivar pid: (sway only)
    :vartype pid: int
    :ivar gaps: (gaps only)
    :vartype gaps: :class:`Gaps <i3ipc.Gaps>`
    :ivar representation: (sway only)
    :vartype representation: str
    :ivar visible: (sway only)
    :vartype visible: bool

    :ivar ipc_data: The raw data from the i3 ipc.
    :vartype ipc_data: dict
    """
    def __init__(self, data, parent, conn):
        self.ipc_data = data
        self._conn = conn
        self.parent = parent

        # set simple properties
        ipc_properties = [
            'border', 'current_border_width', 'floating', 'focus', 'focused', 'fullscreen_mode',
            'id', 'layout', 'marks', 'name', 'num', 'orientation', 'percent', 'scratchpad_state',
            'sticky', 'type', 'urgent', 'window', 'pid', 'app_id', 'representation'
        ]
        for attr in ipc_properties:
            if attr in data:
                setattr(self, attr, data[attr])
            else:
                setattr(self, attr, None)

        # XXX in 4.12, marks is an array (old property was a string "mark")
        if self.marks is None:
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

        self.rect = Rect(data['rect'])
        if 'window_rect' in data:
            self.window_rect = Rect(data['window_rect'])

        self.deco_rect = None
        if 'deco_rect' in data:
            self.deco_rect = Rect(data['deco_rect'])

        self.geometry = None
        if 'geometry' in data:
            self.geometry = Rect(data['geometry'])

        self.gaps = None
        if 'gaps' in data:
            self.gaps = Gaps(data['gaps'])

    def __iter__(self):
        """Iterate through the descendents of this node (breadth-first tree traversal)
        """
        queue = deque(self.nodes)
        queue.extend(self.floating_nodes)

        while queue:
            con = queue.popleft()
            yield con
            queue.extend(con.nodes)
            queue.extend(con.floating_nodes)

    def root(self) -> 'Con':
        """Gets the root container.

        :returns: The root container.
        :rtype: :class:`Con`
        """

        if not self.parent:
            return self

        con = self.parent

        while con.parent:
            con = con.parent

        return con

    def descendants(self) -> List['Con']:
        """Gets a list of all child containers for the container in
        breadth-first order.

        :returns: A list of descendants.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self]

    def descendents(self) -> List['Con']:
        """Gets a list of all child containers for the container in
        breadth-first order.

        .. deprecated:: 2.0.1
           Use :func:`descendants` instead.

        :returns: A list of descendants.
        :rtype: list(:class:`Con`)
        """
        print('WARNING: descendents is deprecated. Use `descendants()` instead.', file=sys.stderr)
        return self.descendants()

    def leaves(self) -> List['Con']:
        """Gets a list of leaf child containers for this container in
        breadth-first order. Leaf containers normally contain application
        windows.

        :returns: A list of leaf descendants.
        :rtype: list(:class:`Con`)
        """
        leaves = []

        for c in self:
            if not c.nodes and c.type == "con" and c.parent.type != "dockarea":
                leaves.append(c)

        return leaves

    def command(self, command: str) -> List[replies.CommandReply]:
        """Runs a command on this container.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :returns: A list of replies for each command in the given command
            string.
        :rtype: list(:class:`CommandReply <i3ipc.CommandReply>`)
        """
        return self._conn.command('[con_id="{}"] {}'.format(self.id, command))

    def command_children(self, command: str) -> List[replies.CommandReply]:
        """Runs a command on the immediate children of the currently selected
        container.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :returns: A list of replies for each command that was executed.
        :rtype: list(:class:`CommandReply <i3ipc.CommandReply>`)
        """
        if not len(self.nodes):
            return

        commands = []
        for c in self.nodes:
            commands.append('[con_id="{}"] {};'.format(c.id, command))

        self._conn.command(' '.join(commands))

    def workspaces(self) -> List['Con']:
        """Gets a list of workspace containers for this tree.

        :returns: A list of workspace containers.
        :rtype: list(:class:`Con`)
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

    def find_focused(self) -> Optional['Con']:
        """Finds the focused container under this container if it exists.

        :returns: The focused container if it exists.
        :rtype: :class:`Con` or :class:`None` if the focused container is not
            under this container
        """
        try:
            return next(c for c in self if c.focused)
        except StopIteration:
            return None

    def find_by_id(self, id: int) -> Optional['Con']:
        """Finds a container with the given container id under this node.

        :returns: The container with this container id if it exists.
        :rtype: :class:`Con` or :class:`None` if there is no container with
            this container id.
        """
        try:
            return next(c for c in self if c.id == id)
        except StopIteration:
            return None

    def find_by_pid(self, pid: int) -> List['Con']:
        """Finds all the containers under this node with this pid.

        :returns: A list of containers with this pid.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self if c.pid == pid]

    def find_by_window(self, window: int) -> Optional['Con']:
        """Finds a container with the given window id under this node.

        :returns: The container with this window id if it exists.
        :rtype: :class:`Con` or :class:`None` if there is no container with
            this window id.
        """
        try:
            return next(c for c in self if c.window == window)
        except StopIteration:
            return None

    def find_by_role(self, pattern: str) -> List['Con']:
        """Finds all the containers under this node with a window role that
        matches the given regex pattern.

        :returns: A list of containers that have a window role that matches the
            pattern.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self if c.window_role and re.search(pattern, c.window_role)]

    def find_named(self, pattern: str) -> List['Con']:
        """Finds all the containers under this node with a name that
        matches the given regex pattern.

        :returns: A list of containers that have a name that matches the
            pattern.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self if c.name and re.search(pattern, c.name)]

    def find_titled(self, pattern: str) -> List['Con']:
        """Finds all the containers under this node with a window title that
        matches the given regex pattern.

        :returns: A list of containers that have a window title that matches
            the pattern.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self if c.window_title and re.search(pattern, c.window_title)]

    def find_classed(self, pattern: str) -> List['Con']:
        """Finds all the containers under this node with a window class that
        matches the given regex pattern.

        :returns: A list of containers that have a window class that matches the
            pattern.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self if c.window_class and re.search(pattern, c.window_class)]

    def find_instanced(self, pattern: str) -> List['Con']:
        """Finds all the containers under this node with a window instance that
        matches the given regex pattern.

        :returns: A list of containers that have a window instance that matches the
            pattern.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self if c.window_instance and re.search(pattern, c.window_instance)]

    def find_marked(self, pattern: str = ".*") -> List['Con']:
        """Finds all the containers under this node with a mark that
        matches the given regex pattern.

        :returns: A list of containers that have a mark that matches the
            pattern.
        :rtype: list(:class:`Con`)
        """
        pattern = re.compile(pattern)
        return [c for c in self if any(pattern.search(mark) for mark in c.marks)]

    def find_fullscreen(self) -> List['Con']:
        """Finds all the containers under this node that are in fullscreen
        mode.

        :returns: A list of fullscreen containers.
        :rtype: list(:class:`Con`)
        """
        return [c for c in self if c.type == 'con' and c.fullscreen_mode]

    def workspace(self) -> Optional['Con']:
        """Finds the workspace container for this node if this container is at
        or below the workspace level.

        :returns: The workspace container if it exists.
        :rtype: :class:`Con` or :class:`None` if this container is above the
            workspace level.
        """
        if self.type == 'workspace':
            return self

        ret = self.parent

        while ret:
            if ret.type == 'workspace':
                break
            ret = ret.parent

        return ret

    def scratchpad(self) -> 'Con':
        """Finds the scratchpad container.

        :returns: The scratchpad container.
        :rtype: class:`Con`
        """
        for con in self.root():
            if con.type == 'workspace' and con.name == "__i3_scratch":
                return con

        return None
