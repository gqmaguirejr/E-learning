#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./customize_DOCX_file.py --json file.json [--file cover_template.docx]
#
# Purpose: The program produces a customized DOCX by setting the custom DOCPROPERIYES to the values from the JSON file
# The JSON file can be produced by extract_custom_DOCX_properties.py
#
# Output: outputs a customized DOCX file: <input_filename>-modified.docx
#
# Example:
# ./customize_DOCX_file.py --json custom_values.json --file za5.docx
#    produces za5-modified.docx
#
#
# Notes:
#    Only one test json file has been run.
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-12-07 G. Q. Maguire Jr.
# Base on earlier JSON_to_cover.py
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

def transform_file(content, dict_of_entries):
    global Verbose_Flag
    # <property fmtid="xxxx" pid="2" name="property_name"><vt:lpwstr>property_value</vt:lpwstr>
    #
    for k in dict_of_entries:
        for name in dict_of_entries[k].keys():
            new_value=lookup_value_for_name(name, dict_of_entries)
            content=replace_value_for_name(name, new_value, content)
    return content

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
                      default="event.json",
                      help="JSON file for extracted data"
                      )

    argp.add_argument('--cycle',
                      type=int,
                      help="cycle of thesis"
                      )

    argp.add_argument('--credits',
                      type=float,
                      help="number_of_credits of thesis"
                      )

    argp.add_argument('--exam',
                      type=int,
                      help="type of exam"
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

    input_filename=args['file']
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
        if fn not in [word_docprop_custom_file_name, word_document_file_name]:
            file_contents = document.read(fn)
        else:
            if Verbose_Flag:
                print("processing {}".format(fn))
            xml_content = document.read(fn).decode('utf-8')
            if fn == word_docprop_custom_file_name:
                file_contents = transform_file(xml_content, dict_of_entries)
            elif fn == word_document_file_name:
                file_contents = mark_first_field_as_dirty(xml_content)
            else:
                print("Unknown file {}".format(fn))
        # in any case write the file_contents out
        zipOut.writestr(fn, file_contents,  compress_type=compression)

    zipOut.close()

    document.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

