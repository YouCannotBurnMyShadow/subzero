# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

import distutils.command.build
import distutils.version
import inspect
import ntpath
import os
import shutil
import sys

import PyInstaller.__main__
from PyInstaller.building.makespec import main as makespec_main
from pkg_resources import EntryPoint

from pyinstaller_utils.windist import bdist_msi

try:
    from distutils.core import setup as distutils_setup
except ImportError:
    from setuptools import setup as distutils_setup

__all__ = ["build_exe", "setup"]


class build_exe(distutils.core.Command):
    description = "build executables from Python scripts"
    user_options = []
    boolean_options = []
    _excluded_args = [
        'scripts',
    ]

    def add_to_path(self, name):
        sourceDir = getattr(self, name.lower())
        if sourceDir is not None:
            sys.path.insert(0, sourceDir)

    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        self.build_exe = None

        for name, parameter in inspect.signature(makespec_main).parameters.items():
            if name not in (self._excluded_args + ['args', 'kwargs']) and not getattr(self, name, None):
                setattr(self, name, None)

    def finalize_options(self):
        distutils.command.build.build.finalize_options(self)
        if self.build_exe is None:
            dirName = "exe.%s-%s" % \
                      (distutils.util.get_platform(), sys.version[0:3])
            self.build_exe = os.path.join(self.build_base, dirName)

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
            for key, value in dict(self.distribution.command_options['build_exe']).items():
                py_options[key] = value[1]
        except (KeyError, TypeError):
            py_options = {}

        os.makedirs(self.build_temp, exist_ok=True)

        for entry_point in entry_points.values():
            scripts.append(self._GenerateScript(entry_point, self.build_temp))

        names = []
        for script in scripts:
            names.append(self._Freeze(script, self.build_temp, self.build_exe, py_options))

        for name in names:
            if name != names[0]:
                self.moveTree(os.path.join(self.build_exe, name), os.path.join(self.build_exe, names[0]))

        self.moveTree(os.path.join(self.build_exe, names[0]), self.build_exe)

        shutil.rmtree(self.build_temp, ignore_errors=True)

        # TODO: Compare file hashes to make sure we haven't replaced files with a different version
        for name in names:
            shutil.rmtree(os.path.join(self.build_exe, name), ignore_errors=True)

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

    def moveTree(self, sourceRoot, destRoot):
        if not os.path.exists(destRoot):
            return False
        ok = True
        for path, dirs, files in os.walk(sourceRoot):
            relPath = os.path.relpath(path, sourceRoot)
            destPath = os.path.join(destRoot, relPath)
            if not os.path.exists(destPath):
                os.makedirs(destPath)
            for file in files:
                destFile = os.path.join(destPath, file)
                if os.path.isfile(destFile):
                    print("Skipping existing file: {}".format(os.path.join(relPath, file)))
                    ok = False
                    continue
                srcFile = os.path.join(path, file)
                # print "rename", srcFile, destFile
                os.rename(srcFile, destFile)
        for path, dirs, files in os.walk(sourceRoot, False):
            if len(files) == 0 and len(dirs) == 0:
                os.rmdir(path)
        return ok

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
        script_path = os.path.join(workpath, '{}.py'.format(entry_point.name))
        with open(script_path, 'w+') as fh:
            fh.write("import {0}\n".format(entry_point.module_name))
            fh.write("{0}.{1}()\n".format(entry_point.module_name, '.'.join(entry_point.attrs)))
            for package in self.distribution.packages + self.distribution.install_requires:
                fh.write("import {0}\n".format(package))

        return script_path

    def _Freeze(self, script, workpath, distpath, options):
        options.setdefault('pathex',[]).append(os.path.dirname(workpath))
        options.setdefault('hiddenimports',[]).extend(self.distribution.packages + self.distribution.install_requires)
        options['name'] = '.'.join(ntpath.basename(script).split('.')[:-1])

        spec_file = PyInstaller.__main__.run_makespec([script], **options)
        PyInstaller.__main__.run_build(None, spec_file, noconfirm=True, workpath=workpath, distpath=distpath)
        os.remove(spec_file)

        return options['name']

def _AddCommandClass(commandClasses, name, cls):
    if name not in commandClasses:
        commandClasses[name] = cls

def setup(**attrs):
    commandClasses = attrs.setdefault("cmdclass", {})
    if sys.platform == "win32":
        if sys.version_info[:2] >= (2, 5):
            _AddCommandClass(commandClasses, "bdist_msi", bdist_msi)
    _AddCommandClass(commandClasses, "build_exe", build_exe)
    distutils_setup(**attrs)
