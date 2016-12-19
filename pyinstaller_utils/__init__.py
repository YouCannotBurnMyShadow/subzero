import distutils
from io import StringIO

import PyRTF

# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

version = "5.0"
__version__ = version

# from pyinstaller_utils.freezer import Freezer, ConstantsModule

import sys

if sys.platform == "win32":
    pass
elif sys.platform == "darwin":
    pass


def build_dir():
    return "exe.{}-{}".format(distutils.util.get_platform(), sys.version[0:3])


def license_text(license_file):
    """
    Generates rich text given a license file-like object
    :param license_file: file-like object
    :return:
    """
    wordpad_header = r'''{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033{\fonttbl{\f0\fnil\fcharset255 Times New Roman;}
{\*\generator Riched20 10.0.14393}\viewkind4\uc1'''.replace('\n', '\r\n')

    r = PyRTF.Renderer()

    doc = PyRTF.Document()
    ss = doc.StyleSheet
    sec = PyRTF.Section()
    doc.Sections.append(sec)

    is_blank = False
    paragraph_text = ''
    for line in license_file:
        if not line or line.isspace():
            is_blank = True
        elif is_blank:
            sec.append(paragraph_text)
            is_blank = False
            paragraph_text = line
        else:
            paragraph_text += ' ' + line

    f = StringIO()
    f.write(wordpad_header)
    r.Write(doc, f)

    return f.getvalue()
