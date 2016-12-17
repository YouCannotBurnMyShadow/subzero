# pyinstaller_utils
PyInstaller Utils allows you to build your PyInstaller executables from setup.py and create MSI installers to distribute
them. PyInstaller Utils uses code from cx_Freeze to avoid reinventing the wheel. Therefore, some files are licensed 
under the PSF license even though the project is licensed under GPL.

## How do I install it?

    pip install pyinstaller_utils

## How do I use it?

In your setup file, replace the default setup import with the followng:

```python
from pyinstaller_utils.dist import setup
```

Then run the following command:

    python setup.py build_exe

That's it! PyInstaller will build all of the entry points and scripts specified in your executable.

## How do I specify options?

In your setup function, you can specify PyInstaller options as follows:

```python
  setup(...
  options={
          'build_exe': {
              'hiddenimports': ['requests'],
              'pathex': ['/my/path', '/their/path'],
              'icon': '/path/to/icon.png',
          }
      },
  ...)
```
The full array of options is of course available in the PyInstaller documentation.


# How can I build an MSI

In your setup, put the following:

```python
setup(...
'bdist_msi': {
    'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01E}',
    'shortcuts': [
      'ProgramMenuFolder\Hello World = my_project'
    ],
}
...)
```

Then run:

    python setup.py bdist_msi
    
Note that PyInstaller Utils currently cannot create shortcuts that are not placed in a root system directory. In other 
words, you can currently have a shortcut on the desktop of in the program menu but on in a folder on the desktop or in 
a folder on the program menu.