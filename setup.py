#!/usr/bin/env python

import os

from setuptools import setup, find_packages

BASE_DIR = os.path.dirname(__file__)
VERSION_PATH = os.path.join(BASE_DIR, 'VERSION')
LICENSE_PATH = os.path.join(BASE_DIR, 'LICENSE')
VERSION = open(VERSION_PATH).read()
LICENSE = open(LICENSE_PATH).readline().strip()

setup(
    name='subzero',
    version=VERSION,
    description='PyInstaller setuptools integration',
    author='Mars Galactic',
    author_email='xoviat@users.noreply.github.com',
    url='https://github.com/xoviat/subzero',
    packages=find_packages(),
    license=LICENSE,
    platforms='any',
    keywords=['pyinstaller'],
    classifiers=[],
    install_requires=['PyInstaller', 'PyRTF3', 'packaging'],
    setup_requires=['setuptools-markdown'],
    long_description_markdown_filename='README.md')
