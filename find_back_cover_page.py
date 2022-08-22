#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./find_back_cover_page.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
#
# Purpose: Check for and determina the page within the PDF file where the back cover is
#          Note that this also checks for old covers.
#
# Example:
# For a single PDF file:
# ./find_back_cover_page.py --pdf ddddddd-FULLTEXT01.pdf
#
# For all the PDF files in the spreadsheet
# ./find_back_cover_page.py -s ../eecs-2022with_coverinfo.xlsx
# Note that this can be fund after updating the original spreadsheet with cover information
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

import requests, time
import pprint

# Use Python Pandas to create XLSX files
import pandas as pd

from bs4 import BeautifulSoup

import faulthandler

# from pdfminer.converter import TextConverter, HTMLConverter
# from pdfminer.layout import LAParams
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
# from pdfminer.pdfpage import PDFPage
# from pdfminer.pdfparser import PDFParser

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTLine, LAParams, LTFigure, LTImage, LTTextLineHorizontal, LTTextBoxHorizontal, LTCurve, LTRect
from typing import Iterable, Any
from pdfminer.layout import LAParams, LTTextBox, LTText, LTChar, LTAnno
import pdfminer.psparser
from pdfminer.pdfdocument import PDFNoValidXRef
from pdfminer.psparser import PSEOF

global item_count
def count_ltitem_hierarchy(o: Any, depth=0):
    """Show location and text of LTItem and all its descendants"""
    global item_count

    name=get_indented_name(o, depth)
    #print("name={}".format(name))
    item_count=item_count+1
    box=get_optional_bbox(o)
    txt=get_optional_text(o)

    if isinstance(o, Iterable):
        for i in o:
            count_ltitem_hierarchy(i, depth + 1)
    return

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
        return ''.join(f'{i:<6.2f}' for i in o.bbox)
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


global found_TRITA_number
global found_www_url
global found_old_back_cover_image
global found_new_back_cover_line
global found_back_cover_page

# old back cover
  # LTTextBoxHorizontal          34  168 141 178  TRITA -EECS-EX-2022:18
  #   LTTextLineHorizontal       34  168 141 178  TRITA -EECS-EX-2022:18
  # LTTextBoxHorizontal          37  65  93  76   www.kth.se
  #   LTTextLineHorizontal       37  65  93  76   www.kth.se

back_cover_old_TRITA_place_x=34.010
back_cover_old_TRITA_place_y=167.625

back_cover_old_www_place_x=37.0
back_cover_old_www_place_y=65.0

# LTFigure                     0   1   595 132  
#   LTImage                    0   1   595 132  

back_cover_old_image_place_x=0
back_cover_old_image_place_y=1
back_cover_old_image_place_width=595
back_cover_old_image_place_height=131 # not the upper corner is 1 pt higher, due to the offset

# new cover
# <LTTextBoxHorizontal(0) 38.685,61.240,161.410,72.349 'TRITA-EECS-EX- 2022:192\n'>
# <LTTextBoxHorizontal(1) 38.685,36.457,78.989,44.427 'www.kth.se\n'>
# <LTLine 19.427,33.375,527.528,33.375>
back_cover_new_TRITA_place_x=38.685
back_cover_new_TRITA_place_y=61.240
back_cover_new_www_place_x=38.685
back_cover_new_www_place_y=36.457
back_cover_new_line_place_x=19.427
back_cover_new_line_place_y=33.375
back_cover_new_line_place_width=510
#(<LTLine 61.960,30.173,549.989,30.173>)

