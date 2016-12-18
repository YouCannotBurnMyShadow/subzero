# pyinstaller_utils
## What is Pyinstaller Utils?

PyInstaller Utils allows you to rapidly deploy your [frozen](http://docs.python-guide.org/en/latest/shipping/freezing/)
Python application with minimal effort and additional code. PyInstaller utils does this by providing a simple and
intuitive wrapper for PyInstaller coupled with an MSI builder. With a few lines of code and a single command, you can
go directly from Python code to a compiled MSI installer. In addition, PyInstaller Utils does not require any 
non-Python dependencies beyond those required by PyInstaller, making it trivial to install.

## How do I install it?

    pip install pyinstaller_utils

## How do I use it?

In your setup file, replace the default setup import with the followng:

```python
from pyinstaller_utils.dist import setup
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
              'icon_file': None,
          },
          'bdist_msi': {
              'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01E}',
              # 'initial_target_dir': r'[ProgramFiles64Folder]\{}\{}' % (company_name, product_name),
              'shortcuts': [
                  'ProgramMenuFolder\Hello World = my_project'
              ],
          }
  ...)
```
The full array of options for build_exe is available in the PyInstaller documentation. Providing an upgrade code is
**strongly recommended** for the bdist_msi command. A license agreement will be added to the installer if there is 
a license text file in the same directory as setup.py.

Note that PyInstaller Utils currently cannot create shortcuts that are not placed in a root system directory. In other 
words, you can currently have a shortcut on the desktop of in the program menu but not in a folder on the desktop or in 
a folder on the program menu. This may be resolved in the future if there is greater interest.
