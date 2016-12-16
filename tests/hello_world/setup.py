from setuptools import find_packages

from pyinstaller_utils.dist import setup

setup(name='hello_world',
      version='0.1.0',
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'my_project = hello_world.__main__:main',
              'gui = hello_world.__main__:gui',
          ]
      },
      options={
          'build_exe': {
              'hiddenimports': [],
          }
      },
      install_requires=[])
