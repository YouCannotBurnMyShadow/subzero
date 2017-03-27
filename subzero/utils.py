import sys

if sys.version_info >= (3, 4):
    from contextlib import suppress
else:
    from contextlib2 import suppress

from PyInstaller.building.makespec import main as makespec_main
import inspect
import uuid
import os
import distutils

entry_keys = [
    'console_scripts',
    'gui_scripts',
]

excluded_args = [
    'scripts',
    'specpath',
]


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


def makespec_args():
    names = ['datas']  # signature does not detect datas for some reason
    for name, parameter in inspect.signature(makespec_main).parameters.items():
        if name not in (excluded_args + ['args', 'kwargs']):
            names.append(name)

    return names


def decode(bytes_or_string):
    if isinstance(bytes_or_string, bytes):
        return bytes_or_string.decode()
    else:
        return bytes_or_string


def is_binary(file):
    return file.endswith(('.so', '.pyd', '.dll', ))


def rename_script(executable):
    # Per issue #32.
    new_script_name = '{}.{}.py'.format(executable.script, str(uuid.uuid4()))
    os.rename(executable.script, new_script_name)
    executable.script = new_script_name


def build_dir():
    return "exe.{}-{}".format(distutils.util.get_platform(), sys.version[0:3])
