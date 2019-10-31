# ##### STDLIB
import logging
import os
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


conf_install = ConfInstall()


logger = logging.getLogger()


def install_linux_packages(packages: List[str],
                           quiet: bool = False,
                           reinstall: bool = False,
                           use_sudo: bool = True,
                           raise_on_returncode_not_zero: bool = True) -> List[lib_shell.ShellCommandResponse]:
    l_results = []
    for package in packages:
        result = install_linux_package(package=package, reinstall=reinstall, raise_on_returncode_not_zero=raise_on_returncode_not_zero,
                                       use_sudo=use_sudo, quiet=quiet)
        l_results.append(result)

    return l_results


def install_linux_package(package: str, parameters: List[str] = [], quiet: bool = False, reinstall: bool = False,
                          use_sudo: bool = True, raise_on_returncode_not_zero: bool = True) -> lib_shell.ShellCommandResponse:
    """
    returns 0 if ok, otherwise returncode

    >>> is_dialog_installed = is_package_installed('dialog')
    >>> result = uninstall_linux_package('dialog', quiet=True)
    >>> assert is_package_installed('dialog') == False
    >>> result1 = install_linux_package('dialog', quiet=True)
    >>> assert is_package_installed('dialog') == True
    >>> result2 = install_linux_package('dialog', quiet=True, reinstall=True)
    >>> assert is_package_installed('dialog') == True
    >>> result3 = install_linux_package('unknown', quiet=True, raise_on_returncode_not_zero = False)
    >>> install_linux_package('unknown', quiet=True, raise_on_returncode_not_zero = True)     # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    subprocess.CalledProcessError: Command 'sudo apt-get install unknown -y' returned non-zero exit status ...

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

        result = lib_shell.run_shell_ls_command(ls_command=l_command,
                                                shell=True,
                                                quiet=quiet,
                                                use_sudo=use_sudo,
                                                raise_on_returncode_not_zero=raise_on_returncode_not_zero,
                                                pass_stdout_stderr_to_sys=True)
    return result


def uninstall_linux_packages(packages: List[str],
                             quiet: bool = False,
                             use_sudo: bool = True,
                             raise_on_returncode_not_zero: bool = True) -> List[lib_shell.ShellCommandResponse]:
    l_result = []
    for package in packages:
        result = uninstall_linux_package(package=package, quiet=quiet, raise_on_returncode_not_zero=raise_on_returncode_not_zero, use_sudo=use_sudo)
        l_result.append(result)
    return l_result


def uninstall_linux_package(package: str,
                            quiet: bool = False,
                            use_sudo: bool = True,
                            raise_on_returncode_not_zero: bool = True) -> lib_shell.ShellCommandResponse:

    result = lib_shell.ShellCommandResponse()

    if is_package_installed(package) or is_wildcard_in_package_name(package):
        l_command = [conf_install.apt_command, 'purge', package, '-y']

        result = lib_shell.run_shell_ls_command(ls_command=l_command,
                                                shell=True,
                                                quiet=quiet,
                                                use_sudo=use_sudo,
                                                raise_on_returncode_not_zero=raise_on_returncode_not_zero,
                                                pass_stdout_stderr_to_sys=True)
    return result


def full_update_and_upgrade(quiet: bool = False) -> None:
    lib_shell.run_shell_command('{apt_command} update'.format(apt_command=conf_install.apt_command),
                                use_sudo=True, shell=True, pass_stdout_stderr_to_sys=True, quiet=quiet)
    lib_shell.run_shell_command('{apt_command} upgrade -y'.format(apt_command=conf_install.apt_command),
                                use_sudo=True, shell=True, pass_stdout_stderr_to_sys=True, quiet=quiet)
    lib_shell.run_shell_command('{apt_command} dist-upgrade -y'.format(apt_command=conf_install.apt_command),
                                use_sudo=True, shell=True, pass_stdout_stderr_to_sys=True, quiet=quiet)
    lib_shell.run_shell_command('{apt_command} autoclean -y'.format(apt_command=conf_install.apt_command),
                                use_sudo=True, shell=True, pass_stdout_stderr_to_sys=True, quiet=quiet)
    lib_shell.run_shell_command('{apt_command} autoremove -y'.format(apt_command=conf_install.apt_command),
                                use_sudo=True, shell=True, pass_stdout_stderr_to_sys=True, quiet=quiet)


def is_wildcard_in_package_name(package: str) -> bool:
    if '*' in package or '?' in package:
        return True
    else:
        return False


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


def download_file(download_link: str, filename: pathlib.Path, quiet: bool = True, use_sudo: bool = False) -> None:
    lib_shell.run_shell_command('wget -nv -c --no-check-certificate -O "{filename}" "{download_link}"'
                                .format(filename=filename, download_link=download_link),
                                quiet=quiet,
                                use_sudo=use_sudo)
    if not filename.exists():
        raise RuntimeError('File "{filename}" can not be downloaded from "{download_link}"'
                           .format(filename=filename, download_link=download_link))


def is_on_travis() -> bool:
    """
    >>> assert is_on_travis() is not None
    """
    is_travis = False
    if 'TRAVIS' in os.environ:                                  # pragma: no cover
        if str(os.environ['TRAVIS']).lower() == 'true':
            is_travis = True
    return is_travis


def is_service_installed(service: str) -> bool:
    """
    >>> assert not is_service_installed('unknown')
    >>> assert is_service_installed('ssh') is not None
    """

    response = lib_shell.run_shell_command(command='systemctl list-units --full -all | fgrep "{service}.service"'.format(service=service),
                                           shell=True, raise_on_returncode_not_zero=False, log_settings=lib_shell.conf_lib_shell.log_settings_qquiet)
    return bool(response.stdout)


def is_service_active(service: str) -> bool:
    """
    >>> assert not is_service_active('unknown')
    >>> if is_service_installed('ssh'):
    ...     is_ssh_active = is_service_active('ssh')
    ...     stop_service('ssh')
    ...     assert not is_service_active('ssh')
    ...     start_service('ssh')
    ...     assert is_service_active('ssh')
    ...     if not is_ssh_active:
    ...         stop_service('ssh')

    """
    response = lib_shell.run_shell_command(command='systemctl is-active {service}'.format(service=service),
                                           shell=True, log_settings=lib_shell.conf_lib_shell.log_settings_qquiet,
                                           raise_on_returncode_not_zero=False)
    if response.stdout.startswith('active'):
        return True
    else:
        return False


def start_service(service: str, quiet: bool = False) -> None:
    """
    >>> import unittest
    >>> unittest.TestCase().assertRaises(RuntimeError, start_service, service='unknown')
    """
    if not is_service_installed(service=service):
        raise RuntimeError('can not start service "{service}", because it is not installed'.format(service=service))
    if not is_service_active(service=service):
        lib_shell.run_shell_command(command='service {service} start'.format(service=service), shell=True, use_sudo=True, quiet=quiet)
        if not is_service_active(service=service):
            raise RuntimeError('can not start service "{service}"'.format(service=service))


def stop_service(service: str, quiet: bool = False) -> None:
    """
    >>> import unittest
    >>> unittest.TestCase().assertRaises(RuntimeError, stop_service, service='unknown')
    """
    if not is_service_installed(service=service):
        raise RuntimeError('can not stop service "{service}", because it is not installed'.format(service=service))
    if is_service_active(service=service):
        lib_shell.run_shell_command(command='service {service} stop'.format(service=service), shell=True, use_sudo=True, quiet=quiet)
        if is_service_active(service=service):
            raise RuntimeError('can not stop service "{service}"'.format(service=service))


def set_inotify_watches(max_user_watches: int = 512*1024):
    """ set inotify watches for pycharm and other applications
        512K is appropriate for most applications
    """
    # TODO
    # add line to /etc/sysctl.conf
    # on Debian systems (like Ubuntu) one should not modify /etc/sysctl.conf, but create a new file in /etc/sysctl.d/.
    # This will keep your system package upgradable.
    # After version 207 SYSTEMD no longer reads from "/etc/sysctl.conf".  It reads from "etc/systctl.d/##-sysctl.conf"  Where ## means any number 01-99.
    # fs.inotify.max_user_watches = 524288 # max_user_watches
    # apply the change:
    # sudo sysctl -p --system
    pass
