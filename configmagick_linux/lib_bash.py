# STDLIB
import getpass
import logging
import os
import pathlib
import sys
from typing import List

# OWN
import lib_log_utils
import lib_shell

# EXT
import psutil       # type: ignore

logger = logging.getLogger()


class ConfBash(object):
    def __init__(self) -> None:
        self.sudo_command = 'sudo'                                  # type: str
        self.number_of_retries = 3                                  # type: int


conf_bash = ConfBash()


class BashCommand(object):
    def __init__(self, command_type: str, command_string: str):

        # command_type: "alias", "keyword", "function", "builtin", "file" or "", if NAME is an alias,
        # shell reserved word, shell function, shell builtin, disk file,
        # or not found, respectively
        self.command_type = command_type           # type: str
        self.command_string = command_string       # type: str


def get_bash_command(bash_command: str) -> BashCommand:
    """ gets type and command string for bash command

    :bash_command internal or external bash command
    :returns BashCommand
    :raises ValueError if command does not exist

    >>> bash_command=get_bash_command('type')
    >>> assert bash_command.command_type == 'builtin'
    >>> assert bash_command.command_string == 'type'

    >>> bash_command=get_bash_command('unknown')  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Traceback (most recent call last):
    ...
    SyntaxError: Bash Command does not exist

    >>> bash_command.command_type
    'builtin'
    >>> bash_command.command_string
    'type'


    """
    ls_command = ['bash', '-c', 'type -t {bash_command}'.format(bash_command=bash_command)]
    shell_response = lib_shell.run_shell_ls_command(ls_command, raise_on_returncode_not_zero=False)
    if shell_response.returncode != 0:
        raise SyntaxError('Bash Command does not exist')
    else:
        command_type = shell_response.stdout.strip()

    ls_command = ['bash', '-c', 'command -v {bash_command}'.format(bash_command=bash_command)]
    shell_response = lib_shell.run_shell_ls_command(ls_command, raise_on_returncode_not_zero=False)
    if shell_response.returncode != 0:
        raise ValueError('Bash Command does not exist')
    else:
        command_string = shell_response.stdout.strip()

    bash_command_object = BashCommand(command_type=command_type, command_string=command_string)
    return bash_command_object


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
        bash_command = get_bash_command('sudo').command_string
        os.execl(bash_command, sys.executable, *sys.argv)
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


def run_shell_command(command: str, quiet: bool = False, use_sudo: bool = True, except_on_fail: bool = True,
                      retries: int = conf_bash.number_of_retries, sudo_command: str = conf_bash.sudo_command) -> int:
    """
    returns 0 if ok, otherwise returncode. prepends "sudo_command" if required

    """

    l_command = lib_shell.shlex_split_multi_platform(command)
    return run_shell_l_command(l_command=l_command, quiet=quiet, use_sudo=use_sudo,
                               except_on_fail=except_on_fail, retries=retries, sudo_command=sudo_command)


def run_shell_l_command(l_command: List[str], quiet: bool = False, use_sudo: bool = True, except_on_fail: bool = True,
                        retries: int = conf_bash.number_of_retries, sudo_command: str = conf_bash.sudo_command) -> int:
    """
    returns 0 if ok, otherwise returncode. prepends "sudo_command" if required

    """

    response = lib_shell.ShellCommandResponse()
    if quiet:
        log_settings = lib_shell.set_log_settings_to_level(logging.NOTSET)
    else:
        log_settings = lib_shell.RunShellCommandLogSettings()

    if use_sudo:
        l_command = prepend_sudo_command(l_command=l_command, sudo_command=sudo_command)

    for n in range(retries):
        response = lib_shell.run_shell_ls_command(ls_command=l_command,
                                                  raise_on_returncode_not_zero=False,
                                                  pass_stdout_stderr_to_sys=not quiet,
                                                  log_settings=log_settings)
        if response.returncode == 0:
            break
    if response.returncode != 0 and except_on_fail:
        raise RuntimeError('command "{command}" failed'.format(command=' '.join(l_command)))
    return int(response.returncode)


def prepend_sudo_command(l_command: List[str], sudo_command: str = 'sudo') -> List[str]:
    if sudo_command_exist(sudo_command=sudo_command):
        l_command = [sudo_command] + l_command
    return l_command


def sudo_command_exist(sudo_command: str = 'sudo') -> bool:
    try:
        get_bash_command(sudo_command)
        return True
    except SyntaxError:
        return False
