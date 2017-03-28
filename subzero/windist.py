import distutils.command.bdist_msi
import distutils.errors
import distutils.util
import ntpath
import os
import re
import shutil
import string
import uuid
import textwrap
from io import StringIO

import pywix
from pkg_resources import resource_filename, resource_string

from .dist import build_exe
from .utils import build_dir

__all__ = ["bdist_msi"]


class bdist_msi(distutils.command.bdist_msi.bdist_msi):
    user_options = distutils.command.bdist_msi.bdist_msi.user_options + [
        ('add-to-path=', None, 'add target dir to PATH environment variable'),
        ('upgrade-code=', None, 'upgrade code to use'),
        ('initial-target-dir=', None, 'initial target directory'),
        ('target-name=', None, 'name of the file to create'),
        ('directories=', None, 'list of 3-tuples of directories to create'),
        ('data=', None, 'dictionary of data indexed by table name'),
        ('product-code=', None, 'product code to use')
    ]

    def finalize_options(self):
        distutils.command.bdist_msi.bdist_msi.finalize_options(self)
        name = self.distribution.get_name()
        fullname = self.distribution.get_fullname()
        author = self.distribution.get_author()
        if self.initial_target_dir is None:
            if distutils.util.get_platform() == "win-amd64":
                programFilesFolder = "ProgramFiles64Folder"
            else:
                programFilesFolder = "ProgramFilesFolder"
            self.initial_target_dir = r"[{}]\{}\{}".format(
                programFilesFolder, author, name)
        if self.add_to_path is None:
            self.add_to_path = False
        if self.target_name is None:
            self.target_name = fullname
        if not self.target_name.lower().endswith(".msi"):
            platform = distutils.util.get_platform().replace("win-", "")
            self.target_name = "%s-%s.msi" % (self.target_name, platform)
        if not os.path.isabs(self.target_name):
            self.target_name = os.path.join(self.dist_dir, self.target_name)
        if self.directories is None:
            self.directories = []
        if self.data is None:
            self.data = {}

        # attempt to find the build directory
        build_found = False
        for i in range(0, 3):
            if os.path.basename(self.bdist_dir) == 'build':
                build_found = True
                break
            else:
                self.bdist_dir = ntpath.dirname(self.bdist_dir)

        if not build_found:
            raise EnvironmentError('Unable to identify build directory!')

        self.bdist_dir = os.path.join(self.bdist_dir, build_dir())
        self.build_temp = os.path.join(
            ntpath.dirname(self.bdist_dir),
            'temp' + ntpath.basename(self.bdist_dir)[3:])
        self.height = 270

    def initialize_options(self):
        distutils.command.bdist_msi.bdist_msi.initialize_options(self)
        self.upgrade_code = None
        self.product_code = None
        self.add_to_path = None
        self.initial_target_dir = None
        self.target_name = None
        self.directories = None
        self.data = None
        self.shortcuts = None

        # TODO: Parse other types of license files
        for file in ['LICENSE', 'LICENSE.txt']:
            if os.path.isfile(file):
                self.license_text = self._license_text(open(file))
                break

    def _compile(self, names, out):
        with open('License.rtf', 'w+') as license_file:
            license_file.write(self.license_text)

        candle_arguments = ['candle', '-arch', 'x64']
        light_arguments = [
            'light', '-ext', 'WixUIExtension', '-cultures:en-us',
            '-dWixUILicenseRtf=License.rtf'
        ]

        for name in names:
            candle_arguments.append('{}.wxs'.format(name))
            light_arguments.append('{}.wixobj'.format(name))

        light_arguments.extend(['-out', out])

        for args in [candle_arguments, light_arguments]:
            pywix.call_wix_command(args)

    def run(self):
        # self.skip_build = True
        if not self.skip_build:
            self.run_command('build_exe')

        self.mkpath(self.dist_dir)
        if os.path.exists(self.target_name):
            os.unlink(self.target_name)

        try:
            shutil.rmtree(self.build_temp)
        except OSError:
            pass

        os.makedirs(self.build_temp, exist_ok=True)

        current_directory = os.getcwd()
        # Resolve all directory names here
        build_temp = os.path.abspath(self.build_temp)
        bdist_dir = os.path.abspath(self.bdist_dir)
        target_name = os.path.abspath(self.target_name)
        files = [
            'Product',
        ]

        for file in files:
            shutil.copy(
                resource_filename('subzero.resources', '{}.wxs'.format(file)),
                self.build_temp)

        os.chdir(build_temp)
        os.environ['bdist_dir'] = bdist_dir
        print(
            pywix.call_wix_command([
                'heat', 'dir', bdist_dir, '-cg', 'ApplicationFiles', '-gg',
                '-sfrag', '-sreg', '-dr', 'INSTALLDIR', '-var',
                'env.bdist_dir', '-t', 'HeatTransform.xslt', '-out',
                'Directory.wxs'
            ]))

        # we need to remove the root directory that heat puts in
        self._repair_harvest()
        self._generate_shortcuts()
        self._generate_globals()
        self._compile(files, target_name)

        wixpdb_name = '{}.wixpdb'.format(os.path.splitext(target_name)[0])
        try:
            shutil.move(wixpdb_name, build_temp)
        except OSError:
            pass

        os.chdir(current_directory)
