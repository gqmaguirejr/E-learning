#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./process_degree_project_proposal.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
#
# Purpose: Extract author information (especially e-mail address) and working title from a degree project proposal that used the LaTeX template
# Write this information to a spreadsheet (the name of which can be specified on the command line).
#
# Example:
# For a single PDF file:
# ./process_degree_project_proposal.py --pdf ddddddd-FULLTEXT01.pdf
#
# For all the PDF files in a directory
# ./process_degree_project_proposal.py --dir xxxxxx
#
#
# To get the correct pdfminer package
# pip install pdfminer.six
#
# 2021-08-09 G. Q. Maguire Jr.
#
# Based on the earlier find_back_cover_page.py
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

# to parse date
from dateutil.parser import parse

# Use datetime() to convert rather that the old pd.datetime()
from datetime import datetime

# Use Python Pandas to create XLSX files
import pandas as pd

import xlsxwriter

#from bs4 import BeautifulSoup

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
        return ''.join(f'{i:<8.2f}' for i in o.bbox)
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


def process_file(filename):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    #
    global found_author_name
    global found_email_address
    global found_working_title
    #

    pages=[]
    
    page_index = -1
    try:
        for page in extract_pages(filename):
            page_index=page_index+1

            if Verbose_Flag:
                print(f'Processing page={page_index}')

            if testing:
                show_ltitem_hierarchy(page)
                print(page)
                continue

            pages.append(page)


    except (PDFNoValidXRef, PSEOF, pdfminer.pdfdocument.PDFNoValidXRef, pdfminer.psparser.PSEOF) as e:
        print(f'Unexpected error in processing the PDF file: {filename} with error {e}')
        return False
    except Exception as e:
        print(f'Error in PDF extractor: {e}')
        return False

    print("Total number of PDF pages={}".format(len(pages)))

    found_left_part_of_page_heading = False
    found_center_part_of_page_heading = False
    found_right_part_of_page_heading = False
    found_working_title = False
    working_title=[]
    found_email_address = False
    email_address=None
    authorname=None
    date_from_heading=None

    page_index = -1
    for page in pages:
        page_index=page_index+1
        if page_index >= 1:
            if len(working_title) == 1:
                working_title=working_title[0].replace('\n', ' ')
            return {
                'authorname': authorname,
                'email': email_address,
                'working_title': working_title,
                'date': date_from_heading,
                'proposal length': len(pages)
            }
        print("process page_index={}".format(page_index))
        for element in page:
            if Verbose_Flag:
                print(f'{element}')

            if isinstance(element, LTTextBoxHorizontal):
                if hasattr(element, 'bbox'):
                    str=element.get_text()
                    if Verbose_Flag:
                        print("LTTextBoxHorizontal str={}".format(str))
                    # look for the page heading
                    # look for the left page heading
                    if not found_left_part_of_page_heading and element.bbox[1] > 820.0 and element.bbox[0] < 45.0:
                        if str.find('Degree project proposal for') >= 0:
                            found_left_part_of_page_heading = True
                            if Verbose_Flag:
                                print('left part of page heading: {}'.format(str))
                            continue
                    if not found_center_part_of_page_heading and element.bbox[1] > 820.0 and element.bbox[0] > 45.0 and element.bbox[0] < 330.0:
                        if str.find('Project proposal') >= 0:
                            found_center_part_of_page_heading = True
                            if Verbose_Flag:
                                print('center part of page heading: {}'.format(str))
                            continue

                    if not found_right_part_of_page_heading and element.bbox[1] > 820.0 and element.bbox[0] > 350.0:
                        if len(str) > 0:
                            found_right_part_of_page_heading = True
                            ## process date
                            date_from_heading=parse(str.strip('\n'))
                            if Verbose_Flag:
                                print('right part of page heading: {}'.format(str))
                            continue

                    # look for the working title - collecting the lines of text until we hit an e-mail address with "@"
                    if not found_working_title and not found_email_address and element.bbox[1] < 820.0:
                        # look for the e-mail address
                        if str.find('@') > 0:
                            found_email_address = True
                            author_and_email=str.split('\n')
                            if Verbose_Flag:
                                print(f'{author_and_email}=')
                            authorname=author_and_email[0]
                            if Verbose_Flag:
                                print('authorname: {}'.format(authorname))
                            email_address=author_and_email[1]
                            if Verbose_Flag:
                                print('email_address: {}'.format(email_address))
                            found_working_title = True # set this flag to stop collecting the title
                            continue
                        else:
                            working_title.append(str)
                            if Verbose_Flag:
                                print('working_title collected: {}'.format(str))
                            continue
                            
    return None



