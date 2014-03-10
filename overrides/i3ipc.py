from gi.repository.GLib import MainLoop
from ..module import get_introspection_module
from ..overrides import override

i3ipc = get_introspection_module('i3ipc')

__all__ = []

class Connection(i3ipc.Connection):
    def main(self):
        main_loop = MainLoop()
        self.connect('ipc_shutdown', lambda self: main_loop.quit())
        main_loop.run()

Connection = override(Connection)
__all__.append('Connection')

class Con(i3ipc.Con):
    def __getattr__(self, name):
        if name == 'nodes':
            return self.get_nodes()
        try:
            return self.get_property(name)
        except TypeError:
            raise AttributeError


Con = override(Con)
__all__.append('Con')
