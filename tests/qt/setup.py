from setuptools import find_packages

from subzero import setup

setup(
    name='qt',
    author='Mars Galactic',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'my_project = hello_world.__main__:main',
        ]
    },
    options={
        'build_exe': {
            'hiddenimports': [],
            'pathex': [],
            'datas': [],
            'optimize_imports': False,
        },
    },
    install_requires=[])
