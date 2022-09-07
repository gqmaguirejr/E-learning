#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./find_and_extract_references.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
#
# Purpose: Find and extract refrences pages
#
# Example:
# For a single PDF file:
# ./find_and_extract_references.py --pdf ddddddd-FULLTEXT01.pdf
#
# For all the PDF files in the spreadsheet
# ./find_and_extract_references.py -s ../eecs-2022.xlsx
# Note that this can be fund after updating the original spreadsheet with cover information
#
# To get the correct pdfminer package od:
# pip install pdfminer.six
#
# 2021-09-04 G. Q. Maguire Jr.
#
import re
import sys
# set the stdout to use UTF8 encoding
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

import json
import argparse
import os			# to make OS calls, here to get time zone info
import subprocess               # to execute a command
import shlex                    # to split a command into arguments

from io import StringIO
from io import BytesIO

import requests, time
import pprint

# Use Python Pandas to create XLSX files
import pandas as pd

import faulthandler

# from pdfminer.converter import TextConverter, HTMLConverter
# from pdfminer.layout import LAParams
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
# from pdfminer.pdfpage import PDFPage
# from pdfminer.pdfparser import PDFParser

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTLine, LAParams, LTFigure, LTImage, LTTextLineHorizontal, LTTextBoxHorizontal, LTCurve
from typing import Iterable, Any
from pdfminer.layout import LAParams, LTTextBox, LTText, LTChar, LTAnno
import pdfminer.psparser
from pdfminer.pdfdocument import PDFNoValidXRef
from pdfminer.psparser import PSEOF


