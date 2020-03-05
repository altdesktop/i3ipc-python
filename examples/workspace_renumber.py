#!/usr/bin/env python3

import i3ipc

# make connection to i3 ipc
i3 = i3ipc.Connection()


# check if workspaces are all in order
def workspaces_ordered(i3conn):
    last_workspace = 0
    for i in sorted(i3conn.get_workspaces(), key=lambda x: x.num):
        number = int(i.num)
        if number != last_workspace + 1:
            return False
        last_workspace += 1
    return True


# find all the workspaces that are out of order and
# the least possible valid workspace number that is unassigned
def find_disordered(i3conn):
    disordered = []
    least_number = None
    workspaces = sorted(i3conn.get_workspaces(), key=lambda x: x.num)
    occupied_workspaces = [int(x.num) for x in workspaces]
    last_workspace = 0
    for i in workspaces:
        number = int(i.num)
        if number != last_workspace + 1:
            disordered.append(number)
            if least_number is None and last_workspace + 1 not in occupied_workspaces:
                least_number = last_workspace + 1
        last_workspace += 1
    return (disordered, least_number)


# renumber all the workspaces that appear out of order from the others
def fix_ordering(i3conn):
    if workspaces_ordered(i3conn):
        return
    else:
        workspaces = i3conn.get_tree().workspaces()
        disordered_workspaces, least_number = find_disordered(i3conn)
        containers = list(filter(lambda x: x.num in disordered_workspaces, workspaces))
        for c in containers:
            for i in c.leaves():
                i.command("move container to workspace %s" % least_number)
            least_number += 1
    return


# callback for when workspace focus changes
def on_workspace_focus(i3conn, e):
    fix_ordering(i3conn)


if __name__ == '__main__':
    i3.on('workspace::focus', on_workspace_focus)
    i3.main()
