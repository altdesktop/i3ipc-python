i3ipc-python
============

An improved Python library to control `i3wm <http://i3wm.org>`__.

About
-----

i3's interprocess communication (or
`ipc <http://i3wm.org/docs/ipc.html>`__) is the interface i3wm uses to
receive
`commands <http://i3wm.org/docs/userguide.html#_list_of_commands>`__
from client applications such as ``i3-msg``. It also features a
publish/subscribe mechanism for notifying interested parties of window
manager events.

i3ipc-python is a Python library for controlling the window manager.
This project is intended to be useful for general scripting, and for
applications that interact with the window manager like status line
generators, notification daemons, and pagers.

If you have an idea for a script to extend i3wm, you can add your script
to the examples folder or make a `script
request <https://github.com/acrisci/i3ipc-python/issues>`__ on the issue
tracker.

Installation
------------

i3ipc is on `PyPI <https://pypi.python.org/pypi/i3ipc>`__.

``pip install i3ipc``

Example
-------

.. code:: python

    #!/usr/bin/env python3

    import i3ipc

    # Create the Connection object that can be used to send commands and subscribe
    # to events.
    i3 = i3ipc.Connection()

    # Print the name of the focused window
    focused = i3.get_tree().find_focused()
    print('Focused window %s is on workspace %s' %
          (focused.name, focused.workspace().name))

    # Query the ipc for outputs. The result is a list that represents the parsed
    # reply of a command like `i3-msg -t get_outputs`.
    outputs = i3.get_outputs()

    print('Active outputs:')

    for output in filter(lambda o: o.active, outputs):
        print(output.name)

    # Send a command to be executed synchronously.
    i3.command('focus left')

    # Take all fullscreen windows out of fullscreen
    for container in i3.get_tree().find_fullscreen():
        container.command('fullscreen')

    # Define a callback to be called when you switch workspaces.
    def on_workspace_focus(self, e):
        # The first parameter is the connection to the ipc and the second is an object
        # with the data of the event sent from i3.
        if e.current:
            print('Windows on this workspace:')
            for w in e.current.leaves():
                print(w.name)

    # Dynamically name your workspaces after the current window class
    def on_window_focus(i3, e):
        focused = i3.get_tree().find_focused()
        ws_name = "%s:%s" % (focused.workspace().num, focused.window_class)
        i3.command('rename workspace to "%s"' % ws_name)

    # Subscribe to events
    i3.on('workspace::focus', on_workspace_focus)
    i3.on("window::focus", on_window_focus)

    # Start the main loop and wait for events to come in.
    i3.main()

Contributing
------------

Please feel free to report bugs, request features or add examples by
submitting a pull request.

License
-------

This work is available under a BSD license (see LICENSE)

Copyright © 2015, Tony Crisci

All rights reserved.
