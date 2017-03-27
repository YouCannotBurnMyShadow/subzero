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
    if not requirements:
        return

    command = [sys.executable, '-m', 'pip', 'install', '--user'] + requirements
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise e


def merge_defaults(a, b):
    """merges b into a and return merged result"""
    key = None
    try:
        if a is None or isinstance(a, str) or isinstance(a, int) or isinstance(
                a, float):
            # border case for first run or if a is a primitive
            a = b
        elif isinstance(a, list):
            # lists can be only appended
            if isinstance(b, list):
                # merge lists
                a.extend(b)
            else:
                # append to list
                a.append(b)
        elif isinstance(a, dict):
            # dicts must be merged
            if isinstance(b, dict):
                for key in b:
                    if key in a:
                        a[key] = merge_defaults(a[key], b[key])
                    else:
                        a[key] = b[key]
            else:
                raise RuntimeError(
                    'Cannot merge non-dict "%s" into dict "%s"' % (b, a))
        else:
            raise RuntimeError('NOT IMPLEMENTED "%s" into "%s"' % (b, a))
    except TypeError as e:
        raise RuntimeError(
            'TypeError "%s" in key "%s" when merging "%s" into "%s"' % (e, key,
                                                                        b, a))
    return a


def setup(**attrs):
    entry_keys = [
        'console_scripts',
        'gui_scripts',
    ]

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
        if sys.version_info[:2] >= (2, 5):
            _AddCommandClass(attrs['cmdclass'], "bdist_msi", bdist_msi)
    _AddCommandClass(attrs['cmdclass'], "build_exe", build_exe)

    install_requirements(attrs['install_requires'])

    for script in attrs['scripts'] + [
            attrs['entry_points'][entry_key] for entry_key in entry_keys
    ]:
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


subzero.dist.setup = setup  # Backwards compatibility

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions
