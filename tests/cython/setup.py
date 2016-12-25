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
