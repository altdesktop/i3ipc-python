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

You'll also need ``python-gobject`` and ``python-dbus`` from your package manager.

Example
-------

.. code:: python

    #!/usr/bin/env python3

    import i3ipc

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
            for w in e.current.leaves():
                print(w.name)

    # Subscribe to the workspace event
    conn.on('workspace::focus', on_workspace)

    # Start the main loop and wait for events to come in.
    conn.main()

Contributing
------------

Please feel free to report bugs, request features or add examples by
submitting a pull request.

License
-------

This work is available under a BSD license (see LICENSE)

Copyright © 2015, Tony Crisci

All rights reserved.
