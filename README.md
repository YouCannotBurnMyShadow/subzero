# subzero
[![build status][2]][3]
[![Codecov][5]][4]
## What is Subzero?

Subzero allows you to rapidly deploy your [frozen][1] Python application with minimal effort and additional
code. Subzero does this by providing a simple and intuitive wrapper for PyInstaller coupled with an MSI
builder. With a few lines of code and a single command, you can go directly from Python code to a compiled MSI
installer. In addition, Subzero does not require any non-Python dependencies beyond those required by
PyInstaller, making it trivial to install.

[1]: http://docs.python-guide.org/en/latest/shipping/freezing/
[2]: https://ci.appveyor.com/api/projects/status/github/xoviat/subzero?branch=master&svg=true
[3]: https://ci.appveyor.com/project/xoviat/pyinstaller-utils
[4]: https://codecov.io/gh/xoviat/subzero
[5]: https://img.shields.io/codecov/c/github/xoviat/subzero.svg?style=flat

## How do I install it?

    pip install subzero

## How do I use it?

In your setup file, replace the default setup import with the followng:

```python
from subzero import setup, Executable
```

Then run the following command:

    python setup.py bdist_msi

That's it! PyInstaller will build all of the entry points and scripts specified in your executable.

## How do I specify options?

In your setup function, you can specify PyInstaller options as follows:

```python
  setup(...
  options={
'         build_exe': {
              'hiddenimports': [],
              'pathex': [],
              'datas': [],
          },
          'bdist_msi': {
              'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01E}',
              'shortcuts': [
                  'ProgramMenuFolder\Hello World = my_project'
              ],
          }
  ...)
```
In addition, options can be specified on a per-executable basis replacing each script or entry point with an instance
of the Executable class and initializing it with the required options, as shown below:

```python
setup(...
      entry_points={
          'console_scripts': [
              'my_project = hello_world.__main__:main',
              Executable('gui = hello_world.__main__:gui', icon_file='Sample.ico', windowed=False),
          ]
      },
...)
```

The full array of options for build_exe is available in the PyInstaller documentation. Providing an upgrade code is
**strongly recommended** for the bdist_msi command. A license agreement will be added to the installer if there is 
a license text file in the same directory as setup.py.

Note that Subzero currently cannot create shortcuts that are not placed in a root system directory. In other 
words, you can currently have a shortcut on the desktop of in the program menu but not in a folder on the desktop or in 
a folder on the program menu. This may be resolved in the future if there is greater interest.

## Cython (currently not in tests)

Cython modules can also be built because Subzero executes the builtin `build` command before calling 
PyInstaller. The following is an example setup.py file for a Cython project:

```python
from setuptools import find_packages, Extension
from subzero import setup

setup(
    name='hello_world',
    author='test_author',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
      'console_scripts': [
          'my_project = hello_world.__main__:main',
      ]
    },
    options={},
    install_requires=[],
    setup_requires=[
        'setuptools>=18.0',
        'cython',
    ],
    ext_modules=[
        Extension(
            'my_module',
            sources=['my_module.pyx'],
        )
    ])
```
