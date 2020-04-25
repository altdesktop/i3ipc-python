#!/usr/bin/env python3

# * Can go straight to a window given a workspace, integer-index of window pair.
#   (for instance for mapping keys to windows in a mode for that)
# * Can also go to workspace, or cycle through the windows on that.
#   (as opposed to going there and the button not having a use while there)

from itertools import cycle
from subprocess import check_output
import i3ipc

def get_windows_on_ws(conn):
    return filter(lambda x: x.window, conn.get_tree().find_focused().workspace().descendents())


def workspace_by_name(conn, workspace):
    return next(filter(lambda ws: ws.name == workspace, conn.get_tree().workspaces()), None)


def window_is_visible(w):
    try:
        xprop = check_output(['xprop', '-id', str(w.window)]).decode()
    except FileNotFoundError:
        raise SystemExit("The `xprop` utility is not found! Please install it and retry.")

    return '_NET_WM_STATE_HIDDEN' not in xprop


def pick_from_list(lst, n, alt=None):
    cnt = len(lst)
    return lst[max(0, min(n, cnt - 1))] if cnt > 0 else alt


def with_prev(gen):
    """Takes a generator, and returns the elements, with the previous element.
The first element only appears as previous. (and the last never-as)
NOTE: maybe add optionals `w_first` and `w_last`"""
    prev = next(gen)
    for el in gen:
        yield prev, el
        prev = el


def main(args):
    conn = i3ipc.Connection()

    workspace = workspace_by_name(conn, args.workspace)  # Find workspace.
    if workspace is None:
        print("Workspace %s not found, making it."%args.workspace)
        conn.command("workspace " + args.workspace)

    else:
        windows =  list(workspace.leaves())  # Find windows in there.
        if args.filter == 'visible':
            windows = filter(window_is_visible, windows)
        elif args.filter != 'none':
            print("WARN: currently only support `visible` as window filter.")

        window = None
        if args.select.isdigit():  # Pick `nth` window in there.
            window = pick_from_list(list(windows), int(args.select))
        # If any selected, cycle next.
        elif args.select in ['c', 'r', 'cycle', 'reverse']:
            cycle_windows = cycle(windows)
            prev, cur_win = \
                next(((p,w) for _i, (p, w)  # Where current window in cycle.
                      in zip(range(len(windows)+1), with_prev(cycle_windows))
                      if w.focused), (None,None))
            if cur_win is None:  # Not in cycle, start with first.
                window = pick_from_list(list(windows), 0)
            else:
                if args.select in ['c', 'cycle']:
                    window = next(cycle_windows)
                else:
                    window = prev

        if window != None:
            print("Focussing %d" % window.window)
            conn.command('[id="%d"] focus' % window.window)
        else:
            print("Did not find window(%s) going to workspace anyway."%args.select)
            conn.command("workspace " + args.workspace)

    if args.mode != 'no':
        conn.command("mode " + args.mode)


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog='nth_window_in_workspace.py',
        description="""Program to:
* Select the nth window from a workspace. (i.e. for mapping each window to a key)
* Go to workspace, or cycle through the windows of the workspace.
  (improvement on just going to the workspace)""")

    parser.add_argument('workspace', help="Name of workspace to go to.")
    parser.add_argument('select',
                        default='0',
                        help="""If integer, that index in workspace.
if `c`,`cycle` cycle forward if already on same workspace. `r`,`reverse` goes
backward.
If none apply goes to the first window in the workspace.""")
    parser.add_argument("--filter",
                        default='none',
                        help="filters to apply, i.e. `visible` or `none`(default)")
    parser.add_argument("--mode",
                        default='default',
                        help="""Convenience feature;
what to change the i3-mode to afterwards. So you can exit the mode after you're done.
Defaultly it goes back to `default`, can set it to `no` to not change mode at all.""")

    main(parser.parse_args())
