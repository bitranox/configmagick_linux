# ##### STDLIB
import logging
import pathlib
import time
from typing import List, Union

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
        self.apt_command = 'apt-get'                                # type: str
        self.sudo_command = 'sudo'                                  # type: str
        self.number_of_retries = 3                                  # type: int


conf_install = ConfInstall()


logger = logging.getLogger()


def install_linux_packages(packages: List[str], quiet: bool = False, reinstall: bool = False,
                           use_sudo: bool = True, except_on_fail: bool = True) -> List[lib_shell.ShellCommandResponse]:
    l_results = []
    for package in packages:
        result = install_linux_package(package=package, quiet=quiet, reinstall=reinstall, except_on_fail=except_on_fail, use_sudo=use_sudo)
        l_results.append(result)

    return l_results


def install_linux_package(package: str, parameters: List[str] = [], quiet: bool = False, reinstall: bool = False,
                          use_sudo: bool = True, except_on_fail: bool = True) -> lib_shell.ShellCommandResponse:
    """
    returns 0 if ok, otherwise returncode

    >>> is_dialog_installed = is_package_installed('dialog')
    >>> result = uninstall_linux_package('dialog', quiet=True)
    >>> result1 = install_linux_package('dialog', quiet=True)
    >>> result2 = install_linux_package('dialog', quiet=True, reinstall=True)
    >>> result3 = install_linux_package('unknown', quiet=True, except_on_fail = False)
    >>> install_linux_package('unknown', quiet=True, except_on_fail = True)     # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    RuntimeError: command "sudo apt-get install unknown -y" failed

    >>> result = uninstall_linux_package('dialog', quiet=True)
    >>> if is_dialog_installed:
    ...     result = install_linux_package('dialog', quiet=True)
    ... else:
    ...     result = uninstall_linux_package('dialog', quiet=True)

    """

    result = lib_shell.ShellCommandResponse()
    if not is_package_installed(package) or reinstall:

        if reinstall:
            l_command = [conf_install.apt_command, 'install', '--reinstall', package, '-y']
        else:
            l_command = [conf_install.apt_command, 'install', package, '-y']

        l_command = l_command + parameters

        result = lib_bash.run_shell_l_command(l_command=l_command,
                                              quiet=quiet,
                                              use_sudo=use_sudo,
                                              except_on_fail=except_on_fail,
                                              retries=conf_install.number_of_retries,
                                              sudo_command=conf_install.sudo_command
                                              )
    return result


def uninstall_linux_packages(packages: List[str], quiet: bool = False,
                             use_sudo: bool = True, except_on_fail: bool = True) -> List[lib_shell.ShellCommandResponse]:
    l_result = []
    for package in packages:
        result = uninstall_linux_package(package=package, quiet=quiet, except_on_fail=except_on_fail, use_sudo=use_sudo)
        l_result.append(result)
    return l_result


def uninstall_linux_package(package: str, quiet: bool = False, use_sudo: bool = True, except_on_fail: bool = True) -> lib_shell.ShellCommandResponse:

    result = lib_shell.ShellCommandResponse()

    if is_package_installed(package):
        l_command = [conf_install.apt_command, 'purge', package, '-y']

        result = lib_bash.run_shell_l_command(l_command=l_command,
                                              quiet=quiet,
                                              use_sudo=use_sudo,
                                              except_on_fail=except_on_fail,
                                              retries=conf_install.number_of_retries,
                                              sudo_command=conf_install.sudo_command
                                              )
    return result


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
    result = lib_regexp.reg_grep(package + ' ', response.stdout)
    if not result:
        return False
    if len(result) != 1:
        raise RuntimeError('can not determine if package "{package}" is installed'.format(package=package))
    if result[0].startswith('ii'):
        return True
    else:
        return False


def wait_for_file_to_be_created(filename: pathlib.Path, max_wait: Union[int, float] = 60, check_interval: Union[int, float] = 1) -> None:
    start_time = time.time()
    while not filename.exists():
        time.sleep(check_interval)
        if time.time() - start_time > max_wait:
            raise TimeoutError('"{filename}" was not created within {max_wait} seconds'
                               .format(filename=filename, max_wait=max_wait))


def wait_for_file_to_be_unchanged(filename: pathlib.Path, max_wait: Union[int, float] = 60, check_interval: Union[int, float] = 1) -> None:
    start_time = time.time()
    old_mtime = filename.stat().st_mtime
    current_mtime = old_mtime + 1
    while old_mtime != current_mtime:
        old_mtime = filename.stat().st_mtime
        time.sleep(check_interval)
        current_mtime = filename.stat().st_mtime
        if time.time() - start_time > max_wait:
            raise TimeoutError('"{filename}" did not remain unchanged within {max_wait} seconds'
                               .format(filename=filename, max_wait=max_wait))


def download_file(download_link: str, filename: pathlib.Path) -> None:
    lib_bash.run_shell_command('wget -nv -c -O "{filename}" "{download_link}"'.format(filename=filename, download_link=download_link))
