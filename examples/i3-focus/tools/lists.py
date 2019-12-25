from . import App

class Lists:
    @staticmethod
    def accum_uniq_apps(result, app):
        exists = False
        for a in result:
            if a.get_title() == app.get_title():
                exists = True

        if not exists:
            result.append(app)

        return result

    @staticmethod
    def find_all_by_focused_app(infos):
        for i in infos:
            if i["focused"]:
                focused_info = i

        focused_app = App(focused_info)

        focused_app_windows_by_class = list(filter(lambda i: i["window_class"] == focused_app.get_window_class(), infos))
        return focused_app_windows_by_class

    @staticmethod
    def find_app_by_title(title, apps):
        for a in apps:
            if a.get_title() == title:
                return a

    @staticmethod
    def find_container_info_by_title(title, infos):
        for i in infos:
            if i["window_title"] == title:
                return i
