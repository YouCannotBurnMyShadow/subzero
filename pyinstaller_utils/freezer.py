# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

"""
Base class for freezing scripts into executables.
"""

from __future__ import print_function

import distutils.sysconfig
import os
import sys

import PyInstaller.__main__
from PyInstaller import DEFAULT_WORKPATH, DEFAULT_DISTPATH
from pkg_resources import EntryPoint

import pyinstaller_utils

__all__ = ["ConfigError", "ConstantsModule", "Executable", "Freezer"]

EXTENSION_LOADER_SOURCE = \
    """
    def __bootstrap__():
        import imp, os, sys
        global __bootstrap__, __loader__
        __loader__ = None; del __bootstrap__, __loader__

        found = False
        for p in sys.path:
            if not os.path.isdir(p):
                continue
            f = os.path.join(p, "%s")
            if not os.path.exists(f):
                continue
            m = imp.load_dynamic(__name__, f)
            import sys
            sys.modules[__name__] = m
            found = True
            break
        if not found:
            del sys.modules[__name__]
            raise ImportError("No module named %%s" %% __name__)
    __bootstrap__()
    """

MSVCR_MANIFEST_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<noInheritable/>
<assemblyIdentity
    type="win32"
    name="Microsoft.VC90.CRT"
    version="9.0.21022.8"
    processorArchitecture="{PROC_ARCH}"
    publicKeyToken="1fc8b3b9a1e18e3b"/>
