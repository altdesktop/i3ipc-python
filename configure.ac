AC_PREREQ(2.69)

AC_INIT([i3ipc-python], [0.1.1], [tony@dubstepdish.com])

AM_INIT_AUTOMAKE([-Wall -Werror foreign -Wno-portability])

AM_PATH_PYTHON([3],, [:])

PKG_CHECK_MODULES([PYGOBJECT], [pygobject-3.0])
PKG_CHECK_MODULES([I3IPC], [i3ipc-glib-1.0 >= 0.1])

AC_ARG_WITH([pygi_overrides_dir],
            AC_HELP_STRING([--with-pygi-overrides-dir], [Path to pygobject overrides directory]))

AC_MSG_CHECKING(for pygobject overrides directory)
if test "x$with_pygi_overrides_dir" = "x" ; then
    overrides_dir="`$PYTHON -c 'import gi; print(gi._overridesdir)' 2>/dev/null`"
    # fallback if the previous failed
    if test "x$overrides_dir" = "x" ; then
        overrides_dir="${pyexecdir}/gi/overrides"
    fi
else
    overrides_dir="$with_pygi_overrides_dir"
fi

PYGI_OVERRIDES_DIR="$overrides_dir"
AC_SUBST(PYGI_OVERRIDES_DIR)
AC_MSG_RESULT($PYGI_OVERRIDES_DIR)

AM_SILENT_RULES([yes])

AC_CONFIG_FILES([
                 Makefile
                 overrides/Makefile
                 ])

AC_OUTPUT
