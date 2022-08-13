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

KTH_logo_x=38.000
KTH_logo_y=736.170
KTH_logo_width=181.0
KTH_logo_height=182.0

KTH_logotype_x=451.65
KTH_logotype_y=790.07
KTH_logotype_width=320.0
KTH_logotype_height=58.0

def check_for_logo_or_logotype(e):
    global Verbose_Flag
    if hasattr(e, 'bbox'):
        x1=int(e.bbox[0])
        y1=int(e.bbox[1])
        x2=int(e.bbox[2])
        y2=int(e.bbox[3])
        if Verbose_Flag:
            print(f'in check_for_logo_or_logotype - bbox: {x1},{y1} {x2},{y2}')
        if rough_comparison(x1, 0) and rough_comparison(y1, 0) and\
           rough_comparison(x2, 595) and (rough_comparison(y2, 841) or  rough_comparison(y2, 842)):
            print("looks like the page is just a picture")
            set_of_errors.add("The cover is just a full page picture")

        print("name={0}, srcsize={1}, bbox={2}".format(e.name, e.srcsize, e.bbox))
        #subelement=<LTImage(Im1) 19.925,735.558,92.105,808.136 (181, 182)> 19,735 92,808
        #name=Im1, srcsize=(181, 182), bbox=(19.924999999999997, 735.558, 92.1047, 808.13649)
        #<LTFigure(Image7) 38.000,736.170,110.850,809.020 matrix=[72.85,0.00,0.00,72.85, (38.00,736.17)]>
        # subelement=<LTImage(Image7) 38.000,736.170,110.850,809.020 (181, 182)>
        # name=Image7, srcsize=(181, 182), bbox=(38.0, 736.17, 110.85, 809.02)

        width, height = e.srcsize
        if abs(width-KTH_logo_width)  < 2.0 and abs(height-KTH_logo_height) < 2.0:
            if abs(x1-KTH_logo_x) < 2.0 and abs(y1-KTH_logo_y) < 2.0:
                set_of_evidence_for_new_cover.add("possible KTH logo")
            else:
                set_of_errors.add("possible KTH logo off by: {0:.2f},{1:.2f}".format(x1-KTH_logo_x, y1-KTH_logo_y))
            return True

        #name=Im0, srcsize=(320, 58), bbox=(449.872, 789.154, 554.6043, 808.13673)
        #<LTFigure(Im1) 19.925,735.558,92.105,808.136 matrix=[72.18,0.00,0.00,72.58, (19.92,735.56)]>
        # <LTFigure(Image8) 451.650,790.070,556.500,809.020 matrix=[104.85,0.00,0.00,18.95, (451.65,790.07)]>
        # subelement=<LTImage(Image8) 451.650,790.070,556.500,809.020 (320, 58)>
        # 451,790 556,809
        # name=Image8, srcsize=(320, 58), bbox=(451.65, 790.07, 556.5, 809.0200000000001)

        if abs(width-KTH_logotype_width)  < 2.0 and abs(height-KTH_logotype_height) < 2.0:
            if abs(x1-KTH_logotype_x) < 2.0 and abs(y1-KTH_logotype_y) < 2.0:
                set_of_evidence_for_new_cover.add("possible KTH English logotype")
            else:
                set_of_errors.add("possible KTH English logotype off by: {0:.2f},{1:.2f}".format(x1-KTH_logotype_x, y1-KTH_logotype_y))
            return True

        if abs(x1-KTH_logotype_x) < 2.0 and abs(y1-KTH_logotype_y) < 2.0:
            set_of_errors.add("possible KTH English logotype wrong size: {0:.2f},{1:.2f}".format(width, height))
            return True

        if abs(width-144.0)  < 2.0 and abs(height-144.0) < 2.0:
            set_of_errors.add("possible left over image ({0:.2f},{1:.2f}) on cover at {2:.2f},{3:.2f}".format(width, height, x1, y1))
        else:
            set_of_errors.add("possible cover image ({0:.2f},{1:.2f}) on cover at {2:.2f},{3:.2f}".format(width, height, x1, y1))
        return False


