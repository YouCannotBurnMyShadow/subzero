#!/usr/bin/env python

import os

from setuptools import setup, find_packages

BASE_DIR = os.path.dirname(__file__)
README_PATH = os.path.join(BASE_DIR, 'README.md')
VERSION_PATH = os.path.join(BASE_DIR, 'VERSION')
LICENSE_PATH = os.path.join(BASE_DIR, 'LICENSE')
REQS_PATH = os.path.join(BASE_DIR, 'requirements.txt')
DESCRIPTION = open(README_PATH).read()
VERSION = open(VERSION_PATH).read()
LICENSE = open(LICENSE_PATH).readline().strip()
INSTALL_REQS = open(REQS_PATH).read().splitlines()

setup(
    name='pyinstaller_utils',
    version=VERSION,
    description='Additions to Pyinstaller that are not currently included in the default code base',
    long_description=DESCRIPTION,
    author='Mars Galactic',
    author_email='xoviat@users.noreply.github.com',
    url='https://github.com/xoviat/pyinstaller_utils',
    packages=find_packages(),
    license=LICENSE,
    platforms='any',
    keywords=['pyinstaller'],
    classifiers=[],
    install_requires=INSTALL_REQS,
    )
