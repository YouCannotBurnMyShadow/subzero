import os
import subprocess
import sys
import tempfile
import pytest
import glob

from subzero.utils import enter_directory, build_dir


def _run_command(setup_command, arguments=[]):
    sys.argv[1:] = [setup_command] + list(arguments)
    exec('\n'.join(open('setup.py')))


def _extract_msi():
    installer = os.path.abspath([
        filename for filename in glob.iglob('dist/*.msi')
        if os.path.isfile(filename)
    ][0])

    tmpdir = tempfile.mkdtemp()

    cmd = 'msiexec /a {MSIPath} /qb TARGETDIR={TARGETDIR}'.format(
        MSIPath=installer, TARGETDIR=tmpdir)
    subprocess.call(cmd.split(' '))

    return tmpdir


# TODO: generate different tests
def test_all():
    this_directory = os.path.dirname(__file__)
    functional_directory = os.path.join(this_directory, 'functional')
    for project in os.listdir(functional_directory):
        with enter_directory(os.path.join(functional_directory, project)):
            assert 'setup.py' in os.listdir()
            _run_command('bdist_msi')
            tmpdir = _extract_msi()
            for executable in glob.iglob(
                    os.path.join(tmpdir, '**/*.exe'), recursive=True):
                assert subprocess.check_output(
                    [executable]) == b'Script executed successfully!\r\n'