cover_line_x0=38.0
cover_line_y0=33.0
cover_line_length=510.0
cover_line_width=1.0

def check_for_cover_line_element(o):
    global Verbose_Flag
    if Verbose_Flag or True:
        print("LTLine: linewith={0}, p0={1},{2}, p1={3},{4}".format(o.linewidth, o.x0, o.y0, o.x1, o.y1))
    # LTLine: linewith=0.99628, p0=38.057,33.375, p1=546.1582,33.375
    if abs(o.linewidth-cover_line_width) < 1.1:
        cover_line_x1=cover_line_x0+cover_line_length
        if abs(o.x0-cover_line_x0) < 2.0 and abs(o.y0-cover_line_y0) < 2.0 and\
           abs(o.x1-cover_line_x1) < 2.0 and abs(o.y1-cover_line_y0) < 2.0:
            set_of_evidence_for_new_cover.add("cover line")
        else:
            if abs(o.x0-cover_line_x0) < 2.0 and abs(o.y0-cover_line_y0) < 2.0:
                set_of_errors.add("cover line length off by: {0:.2f},{1:.2f}".format((o.x1-o.x0)-cover_line_length, o.y1-o.y0))
            elif abs((o.x1-o.x0)-cover_line_length) < 2.0 and abs(o.y1-o.y0) < 1.0:
                set_of_errors.add("cover line off by {0:.2f},{1:.2f}".format(o.x0-cover_line_x0, o.y0-cover_line_y0))
            else:
                set_of_errors.add("cover line off by {0:.2f},{1:.2f} length off by: {2},{3}".format(o.x0-cover_line_x0, o.y0-cover_line_y0, (o.x1-o.x0)-cover_line_length, o.y1-o.y0))



def check_cover_place_and_year(place):
    place=place.strip()
    print("check_cover_place_and_year({})".format(place))
    m=re.match(r"(?P<city>\w+),\s(?P<country>\w+)\s(?P<year>\d+)", place)
    if not m:
        m=re.match(r"(?P<city>\w+),\s(?P<country>\w+),\s(?P<year>\d+)", place)
    if m:
        if m.group('city') == 'Stockholm':
            if m.group('country') == 'Sweden':
                set_of_evidence_for_new_cover.add("cover place English")
            if m.group('country') == 'Sverige':
                set_of_evidence_for_new_cover.add("cover place Swedish")
        year_str=m.group('year')
        if len(year_str) == 4:
            set_of_evidence_for_new_cover.add(f'cover year={year_str}')

# from DOCX 70.920,645.940
cycle_x=70.920
cycle_y=645.940
eng_first_cycle_str='First cycle'
swe_first_cycle_str='Grundnivå'
eng_second_cycle_str='Second cycle'
swe_second_cycle_str='Avancerad nivå'

global cycle

def check_for_cycle_and_credits_element(e):
    global Verbose_Flag
    if hasattr(e, 'bbox'):
        x1=int(e.bbox[0])
        y1=int(e.bbox[1])
        x2=int(e.bbox[2])
        y2=int(e.bbox[3])
        if Verbose_Flag:
            print(f'in check_for_cycle_and_credits_element - bbox: {x1},{y1} {x2},{y2}')

        if not isinstance(e, LTTextBoxHorizontal):
            return

        #LTTextBoxHorizontal          74  638 205 650  Second cycle, 30 credits
        #LTTextLineHorizontal       74  638 205 650  Second cycle, 30 credits
        if abs(x1-cycle_x) < 5.0 and abs(y1-cycle_y) < 20.0:
            cycle_credits=e.get_text()
            check_for_cycle_and_credits(cycle_credits)


