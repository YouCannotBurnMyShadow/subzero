# This file was originally taken from cx_freeze by Anthony Tuininga, and is licensed under the  PSF license.

import distutils.command.build
import distutils.version
import importlib.util
import inspect
import json
import ntpath
import os
import pathlib
import shutil
import subprocess
import sys
from subprocess import CalledProcessError

import PyInstaller.__main__
from PyInstaller.building.makespec import main as makespec_main
from PyInstaller.utils.hooks import collect_submodules
from packaging import version
from pkg_resources import EntryPoint, Requirement

if sys.version_info >= (3, 4):
    from contextlib import suppress
else:
    from contextlib2 import suppress

__all__ = ["build_exe", "setup"]


class build_exe(distutils.core.Command):
    description = "build executables from Python scripts"
    user_options = []
    boolean_options = []
    _excluded_args = [
        'scripts',
        'specpath',
    ]


    @classmethod
    def makespec_args(cls):
        names = ['datas']  # signature does not detect datas for some reason
        for name, parameter in inspect.signature(makespec_main).parameters.items():
            if name not in (cls._excluded_args + ['args', 'kwargs']):
                names.append(name)

        return names

    @staticmethod
    def decode(bytes_or_string):
        if isinstance(bytes_or_string, bytes):
            return bytes_or_string.decode()
        else:
            return bytes_or_string

    @staticmethod
    def is_binary(file):
        return file.endswith((
            '.so',
            '.pyd',
            '.dll',
        ))


    @staticmethod
    def build_dir():
        return "exe.{}-{}".format(distutils.util.get_platform(), sys.version[0:3])

    def add_to_path(self, name):
        sourceDir = getattr(self, name.lower())
        if sourceDir is not None:
            sys.path.insert(0, sourceDir)

    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        self.build_exe = None
        self.optimize_imports = True
        self.executables = []

        for name in self.makespec_args():
            if not getattr(self, name, None):
                setattr(self, name, None)

    def finalize_options(self):
        distutils.command.build.build.finalize_options(self)
        if self.build_exe is None:
            self.build_exe = os.path.join(self.build_base, self.build_dir())

        try:
            self.distribution.install_requires = list(self.distribution.install_requires)
        except TypeError:
            self.distribution.install_requires = []

        try:
            self.distribution.setup_requires = list(self.distribution.setup_requires)
        except TypeError:
            self.distribution.setup_requires = []

        try:
            self.distribution.packages = list(self.distribution.packages)
        except TypeError:
            self.distribution.packages = []

        try:
            self.distribution.scripts = list(self.distribution.scripts)
        except TypeError:
            self.distribution.scripts = []

        self.distribution.entry_points.setdefault('console_scripts', [])

    def run(self):
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

        scripts = self.distribution.scripts
        for required_directory in [self.build_temp, self.build_exe]:
            shutil.rmtree(required_directory, ignore_errors=True)
            os.makedirs(required_directory, exist_ok=True)

        for entry_point in entry_points.values():
            scripts.append(self._generate_script(entry_point, self.build_temp))

        lib_dirs = ['lib', 'lib{}'.format(self.build_dir()[3:])]
        for lib_dir in lib_dirs:
            shutil.rmtree(os.path.join(self.build_base, lib_dir), ignore_errors=True)

        self.run_command('build')

        for default_option in ['pathex', 'hiddenimports', 'binaries']:
            py_options.setdefault(default_option, [])

        # by convention, all paths appended to py_options must be absolute
        py_options['hiddenimports'].extend(self.distribution.install_requires)
        for lib_dir in lib_dirs:
            if os.path.isdir(os.path.join(self.build_base, lib_dir)):
                py_options['pathex'].append(os.path.abspath(os.path.join(self.build_base, lib_dir)))

        if not py_options['pathex']:
            raise ValueError('Unable to find lib directory!')

        if version.parse(sys.version[0:3]) >= version.parse('3.4'):
            for package in self.distribution.packages:
                py_options['hiddenimports'].extend(collect_submodules(package))

        py_options['specpath'] = os.path.abspath(self.build_temp)
        py_options['pathex'].append(os.path.abspath(self.build_temp))

        if not self.optimize_imports:
            self.discover_dependencies(py_options)
        
        names = []
        for script in scripts:
            names.append(self._freeze(script, self.build_temp, self.build_exe, py_options.copy()))

        for name in names[1:]:
            self.move_tree(os.path.join(self.build_exe, name), os.path.join(self.build_exe, names[0]))

        self.move_tree(os.path.join(self.build_exe, names[0]), self.build_exe)

        shutil.rmtree(self.build_temp, ignore_errors=True)

        # TODO: Compare file hashes to make sure we haven't replaced files with a different version
        for name in names:
            shutil.rmtree(os.path.join(self.build_exe, name), ignore_errors=True)

    def discover_dependencies(self, options):
        packages = []
        for requirement in self.distribution.setup_requires:
            requirement = Requirement.parse(requirement)
            packages.append(requirement.key)

        entries = json.loads(self.decode(subprocess.check_output(['pipdeptree', '--json'])))
        updated = True
        while updated:
            updated = False
            for entry in entries:
                if entry['package']['key'] in packages:
                    for dependency in entry['dependencies']:
                        if dependency['key'] not in packages:
                            packages.append(dependency['key'])
                            updated = True

        location_string = 'Location:'
        files_string = 'Files:'
        top_packages = {}
        for package in packages:
            in_header = True
            root = None
            with suppress(CalledProcessError):
                for line in self.decode(subprocess.check_output(['pip', 'show', '-f', package])).splitlines():
                    if in_header and line.startswith(location_string):
                        root = line[len(location_string):].strip()
                    if in_header and line.startswith(files_string):
                        assert root is not None
                        in_header = False
                        continue
                    elif not in_header:
                        top_packages[pathlib.Path(line).parts[0].strip()] = root
                        if self.is_binary(line.strip()):
                            options['pathex'].append(os.path.dirname(os.path.join(root, line.strip())))

        for top_package, root in top_packages.items():
            with suppress(ImportError, ValueError, AttributeError):
                if importlib.util.find_spec(top_package) is not None:
                    options['hiddenimports'].extend(collect_submodules(top_package))
                    options['pathex'].append(root)

        options['pathex'] = list(set(options['pathex']))

    @staticmethod
    def move_tree(sourceRoot, destRoot):
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

    def _generate_script(self, entry_point, workpath):
        """
        Generates a script given an entry point.
        :param entry_point:
        :param workpath:
        :return: The script location
        """

        # note that build_scripts appears to work sporadically

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

    def _freeze(self, script, workpath, distpath, options):
        options['name'] = '.'.join(ntpath.basename(script).split('.')[:-1])

        executable = self.executables.pop(0)
        if executable:
            # We need to apply the script-specific options
            for option_name, script_option in executable.options.items():
                options[option_name] = script_option

        with suppress(OSError):
            os.remove(os.path.join(options['specpath'], '{}.spec'.format(options['name'])))

        spec_file = PyInstaller.__main__.run_makespec([script], **options)
        PyInstaller.__main__.run_build(None, spec_file, noconfirm=True, workpath=workpath, distpath=distpath)
        # os.remove(spec_file)

        return options['name']


class Executable(object):
    def __str__(self):
        return self.script

    def __init__(self, script, **kwargs):
        self.script = script
        self._options = {}

        for name in kwargs:
            if name in build_exe.makespec_args():
                self._options[name] = kwargs[name]

    @property
    def options(self):
        return self._options