font_families_and_names={
    # font_name style
    # family: Computer Modern Text Fonts - info from http://mirrors.ibiblio.org/CTAN/systems/win32/bakoma/fonts/fonts.html
    'cmr': 'Roman',
    'cmti': 'Text Italic',
    'cmsl': 'Text Slanted',
    'cmbx': 'Bold Extended',
    'cmb': 'Bold',
    'cmbxti': 'Bold Extended Italic',
    'cmbxsl': 'Bold Extended Slanted',
    'cmcsc': 'Small Caps',
    'cmtt': 'Typewriter',
    'cmitt': 'Typewriter Italic',
    'cmsltt': 'Typewriter Slanted',
    'cmss': 'SansSerif',
    'cmssbx': 'SansSerif Bold',
    'cmssdc': 'SansSerif DemiCondensed',
    'cmssi': 'SansSerif Italic',
    'cmssq': 'SansSerif Quoted',
    'cmssqi': 'SansSerif Quoted Italic',
    'cminch': 'Large font',
    # family: Computer Modern Math Fonts
    'cmmi': 'Math Italic',
    'cmmib': 'Math Bold Italic',
    'cmsy': 'Math Symbols',
    'cmbsy': 'Math Bold Symbols',
    'cmex': 'Math Extension',
    # family: Computer Modern Exotic Fonts:
    'cmdunh': 'Dunhill Roman',
    'cmff': 'Funny Roman',
    'cmfi': 'Funny Italic',
    'cmfib': 'Roman Fibonacci',
    'cmtcsc': 'Typewriter Caps and Small Caps',
    'cmtex': 'TeX extended ASCII',
    'cmu': 'Unslanted Italic',
    'cmvtt': 'Variable-Width Typewriter',
    # family: METAFONT Logo Fonts
    'logo': 'Roman',
    'logobf': 'Bold',
    'logosl': 'Slant',
    # family: LaTeX Fonts
    'circle': 'Circle Drawing',
    'circlew': 'Circle Drawing',
    'line': 'Line Drawing',
    'linew': 'Line Drawing',
    'lasy': 'LaTeX Symbols',
    'lasyb': 'LaTeX Bold Symbols',
    'lcmss': 'SliTeX Sans Serif',
    'lcmssb': 'SliTeX Sans Serif Bold',
    'lcmssi': 'SliTeX Sans Serif Italic',
    # AMS Fonts
    # family: Euler Font Family
    'euex': 'Extension',
    'eufm': 'Fraktur Medium',
    'eufb': 'Fraktur Bold',
    'eurm': 'Roman Medium',
    'eurb': 'Roman Bold',
    'eusm': 'Script Medium',
    'eusb': 'Script Bold',
    # family: Extra Math Symbol Fonts
    'msam': 'First font',
    'msbm': 'Second font',
    # family: Computer Modern Cyrillic Fonts
    'cmcyr': 'Roman',
    'cmcti': 'Text Italic',
    'cmcsl': 'Text Slanted',
    'cmcbx': 'Bold Extended',
    'cmcb': 'Bold',
    'cmcbxti': 'Bold Extended Italic',
    'cmcbxsl': 'Bold Extended Slanted',
    'cmccsc': 'Small Caps',
    'cmctt': 'Typewriter',
    'cmcitt': 'Typewriter Italic',
    'cmcsltt': 'Typewriter Slanted',
    'cmcss': 'SansSerif',
    'cmcssbx': 'SansSerif Bold',
    'cmcssdc': 'SansSerif DemiCondenced',
    'cmcssi': 'SansSerif Italic',
    'cmcssq': 'SansSerif Quoted',
    'cmcssqi': 'SansSerif Quoted Italic',
    'cmcinch': 'Large font',
    # family: Concrete Fonts
    'ccr': 'Roman',
    'ccsl': 'Slanted',
    'ccslc': 'Condensed Slanted',
    'ccti': 'Text Italic',
    'cccsc': 'Small Caps',
    'ccmi': 'Math Italic',
    'ccmic': 'Math Italic',
    'eorm': 'Roman',
    'eosl': 'Slanted',
    'eocc': 'Small Caps',
    'eoti': 'Text Italic',
    'torm': 'Roman',
    'tosl': 'Slanted',
    'toti': 'Text Italic',
    'tcssdc': 'SansSerif Condensed',
    'xccam': 'Regular',
    'xccbm': 'Regular',
    'xccmi': 'Math Italic',
    'xccsy': 'Math Symbols',
    'xccex': 'Math Extension',
    # family: EC/TC Fonts
    'ecrm': 'Roman Medium',
    'ecti': 'Text Italic',
    'ecbi': 'Bold Extended Text Italic',
    'ecbl': 'Bold Extended Slanted Roman',
    'ecbx': 'Bold Extend Roman',
    'ecsl': 'Roman Slanted',
    'ecci': 'Text Classical Serif Italic',
    'ecrb': 'Roman Bold (Non-Extended)',
    'ecui': 'Unslanted Italic',
    'eccc': 'Caps and Small Caps',
    'ecsc': 'Slanted Caps and Small Caps',
    'ecxc': 'Bold Extended Caps and Small Caps',
    'ecoc': 'Bold Extended Slanted Caps and Small Caps',
    'ecss': 'Sans Serif',
    'ecsi': 'Sans Serif Inclined',
    'ecsx': 'Sans Serif Bold Extended',
    'ecso': 'Sans Serif Bold Extended Oblique',
    'ectt': 'Typewriter Text',
    'ecit': 'Italic Typewriter Text',
    'ecst': 'Slanted Typewriter Text',
    'ectc': 'Typewriter Caps and Small Caps',
    'ecvi': 'Variable Width Italic Typewriter Text',
    'ecvt': 'Variable-Width Typewriter Text',
    'ecdh': 'Dunhill Roman',
    # family: LH Fonts
    'larm': 'Roman Medium',
    'lati': 'Text Italic',
    'labi': 'Bold Extended Text Italic',
    'labl': 'Bold Extended Slanted Roman',
    'labx': 'Bold Extend Roman',
    'lasl': 'Roman Slanted',
    'laci': 'Text Classical Serif Italic',
    'larb': 'Roman Bold (Non-Extended)',
    'laui': 'Unslanted Italic',
    'lacc': 'Caps and Small Caps',
    'lasc': 'Slanted Caps and Small Caps',
    'laxc': 'Bold Extended Caps and Small Caps',
    'laoc': 'Bold Extended Slanted Caps and Small Caps',
    'lass': 'Sans Serif',
    'lasi': 'Sans Serif Inclined',
    'lasx': 'Sans Serif Bold Extended',
    'laso': 'Sans Serif Bold Extended Oblique',
    'latt': 'Typewriter Text',
    'lait': 'Italic Typewriter Text',
    'last': 'Slanted Typewriter Text',
    'latc': 'Typewriter Caps and Small Caps',
    'lavi': 'Variable Width Italic Typewriter Text',
    'lavt': 'Variable-Width Typewriter Text',
    # family: T1 Encoded Fonts (Complete Emulation of the EC fonts)
    't1r': 'Roman',
    't1ti': 'Text Italic',
    't1sl': 'Text Slanted',
    't1bx': 'Bold Extended',
    't1b': 'Bold',
    't1bxti': 'Bold Extended Italic',
    't1bxsl': 'Bold Extended Slanted',
    't1csc': 'Small Caps',
    't1tt': 'Typewriter',
    't1itt': 'Typewriter Italic',
    't1sltt': 'Typewriter Slanted',
    't1ss': 'SansSerif',
    't1ssbx': 'SansSerif Bold',
    't1ssdc': 'SansSerif DemiCondenced',
    't1ssi': 'SansSerif Italic',
    # family: T2 Encoded Fonts (Partial Emulation of the LH/LA fonts)
    't2r': 'Roman',
    't2ti': 'Text Italic',
    't2sl': 'Text Slanted',
    't2bx': 'Bold Extended',
    't2b': 'Bold',
    't2bxti': 'Bold Extended Italic',
    't2bxsl': 'Bold Extended Slanted',
    't2csc': 'Small Caps',
    't2tt': 'Typewriter',
    't2itt': 'Typewriter Italic',
    't2sltt': 'Typewriter Slanted',
    't2ss': 'SansSerif',
    't2ssbx': 'SansSerif Bold',
    't2ssdc': 'SansSerif DemiCondenced',
    't2ssi': 'SansSerif Italic',
    # Font ZOO
    # family: Ralph Smith's Formal Script: (converted at end of 1997)
    'rsfs': 'Script',
    # Diagram Drawing Fonts
    # family: LamsTeX Commutative Diagram Drawing Fonts (converted at end of 1997)
    'lams1': 'Line drawing',
    'lams2': 'Line drawing',
    'lams3': 'Line drawing',
    'lams4': 'Line drawing',
    'lams5': 'Line drawing',
    # family: Xy-Pic Drawing Fonts
    'xyatip': 'upper arrow tips (technical style)',
    'xybtip': 'lower arrow tips (technical style)',
    'xycmat': 'upper arrow tips (Computer Modern style)',
    'xycmbt': 'lower arrow tips (Computer Modern style)',
    'xyeuat': 'upper arrow tips (Euler style)',
    'xyeubt': 'lower arrow tips (Euler style)',
    'xybsql': 'lower squiggles/quarter circles',
    'xycirc': '1/8 circles with varying radii',
    'xydash': 'dashes',
    'xyline': 'line segments',
    'xymisc': 'miscellaneous characters',
    'xyqc': 'quarter circles',
    # MusixTeX Fonts
    'mx': '',
    'xsld': '',
    'xslhd': '',
    'xslhu': '',
    'xslu': '',
    'xslz': '',
    'xslhz': '',
    'mxsps': '',
    # Timing Diagram Fonts
    'timing1': '',
    'timing1s': '',
    'timing2': '',
    'timing2s': '',
    # Miscelaneous Diagram Drawing Fonts
    'arrsy10': '',
    'newcirc': '',
    'ulsy10': '',
    'bbding10': '',
    'dingbat': '',
    'umranda': '',
    'umrandb': '',
    'karta15': '',
    'china10': '',
    'cchess46': ''
}

