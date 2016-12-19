import os
import subprocess
import sys
import tempfile

from multiprocessing import Process


def run_setup_command(setup_command, arguments=[]):
    package_path = os.path.join(os.path.dirname(__file__), 'hello_world')
    os.chdir(package_path)

    sys.argv[1:] = [setup_command] + list(arguments)

    exec('\n'.join(open('setup.py')))


def test_hello_world():
    run_setup_command('build_exe')

    # find the build directory
    for d in os.listdir('build'):
        if d.startswith('exe.') and os.path.isdir(os.path.join('build', d)):
            build_dir = d

    if not build_dir:
        raise ValueError('Unable to locate build directory!')

    output = subprocess.check_output([os.path.join('build', build_dir, 'my_project.exe')])

    assert output == b'Script executed successfully!\r\n'


def test_bdist_msi():
    # Needed because MSIlib does not automatically close file locks
    p = Process(target=run_setup_command, args=('bdist_msi', ['--skip-build'],))
    p.start()
    p.join()

    # find the location of the msi installer
    for f in os.listdir('dist'):
        if f.endswith('.msi') and os.path.isfile(os.path.join('dist', f)):
            dist_file = os.path.join('dist', f)

    dist_file = os.path.abspath(dist_file)
    dest_dir = tempfile.mkdtemp()

    MSIEXEC_COMMAND = 'msiexec /a {MSIPath} /qb TARGETDIR={TARGETDIR}'.format(MSIPath=dist_file, TARGETDIR=dest_dir)
    print(MSIEXEC_COMMAND)

    subprocess.call(MSIEXEC_COMMAND.split(' '))

    output = subprocess.check_output([os.path.join(dest_dir, 'my_project.exe')])

    assert output == b'Script executed successfully!\r\n'
