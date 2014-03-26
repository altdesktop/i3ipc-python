# i3ipc-python

An improved Python library to control [i3wm](http://i3wm.org).

## About

i3's interprocess communication (or [ipc](http://i3wm.org/docs/ipc.html)) is the interface i3wm uses to receive [commands](http://i3wm.org/docs/userguide.html#_list_of_commands) from client applications such as `i3-msg`. It also features a publish/subscribe mechanism for notifying interested parties of window manager events.

i3ipc-python is a Python library for controlling the window manager. This project is intended to be useful for general scripting, and for applications that interact with the window manager like status line generators, notification daemons, and pagers.

If you have an idea for a script to extend i3wm, you can add your script to the examples folder or make a [script request](https://github.com/acrisci/i3ipc-python/issues) on the issue tracker.

## Documentation

The latest documentation can be found [here](http://dubstepdish.com/i3ipc-glib). i3ipc-python is a [GObject introspection](https://developer.gnome.org/gobject/stable/) library (kind of like [gtk](https://developer.gnome.org/)).

## Installation

i3ipc-python requires [i3ipc-GLib](https://github.com/acrisci/i3ipc-glib) and [PyGObject](https://wiki.gnome.org/action/show/Projects/PyGObject).

Then simply do:

```shell
./autogen.sh
sudo make install
```

Or get someone to host a package for your distro.

## Example

```python
#!/usr/bin/env python3

from gi.repository import i3ipc

# Create the Connection object that can be used to send commands and subscribe
# to events.
conn = i3ipc.Connection()

# Query the ipc for outputs. The result is a list that represents the parsed
# reply of a command like `i3-msg -t get_outputs`.
outputs = conn.get_outputs()

print('Active outputs:')

for output in filter(lambda o: o.active, outputs):
    print(output.name)

# Send a command to be executed synchronously.
conn.command('focus left')

# Define a callback to be called when you switch workspaces.
def on_workspace(self, e):
    # The first parameter is the connection to the ipc and the second is an object
    # with the data of the event sent from i3.
    if e.current:
        print('Windows on this workspace:')
        for w in e.current.descendents():
            print(w.name)

# Subscribe to the workspace event
conn.on('workspace', on_workspace)

# Start the main loop and wait for events to come in.
conn.main()
```

## Contributing

We should do what we can to make this library as "Pythonic" as good tastes allows. New features should be implemented on the main project at [i3ipc-GLib](https://github.com/acrisci/i3ipc-glib).

## License

This work is available under the GNU General Public License (See COPYING).

Copyright © 2014, Tony Crisci

All rights reserved.