def remove_fontname_prefix(fontname):
    if len(fontname) > 7:
        return fontname[7:]
    else:
        print(f"in removed_fontname_prefix fontname ({fontname}) is too short, but be at longer than 7 characters")
        return None
    
def style_given_font_name(fontname):
    style=None
    # extract root name
    style=font_families_and_names.get(fontname.lower(), None)
    if style:
        return style
    # trim digits off if they exist
    if len(fontname) > 2:
        if fontname[-1].isdigit():
            shortened_name=fontname[:-1]
            style=style_given_font_name(shortened_name.lower())
    return style

def check_for_emphasis_style(fontname, styles):
    fontname=remove_fontname_prefix(fontname)
    if fontname:
        style=style_given_font_name(fontname)
        if style:
            for s in styles:
                if style.lower().find(s.lower()) >= 0:
                    return True
    return False

def show_ltitem_hierarchy(o: Any, depth=0):
    """Show location and text of LTItem and all its descendants"""
    if depth == 0:
        print('element                        x1  y1  x2  y2   text')
        print('------------------------------ --- --- --- ---- -----')

    print(
        f'{get_indented_name(o, depth):<30.30s} '
        f'{get_optional_bbox(o)} '
        f'{get_optional_text(o)}'
    )

    if isinstance(o, Iterable):
        for i in o:
            show_ltitem_hierarchy(i, depth=depth + 1)


