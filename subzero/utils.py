import sys
import struct
import inspect
import uuid
import os
import distutils
import deepmerge

from PyInstaller import log
from PyInstaller.building.makespec import main as makespec_main
from contextlib import contextmanager
from distutils.debug import DEBUG

if sys.version_info >= (3, 4):
    from contextlib import suppress
else:
    from contextlib2 import suppress

if sys.version_info >= (3, 5):
    from glob import iglob
else:
    import glob
    import glob2

    def iglob(path, recursive=False):
        if recursive:
            return glob2.iglob(path)
        else:
            return glob.iglob(path)


if DEBUG:
    log.logger.setLevel('DEBUG')
else:
    log.logger.setLevel('ERROR')

entry_keys = [
    'console_scripts',
    'gui_scripts',
]

excluded_args = [
    'scripts',
    'specpath',
]


def merge_defaults(a, b):
    merger = deepmerge.Merger(
        # pass in a list of tuple, with the
        # strategies you are looking to apply
        # to each type.
        [(list, ["append"]), (dict, ["merge"])],
        # next, choose the fallback strategies,
        # applied to all other types:
        ["override"],
        # finally, choose the strategies in
        # the case where the types conflict:
        ["override"])

    merger.merge(a, b)
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


def move_tree(source, destination):
    if not os.path.exists(destination):
        return False
    for path, dirs, files in os.walk(source):
        relPath = os.path.relpath(path, source)
        destPath = os.path.join(destination, relPath)
        if not os.path.exists(destPath):
            os.makedirs(destPath)
        for file in files:
            destFile = os.path.join(destPath, file)
            if os.path.isfile(destFile):
                continue
            srcFile = os.path.join(path, file)
            os.rename(srcFile, destFile)
    for path, dirs, files in os.walk(source, False):
        if len(files) == 0 and len(dirs) == 0:
            os.rmdir(path)


def generate_guid():
    """
    generates a GUID
    """
    return str(uuid.uuid1()).upper()


@contextmanager
def enter_directory(path):
    current_directory = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(current_directory)


def get_arch():
    return 8 * struct.calcsize("P")
