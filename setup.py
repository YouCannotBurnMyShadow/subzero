#!/usr/bin/env python

import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

BASE_DIR = os.path.dirname(__file__)
README_PATH = os.path.join(BASE_DIR, 'README.md')
VERSION_PATH = os.path.join(BASE_DIR, 'VERSION')
LICENSE_PATH = os.path.join(BASE_DIR, 'LICENSE')
DESCRIPTION = open(README_PATH).read()
VERSION = open(VERSION_PATH).read()
LICENSE = open(LICENSE_PATH).readline().strip()

setup(
    name='pyinstaller_utils',
    version=VERSION,
    description='Additions to Pyinstaller that are not currently included in the default code base',
    long_description=DESCRIPTION,
    author='Mars Galactic',
    author_email='xoviat@users.noreply.github.com',
    url='https://github.com/xoviat/pyinstaller_utils',
    py_modules=['pyinstaller_utils'],
    license=LICENSE,
    platforms='any',
    keywords=['pyinstaller'],
    classifiers=[],
    )