def get_indented_name(o: Any, depth: int) -> str:
    """Indented name of LTItem"""
    return '  ' * depth + o.__class__.__name__


def get_optional_bbox(o: Any) -> str:
    """Bounding box of LTItem if available, otherwise empty string"""
    if hasattr(o, 'bbox'):
        return ''.join(f'{i:<4.0f}' for i in o.bbox)
    return ''


def get_optional_text(o: Any) -> str:
    """Text of LTItem if available, otherwise empty string"""
    if hasattr(o, 'get_text'):
        return o.get_text().strip()
    return ''

def rough_comparison(a, b):
    if abs(a-b) < 0.1:
        return True
    return False


global found_references_page
references_place_y=630.0
#heading_size_min=19.0      # 24.79
heading_size_min=13.9      # 24.79

found_references_page=False
global found_last_references_page
found_last_references_page=False

# heading rule
# LTLine                       70.87   785.34  524.41  785.34   
page_heading_place_y=780.0
page_heading_size_min=10.0  #10.91
global found_heading_rule
found_heading_rule=False


global found_appendix_page
found_appendix_page=False

# Match against targets including an all caps version of target with a vertical bar
def check_for_one_target_string_alone(txt, targets):
    txt=txt.strip()
    for t in targets:
        # find target along in a section/chapter heading
        if txt.find(t) >= 0 and len(txt) == len(t):
            return True
        # find target in a page heading
        if txt.find('|') > 0 and (txt.find(t) >= 0 or txt.find(t.upper()) >= 0):
            return True
        if txt.find(t) >= 0 and txt.find(t) < 10:
            print("Possible heading {0} in {1} with len(txt)={2}".format(t, txt, len(txt)))
            return True
        if txt.find(t.upper()) >= 0 and txt.find(t.upper()) < 10:
            print("Possible heading {0} in {1} with len(txt)={2}".format(t, txt, len(txt)))
            return True
    return False

# Note that we have to set the globals to the page index (pgnumber)
def check_for_references(o: Any, pgnumber):
    global found_references_page
    global found_last_references_page
    global found_appendix_page
    global Verbose_Flag
    target_strings=['References', 'Bibliography', 'References and Bibliography']
    appendix_strings=['Appendix', 'Appendices']

    txt=o.get_text().strip()
    # This check for the target alone is to avoid the instance of the target in the Table of Contents
    if check_for_one_target_string_alone(txt, target_strings):
        if Verbose_Flag or True:
            print("Found references starting at page:{}".format(pgnumber))
        if not found_references_page:
            found_references_page=pgnumber
        else:
            found_last_references_page=pgnumber
    elif check_for_one_target_string_alone(txt, appendix_strings):
        if Verbose_Flag or True:
            print("Found appendix/appendices at page:{0} - {1}".format(pgnumber, txt))
        if found_references_page:
            print("found_appendix_page={0} found_last_references_page={1}".format(found_appendix_page, found_last_references_page))
            if not found_appendix_page and not found_last_references_page:
                found_appendix_page=True
                found_last_references_page=pgnumber-1
    else:
        return
    return

# check for section/chapter heading being some variant of References
def check_for_references_in_section_heading(o: Any, pgnumber):
    global found_references_page
    global found_last_references_page
    global found_TOC_page
    global Verbose_Flag
    target_strings=['References']

    txt=o.get_text().strip()
    if check_for_one_target_string_alone(txt, target_strings):
        if Verbose_Flag or True:
            print("Found references starting at page:{}".format(pgnumber))
        nbc=count_bold_characters(o)
        print("checking for heading in {0} - nbc={1}".format(txt, nbc))
        if nbc > len(txt)/2:
            # try to avoid the instance of "References" in the table of contents
            if found_TOC_page < pgnumber:
                if not found_references_page:
                    found_references_page=pgnumber
                else:
                    found_last_references_page=pgnumber
    return


