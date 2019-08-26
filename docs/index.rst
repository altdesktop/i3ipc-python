i3ipc-python Documentation
==========================

.. module:: i3ipc

.. toctree::
   :maxdepth: 2
   :caption: Reference:

   connection
   con
   aio-connection
   aio-con
   events
   replies


.. codeauthor:: acrisci

Overview
++++++++

i3ipc-python is a library for controlling `i3 window manager <https://i3wm.org>`_ and `sway <https://swaywm.org>`_. i3 users can use this library to create their own plugin scripts to customize their desktop or integrate i3 into other applications. With this library, you can query the state of the window manager, listen to events, and send commands to i3 to perform window manager actions such as focusing or closing windows.

The main entry point into the features of the library is the :class:`Connection <i3ipc.aio.Connection>` class. This class manages a Unix socket connection to the ipc interface exposed by the window manager. By default, the ``Connection`` will attempt to connect to the running instance of i3 by using information present in the environment or the running X11 display.

.. code-block:: python3

    from i3ipc.aio import Connection

    i3 = await Connection().connect()

You can use the ``Connection`` to query window manager state such as the names of the workspaces and outputs.

.. code-block:: python3

    workspaces = await i3.get_workspaces()
    outputs = await i3.get_outputs()

    for workspace in workspaces:
        print(f'workspace: {workspace.name}')

    for output in outputs:
        print(f'output: {output.name}')

You can use it to send commands to i3 to control the window manager in an automated fashion with the same command syntax as the i3 config or ``i3-msg``.

.. code-block:: python3

    await i3.command('workspace 5')
    await i3.command('focus left')
    await i3.command('kill')

You can use it to query the windows to find specific applications, get information about their windows, and send them window manager commands. The i3 layout tree is represented by the :class:`Con <i3ipc.aio.Con>` class.

.. code-block:: python3

    # get_tree() returns the root container
    tree = await i3.get_tree()

    # get some information about the focused window
    focused = tree.find_focused()
    print(f'Focused window: {focused.name}')
    workspace = focused.workspace()
    print(f'Focused workspace: {workspace.name}')

    # focus firefox and set it to fullscreen mode
    ff = tree.find_classed('Firefox')[0]
    await ff.command('focus')
    await ff.command('fullscreen')

    # iterate through all the container windows (or use tree.leaves() for just
    # application windows)
    for container in workspace:
        print(f'On the focused workspace: {container.name}')

And you can use it to subscribe to window manager events and call a handler when they occur.

.. code-block:: python3

    from i3ipc import Event

    def on_new_window(i3, e):
        print(f'a new window opened: {e.container.name}')

    def on_workspace_focus(i3, e):
        print(f'workspace just got focus: {e.current.name}')

    i3.on(Event.WINDOW_NEW, on_new_window)
    i3.on(Event.WORKSPACE_FOCUS, on_workspace_focus)

    await i3.main()

For more examples, see the `examples <https://github.com/altdesktop/i3ipc-python/tree/master/examples>`_ folder in the repository for useful scripts people have contributed.

Installation
++++++++++++

This library is available on PyPi as `i3ipc <https://pypi.org/project/i3ipc/>`_.

.. code-block:: bash

    pip3 install i3ipc

Contributing
++++++++++++

Development for this library happens on `Github <https://github.com/altdesktop/i3ipc-python>`_. Report bugs or request features there. Contributions are welcome.

License
++++++++

This library is available under a `BSD-3-Clause License <https://github.com/altdesktop/i3ipc-python/blob/master/LICENCE>`_.

© 2015, Tony Crisci

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