# In some cases the TRITA and URL may be set as individual letters, hence check the extracted_data
# For exampe:
extracted_data: [[9.407799999999995, 63.512122, 59.986007619999995, 5.738757999999997, 'T'], [9.407799999999995, 69.25088, 59.986007619999995, 6.7924316000000005, 'R'], [9.407799999999995, 76.0433116, 59.986007619999995, 2.605960600000003, 'I'], [9.407799999999995, 78.6492722, 59.986007619999995, 5.738758000000004, 'T'], [9.407799999999995, 84.3880302, 59.986007619999995, 6.265594800000002, 'A'], [9.407799999999995, 90.65362499999999, 59.986007619999995, 2.605960600000003, ' '], [9.407799999999995, 93.26617105999999, 59.986007619999995, 5.2307368000000025, '–'], [9.407799999999995, 98.49690786, 59.986007619999995, 2.605960600000003, ' '], [9.407800000000002, 101.19224255999998, 58.584245419999995, 5.343630399999995, 'E'], [9.407800000000002, 106.53587295999998, 58.584245419999995, 5.343630399999995, 'E'], [9.407800000000002, 111.87950335999999, 58.584245419999995, 6.256186999999997, 'C'], [9.407800000000002, 118.13569035999998, 58.584245419999995, 4.459297199999995, 'S'], [9.407800000000002, 122.59498755999998, 58.584245419999995, 3.349176799999995, '-'], [9.407800000000002, 125.94416435999997, 58.584245419999995, 5.343630399999995, 'E'], [9.407800000000002, 131.28779475999997, 58.584245419999995, 6.152701199999996, 'X'], [9.407800000000002, 137.44049595999996, 58.584245419999995, 3.3491768000000093, '-'], [9.407800000000002, 140.78967275999997, 58.584245419999995, 4.515744000000012, '2'], [9.407800000000002, 145.30541675999999, 58.584245419999995, 4.515744000000012, '0'], [9.407800000000002, 149.82116075999997, 58.584245419999995, 4.515744000000012, '2'], [9.407800000000002, 154.33690475999998, 58.584245419999995, 4.515744000000012, '2'], [9.407800000000002, 158.85264875999997, 58.584245419999995, 2.1449784000000136, ':'], [9.407800000000002, 160.99762715999998, 58.584245419999995, 4.515744000000012, '1'], [9.407800000000002, 165.51337115999996, 58.584245419999995, 4.515744000000012, '0'], [9.407800000000002, 170.02911515999995, 58.584245419999995, 4.515744000000012, '5'], [7.526240000000001, 63.512122, 34.41748878, 5.433945279999996, 'w'], [7.526240000000001, 68.87080488, 34.41748878, 5.433945280000003, 'w'], [7.526240000000001, 74.31980263999999, 34.41748878, 5.433945280000003, 'w'], [7.526240000000001, 79.7688004, 34.41748878, 2.084768479999994, '.'], [7.526240000000001, 81.8385164, 34.41748878, 3.7631200000000007, 'k'], [7.526240000000001, 85.60163639999999, 34.41748878, 2.084768479999994, 't'], [7.526240000000001, 87.6713524, 34.41748878, 4.184589439999996, 'h'], [7.526240000000001, 91.8107844, 34.41748878, 2.084768479999994, '.'], [7.526240000000001, 93.8805004, 34.41748878, 3.7631200000000007, 's'], [7.526240000000001, 97.6436204, 34.41748878, 4.184589439999996, 'e']]
def check_extracted_data_for_TRITA_and_URL():
    global extracted_data
    global found_TRITA_number
    global found_www_url

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
        if Verbose_Flag:
            print(f'current_string={current_string} and no last_x_offset')

    if Verbose_Flag:
        print("new_extracted_data={}".format(new_extracted_data))

    extracted_data=new_extracted_data
    found_KTH_English_name=False
    for item in extracted_data:
        if isinstance(item, list):
            if len(item) == 5:
                size, current_x_offset, current_y_offset, current_x_width, txt = item
                if Verbose_Flag:
                    print(f'{current_x_offset},{current_y_offset} {size} {txt}')

                txt=txt.strip()
                #extracted_data: [[9.407799999999995, 63.512122, 59.986007619999995, 37.59074646, 'TRITA – '], [9.407800000000002, 101.19224255999998, 58.584245419999995, 73.35261659999998, 'EECS-EX-2022:105'], [7.526240000000001, 63.512122, 34.41748878, 38.31608784, 'www.kth.se']]
                
                # old back cover
                if abs(current_x_offset-back_cover_old_TRITA_place_x) < 2.0 and\
                   abs(current_y_offset-back_cover_old_TRITA_place_y) < 2.0:
                    if txt.find('TRITA') >= 0:
                        found_TRITA_number = True
                        print('found_TRITA_number')
                elif abs(current_x_offset-back_cover_old_www_place_x) < 2.0 and\
                     abs(current_y_offset-back_cover_old_www_place_y) < 2.0:
                    if txt.find('www.kth.se') >= 0:
                        found_www_url = True
                        print('found_www_url')
                # new back cover
                if abs(current_x_offset-back_cover_new_TRITA_place_x) < 2.0 and\
                   abs(current_x_offset-back_cover_new_TRITA_place_y) < 2.0:
                    if txt.find('TRITA') >= 0:
                        found_TRITA_number = True
                        print('found_TRITA_number')
                elif abs(current_x_offset-back_cover_new_www_place_x) < 2.0 and\
                     abs(current_y_offset-back_cover_new_www_place_y) < 2.0:
                    if txt.find('www.kth.se') >= 0:
                        found_www_url = True
                        print('found_www_url')

                if not found_TRITA_number and txt.find('TRITA') >= 0:
                    print("'TRITA' present, but not where expected: {0},{1} width {2} and size={3}".format(current_x_offset, current_y_offset, current_x_width, size))
                    found_TRITA_number = True

                if not found_www_url and txt.find('www.kth.se') >= 0:
                    print("URL present, but not where expected: {0},{1} width {2} and size={3}".format(current_x_offset, current_y_offset, current_x_width, size))
                    found_www_url = True

                # T\nR\nI\nT\n E\nE\nC\nS\n-\nE\nX\n'
                txt=txt.replace('\n', '')
                if not found_TRITA_number and txt.find('TRIT') >= 0:
                    print("'TRITA' present - in form with new lines in it, found {0},{1} width {2} and size={3}".format(current_x_offset, current_y_offset, current_x_width, size))
                    found_TRITA_number = True

                # 'w\nw\nw\n.\nk\nt\nh\n.\ns\ne\n'
                txt=txt.replace('\n', '')
                if not found_www_url and txt.find('www.kth.se') >= 0:
                    print("URL present - in form with new lines in it, found at {0},{1} width {2} and size={3}".format(current_x_offset, current_y_offset, current_x_width, size))
                    found_www_url = True
    
