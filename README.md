# subzero
[![build status][2]][3]
[![Codecov][5]][4]
## What is Subzero?

Subzero allows you to rapidly deploy your [frozen][1] Python application with minimal effort and additional
code. Subzero does this by providing a simple and intuitive wrapper for PyInstaller coupled with an MSI
builder. With a few lines of code and a single command, you can go directly from Python code to a compiled MSI
installer.

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

## Extended import discovery (In beta)

In case PyInstaller cannot discover all of your dependencies, you can set `optimize_imports=False`, as shown below.
This option may discover certain imports previously not found but it may also make your application larger.

```python
    'build_exe': {
        'optimize_imports': False
    },
```

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
