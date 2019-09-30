# ##### STDLIB
import logging
from typing import List

# ##### EXT

# ##### OWN
import lib_regexp
import lib_shell

# ##### PROJECT
try:
    from . import lib_bash                      # type: ignore # pragma: no cover
except ImportError:
    import lib_bash                             # type: ignore # pragma: no cover


class ConfInstall(object):
    def __init__(self) -> None:
        self.apt_command = 'apt-get'                             # type: str
        self.sudo_command = 'sudo'                               # type: str
        self.number_of_retries = 3                               # type: int
        self.sudo_command_exist = self.is_sudo_command_exist()   # type: bool

    def is_sudo_command_exist(self) -> bool:
        try:
            lib_bash.get_bash_command(self.sudo_command)
            return True
        except SyntaxError:
            return False


conf_install = ConfInstall()


logger = logging.getLogger()


def install_linux_packages(packages: List[str], quiet: bool = False, reinstall: bool = False,
                           use_sudo: bool = True, except_on_fail: bool = True) -> int:
    exit_code = 0
    for package in packages:
        exit_code_single = install_linux_package(package=package, quiet=quiet, reinstall=reinstall, except_on_fail=except_on_fail, use_sudo=use_sudo)
        if exit_code_single:
            exit_code = exit_code_single
    return exit_code


def install_linux_package(package: str, quiet: bool = False, reinstall: bool = False, use_sudo: bool = True, except_on_fail: bool = True) -> int:
    """
    returns 0 if ok, otherwise returncode

    >>> is_dialog_installed = is_package_installed('dialog')
    >>> assert uninstall_linux_package('dialog', quiet=True) is not None
    >>> assert install_linux_package('dialog', quiet=True) == 0
    >>> assert install_linux_package('dialog', quiet=True, reinstall=True) == 0
    >>> assert install_linux_package('unknown', quiet=True, except_on_fail = False) != 0
    >>> install_linux_package('unknown', quiet=True, except_on_fail = True)     # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    RuntimeError: Install Package "unknown" failed
    >>> assert uninstall_linux_package('dialog', quiet=True) == 0
    >>> if is_dialog_installed:
    ...     result = install_linux_package('dialog', quiet=True)
    ... else:
    ...     result = uninstall_linux_package('dialog', quiet=True)

    """

    response = lib_shell.ShellCommandResponse()
    if quiet:
        log_settings = lib_shell.set_log_settings_to_level(logging.NOTSET)
    else:
        log_settings = lib_shell.RunShellCommandLogSettings()

    if not is_package_installed(package) or reinstall:

        if reinstall:
            l_command = [conf_install.apt_command, 'install', '--reinstall', package, '-y']
        else:
            l_command = [conf_install.apt_command, 'install', package, '-y']

        if use_sudo:
            l_command = prepend_sudo_command(l_command)

        for n in range(conf_install.number_of_retries):
            response = lib_shell.run_shell_ls_command(ls_command=l_command,
                                                      raise_on_returncode_not_zero=False,
                                                      pass_stdout_stderr_to_sys=not quiet,
                                                      log_settings=log_settings)
            if response.returncode == 0:
                break
        if response.returncode != 0 and except_on_fail:
            raise RuntimeError('Install Package "{package}" failed'.format(package=package))

    return int(response.returncode)


def uninstall_linux_packages(packages: List[str], quiet: bool = False, use_sudo: bool = True, except_on_fail: bool = True) -> int:
    exit_code = 0
    for package in packages:
        exit_code_single = uninstall_linux_package(package=package, quiet=quiet, except_on_fail=except_on_fail, use_sudo=use_sudo)
        if exit_code_single:
            exit_code = exit_code_single
    return exit_code


def uninstall_linux_package(package: str, quiet: bool = False, use_sudo: bool = True, except_on_fail: bool = True) -> int:
    """
    returns 0 if ok, otherwise returncode

    """

    response = lib_shell.ShellCommandResponse()
    if quiet:
        log_settings = lib_shell.set_log_settings_to_level(logging.NOTSET)
    else:
        log_settings = lib_shell.RunShellCommandLogSettings()

    if is_package_installed(package):
        l_command = [conf_install.apt_command, 'purge', package, '-y']

        if use_sudo:
            l_command = prepend_sudo_command(l_command)

        for n in range(conf_install.number_of_retries):
            response = lib_shell.run_shell_ls_command(ls_command=l_command,
                                                      raise_on_returncode_not_zero=False,
                                                      pass_stdout_stderr_to_sys=not quiet,
                                                      log_settings=log_settings)
            if response.returncode == 0:
                break
        if response.returncode != 0 and except_on_fail:
            raise RuntimeError('Uninstall Package "{package}" failed'.format(package=package))

    return int(response.returncode)


def prepend_sudo_command(l_command: List[str]) -> List[str]:
    if conf_install.sudo_command_exist:
        l_command = [conf_install.sudo_command] + l_command
    return l_command


def is_package_installed(package: str) -> bool:
    """
    returns True if installed, otherwise False

    >>> assert is_package_installed('apt') == True
    >>> assert is_package_installed('unknown') == False

    """
    log_settings = lib_shell.set_log_settings_to_level(logging.NOTSET)
    response = lib_shell.run_shell_ls_command(['dpkg', '--list', package],
                                              raise_on_returncode_not_zero=False,
                                              log_settings=log_settings)
    result = lib_regexp.reg_grep(package, response.stdout)
    if not result:
        return False
    if len(result) != 1:
        raise RuntimeError('can not determine')
    if result[0].startswith('ii'):
        return True
    else:
        return False
