# STDLIB
import getpass
import logging
import os
import pathlib
import sys

# OWN
import lib_log_utils
import lib_shell

# EXT
import psutil       # type: ignore

logger = logging.getLogger()


def restart_myself(as_root: bool = False) -> None:
    """Restarts the current program, with file objects and descriptors
       cleanup
    """

    # noinspection PyBroadException
    try:
        p = psutil.Process(os.getpid())
        for handler in p.open_files() + p.connections():
            os.close(handler.fd)
    except Exception:
        lib_log_utils.log_exception_traceback('error on restart myself')
    if as_root:
        os.execl(lib_shell.conf_lib_shell.sudo_command, sys.executable, *sys.argv)
    else:
        os.execl(sys.executable, *sys.argv)


def restart_as_root() -> None:
    restart_myself(as_root=True)


def get_path_home_dir_current_user() -> pathlib.Path:
    """
    # under Linux the $HOME under SUDO points to the /home/user anyway (default = sudo -H)
    >>> path_home_dir = get_path_home_dir_current_user()
    >>> # on max osx path starts with '/Users/'
    >>> assert str(path_home_dir).startswith('/home/') or str(path_home_dir).startswith('/root') or str(path_home_dir).startswith('/Users/')

    """
    username = get_current_username()
    path_home_dir = get_path_home_dir_user(username=username)
    return path_home_dir


def get_path_home_dir_user(username: str) -> pathlib.Path:
    """
    >>> path_home_dir = get_path_home_dir_user(username='root')
    >>> # on max osx path root path is  '/var/root'
    >>> assert str(path_home_dir) == '/root' or str(path_home_dir) == '/var/root'
    """
    path_home_dir = pathlib.Path(os.path.expanduser("~{username}".format(username=username)))
    return path_home_dir


def get_current_username() -> str:
    username = getpass.getuser()
    return username


def get_linux_release_name() -> str:
    """
    >>> assert get_linux_release_name() is not None

    """
    linux_release_name = lib_shell.run_shell_command('lsb_release -c -s', quiet=True).stdout
    return str(linux_release_name)


def get_linux_release_number() -> str:
    """
    returns for instance '18.04'
    >>> assert '.' in get_linux_release_number()

    """
    release = lib_shell.run_shell_command('lsb_release -r -s', quiet=True).stdout
    return str(release)


def get_linux_release_number_major() -> str:
    """
    returns for instance '18'
    >>> assert int(get_linux_release_number_major()) > 11

    """
    release = get_linux_release_number()
    release_major = release.split('.')[0]
    return release_major


def update(quiet: bool = False) -> lib_shell.ShellCommandResponse:
    result = lib_shell.run_shell_command('apt-get update', quiet=quiet, use_sudo=True)
    return result


def get_env_display() -> str:
    """ Returns the Display Variable, or raises if not there

    >>> assert get_env_display() is not None
    """
    if 'DISPLAY' in os.environ:
        display = str(os.environ['DISPLAY'])
    else:
        raise RuntimeError('can not get environment DISPLAY variable')
    return display
