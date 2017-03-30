from setuptools import find_packages

from subzero import setup, Executable

setup(
    name='hello_world',
    author='Mars Galactic',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'my_project = hello_world.__main__:main',
            Executable(
                'gui = hello_world.__main__:gui',
                icon_file='Sample.ico',
                windowed=False),
        ]
    },
    options={
        'build_exe': {
            'hiddenimports': [],
            'pathex': [],
            'datas': [],
        },
        'bdist_msi': {
            'upgrade_code':
            '66620F3A-DC3A-11E2-B341-002219E9B01E',
            'shortcuts': [
                'ProgramMenuFolder\Hello World = my_project',
                # 'ProgramMenuFolder\Hello World\Hello World = my_project',
            ],
        }
    },
    install_requires=[])
