#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./process_degree_project_proposal-XMP.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
#
# Purpose: Extract author information (especially e-mail address), working title, keywords and other information
# from a degree project proposal that used the LaTeX template that has XMP embeded information
#
# Write this information to a spreadsheet (the name of which can be specified on the command line).
#
# Example:
# For a single PDF file:
# ./process_degree_project_proposal-XMP.py --pdf ddddddd-FULLTEXT01.pdf
#
# ./process_degree_project_proposal-XMP.py -v -p proposals_for_testing/Degree_project_proposal_template_multiline_title.pdf -s proposals-processes-date-a.xlsx
#
# For all the PDF files in a directory
# ./process_degree_project_proposal-XMP.py --dir xxxxxx
#
# ./process_degree_project_proposal-XMP.py --dir proposals_for_testing -s proposals-processes-date-a.xlsx
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

# for getting the metadata
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from xmp import xmp_to_dict


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

def process_file_with_XMP_info(filename):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    #
    global found_author_name
    global found_email_address
    global found_working_title
    #

    try:
        if Verbose_Flag:
            print(f'Processing file: {filename}')
        
        fp = open(filename, 'rb')

        parser = PDFParser(fp)

        doc = PDFDocument(parser)
        if Verbose_Flag:
            print(f'{doc=}')

        parser.set_document(doc)

        if Verbose_Flag:
            print(doc.info)        # The "Info" metadata
        if Verbose_Flag:
            print("doc.catalog={}".format(doc.catalog))

        res = resolve1(doc.catalog)
        if Verbose_Flag:
            print("res={}".format(res))

    except Exception as e:
        print(f'Error in PDF extractor: {e}')
        return False


    if 'Metadata' in doc.catalog:
        #metadata = resolve1(doc.catalog['Metadata']).get_data()
        metadata = resolve1(doc.catalog['Metadata']).get_data()
        if Verbose_Flag:
            print("metadata after get_data() = {}".format(metadata))
        return xmp_to_dict(metadata)

    print("Unable to extract metadata from {}".format(filename))
    return None

def fix_ModifyandMetadatTimestamps(df):
    for idx, row in df.iterrows():
        rm = row['xap.ModifyDate']
        if rm and rm.endswith('Z'):
            df.loc[idx, 'xap.ModifyDate']=datetime.strptime(rm, '%Y-%m-%dT%H:%M:%SZ')
        elif rm and '+' in rm:
            df.loc[idx, 'xap.ModifyDate']=datetime.strptime(rm, '%Y-%m-%dT%H:%M:%S%z')
        else:
            print(f'Unknow time format in row {idx} for xap.ModifyDate with value {rm}')

        rm = row['xap.MetadataDate']
        if rm and rm.endswith('Z'):
            df.loc[idx, 'xap.MetadataDate']=datetime.strptime(rm, '%Y-%m-%dT%H:%M:%SZ')
        elif rm and '+' in rm:
            df.loc[idx, 'xap.MetadataDate']=datetime.strptime(rm, '%Y-%m-%dT%H:%M:%S%z')
        else:
            print(f'Unknow time format in row {idx} for xap.MetadataDate with value {rm}')

def restoreBackslash(columns_to_process, df):
    for idx, row in df.iterrows():
        for c in columns_to_process:
            current_value=row[c]
            df.loc[idx, c]=current_value.replace('¢', '\\')
    return df

