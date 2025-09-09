#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./extract_data_from_ISP.py PDF_file
#
# Extract data from an ISP
#
# Output:
#	Outputs some of the information in JSON format for use with the third-cycle thesis termplate
#
# Note
# This program only works with the Englih version of the ISP as a PDF file.
#
# G. Q. Maguire Jr.
#
#
# 2025-09-08
#

import pprint
import optparse
import sys
import os
import json


import faulthandler

import pymupdf # import PyMuPDF

def extract_field(field, field_numberQ, field_numberR, all_pages):
    global Verbose_Flag
    number_of_pages=len(all_pages)
    for pgn in range(0, number_of_pages):
        if Verbose_Flag:
            print(f"{pgn=}")
        blocks=all_pages[pgn]
        for idx, block in enumerate(blocks):
            blocks[idx] = block

        for idx, block in enumerate(blocks):
            bboxX1, bboxY1, bboxX2, bboxY2, str_value, dummy1, dummy2 = block
            if Verbose_Flag:
                print(f"{bboxX1=}, {bboxY1=}, {bboxX2=}, {bboxY2=}, {str_value=}")

            str_v=str_value.split('\n')[field_numberQ]
            if str_v.startswith(field):
                bboxX1, bboxY1, bboxX2, bboxY2, str_value, dummy1, dummy2 = blocks[idx+1]
                return str_value.split('\n')[field_numberR]
    return None

def first_field(s):
    return s.split('\n')[0].strip()

def second_field(s):
    return s.split('\n')[1].strip()

def strip_parents(s):
    if s.startswith('('):
        s=s[1:]
    if s.endswith(')'):
        s=s[:-1]
    return s


def skipto(f, all_blocks, idx):
    found = False
    for i in range(idx, len(all_blocks)):
        bboxX1, bboxY1, bboxX2, bboxY2, str_value, dummy1, dummy2 = all_blocks[i]
        if str_value == f:
            found = True
            return i, found, str_value
    return idx, found, ""


#  all_pages is a dict index by page number, with a list of blocks of the form (bboxX1, bboxY1, bboxX2, bboxY2, str_value)
def get_selected_fields(all_blocks):
    global Verbose_Flag
    fields = dict()
    idx = 0
    idx, found, str_val = skipto('Agreement doctoral student\nDate\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['student']=first_field(str_val)
        idx = idx+1

    idx, found, str_val = skipto('Agreement principal supervisor\nDate\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['main_supervisor']=first_field(str_val)
        idx = idx+1

    idx, found, str_val = skipto('Phone number\nEmail address\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['student_email']=second_field(str_val)
        idx = idx+1

    idx, found, str_val = skipto('Specialisation\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['Specialisation']=first_field(str_val)
        idx = idx+1

    idx, found, str_val = skipto('Participating departments and/or divisions\nOther participating institutes of higher education and organizations\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['department']=first_field(str_val)
        idx = idx+1

    idx, found, str_val = skipto('Subject\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['subject']=first_field(str_val)
        fields['subject_code']=strip_parents(second_field(str_val))
        idx = idx+1

    idx, found, str_val = skipto('Doctoral programme\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['Doctoral programme']=first_field(str_val)
        idx = idx+1

    idx, found, str_val = skipto('4.1 Principal supervisor (to be filled in by the principal supervisor)\n', all_blocks, idx)
    if found:
        idx, found, str_val = skipto( 'School\nSection, unit or equivalent\n', all_blocks, idx)
        if found:
            bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
            fields['main_supervisor_school']=first_field(str_val)
            fields['main_supervisor_unit']=second_field(str_val)
            idx = idx+1

    idx, found, str_val = skipto('4.2 Assistant supervisors (to be filled in by the principal supervisor)\n', all_blocks, idx)
    idx_director_of_studies, found_director_of_studies, str_val_director_of_studies = skipto('4.3 Programme director/Director of studies\n', all_blocks, idx)
    print(f"secondary superrvisors start at {idx} and end at {idx_director_of_studies}")

    if found:
        # for up to 9 additional supervisors
        # This has to be done before '4.3 Programme director/Director of studies\n'

        for supervisor_index in range(1,10):
            supervisor_char=chr(ord('A')+supervisor_index)
            idx, found, str_val = skipto('Name\nTitle\n', all_blocks, idx)
            if found:
                # if this name is coming from the director of studies - stop
                if idx >= idx_director_of_studies:
                    break
                bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
                fields['supervisor'+supervisor_char]=first_field(str_val)
                idx = idx+1

            idx, found, str_val = skipto('School\nSection, unit or equivalent\n', all_blocks, idx)
            if found:
                bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
                fields['supervisor'+supervisor_char+'_school']=first_field(str_val)
                fields['supervisor'+supervisor_char+'_unit']=second_field(str_val)
                idx = idx+1

            idx, found, str_val = skipto('E-mail\nDocent (Reader)/equivalent\n', all_blocks, idx)
            if found:
                bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
                fields['supervisor'+supervisor_char+'_email']=first_field(str_val)
                idx = idx+1

    idx, found, str_val = skipto('5.1 Title of the thesis or doctoral project\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['Title']=first_field(str_val)
        idx = idx+1

    idx, found, str_val = skipto('5.3 Planned form of thesis\n', all_blocks, idx)
    if found:
        bboxX1, bboxY1, bboxX2, bboxY2, str_val, dummy1, dummy2 = all_blocks[idx+1]
        fields['planned_form_of_thesis']=first_field(str_val)
        idx = idx+1

    return fields

def main():
    global Verbose_Flag

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))

    if (len(remainder) < 1):
        print("Insuffient arguments - PDF file name")
        sys.exit()
    elif (len(remainder) == 1):
        input_file=remainder[0]
        output_file=None
    elif (len(remainder) == 2):
        input_file=remainder[0]
        output_file=remainder[1]
    else:
        print("Give arguments - PDF_file output_JSON-file")
        sys.exit()

    print(f"{input_file=}, {output_file=}")

    doc = pymupdf.open(input_file)
    if Verbose_Flag:
        print(f"{doc=}")
        print(f"{len(doc)=}")

    if not output_file: 
        # create in the same directory as the input file
        output_file= os.path.split(input_file)[0] + os.sep + os.path.basename(input_file)[:-4] + ".json"
        print(f"{output_file=}")

    if Verbose_Flag:
        print(f"{target_file=}")

    all_blocks=list()
    for page in doc: # iterate the document pages
        all_blocks.extend(page.get_text("blocks", sort=True)) # get plain text encoded as UTF-8


    fields=get_selected_fields(all_blocks)

    try:
        with open(output_file, 'w') as outfile: 
            json.dump(fields, outfile)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")


if __name__ == "__main__": main()

