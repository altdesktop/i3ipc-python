from collections import deque
from subprocess import check_output
from . import Lists, App


class Menu:
    def __init__(self, i3, menu, menu_args):
        self._i3 = i3
        self._menu = menu
        self._menu_args = menu_args

    def show_menu(self, items):
        menu_input = bytes(str.join('\n', items), 'UTF-8')
        menu_cmd = [self._menu] + ['-l', str(len(items))] + self._menu_args
        menu_result = check_output(menu_cmd, input=menu_input)
        return menu_result.decode().strip()

    def show_menu_app(self, apps):
        titles = list(map(lambda a: a.get_title(), apps))
        selected_title = self.show_menu(titles)
        selected_app = Lists.find_app_by_title(selected_title, apps)
        tree = self._i3.get_tree()
        con = tree.find_by_id(selected_app.get_con_id())
        con.command('focus')

    def show_menu_container_info(self, containers_info):
        titles = self._get_titles_with_app_prefix(containers_info)
        titles_with_suffix = self._add_uniqu_suffix(titles)
        infos_by_title = dict(zip(titles_with_suffix, containers_info))
        selected_title = self.show_menu(titles_with_suffix)
        selected_info = infos_by_title[selected_title]
        tree = self._i3.get_tree()
        con = tree.find_by_id(selected_info["id"])
        con.command('focus')

    def _get_titles_with_app_prefix(self, containers_info):
        return list(map(lambda i: App(i).get_title() + ': ' + i["window_title"], containers_info))

    def _add_uniqu_suffix(self, titles):
        counters = dict()
        titles_with_suffix = []
        for title in titles:
            counters[title] = counters[title] + 1 if title in counters else 1
            if counters[title] > 1:
                title = f'{title} ({counters[title]})'

            titles_with_suffix.append(title)

        return titles_with_suffix
