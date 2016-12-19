import os
import subprocess


def test_hello_world():
    package_path = os.path.join(os.path.dirname(__file__), 'hello_world')
    os.chdir(package_path)

    return_code = subprocess.call(['python', 'setup.py', 'build_exe'])

    assert return_code == 0

    # TODO: Add test coverage for MSI build
