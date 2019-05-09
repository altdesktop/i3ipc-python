#!/usr/bin/env python3

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
        raise SystemExit("The `xprop` utility is not found!" " Please install it and retry.")

    return '_NET_WM_STATE_HIDDEN' not in xprop


def pick_from_list(lst, n, alt=None):
    cnt = len(lst)
    return lst[max(0, min(n, cnt - 1))] if cnt > 0 else alt


def main(args):
    conn = i3ipc.Connection()

    workspace = workspace_by_name(conn, args.workspace)  # Find workspace.
    if workspace is None:
        print("Workspace not found, making it.")
        conn.command("workspace " + args.workspace)

    else:
        windows = workspace.leaves()  # Find windows in there.
        if args.filter == 'visible':
            windows = filter(window_is_visible, windows)
        elif args.filter != 'none':
            print("WARN: currently only support `visible` as window filter.")

        window = pick_from_list(list(windows), args.nth)  # Pick correct window from there.

        if window is not None:
            print("Focussing %d" % window.window)
            conn.command('[id="%d"] focus' % window.window)
        else:
            print("Did not find window(%d) going to workspace anyway." % args.nth)
            conn.command("workspace " + args.workspace)

    if args.mode != 'no':
        conn.command("mode " + args.mode)


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog='nth_window_in_workspace.py',
        description="Program using i3ipc to select the nth window from a workspace.")

    parser.add_argument('workspace', help="Name of workspace to go to.")
    parser.add_argument('nth',
                        type=int,
                        default=0,
                        help="""Nth window in that workspace.
If integer too high it will go to the last one, if no windows in there, goes to the workspace.""")
    parser.add_argument("--filter",
                        default='none',
                        help="filters to apply, i.e. `visible` or `none`(default)")
    parser.add_argument("--mode",
                        default='default',
                        help="""Convenience feature;
what to change the i3-mode to afterwards. So you can exit the mode after you're done.
Defaultly it goes back to `default`, can set it to `no` to not change mode at all.""")

    main(parser.parse_args())
