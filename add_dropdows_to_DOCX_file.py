#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./add_dropdows_to_DOCX_file.py --json file.json [--file cover_template.docx]
#
# Purpose: The program modifies the KTH cover (saved as a DOCX file) by inserting drop-down menus and other configuration for
#          a particular exam and main subject/field of technology/...
#
# Output: outputs a modified DOCX file: <input_filename>-modified.docx
#         More specifically the 'word/document.xml' within the DOCX file is modified.
#
# Example:
# ./add_dropdows_to_DOCX_file.py --json custom_values.json --file za5.docx
#    produces za5-modified.docx
#
#
# Notes:
#    Only limited testing - this is a program still under development
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-12-07 G. Q. Maguire Jr.
# Base on earlier customize_DOCX_file.py
#
import re
import sys
import subprocess

import json
import argparse
import os			# to make OS calls, here to get time zone info

import time

import pprint

from collections import defaultdict


import datetime
import isodate                  # for parsing ISO 8601 dates and times
import pytz                     # for time zones
from dateutil.tz import tzlocal

# for dealing with the DOCX file - which is a ZIP file
import zipfile

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED

modes = { zipfile.ZIP_DEFLATED: 'deflated',
          zipfile.ZIP_STORED:   'stored',
          }

def lookup_value_for_name(name, dict_of_entries):
    for e in dict_of_entries:
        n=dict_of_entries[e].get(name)
        if n:
            return n
    return None

def replace_value_for_name(name, new_value, xml_content):
    offset=0
    pattern1='<property '
    offset=xml_content.find(pattern1, offset)
    while offset >= 0:
        pattern3='name="{}"'.format(name)
        name_offset=xml_content.find(pattern3, offset+len(pattern1))
        if name_offset:
            pattern4='<vt:lpwstr>'
            pattern4_end='</vt:lpwstr>'
            value_offset=xml_content.find(pattern4, name_offset+len(pattern3))
            value_end=xml_content.find(pattern4_end, value_offset+len(pattern4))
            prefix=xml_content[:value_offset+len(pattern4)]
            postfix=xml_content[value_end:]
            return prefix + "{}".format(new_value) + postfix
    return xml_content

def mark_first_field_as_dirty(content):
    # <w:fldChar w:fldCharType="begin" w:dirty="true"/>
    pattern='<w:fldChar w:fldCharType="begin"'
    offset=content.find(pattern)
    if offset >= 0:
        prefix=content[:offset+len(pattern)]
        postfix=content[offset+len(pattern):]
        middle=' w:dirty="true"'
        content=prefix + middle + postfix
    return content

