import socket
import json


class Sockets:
    def __init__(self, socket_file):
        self._socket_file = socket_file
        self._client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def get_containers_history(self):
        self._client.connect(self._socket_file)
        history_json = self._client.recv(4096).decode()
        self._client.close()
        return json.loads(history_json)
