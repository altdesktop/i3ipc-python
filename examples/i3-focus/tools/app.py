import re
import i3ipc

class App:
    def __init__(self, container_info):
        self._container_info = container_info

    def get_con_id(self):
        return self._container_info["id"]

    def get_window_class(self):
        return self._container_info["window_class"]

    def get_title(self):
        # i3 = i3ipc.Connection()
        # print("\n\n")
        # print(vars(i3.get_tree().find_by_id(self._container_info["id"])))
        return re.match(r"^.*?\s*(?P<title>[^-—]+)$", self._container_info["window_title"]).group("title")
