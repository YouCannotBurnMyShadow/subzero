import distutils
import os

from PyInstaller import DEFAULT_WORKPATH
from PyInstaller.building.build_main import Analysis

# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

version = "5.0"
__version__ = version

# from pyinstaller_utils.freezer import Freezer, ConstantsModule

import sys

if sys.platform == "win32":
    pass
elif sys.platform == "darwin":
    pass


def build_dir():
    return "exe.{}-{}".format(distutils.util.get_platform(), sys.version[0:3])

def Entrypoint(dist, group, name,
               scripts=None, pathex=None, hiddenimports=None,
               hookspath=None, excludes=None, runtime_hooks=None, **kwargs):
    import pkg_resources

    # get toplevel packages of distribution from metadata
    def get_toplevel(dist):
        distribution = pkg_resources.get_distribution(dist)
        if distribution.has_metadata('top_level.txt'):
            return list(distribution.get_metadata('top_level.txt').split())
        else:
            return []

    packages = hiddenimports or []
    for distribution in hiddenimports:
        packages += get_toplevel(distribution)

    scripts = scripts or []
    pathex = pathex or []
    # get the entry point
    ep = pkg_resources.get_entry_info(dist, group, name)
    # insert path of the egg at the verify front of the search path
    pathex = [ep.dist.location] + pathex
    # script name must not be a valid module name to avoid name clashes on import
    script_path = os.path.join(DEFAULT_WORKPATH, name + '-script.py')
    print
    "creating script for entry point", dist, group, name
    with open(script_path, 'w') as fh:
        fh.write("import {0}\n".format(ep.module_name))
        fh.write("{0}.{1}()\n".format(ep.module_name, '.'.join(ep.attrs)))
        for package in packages:
            fh.write("import {0}\n".format(package))

    return Analysis([script_path] + scripts, pathex=pathex, hiddenimports=hiddenimports, hookspath=hookspath,
                    excludes=excludes, runtime_hooks=runtime_hooks, **kwargs)