def check_for_references_page_header(o: Any, pgnumber):
    global found_references_page
    global found_last_references_page
    global found_appendix_page
    global found_TOC_page
    global Verbose_Flag
    target_strings=['References', 'Bibliography', 'References and Bibliography']
    appendix_strings=['Appendix', 'Appendices']
    toc_strings=['Contents', 'Table of contents']

    txt=o.get_text().strip()
    print("check for page header in {0} on page {1}".format(txt, pgnumber))

    # in this case there is a new page header, so stop including the pages in the set of reference pages
    if found_references_page and not check_for_one_target_string_alone(txt, target_strings):
        if not found_last_references_page:
            if Verbose_Flag or True:
                print("Change in page headers at page:{0} - {1}".format(pgnumber, txt))
            found_last_references_page=pgnumber-1
    # This check for the target alone is to avoid the instance of the target in the Table of Contents
    elif check_for_one_target_string_alone(txt, target_strings):
        if Verbose_Flag or True:
            print("Found references starting at page:{}".format(pgnumber))
        if not found_references_page:
            found_references_page=pgnumber
        else:
            found_last_references_page=pgnumber
    elif check_for_one_target_string_alone(txt, appendix_strings):
        if Verbose_Flag or True:
            print("Found appendix/appendices at page:{0} - {1}".format(pgnumber, txt))
        if found_references_page:
            print("found_appendix_page={0} found_last_references_page={1}".format(found_appendix_page, found_last_references_page))
            if not found_appendix_page and not found_last_references_page:
                found_appendix_page=True
                found_last_references_page=pgnumber-1
    elif check_for_one_target_string_alone(txt, toc_strings):
        if Verbose_Flag or True:
            print("Found table of contents at page:{0} - {1}".format(pgnumber, txt))
        # found_TOC_page will be the last page with a Contents page heading
        found_TOC_page=pgnumber
    else:
        return
    return

# If there are heading rules, update the expected location for page headings
def check_for_heading_rule(o: Any):
    global page_heading_place_y
    global found_heading_rule
    if found_heading_rule:
        return
    if (o.bbox[1] == o.bbox[3]) and (o.bbox[2] - o.bbox[0]) > 400.0 and (o.bbox[1] > page_heading_place_y):
        found_heading_rule=True
        page_heading_place_y=o.bbox[1]
        print("Found heading rule at {0} - the page heading should be above this".format(page_heading_place_y))

    return

def count_bold_characters(o: Any):
    count=0
    if isinstance(o, LTTextContainer):
        print("in count_bold_characters({})".format(o.get_text()))
        for text_line in o:
            for character in text_line:
                if isinstance(character, LTChar):
                    print("character.fontname={0}, size={1}, ncs={2}, graphicstate={3}".format(character.fontname, character.size, character.ncs, character.graphicstate))
                    if 'Bold' in character.fontname:
                        count=count+1
                    else:
                        if check_for_emphasis_style(character.fontname, ['slanted', 'bold']):
                            count=count+1
    return count


