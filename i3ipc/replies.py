class _BaseReply(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]


class CommandReply(_BaseReply):
    """
    Info about a command that was executed with :func:`Connection.command`.
    """

    def __init__(self, data):
        super(CommandReply, self).__init__(data)

    @property
    def error(self):
        """
        A human-readable error message

        :type: str
        """
        return self.__getattr__('error')

    @property
    def success(self):
        """
        Whether the command executed successfully

        :type: bool
        """
        return self.__getattr__('success')


class VersionReply(_BaseReply):
    """
    Info about the version of the running i3 instance.
    """

    def __init__(self, data):
        super(VersionReply, self).__init__(data)

    @property
    def major(self):
        """
        The major version of i3.

        :type: int
        """
        return self.__getattr__('major')

    @property
    def minor(self):
        """
        The minor version of i3.

        :type: int
        """
        return self.__getattr__('minor')

    @property
    def patch(self):
        """
        The patch version of i3.

        :type: int
        """
        return self.__getattr__('patch')

    @property
    def human_readable(self):
        """
        A human-readable version of i3 containing the precise git version,
        build date, and branch name.

        :type: str
        """
        return self.__getattr__('human_readable')

    @property
    def loaded_config_file_name(self):
        """
        The current config path.

        :type: str
        """
        return self.__getattr__('loaded_config_file_name')


class BarConfigReply(_BaseReply):
    """
    This can be used by third-party workspace bars (especially i3bar, but
    others are free to implement compatible alternatives) to get the bar block
    configuration from i3.

    Not all properties are documented here. A complete list of properties of
    this reply type can be found `here
    <http://i3wm.org/docs/ipc.html#_bar_config_reply>`_.
    """

    def __init__(self, data):
        super(BarConfigReply, self).__init__(data)

    @property
    def colors(self):
        """
        Contains key/value pairs of colors. Each value is a color code in hex,
        formatted #rrggbb (like in HTML).

        :type: dict
        """
        return self.__getattr__('colors')

    @property
    def id(self):
        """
        The ID for this bar.

        :type: str
        """
        return self.__getattr__('id')

    @property
    def mode(self):
        """
        Either ``dock`` (the bar sets the dock window type) or ``hide`` (the
        bar does not show unless a specific key is pressed).

        :type: str
        """
        return self.__getattr__('mode')

    @property
    def position(self):
        """
        Either ``bottom`` or ``top``.

        :type: str
        """
        return self.__getattr__('position')

    @property
    def status_command(self):
        """
        Command which will be run to generate a statusline. Each line on
        stdout of this command will be displayed in the bar. At the moment, no
        formatting is supported.

        :type: str
        """
        return self.__getattr__('status_command')

    @property
    def font(self):
        """
        The font to use for text on the bar.

        :type: str
        """
        return self.__getattr__('font')


class OutputReply(_BaseReply):
    pass


class InputReply(_BaseReply):
    pass


class SeatReply(_BaseReply):
    pass


class WorkspaceReply(_BaseReply):
    pass


class TickReply(_BaseReply):
    pass


class ConfigReply(_BaseReply):
    pass
