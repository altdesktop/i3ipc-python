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
        window_class = self._container_info["window_class"]
        method_name = '_get_title_' + window_class.replace('-', '_').lower()
        method = getattr(self, method_name, self._get_title_based_on_class)
        return method()

    def _get_title_based_on_class(self):
        return self._container_info["window_class"].replace('-', ' ').title()

    def _get_title_based_on_title(self):
        return re.match(r"^.*?\s*(?P<title>[^-—]+)$",
                        self._container_info["window_title"]).group("title")

    # App specific functions

    def _get_title_google_chrome(self):
        is_browser_in_app_mode = self._container_info["window_role"] == "pop-up"
        if is_browser_in_app_mode:
            return self._get_title_based_on_title() + ' (Chrome)'

        return self._get_title_based_on_class()

    def _get_title_st_256color(self):
        title = self._get_title_based_on_title()

        if self._container_info["window_title"] != "Simple Terminal":
            return title + ' (ST)'

        return title