def process_element(o: Any, pgnumber):
    global Verbose_Flag
    global extracted_data
    global found_TRITA_number
    global found_www_url
    global found_old_back_cover_image
    global found_new_back_cover_line
    global image_on_page

    last_x_offset=None
    last_x_width=None
    last_y_offset=None            # y_offset of text characters

    if Verbose_Flag:
        print("Inside process_element ({})".format(o))
    if isinstance(o, LTTextBoxHorizontal):
        if hasattr(o, 'bbox'):
            str=o.get_text()
            # old back cover
            # LTTextBoxHorizontal          34  168 141 178  TRITA -EECS-EX-2022:18
            if abs(o.bbox[0]-back_cover_old_TRITA_place_x) < 2.0 and\
               abs(o.bbox[1]-back_cover_old_TRITA_place_y) < 2.0:
                if str.find('TRITA') >= 0:
                    found_TRITA_number = True
                    print('found_TRITA_number')
            # LTTextBoxHorizontal          37  65  93  76   www.kth.se
            elif abs(o.bbox[0]-back_cover_old_www_place_x) < 2.0 and\
                 abs(o.bbox[1]-back_cover_old_www_place_y) < 2.0:
                if str.find('www.kth.se') >= 0:
                    found_www_url = True
                    print('found_www_url')
            # new back cover
            if abs(o.bbox[0]-back_cover_new_TRITA_place_x) < 2.0 and\
               abs(o.bbox[1]-back_cover_new_TRITA_place_y) < 2.0:
                if str.find('TRITA') >= 0:
                    found_TRITA_number = True
                    print('found_TRITA_number')
            # LTTextBoxHorizontal          37  65  93  76   www.kth.se
            elif abs(o.bbox[0]-back_cover_new_www_place_x) < 2.0 and\
                 abs(o.bbox[1]-back_cover_new_www_place_y) < 2.0:
                if str.find('www.kth.se') >= 0:
                    found_www_url = True
                    print('found_www_url')

            if not found_TRITA_number and str.find('TRITA') >= 0:
                print("'TRITA' present, but not where expected: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))
                found_TRITA_number = True

            if not found_www_url and str.find('www.kth.se') >= 0:
                print("URL present, but not where expected: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))
                found_www_url = True

    elif isinstance(o, LTRect):
        # Note that this case as to be before the LTTextContainer case
        #LTRect                       37  32  556 33   
        if Verbose_Flag:
            print("element is LTRect")
        if hasattr(o, 'bbox'):
            if Verbose_Flag:
                print("found LTRect: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))
            if o.bbox[2] > 500.0 and o.bbox[1] <= 34.0 and o.bbox[3] <= 34.0:
                if abs(o.bbox[0]-o.bbox[2]) >= 490:
                    found_new_back_cover_line=pgnumber
                    print("found_new_back_cover_line: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))

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
        if hasattr(o, 'bbox'):
            if Verbose_Flag:
                print("found line: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))
                print("abs(o.bbox[0]-back_cover_new_line_place_x)={}".format(abs(o.bbox[0]-back_cover_new_line_place_x)))
                print("abs(o.bbox[1]-back_cover_new_line_place_y)={}".format(abs(o.bbox[1]-back_cover_new_line_place_y)))
                print("abs(o.bbox[0]-o.bbox[2])={}".format(abs(o.bbox[0]-o.bbox[2])))
                print("abs(o.bbox[1]-o.bbox[3])={}".format(abs(o.bbox[1]-o.bbox[3])))
            if abs(o.bbox[0]-back_cover_new_line_place_x)  < 25.0 and abs(o.bbox[1]-back_cover_new_line_place_y) < 12.0 and\
               abs(o.bbox[0]-o.bbox[2]) >= 490:
                found_new_back_cover_line=pgnumber
                print("found_new_back_cover_line: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))
                print("found_new_back_cover_line={}".format(found_new_back_cover_line))
            elif abs(o.bbox[1]-o.bbox[3]) < 1.0 and abs(o.bbox[1]) <= 34.0: # a horizontal line
                if abs(o.bbox[0]-o.bbox[2]) >= 400:
                    found_new_back_cover_line=pgnumber
                    print("possibly found_new_back_cover_line at unexpected position: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))
            elif abs(o.bbox[1]-o.bbox[3]) < 1.0 and abs(o.bbox[1]) < 65.0: # a horizontal line
                if abs(o.bbox[0]-o.bbox[2]) >= 400:
                    found_new_back_cover_line=pgnumber
                    print("possibly found_new_back_cover_line at unexpectedly high position: {0},{1} to {2},{3}".format(o.bbox[0], o.bbox[1], o.bbox[2], o.bbox[3]))
            else:
                return    
    elif isinstance(o, LTCurve): #  a curve
        # an old cover has the bottom draw with
        # LTCurve -0.690,0.280,600.669,104.470
        if Verbose_Flag:
            print("LTCurve: {}".format(o))

        if hasattr(o, 'bbox'):
            if Verbose_Flag:
                x1=int(o.bbox[0])
                y1=int(o.bbox[1])
                x2=int(o.bbox[2])
                y2=int(o.bbox[3])
                print(f'in checking LTCurve for old back cover - bbox: {x1},{y1} {x2},{y2}')
            #LTCurve: <LTCurve -0.690,0.280,600.669,104.470>
            if o.bbox[0]  < 0.0 and o.bbox[1] < 1.0 and o.bbox[2] > 600.0 and o.bbox[3] < 105.0:
                found_old_back_cover_image=pgnumber
                print('found_old_back_cover_image on page {0} - done as LTCurve at {1}'.format(pgnumber, o))
    elif isinstance(o, LTFigure):
        if isinstance(o, Iterable):
            for i in o:
                process_element(i, pgnumber)
    elif isinstance(o, LTImage):
        image_on_page=True
        if hasattr(o, 'bbox'):
            if Verbose_Flag:
                x1=int(o.bbox[0])
                y1=int(o.bbox[1])
                x2=int(o.bbox[2])
                y2=int(o.bbox[3])
                print(f'in checking for old back cover - bbox: {x1},{y1} {x2},{y2}')
            if abs(o.bbox[0]-back_cover_old_image_place_x)  < 2.0 and abs(o.bbox[1]-back_cover_old_image_place_x) < 2.0:
                if abs(o.bbox[2]-back_cover_old_image_place_width)  < 2.0 and abs((o.bbox[3]-o.bbox[1])-back_cover_old_image_place_height) < 2.0:
                    found_old_back_cover_image=pgnumber
                    print('found_old_back_cover_image')
                elif abs(o.bbox[2]-back_cover_old_image_place_width)  < 2.0 and o.bbox[3] < back_cover_old_image_place_height:
                    found_old_back_cover_image=pgnumber
                    print('found_old_back_cover_image - with unexpected height {}'.format(o.bbox[3]-o.bbox[1]))
                else:
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
    global found_TRITA_number
    global found_www_url
    global found_old_back_cover_image
    global found_new_back_cover_line
    global found_back_cover_page
    global item_count
    global image_on_page

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


    pages=[]
    
    page_index = -1
    try:
        for page in extract_pages(filename):
            page_index=page_index+1
            extracted_data=[]   # reinitialize this - so we can see the information on the last page processed

            if Verbose_Flag:
                print(f'Processing page={page_index}')

            if testing:
                show_ltitem_hierarchy(page)
                print(page)
                continue

            item_count=1
            count_ltitem_hierarchy(page, depth=0)
            #print("count_ltitem_hierarchy({0})={1}".format(page_index, item_count))
            pages.append(page)


    except (PDFNoValidXRef, PSEOF, pdfminer.pdfdocument.PDFNoValidXRef, pdfminer.psparser.PSEOF) as e:
        print(f'Unexpected error in processing the PDF file: {filename} with error {e}')
        return False
    except Exception as e:
        print(f'Error in PDF extractor: {e}')
        return False

    print("Total number of PDF pages={}".format(len(pages)))
    # reverse list of pages
    pages.reverse()
    found_back_cover_page=False
    found_old_back_cover_page=False
    found_old_back_cover_image=False
    found_new_back_cover_line=False
    found_TRITA_number = False
    found_www_url = False

    for page in pages:
        print("page_index={}".format(page_index))
        image_on_page=False
        for element in page:
            if Verbose_Flag:
                print(f'{element}')
            process_element(element, page_index)

        if not found_TRITA_number or not found_www_url:
            check_extracted_data_for_TRITA_and_URL()

        if found_TRITA_number:
            if found_www_url:
                if isinstance(found_new_back_cover_line, int):
                    found_back_cover_page=page_index
                    print("found new back cover on page {}".format(page_index))
                    return True
                elif found_old_back_cover_image:
                    found_back_cover_page=page_index
                    print("found old back cover on page {}".format(page_index))
                    return True
                elif image_on_page: # a page with both URL and TRITA number and in image is probably an old cover
                    found_old_back_cover_image=True
                    found_back_cover_page=page_index
                    print("found old back cover on page {}".format(page_index))
                    return True
                else:
                    print("despite both finding TRITA and www URL, did not find an image on page {}".format(page_index))
        page_index=page_index-1

    return True



                


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global set_of_errors
    global set_of_evidence_for_new_cover
    global extracted_data
    global cycle
    global found_old_back_cover_image
    global found_new_back_cover_line
    global found_back_cover_page

    argp = argparse.ArgumentParser(description='find_back_cover_page.py: FInd the back_cover page within the PDF file')

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

        if Verbose_Flag:
            print("extracted_data: {}".format(extracted_data))
        if found_back_cover_page:
            if found_old_back_cover_image:
                print("Found old back cover page at {0} in {1}".format(found_back_cover_page, filename))
            if found_new_back_cover_line:
                print("Found new back cover page at {0} in {1}".format(found_back_cover_page, filename))
            return found_back_cover_page
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


    # this column is used to record the page numer of the back cover
    diva_df['Back cover'] = pd.NaT
    diva_df['Back cover version'] = pd.NaT

    for idx, row in diva_df.iterrows():
        found_old_back_cover_image=False
        found_new_back_cover_line=False
        found_back_cover_page=False

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

            if found_back_cover_page:
                print("Found back cover at {0} in {1} by author(s) {2}".format(found_back_cover_page, filename, row['Name']))
                diva_df.loc[idx, 'Back cover'] = found_back_cover_page
                if found_old_back_cover_image:
                    diva_df.loc[idx, 'Back cover version'] = 'Old'
                    print("Old")
                if found_new_back_cover_line:
                    diva_df.loc[idx, 'Back cover version'] = 'New'
                    print("New")

        if args["testing"]:
            break

    # the following was inspired by the section "Using XlsxWriter with Pandas" on http://xlsxwriter.readthedocs.io/working_with_pandas.html
    # set up the output write
    output_spreadsheet_name=spreadsheet_name[:-5]+'with_back_cover_info.xlsx'
    writer = pd.ExcelWriter(output_spreadsheet_name, engine='xlsxwriter')
    diva_df.to_excel(writer, sheet_name='WithCoverInfo')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


