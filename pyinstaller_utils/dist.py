# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

import distutils.command.bdist_rpm
import distutils.command.build
import distutils.command.install
import distutils.core
import distutils.dir_util
import distutils.dist
import distutils.errors
import distutils.log
import distutils.util
import distutils.version
import os
import sys

import PyInstaller.__main__
from PyInstaller import DEFAULT_WORKPATH, DEFAULT_DISTPATH
from pkg_resources import EntryPoint

__all__ = ["bdist_rpm", "build", "build_exe", "install", "install_exe",
           "setup"]


class Distribution(distutils.dist.Distribution):
    def __init__(self, attrs):
        self.executables = []
        distutils.dist.Distribution.__init__(self, attrs)


class bdist_rpm(distutils.command.bdist_rpm.bdist_rpm):
    def finalize_options(self):
        distutils.command.bdist_rpm.bdist_rpm.finalize_options(self)
        self.use_rpm_opt_flags = 1

    def _make_spec_file(self):
        contents = distutils.command.bdist_rpm.bdist_rpm._make_spec_file(self)
        contents.append('%define __prelink_undo_cmd %{nil}')
        return [c for c in contents if c != 'BuildArch: noarch']


class build(distutils.command.build.build):
    user_options = distutils.command.build.build.user_options + [
        ('build-exe=', None, 'build directory for executables')
    ]

    def get_sub_commands(self):
        subCommands = distutils.command.build.build.get_sub_commands(self)
        if self.distribution.executables:
            subCommands.append("build_exe")
        return subCommands

    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        self.build_exe = None

    def finalize_options(self):
        distutils.command.build.build.finalize_options(self)
        if self.build_exe is None:
            dirName = "exe.%s-%s" % \
                      (distutils.util.get_platform(), sys.version[0:3])
            self.build_exe = os.path.join(self.build_base, dirName)


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
        options['pathex'] = [os.path.dirname(workpath)]
        options['hiddenimports'] = self.distribution.packages + self.distribution.install_requires
        if type(script) is tuple:
            options['name'] = script[0]
            script = script[1]

        PyInstaller.__main__.run_build(None, PyInstaller.__main__.run_makespec([script], **options),
                                       noconfirm=True, workpath=workpath, distpath=distpath)

class install(distutils.command.install.install):
    user_options = distutils.command.install.install.user_options + [
        ('install-exe=', None,
         'installation directory for executables')
    ]

    def expand_dirs(self):
        distutils.command.install.install.expand_dirs(self)
        self._expand_attrs(['install_exe'])

    def get_sub_commands(self):
        subCommands = distutils.command.install.install.get_sub_commands(self)
        if self.distribution.executables:
            subCommands.append("install_exe")
        return [s for s in subCommands if s != "install_egg_info"]

    def initialize_options(self):
        distutils.command.install.install.initialize_options(self)
        self.install_exe = None

    def finalize_options(self):
        if self.prefix is None and sys.platform == "win32":
            try:
                import winreg
            except:
                import _winreg as winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"Software\Microsoft\Windows\CurrentVersion")
            prefix = str(winreg.QueryValueEx(key, "ProgramFilesDir")[0])
            metadata = self.distribution.metadata
            self.prefix = "%s/%s" % (prefix, metadata.name)
        distutils.command.install.install.finalize_options(self)
        self.convert_paths('exe')
        if self.root is not None:
            self.change_roots('exe')

    def select_scheme(self, name):
        distutils.command.install.install.select_scheme(self, name)
        if self.install_exe is None:
            if sys.platform == "win32":
                self.install_exe = '$base'
            else:
                metadata = self.distribution.metadata
                dirName = "%s-%s" % (metadata.name, metadata.version)
                self.install_exe = '$base/lib/%s' % dirName


def _AddCommandClass(commandClasses, name, cls):
    if name not in commandClasses:
        commandClasses[name] = cls


def setup(**attrs):
    attrs.setdefault("distclass", Distribution)
    commandClasses = attrs.setdefault("cmdclass", {})
    if sys.platform == "win32":
        if sys.version_info[:2] >= (2, 5):
            pass
        #            _AddCommandClass(commandClasses, "bdist_msi", pyinstaller_utils.bdist_msi)
    elif sys.platform == "darwin":
        pass
    #        _AddCommandClass(commandClasses, "bdist_dmg", pyinstaller_utils.bdist_dmg)
    #        _AddCommandClass(commandClasses, "bdist_mac", pyinstaller_utils.bdist_mac)
    else:
        pass
    #        _AddCommandClass(commandClasses, "bdist_rpm", pyinstaller_utils.bdist_rpm)
    _AddCommandClass(commandClasses, "build", build)
    _AddCommandClass(commandClasses, "build_exe", build_exe)
    #    _AddCommandClass(commandClasses, "install", install)
    #    _AddCommandClass(commandClasses, "install_exe", install_exe)
    distutils.core.setup(**attrs)
