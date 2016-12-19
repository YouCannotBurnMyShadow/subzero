import os
import subprocess
import sys


def test_hello_world():
    package_path = os.path.join(os.path.dirname(__file__), 'hello_world')
    os.chdir(package_path)

    sys.argv[1:] = ['build_exe']

    exec('\n'.join(open('setup.py')))

    # find the build directory
    for d in os.listdir('build'):
        if d.startswith('exe.'):
            build_dir = d

    if not build_dir:
        raise ValueError('Unable to locate build directory!')

    output = subprocess.check_output([os.path.join('build', build_dir, 'my_project.exe')])

    assert output == b'Script executed successfully!\r\n'