def transform_file(content, dict_of_entries, exam, language, cycle):
    global Verbose_Flag

    # # <property fmtid="xxxx" pid="2" name="property_name"><vt:lpwstr>property_value</vt:lpwstr>
    # #
    # for k in dict_of_entries:
    #     for name in dict_of_entries[k].keys():
    #         new_value=lookup_value_for_name(name, dict_of_entries)
    #         content=replace_value_for_name(name, new_value, content)
    if exam == 'kandidate':

        main_subjects={ 'sv': ['arkitektur', 'teknik'],
                        'en': ['Architecture', 'Technology']
                        }

        # the numeric value is the cycle
        all_levels = {1: {'sv': 'Grundnivå', 'en': 'First cycle'},
                      2: {'sv': 'Avancerad nivå', 'en': 'Second cycle'}
                      }
        all_units = {'sv': 'HP', 'en': 'credits'}

        number_of_credits =[15, 30]

        # dela with the subject line
        start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
        end_marker_1='</w:sdtContent></w:sdt></w:p>'
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Main subject'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
	<w:placeholder>
	  <w:docPart w:val="DefaultPlaceholder_1082065159"/>
	</w:placeholder>
	<w:dropDownList>'''
        replacement_1b=replacement_1b1+replacement_1b2+replacement_1b3

        replacement_1c='<w:listItem w:value="{0}"/>'.format(heading)
        for sub in main_subjects[language]:
            replacement_1c=replacement_1c+'<w:listItem w:displayText="{0}" w:value="{0}"/>'.format(sub)
        replacement_1d='''
	</w:dropDownList>
      </w:sdtPr>
      <w:sdtEndPr>
	<w:rPr>
	  <w:rStyle w:val="DefaultParagraphFont"/>
	</w:rPr>
      </w:sdtEndPr>
      <w:sdtContent>
	<w:r w:rsidR="00F934245">
	  <w:rPr>
	    <w:rStyle w:val="Normal"/>
	  </w:rPr>'''
        replacement_1e='<w:t>{}</w:t></w:r></w:sdtContent></w:sdt>'.format(main_subjects[language][0])

        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e

        # do the replacement in the level and points line
        replacement_2a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}, </w:t></w:r><w:sdt>'.format(all_levels[cycle][language])
        replacement_2b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_2b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(all_units[language])
        replacement_2b3='''
	<w:id w:val="-1853569748"/>
	<w:placeholder>
	  <w:docPart w:val="DefaultPlaceholder_1082065159"/>
	</w:placeholder>
	<w:dropDownList>'''
        replacement_2b4='<w:listItem w:value="{}"/>'.format(all_units[language])
        for cred in number_of_credits:
            replacement_2b4=replacement_2b4+'<w:listItem w:displayText="{0}" w:value="{0}"/>'.format(cred)
        replacement_2b5='''
	</w:dropDownList>
      </w:sdtPr>
      <w:sdtEndPr>
	<w:rPr>
	  <w:rStyle w:val="DefaultParagraphFont"/>
	</w:rPr>
      </w:sdtEndPr>
      <w:sdtContent>
	<w:r w:rsidR="00F93424">
	  <w:rPr>
	    <w:rStyle w:val="Normal"/>
	  </w:rPr>'''
        replacement_2b6='''
	  <w:t>15</w:t>
	</w:r>
      </w:sdtContent>'''
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])
        end_marker_2='</w:sdtContent></w:sdt><w:r w:rsidR'

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        start_offset_1=content.find(start_marker_1)
        if start_offset_1 > 0:
            prefix=content[:start_offset_1]
            end_offset_1=content.find(end_marker_1)
            if end_offset_1 > 0:
                postfix=content[end_offset_1:]
                content=prefix + replacement_1 + postfix

        # do second replacement
        start_offset_2=content.find(start_marker_1)
        print("start_offset_2={}".format(start_offset_2))
        if start_offset_2 > 0:
            prefix=content[:start_offset_2]
            end_offset_2=content.find(end_marker_2)
            if end_offset_2 > 0:
                print("end_offset_2={}".format(end_offset_2))
                postfix=content[end_offset_2:]
                content=prefix + replacement_2 + postfix

    else:
        print("Unknown type of exam={}".format(exam))
    return content

exams=['arkitekt',
       'civilingenjör',
       'högskoleingenjör',
       'kandidate',
       'master',
       'magister',
       'CLGYM', # Civilingenjör och lärare (CLGYM)
       'KPULU', # Kompletterande pedagogisk utbildning
       'KPUFU', # Kompletterande pedagogisk utbildning för ämneslärarexamen i matematik, naturvetenskap och teknik för forskarutbildade
       'KUAUT', # Kompletterande utbildning för arkitekter med avslutad utländsk utbildning
       'KUIUT', # Kompletterande utbildning för ingenjörer med avslutad utländsk utbildning
       'LÄRGR'  #Ämneslärarutbildning med inriktning mot teknik, årskurs 7-9
]

def main(argv):
    global Verbose_Flag
    global testing
    global Keep_picture_flag


    argp = argparse.ArgumentParser(description="JSON_to_DOCX_cover.py: to make a thesis cover using the DOCX template")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-j', '--json',
                      type=str,
                      default="customize.json",
                      help="JSON file for extracted data"
                      )

    argp.add_argument('--cycle',
                      type=int,
                      default=None,
                      help="cycle of degree project"
                      )

    argp.add_argument('--credits',
                      type=float,
                      help="number_of_credits of degree project"
                      )

    argp.add_argument('--exam',
                      type=str,
                      default=None,
                      help="type of exam"
                      )

    argp.add_argument('--language',
                      type=str,
                      default='en',
                      help="language sv or en for Swedish or English"
                      )

    argp.add_argument('--area',
                      type=str,
                      help="area of thesis"
                      )

    argp.add_argument('--area2',
                      type=str,
                      help="area of thesis for combined Cinving. and Master's"
                      )

    argp.add_argument('--trita',
                      type=str,
                      help="trita string for thesis"
                      )

    argp.add_argument('--file',
                      type=str,
                      help="DOCX template"
                      )

    argp.add_argument('-p', '--picture',
                      default=False,
                      action="store_true",
                      help="keep the optional picture"
                      )



    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    Keep_picture_flag=args['picture']

    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))

    json_filename=args["json"]
    if not json_filename:
        print("Unknown source for the JSON information: {}".format(json_filename))
        return

    # extras contains information from the command line options
    with open(json_filename, 'r') as json_FH:
        try:
            json_string=json_FH.read()
            dict_of_entries=json.loads(json_string)
        except:
            print("Error in reading={}".format(json_string))
            return

    if Verbose_Flag:
        print("read JSON: {}".format(dict_of_entries))

    exam=args["exam"]

    if exam:
        for e in exams:
            exl=exam.lower()
            el=e.lower()
            if exl == el:
                exam=e
                break
            if el.find(exl) > 0:
                exam=e
                break
    if exam not in exams:
        print("Unknown exam, choose one of {}".format(exams))        

    language=args["language"]
    if language not in ['sv', 'en']:
        print("Unknown language use 'sv' for Swedish or 'en' for English")
        return

    cycle=args['cycle']
    if not cycle:
        cycle=1

    input_filename=args['file']
    if not input_filename:
        print("File name must be specified")
        return

    document = zipfile.ZipFile(input_filename)
    file_names=document.namelist()
    if Verbose_Flag:
        print("File names in ZIP zip file: {}".format(file_names))

    word_document_file_name='word/document.xml'
    word_docprop_custom_file_name='docProps/custom.xml'
    if word_document_file_name not in file_names:
        print("Missing file: {}".format(word_document_file_name))
        return
    
    output_filename="{}-modfied.docx".format(input_filename[:-5])
    print("outputting modified data to {}".format(output_filename))

    zipOut = zipfile.ZipFile(output_filename, 'w')
    for fn in file_names:
        if Verbose_Flag:
            print("processing file: {}".format(fn))
        # copy existing file to archive
        if fn not in [word_document_file_name]:
            file_contents = document.read(fn)
        else:
            if Verbose_Flag:
                print("processing {}".format(fn))
            xml_content = document.read(fn).decode('utf-8')
            if fn == word_document_file_name:
                file_contents = transform_file(xml_content, dict_of_entries, exam, language, cycle)
            else:
                print("Unknown file {}".format(fn))
        # in any case write the file_contents out
        zipOut.writestr(fn, file_contents,  compress_type=compression)

    zipOut.close()

    document.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

