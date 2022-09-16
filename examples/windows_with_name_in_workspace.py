#!/usr/bin/env python3
# print Ids of windows with WM_CLASS on current workspace or workspace with given name
from subprocess import check_output, STDOUT
import i3ipc
import re

def get_windows_on_current_ws(conn):
    return filter(lambda x: x.window,
                  conn.get_tree().find_focused().workspace().descendents())

def workspace_by_name(conn, workspace):
    return next(filter(lambda ws: ws.name==workspace, conn.get_tree().workspaces()), None)

def get_windows_on_ws(conn, name):
    return filter(lambda x: x.window,
                 workspace_by_name(conn, name).descendents())

def main(args):
    if not args.name:
        print("a (non-empty) name argument is required")
        return
    conn = i3ipc.Connection()
    windows = get_windows_on_current_ws(conn)
    if args.workspace:
        windows = get_windows_on_ws(conn, args.workspace)
    for w in windows:
        name = check_output(
            "xprop -id " + str(w.window) + " 2> /dev/null | awk '/^WM_CLASS/{print $4}'",
            shell=True,
            encoding="utf8")
        name = re.sub(r'[\n"]', "", name)
        if name == args.name:
            print(w.window)

if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser(prog='windows_with_name_in_workspace.py',
        description="Program using i3ipc to select the nth window from a workspace.")

    parser.add_argument('--name', "--string", type=str, default=None, help="""windows name in current workspace""")
    parser.add_argument('--workspace', default=None, help="""workspace name""")

    main(parser.parse_args())
