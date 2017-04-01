import distutils.errors
import distutils.util
import os
import shutil
import json
import go_msi
import re
import io

from .utils import build_dir, enter_directory, generate_guid, get_arch
from .rtf import write_rtf
from pyspin.spin import make_spin, Spin1
from distutils.command.bdist_msi import bdist_msi as d_bdist_msi
from PyInstaller import log
from subprocess import CalledProcessError


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
        author = self.distribution.get_author()

        self.directories = self.directories or []
        self.data = self.data or {}
        self.add_to_path = self.add_to_path or False
        self.target_name = self.target_name or ''
        self.upgrade_code = (self.upgrade_code or
                             generate_guid()).strip('{}').upper()

        if self.initial_target_dir is None:
            if distutils.util.get_platform() == 'win-amd64':
                programs_folder = 'ProgramFiles64Folder'
            else:
                programs_folder = 'programs_folder'
            self.initial_target_dir = r'[{}]\{}\{}'.format(
                programs_folder, author, name)

        if not self.target_name.lower().endswith('.msi'):
            platform = distutils.util.get_platform().replace('win-', '')
            self.target_name = '%s-%s.msi' % (self.target_name, platform)
        if not os.path.isabs(self.target_name):
            self.target_name = os.path.join(self.dist_dir, self.target_name)

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

        self._license = os.path.join(self.build_temp,
                                     '{}.rtf'.format(generate_guid()))

    def initialize_options(self):
        distutils.command.bdist_msi.bdist_msi.initialize_options(self)
        self.upgrade_code = None
        self.product_code = None
        self.add_to_path = None
        self.initial_target_dir = None
        self.target_name = None
        self.directories = None
        self.data = None
        self.shortcuts = []

        # TODO: Parse other types of license files
        for file in ['LICENSE', 'LICENSE.txt']:
            if os.path.isfile(file):
                self.license_text = open(file).read()
                break
        else:
            self.license_text = ''

    @make_spin(Spin1, 'Harvesting files...')
    def _harvest_files(self):
        directories = []
        files = []

        with enter_directory(self.bdist_dir):
            for name in os.listdir():
                if os.path.isdir(name):
                    directories.append(name)
                elif name != 'wix.json':
                    files.append(name)

        return files, directories

    def _generate_shortcuts(self):
        invalid = re.compile(r'[\\?|><:/*".]')
        shortcuts = []

        for shortcut in self.shortcuts:
            name, target = [s.strip() for s in shortcut.split('=')]

            assert os.path.isfile(
                os.path.join(self.bdist_dir, '{}.exe'.format(target)))

            shortcuts.append({
                'name': invalid.sub('', name),
                'description': self.description,
                'target': '[INSTALLDIR]\\{}.exe'.format(target),
                'wdir': 'INSTALLDIR',
                'arguments': ''
            })

        return shortcuts

    def _write_license(self, fh):
        lfh = io.StringIO()
        lfh.write(self.license_text)
        lfh.seek(0)

        write_rtf(lfh, fh)

    def _write_json(self, fh):
        files, directories = self._harvest_files(
        )  # Harvesting must be done before any files are written

        config = {
            "product": self.distribution.get_name(),
            "company": self.distribution.get_author(),
            "license": os.path.abspath(self._license),
            "version": self.distribution.metadata.get_version(),
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
        msi = '{}-{}-{}.msi'.format(self.distribution.get_name(),
                                    self.distribution.metadata.get_version(),
                                    build_dir()).replace(' ', '_')

        if get_arch() == 64:
            arch = 'amd64'
        else:
            arch = '386'

        with enter_directory(self.bdist_dir):
            try:
                go_msi.make(msi=msi, arch=arch)
            except CalledProcessError:
                log.logger.exception('go-msi failed')

        shutil.move(
            os.path.join(self.bdist_dir, msi), os.path.join(
                self.dist_dir, msi))

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

        with open(self._license, 'w+') as fh:
            self._write_license(fh)

        with open(os.path.join(self.bdist_dir, 'wix.json'), 'w+') as fh:
            self._write_json(fh)

        self._build_msi()
