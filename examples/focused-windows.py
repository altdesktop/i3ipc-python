#!/usr/bin/env python3

from argparse import ArgumentParser
import i3ipc

i3 = i3ipc.Connection()


def focused_windows():
    tree = i3.get_tree()

    workspaces = tree.workspaces()
    for workspace in workspaces:
        container = workspace

        while container:
            if not hasattr(container, 'focus') or not container.focus:
                break

            container_id = container.focus[0]
            container = container.find_by_id(container_id)

        if container:
            coname = container.name
            wsname = workspace.name

            print('WS', wsname + ':', coname)


if __name__ == '__main__':
    parser = ArgumentParser(description='Print the names of the focused window of each workspace.')
    parser.parse_args()

    focused_windows()
