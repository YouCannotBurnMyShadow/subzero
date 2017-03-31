import io
import textwrap

from PyRTF.Renderer import Renderer
from PyRTF.document.paragraph import ParagraphPropertySet, Paragraph
from PyRTF.Elements import Document, Section


def generate_rtf(fh):
    """
    Generates a rich text file object given a license file-like object
    """
    wordpad_header = textwrap.dedent(r'''
        {\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033{\fonttbl{\f0\fnil\fcharset255 Times New Roman;}
        {\*\generator Riched20 10.0.14393}\viewkind4\uc1
        ''').strip().replace('\n', '\r\n')
    center_space = '            '

    r = Renderer()

    doc = Document()
    ss = doc.StyleSheet
    sec = Section()
    doc.Sections.append(sec)

    is_blank = False
    paragraph_text = ['']
    for line in fh:
        if not line or line.isspace():
            is_blank = True
        if is_blank:
            # first element of paragraph_text is left-aligned, subsequent elements are centered
            is_centered = False
            for sec_line in paragraph_text:
                if is_centered:
                    para_props = ParagraphPropertySet(
                        alignment=ParagraphPropertySet.CENTER)
                    p = Paragraph(ss.ParagraphStyles.Normal, para_props)
                    p.append(sec_line)
                    sec.append(p)
                elif sec_line:  # first element may be nothing, but not whitespace
                    sec.append(sec_line)
                is_centered = True
            is_blank = False
            paragraph_text = ['']
        if line.startswith(center_space):
            paragraph_text.append(line.strip())
            is_blank = True
        else:
            paragraph_text[0] += ' ' + line
            paragraph_text[0] = paragraph_text[0].strip()

    f = io.StringIO()
    f.write(wordpad_header)
    r.Write(doc, f)
    f.seek(0)

    return f
