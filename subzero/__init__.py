import subprocess
import sys
import itertools

from setuptools import setup as distutils_setup

from . import dist
from .dist import build_exe, Executable, entry_keys
from .utils import merge_defaults
from pyspin.spin import make_spin, Spin1

version = "5.0"
__version__ = version


def _AddCommandClass(commandClasses, name, cls):
    if name not in commandClasses:
        commandClasses[name] = cls


@make_spin(Spin1, 'Installing project requirements...')
def install_requirements(requirements):
    if not requirements:
        return

    command = [sys.executable, '-m', 'pip', 'install', '--user'] + requirements
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise e


def setup(**attrs):
    defaults = {
        'cmdclass': {},
        'install_requires': [],
        'scripts': [],
        'entry_points': {entry_key: []
                         for entry_key in entry_keys},
        'options': {
            'build_exe': {
                'executables': [],
            },
        },
    }

    attrs = merge_defaults(attrs, defaults)

    if sys.platform == "win32":
        from .windist import bdist_msi
        _AddCommandClass(attrs['cmdclass'], "bdist_msi", bdist_msi)
    _AddCommandClass(attrs['cmdclass'], "build_exe", build_exe)

    install_requirements(attrs['install_requires'])

    for script in attrs['scripts'] + list(
            itertools.chain(* [
                attrs['entry_points'][entry_key] for entry_key in entry_keys
            ])):
        if isinstance(script, Executable):

            attrs['options']['build_exe']['executables'].append(script)
        else:
            attrs['options']['build_exe']['executables'].append(None)

    attrs['scripts'] = [str(script) for script in attrs['scripts']]
    for entry_key in entry_keys:
        attrs['entry_points'][entry_key] = [
            str(entry_point)
            for entry_point in attrs['entry_points'][entry_key]
        ]

    distutils_setup(**attrs)


from ._version import get_versions

__version__ = get_versions()['version']
del get_versions
