import subprocess
import sys
import StringIO

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
    buffer = StringIO.StringIO()
    command = [sys.executable, '-m', 'pip', 'install', '--user'] + requirements
    if subprocess.call(command, stdout=buffer, stderr=buffer):
        print(buffer.getvalue())
        raise Exception('failed to install project requirements')


def setup(**attrs):
    commandClasses = attrs.setdefault("cmdclass", {})
    if sys.platform == "win32":
        if sys.version_info[:2] >= (2, 5):
            _AddCommandClass(commandClasses, "bdist_msi", bdist_msi)
    _AddCommandClass(commandClasses, "build_exe", build_exe)
    if 'install_requires' in attrs and attrs['install_requires']:
        install_requirements(attrs['install_requires'])

    attrs.setdefault('scripts', [])
    attrs.setdefault('entry_points', {}).setdefault('console_scripts', [])
    attrs.setdefault('options', {}).setdefault('build_exe', {}).setdefault(
        'executables', [])

    for script in attrs['scripts'] + attrs['entry_points']['console_scripts']:
        if type(script) is Executable:
            attrs['options']['build_exe']['executables'].append(script)
        else:
            attrs['options']['build_exe']['executables'].append(None)

    attrs['scripts'] = [str(script) for script in attrs['scripts']]
    attrs['entry_points']['console_scripts'] = \
        [str(entry_point) for entry_point in attrs['entry_points']['console_scripts']]

    distutils_setup(**attrs)


subzero.dist.setup = setup  # Backwards compatibility

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions
