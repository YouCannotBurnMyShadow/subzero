import subprocess
import sys

import subzero.dist

try:
    from setuptools import setup as distutils_setup
except ImportError:
    from distutils.core import setup as distutils_setup

from subzero.dist import build_exe, Executable
from subzero.windist import bdist_msi
from pyspin.spin import make_spin, Spin1

version = "5.0"
__version__ = version


def _AddCommandClass(commandClasses, name, cls):
    if name not in commandClasses:
        commandClasses[name] = cls


@make_spin(Spin1, 'Installing project requirements...')
def install_requirements(requirements):
    command = [sys.executable, '-m', 'pip', 'install', '--user'] + requirements
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise e


def append_scripts(scripts, attrs):
    for script in scripts:
        if isinstance(script, Executable):
            attrs['options']['build_exe']['executables'].append(script)
        else:
            attrs['options']['build_exe']['executables'].append(None)


def setup(**attrs):
    entry_points_keys = [
        'console_scripts',
        'gui_scripts',
    ]

    commandClasses = attrs.setdefault("cmdclass", {})
    if sys.platform == "win32":
        if sys.version_info[:2] >= (2, 5):
            _AddCommandClass(commandClasses, "bdist_msi", bdist_msi)
    _AddCommandClass(commandClasses, "build_exe", build_exe)
    if 'install_requires' in attrs and attrs['install_requires']:
        install_requirements(attrs['install_requires'])

    attrs.setdefault('scripts', [])
    attrs.setdefault('options', {}).setdefault('build_exe', {}).setdefault(
        'executables', [])

    append_scripts(attrs['scripts'], attrs)

    for entry_point_key in entry_points_keys:
        attrs.setdefault('entry_points', {}).setdefault(entry_point_key, [])
        append_scripts(attrs['entry_points'][entry_point_key], attrs)

        attrs['entry_points'][entry_point_key] = [
            str(entry_point)
            for entry_point in attrs['entry_points'][entry_point_key]
        ]

    attrs['scripts'] = [str(script) for script in attrs['scripts']]

    distutils_setup(**attrs)


subzero.dist.setup = setup  # Backwards compatibility

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions
