#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./check_for_new_cover.py --pdf test.pdf
#
# Purpose: check for a New KTH cover versus old KTH cover
#
# Example:
# ./check_for_new_cover.py --pdf test5.pdf
#
# To get the correct pdfminer package od:
# pip install pdfminer.six
#
# 2021-08-09 G. Q. Maguire Jr.
#
import re
import sys
# set the stdout to use UTF8 encoding
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

import json
import argparse
import os			# to make OS calls, here to get time zone info

from io import StringIO
from io import BytesIO

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

def check_main_subject_area(txt):
    if txt.find('DEGREE PROJECT IN COMPUTER SCIENCE AND ENGINEERING') >= 0 or\
       txt.find('Degree Project in Computer Science and Engineering') >= 0 or\
       txt.find('Degree project in Computer Science and Engineering') >= 0 or\
       txt.find('Degree project in Computer Science with') >= 0 or\
       txt.find('DEGREE PROJECT IN ELECTRICAL ENGINEERING') >= 0 or\
       txt.find('Degree Project in Electrical Engineering') >= 0 or\
       txt.find('Degree project in Electrical Engineering') >= 0:
        if txt.find('specialising in ') >= 0 or \
           txt.find('specializing in ') >= 0 or \
           txt.find('specialisation in ') >= 0 or \
           txt.find('Specialisation in ') >= 0 or \
           txt.find('SPECIALISING IN ') >= 0:
            return True
    if txt.find('Degree project in Systems, Control and Robotics') >= 0:
            return True
    if txt.find('Degree Project in Information and Network Engineering') >= 0:
            return True
    return False


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing

    argp = argparse.ArgumentParser(description="extract_pseudo_JSON-from_PDF.py: Extract the pseudo JSON from the end of the thesis PDF file")

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

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    filename=args["pdf"]
    if Verbose_Flag:
        print("filename={}".format(filename))

    extracted_data=[]
    set_of_errors=set()

    for page in extract_pages(filename, page_numbers=[0], maxpages=1):
        show_ltitem_hierarchy(page)

        print(page)
        for element in page:
            print(f'{element}')
            if isinstance(element, LTTextContainer):
                print("element is LTTextContainer")
                for text_line in element:
                    print(f'text_line={text_line}')
                    if isinstance(text_line, LTChar):
                        print("fount an LTChar")
                    elif isinstance(text_line, LTAnno):
                        print("fount an LTAnno")
                    else:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                font_size=character.size
                extracted_data.append([font_size,(element.get_text())])
            elif isinstance(element, LTFigure):
                for subelement in element:
                    print(f'subelement={subelement}')
                    if isinstance(subelement, LTFigure):
                        continue
                    elif isinstance(subelement, LTChar):
                        print("found LTChar: {}".format(subelement.get_text()))
                        font_size=subelement.size
                        extracted_data.append([font_size,(subelement.get_text())])
                    elif isinstance(subelement, LTAnno):
                        print("fount an LTAnno")
                    elif isinstance(subelement, LTLine): #  a line
                        continue
                    elif isinstance(subelement, LTCurve): #  a line
                        continue
                    elif isinstance(subelement, LTImage):
                        if hasattr(subelement, 'bbox'):
                            x1=int(subelement.bbox[0])
                            y1=int(subelement.bbox[1])
                            x2=int(subelement.bbox[2])
                            y2=int(subelement.bbox[3])
                            print(f'{x1},{y1} {x2},{y2}')
                            if rough_comparison(x1, 0) and rough_comparison(y1, 0) and\
                               rough_comparison(x2, 595) and (rough_comparison(y2, 841) or  rough_comparison(y2, 842)):
                               print("looks like the page is just a picture")
                               set_of_errors.add("The cover is just a full page picture")
                        continue
                    else:
                        for character in subelement:
                            if isinstance(character, LTChar):
                                print("found char: {}".format(character))
                                font_size=character.size
                                extracted_data.append([font_size,(character.get_text())])

            elif isinstance(element, LTChar):
                font_size=character.size
                extracted_data.append([font_size,(element.get_text())])
            else:
                print(f'unprocessed element: {element}')

    print("extracted_data: {}".format(extracted_data))
    # Example of an old cover:
    # extracted_data: [[10.990000000000009, 'DEGREE PROJECT  COMPUTER SCIENCE AND ENGINEERING,\nSECOND CYCLE, 30 CREDITS\nSTOCKHOLM SWEDEN2021\n, \n'], [10.990000000000009, 'IN \n'], [19.99000000000001, 'title\n'], [16.00999999999999, 'author in caps\n'], [10.989999999999995, 'KTH ROYAL INSTITUTE OF TECHNOLOGY\nSCHOOL OF ELECTRICAL ENGINEERING AND COMPUTER SCIENCE\n'], [10.989999999999995, ' \n']]

    old_size=-1
    current_string=''
    for item in extracted_data:
        if isinstance(item, list):
            if len(item) == 2:
                size, txt = item
                print(f'{size} {txt}')
                if size < 11 and txt.find('KTH ROYAL INSTITUTE OF TECHNOLOGY') >= 0 and txt.find('SCHOOL OF ') >= 0:
                    set_of_errors.add("Found old cover with school name")
                if size < 8.1 and txt.find('ELECTRICAL ENGINEERING AND COMPUTER SCIENCE') >= 0:
                    set_of_errors.add("Found old cover with school name")

                if check_main_subject_area(txt):
                    set_of_errors.add("Found error in cover with stated specialization")

                txt=txt.strip()
                if txt.find('Degree Project in Interactive Media Technology') >= 0 or\
                   txt.find('Degree project in Interactive Media Technology') >= 0 or\
                   txt.find('Degree project in Interaction Design') >= 0 or \
                   txt.find(' Degree Project in Media Technology') >= 0 or \
                   txt.find('Degree Project in Media Technology') >= 0 or \
                   txt.find('Degree project in data science') >= 0 or \
                   txt.find('DEGREE PROJECT IN MEDIA TECHNOLOGY') >= 0 or \
                   txt.find('Degree project in machine learning') >= 0 or \
                   txt.find('Degree Project in Machine Learning') >= 0 or \
                   txt.find('Degree Project in School of Electrical Engineering and Computer Science') >= 0 or \
                   txt.find("Degree project in Master's Programme, Systems, Control and Robotics") >= 0:
                    set_of_errors.add("Found error in cover with incorrect major subject")

                if txt.find('Examensarbete inom ') >= 0 and txt.find('Degree project in ') >= 0:
                    set_of_errors.add("Found error in cover with both English and Swedish for the degree project")

                if rough_comparison(size, 12.0):
                    print("found 12 point text: {}".format(current_string))
                    if txt.find("Master’s dissertation") >= 0:
                        set_of_errors.add("Found error in cover with incorrect level")
                    if txt.find("Second cycle 120  credits") >= 0:
                         set_of_errors.add("Found error in cover incorrect number of credits")
                    if txt.find("Master’s Programme, ICT Innovation, 120 credit") >= 0:
                         set_of_errors.add("Found error in level")
                         set_of_errors.add("Found error in cover incorrect number of credits")

                if old_size == -1:
                    old_size=size
                if rough_comparison(size, old_size):
                    current_string=current_string+txt
                else: # if size != old_size
                    print(f'current_string({size})={current_string}')
                    if current_string.find('DEGREE PROJECT IN COMPUTER SCIENCE AND ENGINEERING, SPECIALISING IN ') == 0:
                        set_of_errors.add("Found error in cover with stated specialization")
                    if current_string.find('Degree project in Interaction Design') == 0:
                        set_of_errors.add("Found error in cover with incorrect major subject")
                    if rough_comparison(size, 12.0):
                        print("found 12 point text: {}".format(current_string))
                        if current_string.find("Master’s dissertation") >= 0:
                            set_of_errors.add("Found error in cover with incorrect level")
                    if rough_comparison(size, 11.0):
                        print("found 11 point text: {}".format(current_string))
                        if current_string.find("SCHOOL OF ELECTRICAL ENGINEERING AND COMPUTER SCIENCE") >= 0:
                            set_of_errors.add("Found old cover with school name")
                    if rough_comparison(size, 8.0):
                        print("found 8 point text: {}".format(current_string))
                        if current_string.find("E L E C T R I C A L   E N G I N E E R I N G   A N D   C O M P U T E R   S C I E N C E") >= 0:
                            set_of_errors.add("Found old cover with school name")
                    if check_main_subject_area(current_string):
                        set_of_errors.add("Found error in cover with stated specialization")
                    if current_string.find('DegreeProjectinInteractiveMediaTechnology') >= 0:
                        set_of_errors.add("Found error in cover with incorrect major subject")
                    if current_string.find('DegreeProjectinComputerScienceandEngineering,specializingin') >= 0:
                        set_of_errors.add("Found error in cover with incorrect major subject")

                    current_string=''+txt
                    old_size=size

    if len(current_string) > 0:
        print(f'current_string({old_size})={current_string}')

    if current_string.find('Stockholm, Sverige 2021 Stockholm, Sverige 2021') >= 0 or \
       current_string.find('Stockholm, Sverige 2022 Stockholm, Sverige 2022') >= 0 or \
       current_string.find('Stockholm, Sweden 2021 Stockholm, Sweden 2021') >= 0 or \
       current_string.find('Stockholm, Sweden 2021 Stockholm, Sweden 2021') >= 0 :
        set_of_errors.append("Found error in cover with repeated Stockholm, Sverige and date ")

    if current_string.find("SCHOOL OF ELECTRICAL ENGINEERING AND COMPUTER SCIENCE") >= 0:
        set_of_errors.add("Found old cover with school name")
    if current_string.find("SCHOOLOFELECTRICALENGINEERINGANDCOMPUTERSCIENCE") >= 0:
        set_of_errors.add("Found old cover with school name")

    if rough_comparison(old_size, 8.0):
        print("found 8 point text: {}".format(current_string))
        if current_string.find("E L E C T R I C A L   E N G I N E E R I N G   A N D   C O M P U T E R   S C I E N C E") >= 0:
            set_of_errors.add("Found old cover with school name")
        if current_string.find("SCHOOLOFELECTRICALENGINEERINGANDCOMPUTERSCIENCE") >= 0:
            set_of_errors.add("Found old cover with school name")

    if len(set_of_errors):
        for e in set_of_errors:
            print("Error: {}".format(e))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

