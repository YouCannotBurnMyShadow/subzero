# pyinstaller_utils
PyInstaller Utils allows you to build your PyInstaller executables from setup.py (and coming soon: create nice MSI installers to distribute them). 

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
          'PyInstaller': {
              'hiddenimports': ['requests'],
              'pathex': ['/my/path', '/their/path'],
              'icon': '/path/to/icon.png',
          }
      },
  ...)
```
The full array of options is of course available in the PyInstaller documentation.