<file name="MSVCR90.DLL"/>
<file name="MSVCM90.DLL"/>
<file name="MSVCP90.DLL"/>
</assembly>
"""

def process_path_specs(specs):
    """Prepare paths specified as config.
    
    The input is a list of either strings, or 2-tuples (source, target).
    Where single strings are supplied, the basenames are used as targets.
    Where targets are given explicitly, they must not be absolute paths.
    
    Returns a list of 2-tuples, or throws ConfigError if something is wrong
    in the input.
    """
    processedSpecs = []
    for spec in specs:
        if not isinstance(spec, (list, tuple)):
            source = spec
            target = None
        elif len(spec) != 2:
            raise ConfigError("path spec must be a list or tuple of "
                              "length two")
        else:
            source, target = spec
        source = os.path.normpath(source)
        if not target:
            target = os.path.basename(source)
        elif os.path.isabs(target):
            raise ConfigError("target path for include file may not be "
                              "an absolute path")
        processedSpecs.append((source, target))
    return processedSpecs


def get_resource_file_path(dirName, name, ext):
    """Return the path to a resource file shipped with
    
    This is used to find our base executables and initscripts when they are
    just specified by name.
    """
    if os.path.isabs(name):
        return name
    name = os.path.normcase(name)
    fullDir = os.path.join(os.path.dirname(pyinstaller_utils.__file__), dirName)
    if os.path.isdir(fullDir):
        for fileName in os.listdir(fullDir):
            checkName, checkExt = \
                os.path.splitext(os.path.normcase(fileName))
            if name == checkName and ext == checkExt:
                return os.path.join(fullDir, fileName)


class Freezer(object):
    def __init__(self, scripts, entry_points, constantsModules=[], includes=[],
                 excludes=[], packages=[], replacePaths=[], compress=True,
                 optimizeFlag=0, path=None, options=[],
                 targetDir=None, binIncludes=[], binExcludes=[],
                 binPathIncludes=[], binPathExcludes=[],
                 includeFiles=[], zipIncludes=[], silent=False,
                 namespacePackages=[], metadata=None,
                 includeMSVCR=False, zipIncludePackages=[],
                 zipExcludePackages=["*"]):
        # TODO: Understand why this varible is present
        targetDir = None
        distDir = None

        try:
            self.scripts = list(scripts)
        except TypeError:
            self.scripts = []
        try:
            self.entry_points = EntryPoint.parse_map(entry_points)['console_scripts']
        except KeyError:
            self.entry_points = []
        try:
            self.options = {}
            for key, value in dict(options['PyInstaller']).items():
                self.options[key] = value[1]
        except (KeyError, TypeError):
            self.options = {}
        self.constantsModules = list(constantsModules)
        self.includes = list(includes)
        self.excludes = list(excludes)
        self.packages = list(packages)
        self.namespacePackages = list(namespacePackages)
        self.replacePaths = list(replacePaths)
        self.compress = compress
        self.optimizeFlag = optimizeFlag
        self.path = path
        self.includeMSVCR = includeMSVCR
        self.targetDir = targetDir
        self.distDir = distDir
        self.binIncludes = [os.path.normcase(n) \
                            for n in self._GetDefaultBinIncludes() + binIncludes]
        self.binExcludes = [os.path.normcase(n) \
                            for n in self._GetDefaultBinExcludes() + binExcludes]
        self.binPathIncludes = [os.path.normcase(n) for n in binPathIncludes]
        self.binPathExcludes = [os.path.normcase(n) \
                                for n in self._GetDefaultBinPathExcludes() + binPathExcludes]
        self.includeFiles = process_path_specs(includeFiles)
        self.zipIncludes = process_path_specs(zipIncludes)
        self.silent = silent
        self.metadata = metadata
        self.zipIncludePackages = list(zipIncludePackages)
        self.zipExcludePackages = list(zipExcludePackages)
        self._VerifyConfiguration()

    def _GetDefaultBinExcludes(self):
        """Return the file names of libraries that need not be included because
           they would normally be expected to be found on the target system or
           because they are part of a package which requires independent
           installation anyway."""
        if sys.platform == "win32":
            return ["comctl32.dll", "oci.dll", "cx_Logging.pyd"]
        else:
            return ["libclntsh.so", "libwtc9.so"]

    def _GetDefaultBinIncludes(self):
        """Return the file names of libraries which must be included for the
           frozen executable to work."""
        if sys.platform == "win32":
            pythonDll = "python%s%s.dll" % sys.version_info[:2]
            return [pythonDll, "gdiplus.dll", "mfc71.dll", "msvcp71.dll",
                    "msvcr71.dll"]
        else:
            soName = distutils.sysconfig.get_config_var("INSTSONAME")
            if soName is None:
                return []
            pythonSharedLib = self._RemoveVersionNumbers(soName)
            return [pythonSharedLib]

    def _GetDefaultBinPathExcludes(self):
        """Return the paths of directories which contain files that should not
           be included, generally because they contain standard system
           libraries."""
        return []

    def _VerifyConfiguration(self):
        if self.compress is None:
            self.compress = True
        if self.targetDir is None:
            self.targetDir = DEFAULT_WORKPATH
        if self.distDir is None:
            self.distDir = DEFAULT_DISTPATH
        if self.path is None:
            self.path = sys.path

        for sourceFileName, targetFileName in \
                        self.includeFiles + self.zipIncludes:
            if not os.path.exists(sourceFileName):
                raise ConfigError("cannot find file/directory named %s",
                                  sourceFileName)
            if os.path.isabs(targetFileName):
                raise ConfigError("target file/directory cannot be absolute")

        self.zipExcludeAllPackages = "*" in self.zipExcludePackages
        self.zipIncludeAllPackages = "*" in self.zipIncludePackages
        if self.zipExcludeAllPackages and self.zipIncludeAllPackages:
            raise ConfigError("all packages cannot be included and excluded " \
                              "from the zip file at the same time")
        for name in self.zipIncludePackages:
            if name in self.zipExcludePackages:
                raise ConfigError("package %s cannot be both included and " \
                                  "excluded from zip file", name)

    def _GenerateScript(self, entry_point):
        """
        Generates a script given an entry point.
        :param entry_point:
        :return: The script location
        """

        # entry_point.attrs is tuple containing function
        # entry_point.module_name is string representing module name
        # entry_point.name is string representing script name

        # script name must not be a valid module name to avoid name clashes on import
        script_path = os.path.join(self.targetDir, '{}-script.py'.format(entry_point.name))
        with open(script_path, 'w') as fh:
            fh.write("import {0}\n".format(entry_point.module_name))
            fh.write("{0}.{1}()\n".format(entry_point.module_name, '.'.join(entry_point.attrs)))
            for package in self.packages:
                fh.write("import {0}\n".format(package))

        return script_path

    def _Freeze(self):
        self.options['pathex'] = [os.path.dirname(self.targetDir)]

        PyInstaller.__main__.run_build(None, PyInstaller.__main__.run_makespec(self.scripts, **self.options),
                                       noconfirm=True, workpath=self.targetDir, distpath=self.distDir)

    def Freeze(self):
        os.makedirs(self.targetDir)

        for entry_point in self.entry_points.values():
            self.scripts.append(self._GenerateScript(entry_point))

        self._Freeze()

class ConfigError(Exception):
    def __init__(self, format, *args):
        self.what = format % args

    def __str__(self):
        return self.what


class ConstantsModule(object):
    def __init__(self, releaseString=None, copyright=None,
                 moduleName="BUILD_CONSTANTS", timeFormat="%B %d, %Y %H:%M:%S"):
        self.moduleName = moduleName
        self.timeFormat = timeFormat
        self.values = {}
        self.values["BUILD_RELEASE_STRING"] = releaseString
        self.values["BUILD_COPYRIGHT"] = copyright

    def Create(self, finder):
        """Create the module which consists of declaration statements for each
           of the values."""
        today = datetime.datetime.today()
        sourceTimestamp = 0
        for module in finder.modules:
            if module.file is None:
                continue
            if module.inZipFile:
                continue
            if not os.path.exists(module.file):
                raise ConfigError("no file named %s (for module %s)",
                                  module.file, module.name)
            timestamp = os.stat(module.file).st_mtime
            sourceTimestamp = max(sourceTimestamp, timestamp)
        sourceTimestamp = datetime.datetime.fromtimestamp(sourceTimestamp)
        self.values["BUILD_TIMESTAMP"] = today.strftime(self.timeFormat)
        self.values["BUILD_HOST"] = socket.gethostname().split(".")[0]
        self.values["SOURCE_TIMESTAMP"] = \
            sourceTimestamp.strftime(self.timeFormat)
        module = finder._AddModule(self.moduleName)
        sourceParts = []
        names = list(self.values.keys())
        names.sort()
        for name in names:
            value = self.values[name]
            sourceParts.append("%s = %r" % (name, value))
        source = "\n".join(sourceParts)
        module.code = compile(source, "%s.py" % self.moduleName, "exec")
        return module

class VersionInfo(object):
    def __init__(self, version, internalName=None, originalFileName=None,
                 comments=None, company=None, description=None,
                 copyright=None, trademarks=None, product=None, dll=False,
                 debug=False, verbose=True):
        parts = version.split(".")
        while len(parts) < 4:
            parts.append("0")
        self.version = ".".join(parts)
        self.internal_name = internalName
        self.original_filename = originalFileName
        self.comments = comments
        self.company = company
        self.description = description
        self.copyright = copyright
        self.trademarks = trademarks
        self.product = product
        self.dll = dll
        self.debug = debug
        self.verbose = verbose