def check_for_cycle_and_credits(cycle_credits):
    global Verbose_Flag
    global cycle
    number_of_credits=None
    cycle_credits=cycle_credits.strip()

    if Verbose_Flag:
        print("check_for_cycle_and_credits({})".format(cycle_credits))
    if re.search(eng_first_cycle_str,  cycle_credits, re.IGNORECASE):
        set_of_evidence_for_new_cover.add("English 1st cycle")
        cycle=1
        if not re.search(eng_first_cycle_str,  cycle_credits):
            set_of_errors.add("Case error in cycle")                            

    elif re.search(swe_first_cycle_str,  cycle_credits, re.IGNORECASE):
        set_of_evidence_for_new_cover.add("Swedish 1st cycle")
        cycle=1
        if not re.search(swe_first_cycle_str,  cycle_credits):
            set_of_errors.add("Case error in cycle")

    elif re.search(eng_second_cycle_str,  cycle_credits, re.IGNORECASE):
        set_of_evidence_for_new_cover.add("English 2nd cycle")
        cycle=2
        if not re.search(eng_second_cycle_str,  cycle_credits):
            set_of_errors.add("Case error in cycle")

    elif re.search(swe_second_cycle_str,  cycle_credits, re.IGNORECASE):
        set_of_evidence_for_new_cover.add("Swedish 2nd cycle")
        cycle=2
        if not re.search(swe_second_cycle_str,  cycle_credits):
            set_of_errors.add("Case error in cycle")
    else:
        if cycle_credits.find("Master’s dissertation") >= 0:
            set_of_errors.add("Found error in cover with incorrect level")
        if cycle_credits.find("Master’s Programme, ICT Innovation, 120 credit") >= 0:
            set_of_errors.add("Found error in cover with incorrect level")
            set_of_errors.add("Found error in cover incorrect number of credits")

    # check capitalization of credits
    credits_str='credits'
    hp_str='hp'
    if ("English 1st cycle" in set_of_evidence_for_new_cover) or\
       ("English 2nd cycle" in set_of_evidence_for_new_cover):
        if re.search(credits_str,  cycle_credits, re.IGNORECASE) and\
           not re.search(credits_str,  cycle_credits):
            set_of_errors.add("Case error in credits")
        elif re.search(hp_str,  cycle_credits, re.IGNORECASE):
            set_of_errors.add("Swedish credits units used with an English cycle")
        else:
            print("English cycle information")
    if ("Swedish 1st cycle" in set_of_evidence_for_new_cover) or\
       ("Swedish 2nd cycle" in set_of_evidence_for_new_cover):
        if re.search(hp_str,  cycle_credits, re.IGNORECASE) and\
           not re.search(hp_str,  cycle_credits):
            set_of_errors.add("Case error in credits")
        elif re.search(credits_str,  cycle_credits, re.IGNORECASE):
            set_of_errors.add("English credits units used with an Swedish cycle")
        else:
            print("Swedish cycle information")


    # check numeric number of credits
    # note that one has to look for a comma and space
    # as a comma could be part of the number of credits, such as "7,5 hp"
    last_comma=cycle_credits.rfind(', ')
    if last_comma >= 0:
        credits_substr=cycle_credits[last_comma+2:].strip()
        split_credits_substr=credits_substr.split(' ')
        if len(split_credits_substr) == 2:
            first=split_credits_substr[0]
            if first.find(',') >= 0:
                first=first.replace(',', '.') # convert to a decimal point
            number_of_credits=float(first)
            set_of_evidence_for_new_cover.add(f'number of credits={number_of_credits}')
        else:
            print("Unexpected problem in parsing number of credits")

    if number_of_credits:
        if number_of_credits > 30.0:
            set_of_errors.add(f'Unexpectedly large number of credits({number_of_credits})')
        if Verbose_Flag:
            print(f'credits={number_of_credits}')
    print("cycle={}".format(cycle))
    return cycle

