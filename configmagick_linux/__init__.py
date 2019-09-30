import pathlib

from .configmagick_linux import *
from .lib_bash import *
from .lib_install import *


def get_version() -> str:
    with open(str(pathlib.Path(__file__).parent / 'version.txt'), mode='r') as version_file:
        version = version_file.readline()
    return version


__title__ = 'configmagick_linux'
__version__ = get_version()
__name__ = 'configmagick_linux'
