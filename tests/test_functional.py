import os
import subprocess
import sys
import tempfile
import pytest

from subzero.utils import enter_directory, build_dir, iglob

this_directory = os.path.dirname(__file__)
functional_directory = os.path.join(this_directory, 'functional')


def _run_command(setup_command, arguments=[]):
    sys.argv[1:] = [setup_command] + list(arguments)
    exec('\n'.join(open('setup.py')))


def _extract_msi():
    installer = os.path.abspath([
        filename for filename in iglob('dist/*.msi')
        if os.path.isfile(filename)
    ][0])

    tmpdir = tempfile.mkdtemp()

    cmd = 'msiexec /a {MSIPath} /qb TARGETDIR={TARGETDIR}'.format(
        MSIPath=installer, TARGETDIR=tmpdir)
    subprocess.call(cmd.split(' '))

    return tmpdir


@pytest.fixture(params=os.listdir(functional_directory))
def get_executables(request):
    with enter_directory(os.path.join(functional_directory, request.param)):
        assert 'setup.py' in os.listdir()
        _run_command('bdist_msi')
        tmpdir = _extract_msi()
        executables = []
        for executable in iglob(
                os.path.join(tmpdir, '**/*.exe'), recursive=True):
            executables.append(os.path.abspath(executable))

        yield executables


def test_executables(get_executables):
    for executable in get_executables:
        with enter_directory(os.path.dirname(executable)):
            assert subprocess.check_output(
                [os.path.basename(executable)],
                stderr=sys.stderr).strip() == b'execution okay'