# the following is based upon https://www.kth.se/en/student/studier/examen/huvudomraden-i-kandidat-och-magisterexamina-pa-kth-1.2239
valid_major_subjects={1: {'eng': ['Technology', 'Architecture'],
                          'swe': ['teknik', 'arkitektur']},
                      2: {'eng': ['Architecture',
                                  'Biotechnology',
                                  'Computer Science and Engineering',
                                  'Electrical Engineering',
                                  'Industrial Management',
                                  'Information and Comunication Technology',
                                  'Chemical Science and Engineering',
                                  'Mechanical Engineering',
                                  'Mathematics',
                                  'Material Science and Engingeering',
                                  'Medical Engineering',
                                  'Environmental Engineering',
                                  'The Built Environment',
                                  'Technology and Economics',
                                  'Technology and Health',
                                  'Technology and Learning'
                                  'Technology and Management',
                                  'Engineering Physics'
                                  ],
                          'swe': ['arkitektur',
                                  'bioteknik',
                                  'datalogi och datateknik'
                                  'elektroteknik',
                                  'industriell ekonomi',
                                  'informations- och kommunikationsteknik',
                                  'kemiteknik',
                                  'maskinteknik',
                                  'matematik',
                                  'materialteknik',
                                  'medicinsk teknik',
                                  'miljöteknik',
                                  'samhällsbyggnad',
                                  'teknik och ekonomi',
                                  'teknik och hälsa',
                                  'teknik och lärande',
                                  'teknik och management'
                                  'teknisk fysik'
                                  ]}
                      }


valid_subjects_with_learning={1: {'eng': ['Technology and Learning',
                                          'Mathematics and Learning',
                                          'Physics and Learning',
                                          'Chemistry and Learning'
                                          ],
                                  'swe': ['teknik och lärande',
                                          'matematik och lärande',
                                          'fysik och lärande',
                                          'kemi och lärande'
                                          ]
                                  },
                              2: {'eng': [],
                                  'swe': []
                                  }
                              }

cover_place_x=39.0
cover_place_y=38.0
degree_str_x=74.0 
degree_str_y=669.0

