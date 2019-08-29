#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
This script dynamically renames workspaces after the focused window name.

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
https://github.com/nwg-piotr

License: BSD 3-Clause

*** Pay attention to the fact, that your workspaces need to be NUMBERED, NOT NAMED for the script to work.

Use:
bindsym $mod+1 workspace number 1

instead of:
bindsym $mod+1 workspace 1

in your ~/.config/sway/config or ~/.config/i3/config file.
"""

from i3ipc import Connection, Event

# truncate workspace name to this value
max_length = 30

i3 = Connection()


# A glyph will substitute the WS name if no window active, otherwise it'll be prepended before the window name.
# Glyphs below should look well with the icomoon font installed.
# Add more glyphs if you use more than 8 workspaces.
def glyph(ws_number):
    glyphs = ["", "", "", "", "", "", "", ""]  # redefine according to you taste
    # Or you may use words instead of glyphs:
    # glyphs = ["HOME", "WWW", "FILE", "GAME", "TERM", "PIC", "TXT", "CODE"]
    try:
        return glyphs[ws_number - 1]
    except IndexError:
        return "?"


# Name the workspace after the focused window name
def assign_generic_name(i3, e):
    if not e.change == 'rename':  # avoid looping
        try:
            con = i3.get_tree().find_focused()
            if not con.type == 'workspace':  # avoid renaming new empty workspaces on 'binding' event
                if not e.change == 'new':
                    # con.type == 'floating_con'        - indicates floating enabled in Sway
                    # con.floating                      - may be equal 'auto_on' or 'user_on' in i3
                    is_floating = con.type == 'floating_con' or con.floating and '_on' in con.floating

                    # Tiling mode or floating indication. Change symbols if necessary.
                    layout = con.parent.layout
                    if layout == 'splith':
                        split_text = '⇢' if not is_floating else ''
                    elif layout == 'splitv':
                        split_text = '⇣' if not is_floating else ''
                    else:
                        split_text = ''

                    ws_old_name = con.workspace().name
                    ws_name = "%s: %s\u00a0%s %s " % (
                        con.workspace().num, glyph(con.workspace().num), split_text, con.name)
                    name = ws_name if len(ws_name) <= max_length else ws_name[:max_length - 1] + "…"

                    i3.command('rename workspace "%s" to %s' % (ws_old_name, name))
                else:
                    # In sway we may open a new window w/o moving focus; let's give the workspace a name anyway.
                    con = i3.get_tree().find_by_id(e.container.id)
                    ws_num = con.workspace().num
                    w_name = con.name if con.name else ''

                    if w_name and ws_num:
                        name = "%s: %s\u00a0%s" % (ws_num, glyph(ws_num), w_name)
                        i3.command('rename workspace "%s" to %s' % (ws_num, name))

            else:
                # Give the (empty) workspace a generic name: "number: glyph" (like "1: ")
                ws_num = con.workspace().num
                ws_new_name = "%s: %s" % (ws_num, glyph(ws_num))

                i3.command('rename workspace to "{}"'.format(ws_new_name))

        except Exception as ex:
            exit(ex)


def main():
    # Subscribe to events
    i3.on(Event.WORKSPACE_FOCUS, assign_generic_name)
    i3.on(Event.WINDOW_FOCUS, assign_generic_name)
    i3.on(Event.WINDOW_TITLE, assign_generic_name)
    i3.on(Event.WINDOW_CLOSE, assign_generic_name)
    i3.on(Event.WINDOW_NEW, assign_generic_name)
    i3.on(Event.BINDING, assign_generic_name)

    i3.main()


if __name__ == "__main__":
    main()