def process_element(o: Any, pgnumber):
    global extracted_data
    last_x_offset=None
    last_x_width=None
    last_y_offset=None            # y_offset of text characters

    if isinstance(o, LTTextBoxHorizontal):
        for text_line in o:
            if hasattr(text_line, 'bbox'):
                last_x_offset=text_line.bbox[0]
                last_y_offset=text_line.bbox[1]
                last_x_width=text_line.bbox[2]-text_line.bbox[0]
            if Verbose_Flag:
                print(f'text_line={text_line}')
            if hasattr(text_line, 'size'):
                font_size=text_line.size
            else:
                font_size=0
            if isinstance(text_line, LTAnno):
                print("found an LTAnno")

        # Check in page heading
        # LTTextBoxHorizontal          402.96  783.59  496.06  794.50   REFERENCES | 69
        # LTTextLineHorizontal       402.96  783.59  496.06  794.50   REFERENCES | 69
        if (o.bbox[1]-page_heading_place_y) >= 0.0: # and (o.bbox[3]-o.bbox[1]) >= page_heading_size_min:
            check_for_references_page_header(o, pgnumber)
        #
        #LTTextBoxHorizontal          127.56  638.43  261.19  663.22   References
        #LTTextLineHorizontal       127.56  638.43  261.19  663.22   References
        # elif (o.bbox[1]-references_place_y) > 0.0 and (o.bbox[3]-o.bbox[1]) >= heading_size_min:
        #     check_for_references(o, pgnumber)
        else:
            # check for section/chapter heading
            check_for_references_in_section_heading(o, pgnumber)
            return

    elif isinstance(o, LTTextContainer):
        if Verbose_Flag:
            print("element is LTTextContainer")
        for text_line in o:
            if Verbose_Flag:
                print(f'text_line={text_line}')
            if isinstance(text_line, LTAnno):
                if Verbose_Flag:                
                    print("found an LTAnno")
            else:
                font_size=text_line.size
                if Verbose_Flag:
                    print("font_size of text_line={}".format(text_line.size))
            if hasattr(text_line, 'bbox'):
                last_x_offset=text_line.bbox[0]
                last_y_offset=text_line.bbox[1]
                last_x_width=text_line.bbox[2]-text_line.bbox[0]
        extracted_data.append([font_size, last_x_offset, last_y_offset, last_x_width, (o.get_text())])
    elif isinstance(o, LTLine): #  a line
        #  LTLine                       70.87   785.34  524.41  785.34   
        check_for_heading_rule(o)
        return
    elif isinstance(o, LTFigure):
        if isinstance(o, Iterable):
            for i in o:
                process_element(i, pgnumber)
    elif isinstance(o, LTImage):
        return
        
    elif isinstance(o, LTChar):
        if Verbose_Flag:
            print("found LTChar: {}".format(o.get_text()))
        if hasattr(o, 'bbox'):
            last_x_offset=o.bbox[0]
            last_y_offset=o.bbox[1]
            last_x_width=o.bbox[2]-o.bbox[0]
            font_size=o.size
        extracted_data.append([font_size, last_x_offset, last_y_offset, last_x_width, (o.get_text())])
    elif isinstance(o, LTAnno):
        return
    elif isinstance(o, LTCurve): #  a curve
        return
    else:
        print(f'unprocessed element: {o}')
        if isinstance(o, Iterable):
            for i in o:
                process_element(i, pgnumber)