def write_to_spreadsheet(list_of_extracted_data):
    global Verbose_Flag
    if args["spreadsheet"]:
        spreadsheet_name=args["spreadsheet"]
        if not spreadsheet_name.endswith('.xlsx'):
            print("must give the name of a .xlsx spreadsheet file")
            return

        extracted_df=pd.json_normalize(list_of_extracted_data)
        # convert the datetime column to a date column
        extracted_df['xap.CreateDate']=pd.to_datetime(extracted_df['xap.CreateDate'], format=('%Y-%m-%dT%H:%M:%S'))
        # Note that the following have times ending in a Z, so we have to remove this
        fix_ModifyandMetadatTimestamps(extracted_df)
        extracted_df['xap.ModifyDate'] = extracted_df['xap.ModifyDate'].apply(lambda a: datetime.strftime(a,"%Y-%m-%d %H:%M:%S"))
        extracted_df['xap.ModifyDate'] = pd.to_datetime(extracted_df['xap.ModifyDate'])
        extracted_df['xap.MetadataDate'] = extracted_df['xap.MetadataDate'].apply(lambda a: datetime.strftime(a,"%Y-%m-%d %H:%M:%S"))
        extracted_df['xap.MetadataDate'] = pd.to_datetime(extracted_df['xap.MetadataDate'])

 
        writer = pd.ExcelWriter(spreadsheet_name, engine='xlsxwriter')
        columns_to_drop=[
            'dc.type',
            'rdf.Description',
            'rdf.Bag',
            'rdf.Seq',
            'rdf.Alt',
            'rdf.li',
            'http://www.aiim.org/pdfa/ns/extension/.schemas',
            'http://www.aiim.org/pdfa/ns/schema#.schema',
            'http://www.aiim.org/pdfa/ns/schema#.prefix',
            'http://www.aiim.org/pdfa/ns/schema#.namespaceURI',
            'http://www.aiim.org/pdfa/ns/schema#.property',
            'http://www.aiim.org/pdfa/ns/schema#.valueType',
            'http://www.aiim.org/pdfa/ns/property#.name',
            'http://www.aiim.org/pdfa/ns/property#.valueType',
            'http://www.aiim.org/pdfa/ns/property#.category',
            'http://www.aiim.org/pdfa/ns/property#.description',
            'http://www.aiim.org/pdfa/ns/type#.type',
            'http://www.aiim.org/pdfa/ns/type#.namespaceURI',
            'http://www.aiim.org/pdfa/ns/type#.prefix',
            'http://www.aiim.org/pdfa/ns/type#.description',
            'http://www.aiim.org/pdfa/ns/type#.field',
            'http://www.aiim.org/pdfa/ns/field#.name',
            'http://www.aiim.org/pdfa/ns/field#.valueType',
            'http://www.aiim.org/pdfa/ns/field#.description',
            'dc.format',
            'dc.source',
            'xapmm.DocumentID',
	    'xapmm.InstanceID',
	    'xapmm.VersionID',
            'xapmm.RenditionClass',
            'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/.CreatorContactInfo',
            'http://ns.adobe.com/xap/1.0/t/pg/.NPages',
            'http://prismstandard.org/namespaces/basic/3.0/.complianceProfile'
            ]
        extracted_df.drop(columns_to_drop,inplace=True,axis=1)

        # <rdf:li xml:lang="en-US">Background: "Place the background text here."</rdf:li>
        # <rdf:li xml:lang="en-GB">ResearchQuestion: "Put the research question here."</rdf:li>
        # <rdf:li xml:lang="en-BZ">Hypothesis: "Put the hypothesis here."</rdf:li>
        # <rdf:li xml:lang="en-CA">ResearchMethod: "Put the research method here."</rdf:li>
        # <rdf:li xml:lang="en-CB">BackgroundOfTheStudent: "Put the background of the student here."</rdf:li>
        # <rdf:li xml:lang="en-IE">ExternalSupervisor: "Put the external supervisor and company/organization here. If this is not applicable, say NA."</rdf:li>
        # <rdf:li xml:lang="en-JM">SuggestedExaminer: "Put the suggested examiner here; otherwise, say None."</rdf:li>
        # <rdf:li xml:lang="en-NZ">SuggestedSupervisor: "Put the suggested supervisor here; otherwise, say None."</rdf:li>
        # <rdf:li xml:lang="en-PH">Resources: "Put the resource information here."</rdf:li>
        # <rdf:li xml:lang="en-TT">Eligibility: "Put the eligibility information here."</rdf:li>
        # <rdf:li xml:lang="en-ZW">StudyPlanning: "Put the study planning information here."</rdf:li>

        columns_to_rename= {'dc.description.en-US': 'Background',
                            'dc.description.en-GB': 'Research Question',
                            'dc.description.en-BZ': 'Hypothesis',
                            'dc.description.en-CA': 'Research Method',
                            'dc.description.en-CB': 'Background of the Student',
                            'dc.description.en-IE': 'External Supervisor',
                            'dc.description.en-JM': 'Suggested Examiner',
                            'dc.description.en-NZ': 'Suggested Supervisor',
                            'dc.description.en-PH': 'Resources',
                            'dc.description.en-TT': 'Eligibility',
                            'dc.description.en-ZW': 'Study Planning',
                            'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/.CiEmailWork': 'email',
                            'http://prismstandard.org/namespaces/basic/3.0/.pageCount': 'pageCount',
                            'dc.subject': 'keywords',
                            'dc.creator': 'author(s)'
                            }
        extracted_df.rename(columns = columns_to_rename, inplace = True)

        columns_to_process=['Background', 'Research Question', 'Hypothesis', 'Research Method',
                            'Background of the Student', 'External Supervisor', 'Suggested Examiner',
                            'Suggested Supervisor', 'Resources', 'Eligibility', 'Study Planning'
                            ]

        extracted_df=restoreBackslash(columns_to_process, extracted_df)
        
        # move some columns to the start
        cols_at_start=['author(s)', 'email', 'keywords', 'dc.title.en', 'dc.description.en', 'dc.title.sv', 'dc.description.sv',
                       'dc.language', 'xap.CreateDate',
                       #'xap.ModifyDate', 'xap.MetadataDate',
                       'xap.CreatorTool'
                       ]
        extracted_df = extracted_df[cols_at_start  + [c for c in extracted_df if c not in cols_at_start]]

        # sort by xap.CreateDate
        extracted_df.sort_values(by=['xap.CreateDate'],inplace=True)

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
        create_date_column=column_name_to_excel_letter(extracted_df, 'xap.CreateDate')
        modify_date_column=column_name_to_excel_letter(extracted_df, 'xap.ModifyDate')
        metadata_date_column=column_name_to_excel_letter(extracted_df, 'xap.MetadataDate')

        # format in the desired date format
        worksheet.set_column(f'{create_date_column}2:{create_date_column}{max_row+1}', 20, date_fmt)
        worksheet.set_column(f'{modify_date_column}2:{modify_date_column}{max_row+1}', 20, date_fmt)
        worksheet.set_column(f'{metadata_date_column}2:{metadata_date_column}{max_row+1}', 20, date_fmt)

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
                      default=False,
                      help="read PDF file"
                      )

    argp.add_argument('-d', '--dir',
                      type=str,
                      default=False,
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

        if not filename.endswith('.pdf'):
            print("File extentsion must be .pdf")
            return
        extracted_data=process_file_with_XMP_info(filename)

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
                if not f.endswith('.pdf'):
                    print("File extentsion must be .pdf, skipping")
                    continue

                extracted_data=process_file_with_XMP_info(f)
        
                if isinstance(extracted_data, dict):
                    extracted_data.update({'filename': filename})
                    if Verbose_Flag:
                        print("extracted data for {0}: {1}".format(f, extracted_data))
                    list_of_extracted_data.append(extracted_data)

        if len(list_of_extracted_data) > 0:
            write_to_spreadsheet(list_of_extracted_data)
        return

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
