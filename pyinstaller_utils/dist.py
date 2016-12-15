# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

import distutils.version
import os
import sys

import PyInstaller.__main__
from PyInstaller import DEFAULT_WORKPATH, DEFAULT_DISTPATH
from pkg_resources import EntryPoint

try:
    from distutils.core import setup as distutils_setup
except ImportError:
    from setuptools import setup as distutils_setup

__all__ = ["build_exe", "setup"]


class build_exe(distutils.core.Command):
    description = "build executables from Python scripts"
    user_options = []
    boolean_options = []

    def add_to_path(self, name):
        sourceDir = getattr(self, name.lower())
        if sourceDir is not None:
            sys.path.insert(0, sourceDir)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        metadata = self.distribution.metadata

        try:
            self.distribution.install_requires = list(self.distribution.install_requires)
        except TypeError:
            self.distribution.install_requires = []

        try:
            self.distribution.packages = list(self.distribution.packages)
        except TypeError:
            self.distribution.packages = []

        try:
            scripts = list(self.distribution.scripts)
        except TypeError:
            scripts = []
        try:
            entry_points = EntryPoint.parse_map(self.distribution.entry_points)['console_scripts']
        except KeyError:
            entry_points = []
        try:
            py_options = {}
            for key, value in dict(self.distribution.command_options['PyInstaller']).items():
                py_options[key] = value[1]
        except (KeyError, TypeError):
            py_options = {}

        os.makedirs(DEFAULT_WORKPATH, exist_ok=True)

        for entry_point in entry_points.values():
            scripts.append(self._GenerateScript(entry_point, DEFAULT_WORKPATH))

        for script in scripts:
            self._Freeze(script, DEFAULT_WORKPATH, DEFAULT_DISTPATH, py_options)

    def set_source_location(self, name, *pathParts):
        envName = "%s_BASE" % name.upper()
        attrName = name.lower()
        sourceDir = getattr(self, attrName)
        if sourceDir is None:
            baseDir = os.environ.get(envName)
            if baseDir is None:
                return
            sourceDir = os.path.join(baseDir, *pathParts)
            if os.path.isdir(sourceDir):
                setattr(self, attrName, sourceDir)

    def _GenerateScript(self, entry_point, workpath):
        """
        Generates a script given an entry point.
        :param entry_point:
        :param workpath:
        :return: The script location
        """

        # entry_point.attrs is tuple containing function
        # entry_point.module_name is string representing module name
        # entry_point.name is string representing script name

        # script name must not be a valid module name to avoid name clashes on import
        script_path = os.path.join(workpath, '{}-script.py'.format(entry_point.name))
        with open(script_path, 'w+') as fh:
            fh.write("import {0}\n".format(entry_point.module_name))
            fh.write("{0}.{1}()\n".format(entry_point.module_name, '.'.join(entry_point.attrs)))
            for package in self.distribution.packages + self.distribution.install_requires:
                fh.write("import {0}\n".format(package))

        return entry_point.name, script_path

    def _Freeze(self, script, workpath, distpath, options):
        options.setdefault('pathex',[]).append(os.path.dirname(workpath))
        options.setdefault('hiddenimports',[]).extend(self.distribution.packages + self.distribution.install_requires)
        if type(script) is tuple:
            options['name'] = script[0]
            script = script[1]

        PyInstaller.__main__.run_build(None, PyInstaller.__main__.run_makespec([script], **options),
                                       noconfirm=True, workpath=workpath, distpath=distpath)

def _AddCommandClass(commandClasses, name, cls):
    if name not in commandClasses:
        commandClasses[name] = cls

def setup(**attrs):
    # attrs.setdefault("distclass", Distribution)
    commandClasses = attrs.setdefault("cmdclass", {})
    _AddCommandClass(commandClasses, "build_exe", build_exe)
    distutils_setup(**attrs)
