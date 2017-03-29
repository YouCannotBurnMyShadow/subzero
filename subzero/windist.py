import distutils.errors
import distutils.util
import os
import shutil
import json
import go_msi

from .utils import build_dir, enter_directory, generate_guid
from pyspin.spin import make_spin, Spin1
from distutils.command.bdist_msi import bdist_msi as d_bdist_msi

__all__ = ["bdist_msi"]


class bdist_msi(d_bdist_msi):
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
                programs_folder = "ProgramFiles64Folder"
            else:
                programs_folder = "programs_folder"
            self.initial_target_dir = r"[{}]\{}\{}".format(
                programs_folder, author, name)
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
                self.bdist_dir = os.path.dirname(self.bdist_dir)

        if not build_found:
            raise EnvironmentError('Unable to identify build directory!')

        self.bdist_dir = os.path.join(self.bdist_dir, build_dir())
        self.build_temp = os.path.join(
            os.path.dirname(self.bdist_dir),
            'temp' + os.path.basename(self.bdist_dir)[3:])
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
                self.license_text = open(file).read()
                break

    @make_spin(Spin1, 'Harvesting files...')
    def _harvest_files(self):
        directories = []
        files = []

        for dirpath, dirnames, filenames in os.walk(self.build_temp):

            for dirname in dirnames:
                directories.append(
                    os.path.relpath(
                        os.path.join(self.build_temp, dirpath, dirname),
                        self.build_temp))

            for filename in filenames:
                files.append(
                    os.path.relpath(
                        os.path.join(self.build_temp, dirpath, filename),
                        self.build_temp))

        return files, directories

    def _generate_shortcuts(self):
        return [{
            "name": "go-msi",
            "description": "Easy msi pakage for Go",
            "target": "[INSTALLDIR]\\go-msi.exe",
            "wdir": "INSTALLDIR",
            "arguments": ""
        }]

    def _write_json(self, fh):
        license_name = 'LICENSE'
        license_path = os.path.join(self.build_temp, license_name)
        with open(license_path, 'w+') as lfh:
            lfh.write(self.license_text)

        files, directories = self._harvest_files()

        config = {
            "product": self.distribution.get_name(),
            "company": self.distribution.get_author(),
            "license": license_name,
            "upgrade-code": self.upgrade_code,
            "files": {
                "guid": generate_guid(),
                "items": files
            },
            "directories": directories,
            "shortcuts": {
                "guid": generate_guid(),
                "items": self._generate_shortcuts(),
            },
        }

        # write the file
        json.dump(config, fh)

    @make_spin(Spin1, 'Building installer...')
    def _build_msi(self):
        with enter_directory(self.build_temp):
            go_msi.make()

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

        # Resolve all directory names here
        # build_temp = os.path.abspath(self.build_temp)
        # bdist_dir = os.path.abspath(self.bdist_dir)
        # target_name = os.path.abspath(self.target_name)

        with open(os.path.join(self.build_temp, 'wix.json'), 'w+') as fh:
            self._write_json(fh)

        self._build_msi()
