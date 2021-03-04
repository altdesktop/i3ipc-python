#!/usr/bin/python

import re
import sys

import psutil
import i3ipc

def get_window_id_by_pid(pid):
    with open('/proc/{}/environ'.format(pid), 'r') as f:
        pid_env = f.read()
    match = re.search(r'WINDOWID=(\d+)', pid_env)
    wid = int(match.group(1))
    return wid

def get_session_pid(session_name):
    for process in psutil.process_iter():
        if '--servername {}'.format(session_name.lower()) in ' '.join(process.cmdline()).lower():
            yield process.pid

def get_vim_window_id(session_name):
    while True:
        try:
            pid = next(get_session_pid(session_name))
        except StopIteration:
            break
        if pid is None:
            continue
        else:
            break
    return get_window_id_by_pid(pid)


def main():
    for line in sys.stdin:
        vim_window_id = get_vim_window_id(line.strip('\n'))
        break
    if vim_window_id is not None:
        con = i3ipc.Connection()
        con.command('[id=%s] focus' % vim_window_id)


if __name__ == "__main__":
    main()