def process_file(filename):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global set_of_errors
    global set_of_evidence_for_new_cover
    global extracted_data
    global cycle
    global found_references_page
    global found_last_references_page
    global found_appendix_page

    extracted_data=[]
    set_of_errors=set()
    set_of_evidence_for_new_cover=set()
    major_subject=None            # the major subject
    cycle=None                    # the cycle number
    place=None                    # the place from the cover
    font_size=None                # the latest font size
    last_x_offset=None
    last_x_width=None
    last_y_offset=None            # y_offset of text characters



    page_index = 0
    try:
        for page in extract_pages(filename):
            page_index=page_index+1
            if Verbose_Flag:
                print(f'Processing page={page_index}')

            if testing:
                show_ltitem_hierarchy(page)
                print(page)
                continue

            for element in page:
                if Verbose_Flag:
                    print(f'{element}')
                process_element(element, page_index)

    except (PDFNoValidXRef, PSEOF, pdfminer.pdfdocument.PDFNoValidXRef, pdfminer.psparser.PSEOF) as e:
        print(f'Unexpected error in processing the PDF file: {filename} with error {e}')
        return False
    except Exception as e:
        print(f'Error in PDF extractor: {e}')
        return False

    if found_references_page:
        if not found_appendix_page and not found_last_references_page:
            found_last_references_page=page_index-1
            print("Assuming references end on page {}".format(found_last_references_page))
    return True


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global set_of_errors
    global set_of_evidence_for_new_cover
    global extracted_data
    global cycle
    global found_references_page
    global found_last_references_page

    argp = argparse.ArgumentParser(description='find_and_extract_references.py: FInd reference page(s) within the PDF file')

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-p', '--pdf',
                      type=str,
                      default="test.pdf",
                      help="read PDF file"
                      )

    argp.add_argument('-s', '--spreadsheet',
                      type=str,
                      default=False,
                      help="spreadsheet file"
                      )

    argp.add_argument('-n', '--nth',
                      type=int,
                      default=False,
                      help="Number of rows to skip"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]
    testing=args["testing"]

    if not args["spreadsheet"]:
        filename=args["pdf"]
        if Verbose_Flag:
            print("filename={}".format(filename))

        if not process_file(filename):
            return
        if found_references_page:
            print("Found references page at {0} in {1}".format(found_references_page, filename))
        if not found_last_references_page:
            print("found_last_references_page was not set, setting it to found_references_page={}".format(found_references_page))
            found_last_references_page=found_references_page

        if found_last_references_page:
            print("Last references page at {0}".format(found_last_references_page))
            
            if filename.endswith('.pdf'):
                output_filename="{0}-refpages.pdf".format(filename[:-4])
            else:
                output_filename="output.pdf"

            cmd="qpdf {0} --pages . {1}-{2} -- {3}".format(filename, found_references_page, found_last_references_page, output_filename)
            if Verbose_Flag or True:
                print("cmd: {0}".format(cmd))

            with subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE) as proc:
                cmd_ouput=proc.stdout.read()
                if len(cmd_ouput) > 0:
                    print(cmd_ouput)
            return found_references_page
        else:
            return -1
    
    # the following handles the case of processing the available files based upon a spreadsheet
    spreadsheet_name=args["spreadsheet"]
    if not spreadsheet_name.endswith('.xlsx'):
        print("must give the name of a .xlsx spreadsheet file")
        return

    skip_to_row=args['nth']

    diva_df=pd.read_excel(open(spreadsheet_name, 'rb'))

    column_names=list(diva_df)
    # add columns for new information


    # this column is used to record the starting page numer of the For DIVA pages that have NOT been removed
    diva_df['For DIVA page(s) present'] = pd.NaT


    for idx, row in diva_df.iterrows():
        found_references_page=False
        found_last_references_page=False
        if skip_to_row and idx < skip_to_row:
            continue
        url=row['FullTextLink']
        author=row['Name']
        pid=row['PID']
        if pd.isna(url):
            print("no full text for thesis by {}".format(author))
        else:
            print(f'{idx}: {author}  {url}')
            last_slash_in_url=url.rfind('/')
            if last_slash_in_url < 0:
                print("Cannot find file name in URL")
                continue
            filename="{0}-{1}".format(pid, url[last_slash_in_url+1:])
            print(f'reading file {filename}')

            if not process_file(filename):
                diva_df.loc[idx, 'Unexpected error when processing file']=filename
                continue

            if found_references_page:
                print("Found references page at {0} in {1} by author(s) {2}".format(found_references_page, filename, row['Name']))
                if found_last_references_page:
                    diva_df.loc[idx, 'References page(s) present'] = "{0}-{1}".format(found_references_page, found_last_references_page)
                else:
                    diva_df.loc[idx, 'References page(s) present'] = "{0}".format(found_references_page)

                if filename.endswith('.pdf'):
                    output_filename="{0}-refpages.pdf".format(filename[:-4])
                else:
                    output_filename="{0}-refpages.pdf".format(filename)

                if found_last_references_page:
                    cmd="qpdf {0} --pages . {1}-{2} -- {3}".format(filename, found_references_page, found_last_references_page, output_filename)
                else:
                    cmd="qpdf {0} --pages . {1} -- {2}".format(filename, found_references_page, output_filename)
                if Verbose_Flag:
                    print("cmd: {0}".format(cmd))

                with subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE) as proc:
                    cmd_ouput=proc.stdout.read()
                    if len(cmd_ouput) > 0:
                        print(cmd_ouput)

        if args["testing"]:
            break

    # the following was inspired by the section "Using XlsxWriter with Pandas" on http://xlsxwriter.readthedocs.io/working_with_pandas.html
    # set up the output write
    output_spreadsheet_name=spreadsheet_name[:-5]+'with_references_info.xlsx'
    writer = pd.ExcelWriter(output_spreadsheet_name, engine='xlsxwriter')
    diva_df.to_excel(writer, sheet_name='ReferencesInfo')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

