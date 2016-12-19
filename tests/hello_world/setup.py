from setuptools import find_packages

from pyinstaller_utils.dist import setup

setup(name='hello_world',
      author='test_author',
      version='0.1.0',
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'my_project = hello_world.__main__:main',
              'gui = hello_world.__main__:gui',
          ]
      },
      options={
          'build_exe': {
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
      },
      install_requires=[])
