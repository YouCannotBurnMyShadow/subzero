# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

import distutils.command.bdist_msi
import distutils.errors
import distutils.util
import msilib
import ntpath
import os
import re
from io import StringIO

import PyRTF

from subzero.dist import build_exe

__all__ = ["bdist_msi"]


def license_text(license_file):
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


# force the remove existing products action to happen first since Windows
# installer appears to be braindead and doesn't handle files shared between
# different "products" very well
sequence = msilib.sequence.InstallExecuteSequence
for index, info in enumerate(sequence):
    if info[0] == 'RemoveExistingProducts':
        sequence[index] = (info[0], info[1], 1450)


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
    x = y = 50
    width = 370
    height = 300
    title = "[ProductName] Setup"
    modeless = 1
    modal = 3

    def add_config(self, fullname):
        if self.add_to_path:
            msilib.add_data(self.db, 'Environment',
                            [("E_PATH", "=-*Path", r"[~];[TARGETDIR]", "TARGETDIR")])
        if self.directories:
            msilib.add_data(self.db, "Directory", self.directories)
        msilib.add_data(self.db, 'CustomAction',
                        [("A_SET_TARGET_DIR", 256 + 51, "TARGETDIR",
                          self.initial_target_dir)])
        msilib.add_data(self.db, 'InstallExecuteSequence',
                        [("A_SET_TARGET_DIR", 'TARGETDIR=""', 401)])
        msilib.add_data(self.db, 'InstallUISequence',
                        [("PrepareDlg", None, 140),
                         ("A_SET_TARGET_DIR", 'TARGETDIR=""', 401),
                         ('LicenseDlg', 'not Installed', 1230),
                         ('MaintenanceTypeDlg',
                          'Installed and not Resume and not Preselected', 1250),
                         ('ProgressDlg', None, 1280)
                         ])

        # TODO: Add ability to pass arguments to executable
        # TODO: Validate shortcut values against known MSI table
        # TODO: Add ability to specify nested shortcuts
        for index, shortcut in enumerate(self.shortcuts):
            shortcut = shortcut.split('=')
            baseName = '{}.exe'.format(shortcut[1].strip())
            shortcutPath = shortcut[0].strip()
            shortcutName = ntpath.basename(shortcutPath)
            shortcutDir = ntpath.dirname(shortcutPath)

            msilib.add_data(self.db, 'Shortcut',
                            [('S_APP_{}'.format(index), shortcutDir,
                              shortcutName, 'TARGETDIR',
                              '[TARGETDIR]{}'.format(baseName), None, None, None,
                              None, None, None, 'TARGETDIR')])

        for tableName, data in self.data.items():
            msilib.add_data(self.db, tableName, data)

    def add_cancel_dialog(self):
        dialog = msilib.Dialog(self.db, 'CancelDlg', 50, 50, 260, 85, 3,
                               self.title, 'No', 'No', 'No')
        dialog.text('Text', 48, 15, 194, 30, 3,
                    'Are you sure you want to cancel [ProductName] installation?')
        button = dialog.pushbutton('Yes', 72, 57, 56, 17, 3, 'Yes', 'No')
        button.event('EndDialog', 'Exit')
        button = dialog.pushbutton('No', 132, 57, 56, 17, 3, 'No', 'Yes')
        button.event('EndDialog', 'Return')

    def add_error_dialog(self):
        dialog = msilib.Dialog(self.db, 'ErrorDlg', 50, 10, 330, 101, 65543,
                               self.title, 'ErrorText', None, None)
        dialog.text('ErrorText', 50, 9, 280, 48, 3, '')
        for text, x in [('No', 120), ('Yes', 240), ('Abort', 0),
                        ('Cancel', 42), ('Ignore', 81), ('Ok', 159), ('Retry', 198)]:
            button = dialog.pushbutton(text[0], x, 72, 81, 21, 3, text, None)
            button.event('EndDialog', 'Error%s' % text)

    def add_exit_dialog(self):
        dialog = distutils.command.bdist_msi.PyDialog(self.db, 'ExitDialog',
                                                      self.x, self.y, self.width, self.height, self.modal,
                                                      self.title, 'Finish', 'Finish', 'Finish')
        dialog.title('Completing the [ProductName] installer')
        dialog.back('Back', 'Finish', active=False)
        dialog.cancel('Cancel', 'Back', active=False)
        dialog.text('Description', 15, 207, 320, 20, 0x30003,
                    'Click the Finish button to exit the installer.')
        button = dialog.next('Finish', 'Cancel', name='Finish')
        button.event('EndDialog', 'Return')

    def add_fatal_error_dialog(self):
        dialog = distutils.command.bdist_msi.PyDialog(self.db, 'FatalError',
                                                      self.x, self.y, self.width, self.height, self.modal,
                                                      self.title, 'Finish', 'Finish', 'Finish')
        dialog.title('[ProductName] installer ended prematurely')
        dialog.back('Back', 'Finish', active=False)
        dialog.cancel('Cancel', 'Back', active=False)
        dialog.text('Description1', 15, 70, 320, 80, 0x30003,
                    '[ProductName] setup ended prematurely because of an error. '
                    'Your system has not been modified. To install this program '
                    'at a later time, please run the installation again.')
        dialog.text('Description2', 15, 155, 320, 20, 0x30003,
                    'Click the Finish button to exit the installer.')
        button = dialog.next('Finish', 'Cancel', name='Finish')
        button.event('EndDialog', 'Exit')

    def add_files(self):
        db = self.db
        cab = msilib.CAB('distfiles')
        f = msilib.Feature(db, 'default', 'Default Feature', 'Everything', 1, directory='TARGETDIR')
        f.set_current()
        rootdir = os.path.abspath(self.bdist_dir)
        root = msilib.Directory(db, cab, None, rootdir, 'TARGETDIR', 'SourceDir')
        db.Commit()
        todo = [root]
        while todo:
            dir = todo.pop()
            for file in os.listdir(dir.absolute):
                if os.path.isdir(os.path.join(dir.absolute, file)):
                    newDir = msilib.Directory(db, cab, dir, file, file,
                                              "%s|%s" % (dir.make_short(file), file))
                    todo.append(newDir)
                else:
                    dir.add_file(file)
        cab.commit(db)

    def add_files_in_use_dialog(self):
        dialog = distutils.command.bdist_msi.PyDialog(self.db, 'FilesInUse',
                                                      self.x, self.y, self.width, self.height, 19, self.title,
                                                      'Retry', 'Retry', 'Retry', bitmap=False)
        dialog.text('Title', 15, 6, 200, 15, 0x30003,
                    r'{\DlgFontBold8}Files in Use')
        dialog.text('Description', 20, 23, 280, 20, 0x30003,
                    'Some files that need to be updated are currently in use.')
        dialog.text('Text', 20, 55, 330, 50, 3,
                    'The following applications are using files that need to be '
                    'updated by this setup. Close these applications and then '
                    'click Retry to continue the installation or Cancel to exit '
                    'it.')
        dialog.control('List', 'ListBox', 20, 107, 330, 130, 7,
                       'FileInUseProcess', None, None, None)
        button = dialog.back('Exit', 'Ignore', name='Exit')
        button.event('EndDialog', 'Exit')
        button = dialog.next('Ignore', 'Retry', name='Ignore')
        button.event('EndDialog', 'Ignore')
        button = dialog.cancel('Retry', 'Exit', name='Retry')
        button.event('EndDialog', 'Retry')

    def add_maintenance_type_dialog(self):
        dialog = distutils.command.bdist_msi.PyDialog(self.db,
                                                      "MaintenanceTypeDlg", self.x, self.y, self.width, self.height,
                                                      self.modal, self.title, "Next", "Next", "Cancel")
        dialog.title("Welcome to the [ProductName] Setup Wizard")
        dialog.text("BodyText", 15, 63, 330, 42, 3,
                    "Select whether you want to repair or remove [ProductName].")
        group = dialog.radiogroup("RepairRadioGroup", 15, 108, 330, 60, 3,
                                  "MaintenanceForm_Action", "", "Next")
        group.add("Repair", 0, 18, 300, 17, "&Repair [ProductName]")
        group.add("Remove", 0, 36, 300, 17, "Re&move [ProductName]")
        dialog.back("Back", None, active=False)
        button = dialog.next("Finish", "Cancel")
        button.event("[REINSTALL]", "ALL",
                     'MaintenanceForm_Action="Repair"', 5)
        button.event("[Progress1]", "Repairing",
                     'MaintenanceForm_Action="Repair"', 6)
        button.event("[Progress2]", "repairs",
                     'MaintenanceForm_Action="Repair"', 7)
        button.event("Reinstall", "ALL",
                     'MaintenanceForm_Action="Repair"', 8)
        button.event("[REMOVE]", "ALL",
                     'MaintenanceForm_Action="Remove"', 11)
        button.event("[Progress1]", "Removing",
                     'MaintenanceForm_Action="Remove"', 12)
        button.event("[Progress2]", "removes",
                     'MaintenanceForm_Action="Remove"', 13)
        button.event("Remove", "ALL",
                     'MaintenanceForm_Action="Remove"', 14)
        button.event("EndDialog", "Return",
                     'MaintenanceForm_Action<>"Change"', 20)
        button = dialog.cancel("Cancel", "RepairRadioGroup")
        button.event("SpawnDialog", "CancelDlg")

    def add_prepare_dialog(self):
        dialog = distutils.command.bdist_msi.PyDialog(self.db, "PrepareDlg",
                                                      self.x, self.y, self.width, self.height, self.modeless,
                                                      self.title, "Cancel", "Cancel", "Cancel")
        dialog.text("Description", 15, 70, 320, 40, 0x30003,
                    "Please wait while the installer prepares to guide you through "
                    "the installation.")
        dialog.title("Welcome to the [ProductName] installer")
        text = dialog.text("ActionText", 15, 110, 320, 20, 0x30003,
                           "Pondering...")
        text.mapping("ActionText", "Text")
        text = dialog.text("ActionData", 15, 135, 320, 30, 0x30003, None)
        text.mapping("ActionData", "Text")
        dialog.back("Back", None, active=False)
        dialog.next("Next", None, active=False)
        button = dialog.cancel("Cancel", None)
        button.event("SpawnDialog", "CancelDlg")

    def add_progress_dialog(self):
        dialog = distutils.command.bdist_msi.PyDialog(self.db, "ProgressDlg",
                                                      self.x, self.y, self.width, self.height, self.modeless,
                                                      self.title, "Cancel", "Cancel", "Cancel", bitmap=False)
        dialog.text("Title", 20, 15, 200, 15, 0x30003,
                    r"{\DlgFontBold8}[Progress1] [ProductName]")
        dialog.text("Text", 35, 65, 300, 30, 3,
                    "Please wait while the installer [Progress2] [ProductName].")
        dialog.text("StatusLabel", 35, 100, 35, 20, 3, "Status:")
        text = dialog.text("ActionText", 70, 100, self.width - 70, 20, 3,
                           "Pondering...")
        text.mapping("ActionText", "Text")
        control = dialog.control("ProgressBar", "ProgressBar", 35, 120, 300,
                                 10, 65537, None, "Progress done", None, None)
        control.mapping("SetProgress", "Progress")
        dialog.back("Back", "Next", active=False)
        dialog.next("Next", "Cancel", active=False)
        button = dialog.cancel("Cancel", "Back")
        button.event("SpawnDialog", "CancelDlg")

    def add_properties(self):
        metadata = self.distribution.metadata
        props = [
            ('DistVersion', metadata.get_version()),
            ('DefaultUIFont', 'DlgFont8'),
            ('ErrorDialog', 'ErrorDlg'),
            ('Progress1', 'Install'),
            ('Progress2', 'installs'),
            ('MaintenanceForm_Action', 'Repair'),
            ('ALLUSERS', '1'),
        ]
        email = metadata.author_email or metadata.maintainer_email
        if email:
            props.append(("ARPCONTACT", email))
        if metadata.url:
            props.append(("ARPURLINFOABOUT", metadata.url))
        if self.upgrade_code is not None:
            props.append(("UpgradeCode", self.upgrade_code))
        msilib.add_data(self.db, 'Property', props)

    def add_license_dialog(self):
        if self.license_text:
            dialog = distutils.command.bdist_msi.PyDialog(self.db, 'LicenseDlg',
                                                          self.x, self.y, self.width, self.height, self.modal,
                                                          self.title, 'Next', 'Next', 'Cancel', bitmap=False)
            dialog.title('License Agreement')
            dialog.control('ScrollableText', 'ScrollableText', 20, 60, 330, 140, 7, None,
                           self.license_text, None, None)
            dialog.checkbox('AcceptLicense', 20, 207, 330, 18, 3, 'LicenseAccepted',
                            'I accept the terms in the License Agreement', None)
            dialog.back('Back', 'Next', active=False)

            button = dialog.next('Next', 'Cancel', active=False)
            # button.event('SetTargetPath', 'TARGETDIR', ordering=1)
            button.event('SpawnWaitDialog', 'WaitForCostingDlg', ordering=1)
            button.event('EndDialog', 'Return', ordering=2)
            button.condition('Enable', 'LicenseAccepted')
            button.condition('Disable', 'Not LicenseAccepted')

            button = dialog.cancel('Cancel', 'Back')
            button.event('SpawnDialog', 'CancelDlg')

    def add_text_styles(self):
        msilib.add_data(self.db, 'TextStyle',
                        [("DlgFont8", "Tahoma", 9, None, 0),
                         ("DlgFontBold8", "Tahoma", 8, None, 1),
                         ("VerdanaBold10", "Verdana", 10, None, 1),
                         ("VerdanaRed9", "Verdana", 9, 255, 0)
                         ])

    def add_ui(self):
        self.add_text_styles()
        self.add_error_dialog()
        self.add_fatal_error_dialog()
        self.add_cancel_dialog()
        self.add_exit_dialog()
        self.add_user_exit_dialog()
        self.add_files_in_use_dialog()
        self.add_wait_for_costing_dialog()
        self.add_prepare_dialog()
        self.add_license_dialog()
        self.add_progress_dialog()
        self.add_maintenance_type_dialog()

    def add_upgrade_config(self, sversion):
        if self.upgrade_code is not None:
            msilib.add_data(self.db, 'Upgrade',
                            [(self.upgrade_code, None, sversion, None, 513, None,
                              "REMOVEOLDVERSION"),
                             (self.upgrade_code, sversion, None, None, 257, None,
                              "REMOVENEWVERSION")
                             ])

    def add_user_exit_dialog(self):
        dialog = distutils.command.bdist_msi.PyDialog(self.db, 'UserExit',
                                                      self.x, self.y, self.width, self.height, self.modal,
                                                      self.title, 'Finish', 'Finish', 'Finish')
        dialog.title('[ProductName] installer was interrupted')
        dialog.back('Back', 'Finish', active=False)
        dialog.cancel('Cancel', 'Back', active=False)
        dialog.text('Description1', 15, 70, 320, 80, 0x30003,
                    '[ProductName] setup was interrupted. Your system has not '
                    'been modified. To install this program at a later time, '
                    'please run the installation again.')
        dialog.text('Description2', 15, 207, 320, 20, 0x30003,
                    'Click the Finish button to exit the installer.')
        button = dialog.next('Finish', 'Cancel', name='Finish')
        button.event('EndDialog', 'Exit')

    def add_wait_for_costing_dialog(self):
        dialog = msilib.Dialog(self.db, "WaitForCostingDlg", 50, 10, 260, 85,
                               self.modal, self.title, "Return", "Return", "Return")
        dialog.text("Text", 48, 15, 194, 30, 3,
                    "Please wait while the installer finishes determining your "
                    "disk space requirements.")
        button = dialog.pushbutton("Return", 102, 57, 56, 17, 3, "Return",
                                   None)
        button.event("EndDialog", "Exit")

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
                self.license_text = license_text(open(file))
                break

    def run(self):
        # self.skip_build = True
        if not self.skip_build:
            self.run_command('build_exe')
        '''
        install = self.reinitialize_command('install', reinit_subcommands=1)
        install.prefix = self.bdist_dir
        install.skip_build = self.skip_build
        install.warn_dir = 0
        distutils.log.info("installing to %s", self.bdist_dir)
        install.ensure_finalized()
        install.run()
        '''
        self.mkpath(self.dist_dir)
        fullname = self.distribution.get_fullname()
        if os.path.exists(self.target_name):
            os.unlink(self.target_name)
        metadata = self.distribution.metadata
        author = metadata.author or metadata.maintainer or "UNKNOWN"
        version = metadata.get_version()
        sversion = "%d.%d.%d" % \
                   distutils.version.StrictVersion(version).version
        if self.product_code is None:
            self.product_code = msilib.gen_uuid()
        self.db = msilib.init_database(self.target_name, msilib.schema,
                                       self.distribution.metadata.name, self.product_code, sversion,
                                       author)
        msilib.add_tables(self.db, msilib.sequence)
        self.add_properties()
        self.add_config(fullname)
        self.add_upgrade_config(sversion)
        self.add_ui()
        self.add_files()
        self.db.Commit()
        self.distribution.dist_files.append(('bdist_msi', sversion or 'any', self.target_name))

        '''
        if not self.keep_temp:
            distutils.dir_util.remove_tree(self.bdist_dir,
                                           dry_run=self.dry_run)
        '''
