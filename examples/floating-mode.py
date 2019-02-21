#!/usr/bin/env python3

# budRich@budlabs - 2019
#
# this will make all new windows floating
# due to the way i3 handles for_window rules
# setting a "global rule" to make all new
# windows floating, may have undesired side effects.
#
# https://github.com/i3/i3/issues/3628
# https://github.com/i3/i3/pull/3188
# https://old.reddit.com/r/i3wm/comments/85ctji/when_windows_are_floating_by_default_how_do_i/

from i3ipc import Connection
i3 = Connection()


def set_floating(i3, event):
    event.container.command('floating enable')


i3.on('window::new', set_floating)
i3.main()
