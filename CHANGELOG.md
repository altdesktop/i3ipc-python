# Changelog

## Version 2.2.1

Version 2.2.1 includes sway comatibility enhancements (#98) and other bugfixes.

* Make the sway INPUT event subscribable (#127).
* Remove the enum-compat dependency (#128).
* Add examples and docs to MANIFEST.in (#132).
* Add sway-specific fields to OutputReply (#137).
* Add `find_by_pid()` method for sway (#142).
* Add side properties to Gaps object (#143).
* Add `ipc_data` attribute to objects (8947b9f).
* Add all known sway properties (e6c7f1b).
* Fix scratchpad for sway (f11e729).
* Bug: fix crash after reload then restart (#148).

## Version 2.1.1

Version 2.1.1 includes bugfixes and new features.

* Regression: emit detailed events correctly (#126)
* Regression: null values in replies should be python None (#123)
* Add the sway input event (#122)
* Raise handler exceptions from Connection.main() (the old behavior was just to exit silently which is wrong) (#125)

## Version 2.0.1

Version 2.0.1 is a major release which adds breaking changes and major new features.

i3ipc-python is now Python 3 only.

This release adds the asyncio connection class. New code for Python 3.6 or greater is recommended to use this class over the old blocking connection.

* (breaking) Remove python2 support (#110)
* (breaking) Use the `Rect` class for `OutputReply` and `WorkspaceReply` rect attributes (cec29f9).
* (breaking) Make socket-related members of the `Connection` private (4936704)
    - `cmd_socket`, `cmd_lock`, `sub_socket`, `sub_lock`, `MAGIC`, `_event_socket_setup()`, `_event_socket_teardown()`, `_event_socket_poll()`
* (breaking) Make event-related members of the `Connection` private (8424811)
    - `subscribe()`, `EventType`
* (breaking) Remove `GenericEvent` in favor of specific events `OutputEvent`, `ModeEvent`, and `ShutdownEvent`.
* (breaking) Remove the `PropsObject` (6ddbc22)
* Add asyncio support with the new `aio.Connection` class.
* Add `Event` class for event subscription by enum (#59)
* Add the `app_id` attribute to the `Con` class (sway only) (#113).
* Get the socket path from the root window with python-xlib (#116).
* Add a commands to get inputs and seats (sway only) (#115).
* Add `event_state_mask` and `symbols` (sway only) to `BindingInfo` (262246d).
* Add version info in `__version__.py` (ee779b).
* Use real X windows in tests (4e9746c).
* Run tests in a docker container (97d0455).
* Add type annotations for all public members.
* Completely rewrite the documentation.

## Version 1.7.1

Version 1.7.1 adds some bugfixes and features.

* Add support to get socketpath from the `sway` binary (93a8f0c).
* Return empty list on commands that don't return a result (cf55812).
* Implement the `SHUTDOWN` event (d338889).
* Implement the autoreconnect feature (fa3a813).
* Make sending commands thread safe (e9fcefa).
* Add `title` attribute to `Con` class (34ea24e).
* Add `pid` attribute to `Con` class for sway (bd0224e).

## Version 1.6.0

Version 1.6.0 adds the following bugfixes and features:

* Properly tear down subscription socket (#83)
* Implement send_tick message and tick event
* Add a timeout parameter to the main function
* Implement GET_BINDING_MODES
* Implement GET_CONFIG
* Implement GET_MARKS
* Fix pickling of types by fixing a _ReplyType exception (#89)
* Add the sticky property

## Version 1.5.1

Version 1.5.1 adds the following bugfixes and features:

* add the Connection::off() function to stop listening to events
* add a timeout parameter to the main loop to terminate after some time
* use SHUT_RDWR on the socket to fix some bugs with main_quit()

## Version 1.5.0

Version 1.5.0 adds the following bugfixes and features:

* fix bug where floating nodes are not in the tree
* add support for SWAYSOCK and other fixes for sway

## Version 1.4.0

Version 1.4.0 adds the following bugfixes and features:

* Add container property 'floating'
* Add container property 'focus' (the focus stack)
* Add container info for window gaps
* Use native byte order everywhere
* Add descendents iterator to Con
* Add `Con.find_instanced()`
* Add documentation and tests
* List descendents BFS
* Allow usage from external event loops
* bug: return command result in `Con.command()`

## Version 1.3.0

Version 1.3.0 adds the following bugfixes and features:

- Remove python-xlib dependency by getting the socket path from i3
  binary.
- The `Con::command_children()` method should work properly.
- Make `socket.recv()` robust against interruptions.
- Change `Con::mark` to `Con::marks` for the new ipc api (might be
  breaking).
- Add `Con::window_rect` and `Con::deco_rect` properties.
- Fix encoding problems in reading README.
- `Con::workspace()` returns self if it is a workspace instead of None.
- Fix the ipc-shutdown event.
- The library is now installed as a directory instead of a single file.
- Make the main loop work in multi-threaded environments.
- Add Travis CI.
- Add a test suite.
- Add robustness against UTF-8 errors by replacing bad UTF-8.

## Version 1.2.0

Version 1.2.0 adds the following features:

- Obey I3SOCK environment variable
- Add Con::find_fullscreen()
- Added properties: `scratchpad_state`, `window_role`
- Con::find_marked() - make pattern optional

And the following bugfixes:
- Fix crash on `barconfig_update` event
- Use underscores to subscribe to `barconfig_update` event
- Correctly put floating nodes in the `floating_nodes` list of the Con

## Version 1.1.6

Version 1.1.6 adds the following bug fixes

- Use enum-compat instead of enum34
- Safely set window class and instance (fixes crashes for windows with
  no class or instance)

## Version 1.1.4

Version 1.1.4 includes the following enhancements and bug fixes:

- Convert README to rst
- fix con::command() formatting
- fix searches to not crash when windows don't have the searched-for
  property
- always set class properties
- get_bar_config() defaults to the first bar id
- add get_bar_config_list()

## Version 1.1.1

This version includes the following improvements:

- Python 2 support
- Support the `window_instance` container property
- Pep8 compliance code cleanup

## Version 0.1.1

This version contains the following feature enhancements:

- Bump required i3ipc-GLib to version 0.1.1
- Connection `main` method quits the main loop when the ipc shuts down

## Version 0.0.1

This is the initial release of i3ipc-python, an improved Python library to control [i3wm](http://i3wm.org).
