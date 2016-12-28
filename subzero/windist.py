# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

import distutils.command.bdist_msi
import distutils.errors
import distutils.util
import ntpath
import os
import re
import shutil
import string
import uuid
from io import StringIO

import PyRTF
import lxml.etree as le
import pywix
from pkg_resources import resource_filename, resource_string

from subzero.dist import build_exe

__all__ = ["bdist_msi"]


class bdist_msi(distutils.command.bdist_msi.bdist_msi):
    _shortcut_components = []

    user_options = distutils.command.bdist_msi.bdist_msi.user_options + [
        ('add-to-path=', None, 'add target dir to PATH environment variable'),
        ('upgrade-code=', None, 'upgrade code to use'),
        ('initial-target-dir=', None, 'initial target directory'),
        ('target-name=', None, 'name of the file to create'),
        ('directories=', None, 'list of 3-tuples of directories to create'),
        ('data=', None, 'dictionary of data indexed by table name'),
        ('product-code=', None, 'product code to use')
    ]

    def _split_path(self, path):
        folders = []
        while 1:
            path, folder = os.path.split(path)

            if folder != "":
                folders.append(folder)
            else:
                if path != "":
                    folders.append(path)

                break

        folders.reverse()

        return folders

    def _license_text(self, license_file):
        """
        Generates rich text given a license file-like object
        :param license_file: file-like object
        :return:
        """
        wordpad_header = r'''{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033{\fonttbl{\f0\fnil\fcharset255 Times New Roman;}
{\*\generator Riched20 10.0.14393}\viewkind4\uc1'''.replace('\n', '\r\n')
        center_space = '            '

        pattern = re.compile(r'{}\s*'.format(center_space))

        r = PyRTF.Renderer()

        doc = PyRTF.Document()
        ss = doc.StyleSheet
        sec = PyRTF.Section()
        doc.Sections.append(sec)

        is_blank = False
        paragraph_text = ['']
        for line in license_file:
            if not line or line.isspace():
                is_blank = True
            if is_blank:
                # first element of paragraph_text is left-aligned, subsequent elements are centered
                is_centered = False
                for sec_line in paragraph_text:
                    if is_centered:
                        para_props = PyRTF.ParagraphPS(alignment=PyRTF.ParagraphPS.CENTER)
                        p = PyRTF.Paragraph(ss.ParagraphStyles.Normal, para_props)
                        p.append(sec_line)
                        sec.append(p)
                    elif sec_line:  # first element may be nothing, but not whitespace
                        sec.append(sec_line)
                    is_centered = True
                is_blank = False
                paragraph_text = ['']
            if line.startswith(center_space):
                paragraph_text.append(line.strip())
                is_blank = True
            else:
                paragraph_text[0] += ' ' + line
                paragraph_text[0] = paragraph_text[0].strip()

        f = StringIO()
        f.write(wordpad_header)
        r.Write(doc, f)

        return f.getvalue()

    def finalize_options(self):
        initial_set = (self.distribution.author and self.distribution.name) and not self.initial_target_dir

        distutils.command.bdist_msi.bdist_msi.finalize_options(self)
        name = self.distribution.get_name()
        fullname = self.distribution.get_fullname()
        author = self.distribution.get_author()
        if self.initial_target_dir is None:
            if distutils.util.get_platform() == "win-amd64":
                programFilesFolder = "ProgramFiles64Folder"
            else:
                programFilesFolder = "ProgramFilesFolder"
            self.initial_target_dir = r"[{}]\{}\{}".format(programFilesFolder, author, name)
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

        self.bdist_dir = os.path.join(self.bdist_dir, build_exe.build_dir())
        self.build_temp = os.path.join(ntpath.dirname(self.bdist_dir), 'temp' + ntpath.basename(self.bdist_dir)[3:])
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

    def _generate_id(self):
        return 'cmp{}'.format(str(uuid.uuid1()).replace('-', '').upper())

    def _generate_element(self, directory, subdirs={}, root=False):
        if root:
            attr = {
                'Id': directory,
            }
        else:
            attr = {
                'Name': directory,
                'Id': self._generate_id(),
            }
        element = le.Element('Directory', attr)

        for name, subdir in subdirs.items():
            if type(subdir) is dict:
                element.append(self._generate_element(name, subdir))
            else:
                component_id = self._generate_id()
                self._shortcut_components.append(component_id)
                component = le.Element('Component', {
                    'Id': component_id,
                    'Guid': '*',
                })
                component.append(le.Element('Shortcut', {
                    'Id': self._generate_id(),
                    'Name': name,
                    'Target': '[INSTALLDIR]{}.exe'.format(subdir),
                    'WorkingDirectory': 'INSTALLDIR',
                }))
                component.append(le.Element('RegistryValue', {
                    'Root': 'HKCU',
                    'Key': 'Software\Microsoft\{{{}}}'.format(str(uuid.uuid1())),
                    'Name': 'installed',
                    'Type': 'integer',
                    'Value': str(1),
                    'KeyPath': 'yes',
                }))
                element.append(component)

        return element

    def _generate_shortcuts(self):
        # The first order of business to to generate a unified directory tree
        tree = {}
        for shortcut in self.shortcuts:
            shortcut = shortcut.split('=')
            shortcut_target = shortcut[1].strip()
            shortcut_dirs = self._split_path(os.path.dirname(shortcut[0].strip()))
            shortcut_name = os.path.basename(shortcut[0].strip())  # not efficient, but more readable

            subtree = tree
            for shortcut_dir in shortcut_dirs:
                subtree.setdefault(shortcut_dir, {})
                subtree = subtree[shortcut_dir]

            subtree[shortcut_name] = shortcut_target

        # <Wix xmlns="http://schemas.microsoft.com/wix/2006/wi"><Fragment><DirectoryRef Id="INSTALLDIR">
        Wix = le.Element('Wix', {
            'xmlns': 'http://schemas.microsoft.com/wix/2006/wi',
        })
        Fragment = le.Element('Fragment')
        DirectoryRef = le.Element('DirectoryRef', {
            'Id': 'TARGETDIR',
        })

        Wix.append(Fragment)
        Fragment.append(DirectoryRef)

        for name, subdirs in tree.items():
            DirectoryRef.append(self._generate_element(name, subdirs, True))

        Fragment = le.Element('Fragment')
        ComponentGroup = le.Element('ComponentGroup', {
            'Id': 'ApplicationShortcuts',
        })
        for shortcut_component in self._shortcut_components:
            ComponentGroup.append(le.Element('ComponentRef', {
                'Id': shortcut_component,
            }))

        Wix.append(Fragment)
        Fragment.append(ComponentGroup)

        with open('Shortcuts.wxs', 'wb+') as f:
            f.write(le.tostring(Wix, pretty_print=True))

    def _repair_harvest(self):
        doc = le.parse('Directory.wxs')
        elems = doc.xpath('//*[@Name="{}"]'.format(os.path.basename(self.bdist_dir)))
        assert len(elems) == 1
        elem = elems[0]
        parent = elem.getparent()
        parent.remove(elem)
        for child in elem:
            parent.append(child)

        with open('Directory.wxs', 'wb+') as f:
            f.write(le.tostring(doc, pretty_print=True))

    def _generate_globals(self):
        metadata = self.distribution.metadata
        author = metadata.author or metadata.maintainer or "UNKNOWN"
        version = metadata.get_version()
        fullname = self.distribution.get_name()

        variables = {
            'ProductVersion': version,
            'ProductUpgradeCode': self.upgrade_code,
            'ProductName': string.capwords(' '.join(fullname.replace('-', '_').split('_'))),
            'Author': author,
        }

        # horrible way to do this, but etree doesn't support question marks
        xml = ['<?xml version="1.0" encoding="utf-8"?>', '<Include>']

        for name, variable in variables.items():
            xml.append('<?define {} = "{}" ?>'.format(name, variable))

        xml.append('</Include>')

        with open('Globals.wxs', 'w+') as f:
            f.write('\n'.join(xml))

    def _compile(self, names, out):
        with open('License.rtf', 'w+') as license_file:
            license_file.write(self.license_text)

        candle_arguments = ['candle', '-arch', 'x64']
        light_arguments = ['light', '-ext', 'WixUIExtension', '-cultures:en-us', '-dWixUILicenseRtf=License.rtf']

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
            shutil.copy(resource_filename('subzero.resources', '{}.wxs'.format(file)), self.build_temp)

        shutil.copy(resource_filename('subzero.resources', 'HeatTransform.xslt'), self.build_temp)
        with open(os.path.join(self.build_temp, 'remove_burn.js'), 'w+') as f:
            f.write(resource_string('subzero.resources', 'remove_burn.js').decode()
                    .replace('upgrade_code', self.upgrade_code).replace('\n', '\r\n'))

        files.extend([
            'Directory',
            'Shortcuts',
        ])

        os.chdir(build_temp)
        os.environ['bdist_dir'] = bdist_dir
        print(pywix.call_wix_command(['heat', 'dir', bdist_dir, '-cg', 'ApplicationFiles',
                                      '-gg', '-sfrag', '-sreg', '-dr', 'INSTALLDIR', '-var', 'env.bdist_dir',
                                      '-t', 'HeatTransform.xslt', '-out', 'Directory.wxs']))

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
