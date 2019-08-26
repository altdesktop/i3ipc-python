i3ipc-python
============

An improved Python library to control `i3wm <http://i3wm.org>`__ and `sway <https://swaywm.org/>`__.

About
-----

i3's interprocess communication (or `ipc <http://i3wm.org/docs/ipc.html>`__) is the interface i3wm uses to receive `commands <http://i3wm.org/docs/userguide.html#_list_of_commands>`__ from client applications such as ``i3-msg``. It also features a publish/subscribe mechanism for notifying interested parties of window manager events.

i3ipc-python is a Python library for controlling the window manager.  This project is intended to be useful for general scripting, and for applications that interact with the window manager like status line generators, notification daemons, and window pagers.

If you have an idea for a script to extend i3wm, you can add your script to the `examples folder <https://github.com/acrisci/i3ipc-python/tree/master/examples>`__.

For details on how to use the library, see the `reference documentation <https://i3ipc-python.readthedocs.io/en/latest/>`__.

Installation
------------

i3ipc is on `PyPI <https://pypi.python.org/pypi/i3ipc>`__.

``pip3 install i3ipc``

Example
-------

.. code:: python3

    from i3ipc import Connection, Event

    # Create the Connection object that can be used to send commands and subscribe
    # to events.
    i3 = Connection()

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

    # Print the names of all the containers in the tree
    root = i3.get_tree()
    print(root.name)
    for con in root:
        print(con.name)

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
    i3.on(Event.WORKSPACE_FOCUS, on_workspace_focus)
    i3.on(Event.WINDOW_FOCUS, on_window_focus)

    # Start the main loop and wait for events to come in.
    i3.main()

Asyncio Support
---------------

Support for asyncio is included in the ``i3ipc.aio`` package. The interface is similar to the blocking interface but the methods that interact with the socket are coroutines.

.. code:: python3

    from i3ipc.aio import Connection
    from i3ipc import Event

    import asyncio

    async def main():
        def on_window(self, e):
            print(e)

        c = await Connection(auto_reconnect=True).connect()

        workspaces = await c.get_workspaces()

        c.on(Event.WINDOW, on_window)

        await c.main()

    asyncio.get_event_loop().run_until_complete(main())

Contributing
------------

Development happens on `Github <https://github.com/altdesktop/i3ipc-python>`__. Please feel free to report bugs, request features or add examples by submitting a pull request.

License
-------

This work is available under a BSD-3-Clause license (see LICENSE).

Copyright © 2015, Tony Crisci

All rights reserved.
