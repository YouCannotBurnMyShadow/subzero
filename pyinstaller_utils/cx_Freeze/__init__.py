# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

version = "5.0"
__version__ = version

import sys

if sys.platform == "win32":
    pass
elif sys.platform == "darwin":
    pass

del dist
del finder
del freezer