def write_to_spreadsheet(list_of_extracted_data):
    global Verbose_Flag
    if args["spreadsheet"]:
        spreadsheet_name=args["spreadsheet"]
        if not spreadsheet_name.endswith('.xlsx'):
            print("must give the name of a .xlsx spreadsheet file")
            return

        extracted_df=pd.json_normalize(list_of_extracted_data)
        # convert the datetime column to a date column
        extracted_df.date=extracted_df.date.dt.date
        writer = pd.ExcelWriter(spreadsheet_name, engine='xlsxwriter')
        extracted_df.to_excel(writer, sheet_name='WithCoverInfo')
        workbook = writer.book

        # set up the desired date format for the spreadsheet
        date_fmt_dict={'num_format':'yyyy-mm-dd', 'bold': True}
        date_fmt = workbook.add_format(date_fmt_dict)
        worksheet=workbook.get_worksheet_by_name('WithCoverInfo')

        # add some annotation in cell 0,0
        worksheet.write(0, 0, 'extracted data') 

        # Get the dimensions of the dataframe.
        (max_row, max_col) = extracted_df.shape

        # compute what spreadsheet column the date is in
        date_column=column_name_to_excel_letter(extracted_df, 'date')

        # format in the desired date format
        worksheet.set_column(f'{date_column}2:{date_column}{max_row+1}', 16, date_fmt)

        # Close the Pandas Excel writer and output the Excel file.
        writer.close()
    return

def column_name_to_excel_letter(df, column_name):
    # The +1 is needed because the first column is an index and has no column heading
    col_no = df.columns.get_loc(column_name) + 1
    return xlsxwriter.utility.xl_col_to_name(col_no)

def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global args
    
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

    argp.add_argument('-d', '--dir',
                      type=str,
                      default=".",
                      help="read PDF files in the dpescified directory"
                      )

    argp.add_argument('-s', '--spreadsheet',
                      type=str,
                      default=False,
                      help="spreadsheet file"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]
    testing=args["testing"]

    if not args["dir"]:
        filename=args["pdf"]
        if Verbose_Flag:
            print("filename={}".format(filename))

        extracted_data=process_file(filename)
        if not extracted_data:
            print("No data was extracted")
            return -1
        else:
            print("extracted_data: {}".format(extracted_data))
            if args["spreadsheet"]:
                spreadsheet_name=args["spreadsheet"]
                if not spreadsheet_name.endswith('.xlsx'):
                    print("must give the name of a .xlsx spreadsheet file")
                    return

                list_of_extracted_data=[extracted_data]
                write_to_spreadsheet(list_of_extracted_data)

            return
    else:
        list_of_extracted_data=[]
        # process the pdf files in the specified directory
        for filename in os.listdir(args["dir"]):
            f = os.path.join(args["dir"], filename)
            # checking if it is a file
            if os.path.isfile(f):
                print(f)
                extracted_data=process_file(f)
                extracted_data.update({'filename': filename})
                print("extracted data for {0}: {1}".format(f, extracted_data))
                list_of_extracted_data.append(extracted_data)

        if len(list_of_extracted_data) > 0:
            write_to_spreadsheet(list_of_extracted_data)
        return

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


