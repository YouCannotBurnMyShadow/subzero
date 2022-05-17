# subzero

[![Codacy Badge][6]][7]
[![build status][2]][3]
[![Codecov][5]][4]

## What is Subzero?

The goal of subzero is to allow simple and rapid deployment of [frozen][1] Python applications with minimal
additional effort and developer time. In contrast to other solutions, subzero's philosophy is that having a 
working application, quickly is more important than optimizing for size or other factors and that generating
your end product (be it an MSI, or other installer) should take only a few minutes to set up. Subzero builds
on the extensive development work of other projects, and doesn't re-invent the wheel. Rather, it ties everything
together in a simple and intuitive manner.

## How do I use it?

In your setup file, replace the default setup import with the followng:

```python
from subzero import setup, Executable
```

Then run the following command:

    python setup.py bdist_msi

Subzero will the build executables specified in the `entry_points` and `scripts` sections and 
then create an installer that contains those executables.

## Example

```python
setup(
    name='Name',
    author='Author',
    packages=find_packages(),
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    install_requires=[
        'paramiko',
    ],
    entry_points={
        'gui_scripts': [
            Executable(
                    'gui = app.__main__:gui',
                    icon_file='Icon.ico'),
        ],
        'console_scripts': [
            'console = app.__main__:console',
        ],
    },
    options={
        'build_exe': {
            'pathex':
            [os.path.join(os.path.dirname(PyQt5.__file__), 'Qt', 'bin')],
            'datas':
            [datafile, '.')],
        },
        'bdist_msi': {
            'upgrade_code': '84b31ed7-3985-46ad-9d07-eb4140a6d44a',
            'shortcuts': ['My Program = gui'],
            'wix_template_dir': os.path.abspath('./wix_templates'),
        }
    })
```

Options are applied first globally from the options dictionary passed to `setup`, and then for each executable
if the `Executable` class is present for that particular `entry_point` or `script`.

The full array of options for build_exe is available in the PyInstaller documentation. Providing an upgrade code is
**strongly recommended** for the bdist_msi command. A license agreement will be added to the installer if there is 
a license text file in the same directory as setup.py.

## Extended import discovery (In beta)

In case PyInstaller cannot discover all of your dependencies, you can set `optimize_imports=False`, as shown below.
This option may discover certain imports previously not found but it may also make your application larger. Note that
you must add your package requirements in `install_requires` for this option to work!

```python
    'build_exe': {
        'optimize_imports': False
    },
```

## Cython

Cython modules can also be built because Subzero executes the builtin `build` command before calling 
PyInstaller. Just add your modules to the `ext_modules` key:

```python
from setuptools import find_packages, Extension
from subzero import setup

setup(
    name='hello_world',
    ext_modules=[
        Extension(
            'my_module',
            sources=['my_module.pyx'],
        )
    ])
```


[1]: http://docs.python-guide.org/en/latest/shipping/freezing/
[2]: https://ci.appveyor.com/api/projects/status/github/xoviat/subzero?branch=master&svg=true
[3]: https://ci.appveyor.com/project/xoviat/pyinstaller-utils
[4]: https://codecov.io/gh/xoviat/subzero
[5]: https://img.shields.io/codecov/c/github/xoviat/subzero.svg?style=flat
[6]: https://api.codacy.com/project/badge/Grade/1568bcb5178b4e4d80dae7840df03f08
[7]: https://www.codacy.com/app/pywin32/subzero?utm_source=github.com&utm_medium=referral&utm_content=xoviat/subzero&utm_campaign=badger
