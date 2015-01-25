#!/usr/bin/env python3

import Xlib, struct, json, socket, re
from Xlib import display
from enum import Enum

class MessageType(Enum):
    COMMAND = 0
    GET_WORKSPACES = 1
    SUBSCRIBE = 2
    GET_OUTPUTS = 3
    GET_TREE = 4
    GET_MARKS = 5
    GET_BAR_CONFIG = 6
    GET_VERSION = 7

class Event():
    WORKSPACE =         (1 << 0)
    OUTPUT =            (1 << 1)
    MODE =              (1 << 2)
    WINDOW =            (1 << 3)
    BARCONFIG_UPDATE =  (1 << 4)
    BINDING =           (1 << 5)


class _ReplyType(dict):
    def __getattr__(self, name):
            return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

class CommandReply(_ReplyType):
    pass

class VersionReply(_ReplyType):
    pass

class BarConfigReply(_ReplyType):
    pass

class OutputReply(_ReplyType):
    pass

class WorkspaceReply(_ReplyType):
    pass

class WorkspaceEvent():
    def __init__(self, data, conn):
        self.change = data['change']
        self.current = None
        self.old = None

        if 'current' in data and data['current']:
            self.current = Con(data['current'], None, conn)

        if 'old' in data and data['old']:
            self.old = Con(data['old'], None, conn)

class GenericEvent():
    def __init__(self, data):
        self.change = data['change']

class WindowEvent():
    def __init__(self, data, conn):
        self.change = data['change']
        self.container = Con(data['container'], None, conn)

class BarconfigUpdateEvent():
    def __init__(self, data):
        self.id = data['id']
        self.hidden_state = data['hidden_state']
        self.mode = data['mode']

class BindingInfo():
    def __init__(self, data):
        self.command = data['command']
        self.mods = data['mods']
        self.input_code = data['input_code']
        self.symbol = data['symbol']
        self.input_type = data['input_type']

class BindingEvent():
    def __init__(self, data):
        self.change = data['change']
        self.binding = BindingInfo(data['binding'])

class _PubSub():
    def __init__(self, conn):
        self.conn = conn
        self._subscriptions = []

    def subscribe(self, detailed_event, handler):
        event = detailed_event.replace('_', '-')
        detail = ''

        if detailed_event.count('::') > 0:
            [event, detail] = detailed_event.split('::')

        self._subscriptions.append({ 'event': event, 'detail': detail, 'handler': handler })

    def emit(self, event, data):
        detail = ''

        if data:
            detail = data.change

        for s in self._subscriptions:
            if s['event'] == event:
                if not s['detail'] or s['detail'] == detail:
                    if data:
                        s['handler'](self.conn, data)
                    else:
                        s['handler'](self.conn)

