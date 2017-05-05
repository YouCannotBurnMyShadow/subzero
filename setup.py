#!/usr/bin/env python

import os

from setuptools import setup, find_packages

import versioneer

setup(
    name='subzero',
    version=versioneer.get_version(),
    description='PyInstaller setuptools integration',
    author='Mars Galactic',
    author_email='xoviat@users.noreply.github.com',
    url='https://github.com/xoviat/subzero',
    packages=find_packages(),
    license=open(
        os.path.join(os.path.dirname(__file__), 'LICENSE')).readline().strip(),
    platforms='any',
    keywords=['pyinstaller'],
    classifiers=[],
    install_requires=[
        'PyInstaller',
        'packaging',
        'pipdeptree',
        'pyspin',
        'deepmerge',
        'PyRTF3>=0.47.3',
        'pywix>=0.2;sys_platform == "win32"',
        'glob2;python_version<"3.5"',
        'pathlib;python_version<"3.4"',
        'contextlib2;python_version<"3.4"',
    ],
    cmdclass=versioneer.get_cmdclass(),
    setup_requires=['setuptools-markdown'],
    long_description_markdown_filename='README.md')