def process_element(o: Any):
    last_x_offset=None
    last_x_width=None
    last_y_offset=None            # y_offset of text characters

    if isinstance(o, LTTextBoxHorizontal):
        for text_line in o:
            if hasattr(text_line, 'bbox'):
                last_x_offset=text_line.bbox[0]
                last_y_offset=text_line.bbox[1]
                last_x_width=text_line.bbox[2]-text_line.bbox[0]
            print(f'text_line={text_line}')
            if hasattr(text_line, 'size'):
                font_size=text_line.size
            else:
                font_size=0
            if isinstance(text_line, LTAnno):
                print("found an LTAnno")

            # if isinstance(text_line, LTChar):
            #     print("fount an LTChar")
            # elif isinstance(text_line, LTAnno):
            #     print("fount an LTAnno")
            # else:
            #     for character in text_line:
            #         if isinstance(character, LTChar):
            #             font_size=character.size
        extracted_data.append([font_size, last_x_offset, last_y_offset, last_x_width, (o.get_text())])

        #LTTextBoxHorizontal          39  38  131 46   Stockholm, Sweden, 2022
        #LTTextLineHorizontal       39  38  131 46   Stockholm, Sweden, 2022

        if abs(o.bbox[0]-cover_place_x) < 2.0 and abs(o.bbox[1]-cover_place_y) < 2.0:
            place=o.get_text()
            check_cover_place_and_year(place)

        #LTTextBoxHorizontal          74  669 358 681  Degree Project in Computer Science and Engineering
        #LTTextLineHorizontal       74  669 358 681  Degree Project in Computer Science and Engineering
        if abs(o.bbox[0]-degree_str_x) < 5.0 and abs(o.bbox[1]-degree_str_y) < 2.0:
            dp=o.get_text()
            english_dp='Degree Project in'
            idx=dp.find(english_dp)
            if idx >= 0:
                set_of_evidence_for_new_cover.add("English major subject")
                major_subject=dp[len(english_dp)+1:].strip()

            english_dp_error_in_capitalization='Degree project in'
            idx=dp.find(english_dp_error_in_capitalization)
            if idx >= 0:
                set_of_evidence_for_new_cover.add("English major subject")
                major_subject=dp[len(english_dp)+1:].strip()
                set_of_errors.add('Case error in "Project"')


            swedish_dp='Examensarbete inom'
            idx=dp.find(swedish_dp)
            if idx >= 0:
                set_of_evidence_for_new_cover.add("Swedish major subject")
                major_subject=dp[len(swedish_dp)+1:].strip()

        check_for_cycle_and_credits_element(o)

    elif isinstance(o, LTTextContainer):
        print("element is LTTextContainer")
        for text_line in o:
            print(f'text_line={text_line}')
            if isinstance(text_line, LTAnno):
                print("found an LTAnno")
            else:
                font_size=text_line.size
                print("font_size of text_line={}".format(text_line.size))
            if hasattr(text_line, 'bbox'):
                last_x_offset=text_line.bbox[0]
                last_y_offset=text_line.bbox[1]
                last_x_width=text_line.bbox[2]-text_line.bbox[0]
            # if isinstance(text_line, LTChar):
            #     print("found an LTChar")
            #     font_size=text_line.size
            # elif isinstance(text_line, LTAnno):
            #     print("found an LTAnno")
            # else:
            #     for character in text_line:
            #         if isinstance(character, LTChar):
            #             font_size=character.size
        extracted_data.append([font_size, last_x_offset, last_y_offset, last_x_width, (o.get_text())])
    elif isinstance(o, LTLine): #  a line
        check_for_cover_line_element(o)
    elif isinstance(o, LTFigure):
        if isinstance(o, Iterable):
            for i in o:
                process_element(i)
    elif isinstance(o, LTImage):
        check_for_logo_or_logotype(o)
        
    elif isinstance(o, LTChar):
        print("found LTChar: {}".format(o.get_text()))
        if hasattr(o, 'bbox'):
            last_x_offset=o.bbox[0]
            last_y_offset=o.bbox[1]
            last_x_width=o.bbox[2]-o.bbox[0]
            font_size=o.size
        extracted_data.append([font_size, last_x_offset, last_y_offset, last_x_width, (o.get_text())])
    elif isinstance(o, LTAnno):
        print("fount an LTAnno")
    elif isinstance(o, LTCurve): #  a curve
        print("found an LTCurve")
    else:
        print(f'unprocessed element: {o}')
        if isinstance(o, Iterable):
            for i in o:
                process_element(i)


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global set_of_errors
    global set_of_evidence_for_new_cover
    global extracted_data
    global cycle

    argp = argparse.ArgumentParser(description="check_for_new_cover.py: Check the thesis PDF file to see if it OK")

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
    set_of_evidence_for_new_cover=set()
    major_subject=None            # the major subject
    cycle=None                    # the cycle number
    place=None                    # the place from the cover
    font_size=None                # the latest font size
    last_x_offset=None
    last_x_width=None
    last_y_offset=None            # y_offset of text characters

    for page in extract_pages(filename, page_numbers=[0], maxpages=1):
        show_ltitem_hierarchy(page)

        print(page)
        for element in page:
            print(f'{element}')
            process_element(element)
            
    if Verbose_Flag:
        print("extracted_data: {}".format(extracted_data))
    # Example of an old cover:
    # extracted_data: [[10.990000000000009, 'DEGREE PROJECT  COMPUTER SCIENCE AND ENGINEERING,\nSECOND CYCLE, 30 CREDITS\nSTOCKHOLM SWEDEN2021\n, \n'], [10.990000000000009, 'IN \n'], [19.99000000000001, 'title\n'], [16.00999999999999, 'author in caps\n'], [10.989999999999995, 'KTH ROYAL INSTITUTE OF TECHNOLOGY\nSCHOOL OF ELECTRICAL ENGINEERING AND COMPUTER SCIENCE\n'], [10.989999999999995, ' \n']]

    old_size=-1
    size=None
    current_string=''
    first_x_offset=None
    last_x_offset=None
    last_x_width=None
    last_y_offset=None
    last_size=None
    new_extracted_data=[]

    # collect individual characters and build into string - adding spaces as necessary
    for item in extracted_data:
        if isinstance(item, list):
            if len(item) == 5:
                size, current_x_offset, current_y_offset, current_x_width, txt = item
                if Verbose_Flag:
                    print(f'{current_x_offset},{current_y_offset} {size} {txt}')
                if not last_size:
                    last_size=size
                if not first_x_offset:
                    first_x_offset=current_x_offset
                if not last_y_offset:
                    last_y_offset=current_y_offset
                if rough_comparison(last_y_offset, current_y_offset):
                    if Verbose_Flag:
                        print(f'{txt} {current_x_offset} {last_x_offset} {last_x_width}')
                    if not last_x_offset:
                        last_x_offset=current_x_offset+current_x_width
                        last_x_width=current_x_width
                        current_string=current_string+txt
                        if Verbose_Flag:
                            print("direct insert current_string={}".format(current_string))
                    elif current_x_offset > (last_x_offset+0.2*last_x_width): # just a little faster than adjact characters
                        if Verbose_Flag:
                            print("last_x_offset+last_x_width={}".format(last_x_offset, last_x_width))
                        current_string=current_string+' '+txt
                        if Verbose_Flag:
                            print("inserted space current_string={}".format(current_string))
                        last_x_offset=current_x_offset+current_x_width
                        last_x_width=current_x_width
                    else:
                        current_string=current_string+txt
                        if Verbose_Flag:
                            print("second direct insert current_string={}".format(current_string))
                        last_x_offset=current_x_offset+current_x_width
                        last_x_width=current_x_width
                else:
                    if last_x_offset:
                        new_extracted_data.append([last_size, first_x_offset, last_y_offset, last_x_offset-first_x_offset, current_string])
                    else:
                        new_extracted_data.append([last_size, first_x_offset, last_y_offset, 0, current_string])
                        if Verbose_Flag:
                            print(f'current_string={current_string} and no last_x_offset')
                    current_string=""+txt
                    first_x_offset=current_x_offset
                    last_y_offset=current_y_offset
                    last_x_offset=None
                    last_x_width=None
                    last_size=None
    
    if last_x_offset:
        new_extracted_data.append([size, first_x_offset, current_y_offset, last_x_offset-first_x_offset, current_string])
    else:
        print(f'current_string={current_string} and no last_x_offset')

    print("new_extracted_data={}".format(new_extracted_data))

    extracted_data=new_extracted_data
    for item in extracted_data:
        if isinstance(item, list):
            if len(item) == 5:
                size, current_x_offset, current_y_offset, current_x_width, txt = item
                print(f'{current_x_offset},{current_y_offset} {size} {txt}')

                if size < 11 and txt.find('KTH ROYAL INSTITUTE OF TECHNOLOGY') >= 0 and txt.find('SCHOOL OF ') >= 0:
                    set_of_errors.add("Found old cover with school name")
                if size < 8.1 and txt.find('ELECTRICAL ENGINEERING AND COMPUTER SCIENCE') >= 0:
                    set_of_errors.add("Found old cover with school name")

                if check_main_subject_area(txt):
                    set_of_errors.add("Found error in cover with stated specialization")

                txt=txt.strip()
                if abs(current_x_offset-74) < 5.0 and abs(current_y_offset-669) < 2.0:
                    dp=txt
                    english_dp='Degree Project in'
                    idx=dp.find(english_dp)
                    if idx >= 0:
                        set_of_evidence_for_new_cover.add("English major subject")
                        major_subject=dp[len(english_dp)+1:].strip()

                    swedish_dp='Examensarbete inom'
                    idx=dp.find(swedish_dp)
                    if idx >= 0:
                        set_of_evidence_for_new_cover.add("Swedish major subject")
                        major_subject=dp[len(swedish_dp)+1:].strip()


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


                if txt.find('DEGREE PROJECT') >= 0:
                    if txt.isupper():
                        set_of_errors.add("Case error in Degree project line - it appears to be in all uppercase")
                    else:
                        set_of_errors.add("Case error in Degree project line")
                    
                # if size < 11 and (txt.find('cycle') >= 0 or txt.find('Cycle') >= 0):
                #     print(f'cycle line at {current_x_offset},{current_y_offset}')
                if abs(current_x_offset-cycle_x) < 5.0 and abs(current_y_offset-cycle_y) < 12.0:
                    check_for_cycle_and_credits(txt)
                    if txt.find("Second cycle 120  credits") >= 0:
                        set_of_errors.add("Found error in cover incorrect number of credits")


                if abs(current_x_offset-39) < 2.0 and abs(current_y_offset-38) < 3.0:
                    check_cover_place_and_year(txt)

    duplicate_place= -1
    for item in extracted_data:
        if isinstance(item, list):
            if len(item) == 5:
                size, current_x_offset, current_y_offset, current_x_width, txt = item

                if txt.find('Stockholm, Sverige') >= 0:
                    duplicate_place=duplicate_place+1 
                if txt.find('Stockholm, Sverige') >= 0:
                    duplicate_place=duplicate_place+1 
    if duplicate_place > 1:
        set_of_errors.append("Found error in cover with repeated Stockholm and date ")

    if major_subject:
        print("Major subject: {}".format(major_subject))
        if cycle and cycle in [1,2]:
            if cycle == 1:
                if "English 1st cycle" in set_of_evidence_for_new_cover:
                    if major_subject in valid_major_subjects[cycle]['eng']:
                        set_of_evidence_for_new_cover.add('valid major subject')
                    elif major_subject in valid_subjects_with_learning[cycle]['eng']:
                        set_of_evidence_for_new_cover.add('valid major subject with learning')
                    else:
                        set_of_errors.add(f'Invalid first cycle major subject: {major_subject}')
                elif "Swedish 1st cycle" in set_of_evidence_for_new_cover:
                    if major_subject in valid_major_subjects[cycle]['swe']:
                        set_of_evidence_for_new_cover.add('valid major subject')
                    elif major_subject in valid_subjects_with_learning[cycle]['swe']:
                        set_of_evidence_for_new_cover.add('valid major subject with learning')
                    else:
                        set_of_errors.add(f'Invalid first cycle major subject: {major_subject}')
                else:
                    print(f'Unhandled case of checking a first cycle major subject: {major_subject}')
            elif cycle == 2:
                if "English 2nd cycle" in set_of_evidence_for_new_cover:
                    if major_subject in valid_major_subjects[cycle]['eng']:
                        set_of_evidence_for_new_cover.add('valid major subject')
                    else:
                        set_of_errors.add(f'Invalid second cycle major subject: {major_subject}')
                elif "Swedish 2nd cycle" in set_of_evidence_for_new_cover:
                    if major_subject in valid_major_subjects[cycle]['swe']:
                        set_of_evidence_for_new_cover.add('valid major subject')
                    else:
                        set_of_errors.add(f'Invalid second cycle major subject: {major_subject}')
                else:
                    print(f'Unhandled case of checking a second cycle major subject: {major_subject}')
            else:
                print(f'Unhandled case for cycle={cycle}')
        else:
            print(f"Unhandled case for cycle={cycle}")


    if len(set_of_evidence_for_new_cover) > 0:
        print("set_of_evidence_for_new_cover: {}".format(set_of_evidence_for_new_cover))



    if len(set_of_errors):
        for e in set_of_errors:
            print("Error: {}".format(e))



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