# this is for compatability with i3ipc-glib
class _PropsObject():
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)

    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, "_obj"), name)

    def __delattr__(self, name):
        delattr(object.__getattribute__(self, "_obj"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_obj"), name, value)

class Connection():
    MAGIC = 'i3-ipc'  # safety string for i3-ipc
    _chunk_size = 1024  # in bytes
    _timeout = 0.5  # in seconds
    _struct_header = '<%dsII' % len(MAGIC.encode('utf-8'))
    _struct_header_size = struct.calcsize(_struct_header)

    def __init__(self):
        d = Xlib.display.Display()
        r = d.screen().root
        data = r.get_property(d.get_atom('I3_SOCKET_PATH'), d.get_atom('UTF8_STRING'), 0, 9999)

        if not data.value:
            raise Exception('could not get i3 socket path')

        self._pubsub = _PubSub(self)
        self.props = _PropsObject(self)
        self.subscriptions = 0
        self.socket_path = data.value
        self.cmd_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.cmd_socket.connect(self.socket_path)

    def _pack(self, msg_type, payload):
        """
        Packs the given message type and payload. Turns the resulting
        message into a byte string.
        """
        pb = payload.encode()
        return self.MAGIC.encode() + struct.pack('=II', len(pb), msg_type.value) + pb
    
    def _unpack(self, data):
        """
        Unpacks the given byte string and parses the result from JSON.
        Returns None on failure and saves data into "self.buffer".
        """
        data_size = len(data)
        msg_magic, msg_length, msg_type = self._unpack_header(data)
        msg_size = self._struct_header_size + msg_length
        # XXX: Message shouldn't be any longer than the data
        return data[self._struct_header_size:msg_size].decode('utf-8')

    def _unpack_header(self, data):
        """
        Unpacks the header of given byte string.
        """
        return struct.unpack(self._struct_header, data[:self._struct_header_size])

    def _ipc_recv(self, sock):
        data = sock.recv(14)

        if len(data) == 0:
            # EOF
            return '', 0

        msg_magic, msg_length, msg_type = self._unpack_header(data)
        msg_size = self._struct_header_size + msg_length
        while len(data) < msg_size:
            data += sock.recv(msg_length)
        return self._unpack(data), msg_type

    def _ipc_send(self, sock, message_type, payload):
        sock.sendall(self._pack(message_type, payload))
        data, msg_type = self._ipc_recv(sock)
        return data

    def message(self, message_type, payload):
        return self._ipc_send(self.cmd_socket, message_type, payload)

    def command(self, payload):
        data = self.message(MessageType.COMMAND, payload)
        return json.loads(data, object_hook=CommandReply)

    def get_version(self):
        data = self.message(MessageType.GET_VERSION, '')
        return json.loads(data, object_hook=VersionReply)

    def get_bar_config(self, bar_id):
        data = self.message(MessageType.GET_BAR_CONFIG, bar_id)
        return json.loads(data, object_hook=BarConfigReply)

    def get_outputs(self):
        data = self.message(MessageType.GET_OUTPUTS, '')
        return json.loads(data, object_hook=OutputReply)

    def get_workspaces(self):
        data = self.message(MessageType.GET_WORKSPACES, '')
        return json.loads(data, object_hook=WorkspaceReply)

    def get_tree(self):
        data = self.message(MessageType.GET_TREE, '')
        return Con(json.loads(data), None, self)

    def subscribe(self, events):
        events_obj = []
        if events & Event.WORKSPACE:
            events_obj.append("workspace")
        if events & Event.OUTPUT:
            events_obj.append("output")
        if events & Event.MODE:
            events_obj.append("mode")
        if events & Event.WINDOW:
            events_obj.append("window")
        if events & Event.BARCONFIG_UPDATE:
            events_obj.append("barconfig_update")
        if events & Event.BINDING:
            events_obj.append("binding")

        data = self._ipc_send(self.sub_socket, MessageType.SUBSCRIBE, json.dumps(events_obj))
        result = json.loads(data, object_hook=CommandReply)
        self.subscriptions |= events
        return result

    def on(self, detailed_event, handler):
        event = detailed_event.replace('_', '-')
        detail = ''

        if detailed_event.count('::') > 0:
            [event, detail] = detailed_event.split('::')

        # special case: ipc-shutdown is not in the protocol
        if event == 'ipc-shutdown':
            self._pubsub.subscribe(event, handler)
            return

        event_type = 0
        if event == "workspace":
            event_type = Event.WORKSPACE
        elif event == "output":
            event_type = Event.OUTPUT
        elif event == "mode":
            event_type = Event.MODE
        elif event == "window":
            event_type = Event.WINDOW
        elif event == "barconfig_update":
            event_type = Event.BARCONFIG_UPDATE
        elif event == "binding":
            event_type = Event.BINDING

        if not event_type:
            raise Exception('event not implemented')

        self.subscriptions |= event_type

        self._pubsub.subscribe(detailed_event, handler)

    def main(self):
        self.sub_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sub_socket.connect(self.socket_path)

        self.subscribe(self.subscriptions)

        while True:
            if self.sub_socket == None:
                break

            data, msg_type = self._ipc_recv(self.sub_socket)

            if len(data) == 0:
                # EOF
                self._pubsub.emit('ipc-shutdown', None)
                break

            data = json.loads(data)
            msg_type = 1 << (msg_type & 0x7f)
            event_name = ''
            event = None

            if msg_type == Event.WORKSPACE:
                event_name = 'workspace'
                event = WorkspaceEvent(data, self)
            elif msg_type == Event.OUTPUT:
                event_name = 'output'
                event = GenericEvent(data)
            elif msg_type == Event.MODE:
                event_name = 'mode'
                event = GenericEvent(data)
            elif msg_type == Event.WINDOW:
                event_name = 'window'
                event = WindowEvent(data, self)
            elif msg_type == Event.BARCONFIG_UPDATE:
                event_name = 'barconfig_update'
                event = BarconfigUpdateEvent(data)
            elif msg_type == Event.BINDING:
                event_name = 'binding'
                event = BindingEvent(data)
            else:
                # we have not implemented this event
                continue

            self._pubsub.emit(event_name, event)

    def main_quit(self):
        self.sub_socket.close()
        self.sub_socket = None

class Rect():
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.height = data['height']
        self.width = data['width']

class Con():
    def __init__(self, data, parent, conn):
        self.props = _PropsObject(self)
        self._conn = conn
        self.parent = parent

        # set simple properties
        ipc_properties = ['border', 'current_border_width', 'focused',
                'fullscreen_mode', 'id', 'layout', 'mark', 'name',
                'orientation', 'percent', 'type', 'urgent', 'window']
        for attr in ipc_properties:
            if attr in data:
                setattr(self, attr, data[attr])

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
        for n in data['nodes']:
            self.nodes.append(Con(n, self, conn))

        self.floating_nodes = []
        for n in data['floating_nodes']:
            self.nodes.append(Con(n, self, conn))

        if 'window_properties' in data:
            self.window_class = data['window_properties']['class']

        self.rect = Rect(data['rect'])

    def root(self):
        if not self.parent:
            return self

        con = self.parent

        while con.parent:
            con = con.parent

        return con

    def descendents(self):
        descendents = []
        def collect_descendents(con):
            for c in con.nodes:
                descendents.append(c)
                collect_descendents(c)
            for c in con.floating_nodes:
                descendents.append(c)
                collect_descendents(c)

        collect_descendents(self)
        return descendents

    def leaves(self):
        leaves = []

        for c in self.descendents():
            if not len(c.nodes) and c.type == "con" and c.parent.type != "dockarea":
                leaves.append(c)

        return leaves

    def command(self, command):
        self._conn.command('[id="{}"] {}', self.id, command)

    def command_children(self):
        if not len(self.nodes):
            return

        commands = []
        for c in self.nodes:
            commands.append('[id="{}" {};', self.id, command)

        self._conn.command(' '.join(commands))

    def workspaces(self):
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
        try:
            return next(c for c in self.descendents() if c.focused)
        except StopIteration:
            return None

    def find_by_id(self, id):
        try:
            return next(c for c in self.descendents() if c.id == id)
        except StopIteration:
            return None

    def find_by_window(self, window):
        try:
            return next(c for c in self.descendents() if c.window == window)
        except StopIteration:
            return None

    def find_named(self, pattern):
        return [c for c in self.descendents() if re.search(pattern, c.name)]

    def find_classed(self, pattern):
        return [c for c in self.descendents() if re.search(pattern, c.window_class)]

    def find_marked(self, pattern):
        return [c for c in self.descendents() if re.search(pattern, c.mark)]

    def workspace(self):
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
