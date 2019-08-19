Welcome to i3ipc-python's documentation!
========================================

.. sectionauthor:: joepvd

.. module:: i3ipc

.. toctree::
   :maxdepth: 2
   :caption: Reference:

   connection
   con
   aio-connection
   aio-con


.. codeauthor:: acrisci

``i3ipc`` is a python 2 and 3 library to interface with the i3 window manager.
A lot of the behavior of the i3 window manager can be configured in the
configuration file, but some more advanced usage can make use of the IPC
mechanism that i3 exposes.  ``i3ipc`` is a library that makes this easier.  Use
it to connect to the active i3 session, to query and select containers, to perform
actions, and to do all this while listening to events.

Getting started
+++++++++++++++

This part will get you going as fast as possible. It will guide you into installing
the library, using it to make a connection, querying the containers and other entities
in the current session, act on them, and how to listen to and act on events.

Installing :mod:`i3ipc`
-----------------------

:mod:`i3ipc` is on PyPI. Install it with:

.. code:: shell

    $ pip install i3ipc

or

.. code:: shell

    $ pip3 install i3ipc


If you want to install the development version, do this:

.. TODO:: Verify the correctness of this after next release

.. code:: shell

    $ git clone https://github.com/acrisci/i3ipc
    $ cd i3ipc
    $ python3 setup.py install --user

Connect to an :command:`i3` session
-----------------------------------

To get a first impression of its possibilities, consider this:

.. code:: python

    >>> import i3ipc
    >>> i3 = i3ipc.Connection()

After importing the library, open a session to the currently running ``i3``
session by creating a Connection object.  This object can be used to send
commands and subscribe to events.  If you have trouble to connect, you
probably have a custom ``i3socket``.  Have a look :class:`here <Connection>`
to get some clues of how the guessing takes place, and how to pass the
socket file name to the class.


Querying the container tree
---------------------------

With the :class:`Connection()` object, some methods are exposed to the object
``i3``.  Right now, we want to query the tree of containers, for which we need
the :meth:`get_tree`::

    >>> tree = i3.get_tree()

This will return the ``root`` container with all information about all its
children. A number of searching methods are exposed.  Here is an incomplete list:


:meth:`~Con.leaves`
    Returns a list of leaves, so the end points of the tree.  This are the windows that
    are managed by :command:`i3`.
:meth:`~Con.find_classed`
    Returns a list of containers where the window class matches the regular expression
    as a parameter.
:meth:`~i3ipc.Con.find_focused`
    Finds the focused window and returns the corresponding :obj:`Con` object.

The container objects contain information about themselves, and about their parents
and children. The children (if any) can be find in the List :attr:`~Con.nodes`.
The parent container can be found in :attr:`~Con.parent`.

Some properties that :command:`i3` maintain can be directly queried from the :obj:`Con`
object. Some examples:

:attr:`~Con.window_class`
    Returns the window_class window property of the current container
:attr:`~Con.type`
    Returns the window type of the current container. This is one of 
:attr:`~Con.window_title`
    Returns the window title.


.. code:: python

    >>> tree = i3.get_tree()
    >>> focused = tree.find_focused()
    >>> print('Focused window %s is on workspace %s' %
          (focused.name, focused.workspace().name))


Changing the state: Executing commands
--------------------------------------


Changing the state of a container or the ``i3``-session is exposed with the
:meth:`Con.command` method which takes the same syntax as you would put in
``i3/config`` or in an :command:`i3-msg` command:

.. code:: python

    >>> for container in i3.get_tree().find_fullscreen():
        container.command('fullscreen')

Now all the previously fullscreen containers will be embedded again in the workspace.


.. note::

    Both the classes :class:`Connection` and :class:`Con` have a :meth:`command` method.
    The difference is that :meth:`Con.command` always includes the string ``[con_id=Con.id]``
    in the command, effectively making the command work on the currently active :obj:`Con`.
    If the command is a container specific one, :meth:`Connection.command` will act on
    whatever container happens to be focused right now.


Something about where to find a consise summary about command syntax and semantics, the
i3 manual spreads this info out everywhere, and is (rightly) more focused on
the config file.


Listening to events
-------------------

The IPC facilities of :command:`i3` expose the possibility to listen to `events
<http://i3wm.org/docs/ipc.html#_events>`_.  The python :module:`i3ipc` library
of course provides with this possibility.

The idea is to define some functions, which can be registered to trigger when
an event occurs.  Here is an example:

.. code:: python

    import i3ipc

    i3 = i3ipc.Connection()

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


Some examples
-------------

We need to work with a web based ticketing system.  We either have the window
open or not.  Browser is configured to not work with tabs: we prefer to
have the window manager manage windows.  On the press of a button, we want
to focus the inbox of tickets if it is present, or start it.  To effectively
determine if there is a window with the inbox of problems open, we use marks.
Problem: We do not want to mark the window manually.  We also cannot rely on
the window title to set the mark, as the web has links, we will click them.
We do not want an arbitrary windows to be tagged as our main target.

Enter this script:

.. code-block:: python
    :linenos:

    #!/usr/bin/env python3

    import i3ipc

    tag = 'tickets'
    site = 'https://myproblemprovider.io/handcrafted/problems_for_me'
    class_browsers = {'Firefox', 'google_chrome', 'Surf', 'Iceweasel', 'chromium',
            'Chromium', 'opera', 'konqueror'}

    def mark_when_new_browser_window(self, event):
        con = event.container
        if con.window_class not in class_browsers:
            return
        con.command('mark {}'.format(tag))
        exit(0)

    i3 = i3ipc.Connection()
    marked = i3.get_tree().find_marked(tag)
    try:
        marked[0].command('focus')
        exit(0)
    except IndexError:
        i3.on('window::new', mark_when_new_browser_window)
        i3.command('exec x-www-browser --new-window {}'.format(site))
        i3.main()

What this does, look at line 18. Her3e, containers with a mark matched by the regular
expression ``tag`` are returned. If there is a first element of the matches, it is
focused in the ``try:``-block, and the script exits immediately.  If there is no
first element with that mark, a listener for newly created windows is registered
in line 23. Then, a new browser window is started pointing at the ticket page.
The listen event loop is started in line 25. Then, when new windows appear, the
function :func:`mark_when_new_browser_window` is executed.  If it is not a browser,
listening will continue. If the new window *is* a browser, 

Development and bugs
--------------------

Development happens on `github <https://github.com/acrisci/i3ipc-python>`_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. automodule:: i3ipc
    :members:
    :exclude-members: MessageType
