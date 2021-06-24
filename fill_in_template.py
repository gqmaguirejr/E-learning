#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./fill_in_template.py --pdf template.pdf --json data.json
#
# Purpose: fill in a KTH cover template with data from a JSON file
#
# Example:
# ./fill_in_template.py --pdf "KTH_Omslag_Exjobb_Formulär_Final_dummy_EN-20210623.pdf" --json jussi.json --trita "TRITA-EECS-EX-2021:330"
#
# 2021-06-24 G. Q. Maguire Jr.
#
import re
import sys

import json
import argparse
import os			# to make OS calls, here to get time zone info

import pdfrw
import datetime 

# The basics filling in fileds of a PDF file are based on the web page:
#  Andrew Krcatovich, "Use Python to Fill PDF Files!", Oct 31, 2020
#  https://akdux.com/python/2020/10/31/python-fill-pdf-files.html

# Some keys 
ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_VAL_KEY = '/V'
ANNOT_RECT_KEY = '/Rect'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'

def fill_pdf(template_pdf, output_pdf_path, data_dict):
    for page in template_pdf.pages:
        annotations = page[ANNOT_KEY]
        for annotation in annotations:
            if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                if annotation[ANNOT_FIELD_KEY]:
                    key = annotation[ANNOT_FIELD_KEY][1:-1]
                    if key in data_dict.keys():
                        if type(data_dict[key]) == bool:
                            if data_dict[key] == True:
                                annotation.update(pdfrw.PdfDict(
                                    AS=pdfrw.PdfName('Yes')))
                        else:
                            annotation.update(
                                pdfrw.PdfDict(V='{}'.format(data_dict[key]))
                            )
                            annotation.update(pdfrw.PdfDict(AP=''))
    template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
    pdfrw.PdfWriter().write(output_pdf_path, template_pdf)
    
# rectangles have the formÖ: bottom_left_x, bottom_left_y, top_right_x, top_right_y
def pdf_fields(template_pdf):
    for page in template_pdf.pages:
        annotations = page[ANNOT_KEY]
        for annotation in annotations:
            print("annotation={}".format(annotation))
            if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                if annotation[ANNOT_FIELD_KEY]:
                    key = annotation[ANNOT_FIELD_KEY][1:-1]
                    print("key={0}".format(key, ))
                    # if key == 'Bild':
                    #         annotation.update(
                    #             pdfrw.PdfDict(MK='{}')
                    #         )
                    height=float(annotation['/Rect'][3])-float(annotation['/Rect'][1])
                    print("height of rect={}".format(height))

def pdf_fields_modify(template_pdf):
    for page in template_pdf.pages:
        annotations = page[ANNOT_KEY]
        for annotation in annotations:
            print("annotation={}".format(annotation))
            if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                if annotation[ANNOT_FIELD_KEY]:
                    key = annotation[ANNOT_FIELD_KEY][1:-1]
                    print("key={0}".format(key, ))
                    # if key == 'Bild':
                    #         annotation.update(
                    #             pdfrw.PdfDict(MK='{}')
                    #         )
                    height=float(annotation['/Rect'][3])-float(annotation['/Rect'][1])
                    print("height of rect={}".format(height))


                    if key == 'Titel':
                        type_of_value=type(annotation['/Rect'])
                        print("type_of_value={}".format(type_of_value))
                        new_base=440.0
                        new_top=annotation['/Rect'][3]
                        a_value=[66.3714, new_base, 529.284, new_top]
                        annotation.update(
                            # was ['66.3714', '419.512', '529.284', '475.445']
                            pdfrw.PdfDict(Rect=pdfrw.objects.pdfarray.PdfArray([66.3714, new_base, 529.284, new_top]))
                        )

                    if key == 'Underrubrik':
                        type_of_value=type(annotation['/Rect'])
                        print("type_of_value={}".format(type_of_value))
                        new_base=370.0
                        new_top=new_base+height
                        a_value=[66.3714, new_base, 529.284, new_top]
                        annotation.update(
                            # was ['66.3714', '419.512', '529.284', '475.445']
                            pdfrw.PdfDict(Rect=pdfrw.objects.pdfarray.PdfArray([66.3714, new_base, 529.284, new_top]))
                        )

                    if key == 'Namn på författare':
                        type_of_value=type(annotation['/Rect'])
                        print("type_of_value={}".format(type_of_value))
                        new_base=300.0
                        new_top=new_base+height
                        a_value=[66.3714, new_base, 529.284, new_top]
                        annotation.update(
                            # was ['66.3714', '419.512', '529.284', '475.445']
                            pdfrw.PdfDict(Rect=pdfrw.objects.pdfarray.PdfArray([66.3714, new_base, 529.284, new_top]))
                        )

                    if key == 'Bild':
                        type_of_value=type(annotation['/Rect'])
                        print("type_of_value={}".format(type_of_value))
                        new_base=35.0
                        new_top=new_base+10.0
                        a_value=[66.3714, new_base, 529.284, new_top]
                        annotation.update(
                            # was ['66.3714', '419.512', '529.284', '475.445']
                            pdfrw.PdfDict(Rect=pdfrw.objects.pdfarray.PdfArray([66.3714, new_base, 529.284, new_top]))
                        )



def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing

    argp = argparse.ArgumentParser(description="fill_in_template.py: fill in a template with data from JSON file")

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

    argp.add_argument('-j', '--json',
                      type=str,
                      default="data.json",
                      help="JSON file"
                      )

    argp.add_argument('--trita',
                      type=str,
                      help="trita string for thesis"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    pdf_template=args["pdf"]
    if Verbose_Flag:
        print("pdf_template={}".format(pdf_template))

    json_filename=args["json"]

    if json_filename:
        with open(json_filename, 'r') as data_FH:
            try:
                data_string=data_FH.read()
                data_dict=json.loads(data_string)
            except:
                print("Error in reading={}".format(data_string))
                return

    if Verbose_Flag:
        print("read JSON: {}".format(data_dict))

    # use a fixed output file name for now
    pdf_output = "output.pdf"
 
    # form_dict = {
    #     'Examensarbete inom ämnesområde': "Degree Project in Media Technology",
    #     'Grundnivå/avancerad': "Second cycle, 30 Credits",
    #     'Titel': "An iterative design process for visualizing historical air temperature recordings effectively in a single display",
    #     'Underrubrik': "A user study on narrative visualizations of geospatial time-dependent data",
    #     'Namn på författare': "Jussi Kangas",
    #     'Sverige, 2021': "Sweden, 2021",
    #     'TRITA - XXX-XXX 2021:XX': "TRITA-EECS-EX-2021:330"
    # }

    form_dict=dict()

    # "Title": {"Main title": "This is the title in the language of the thesis", "Subtitle": "An subtitle in the language of the thesis", "Language": "eng"}, "Alternative title": {"Main title": "Detta är den svenska översättningen av titeln", "Subtitle": "Detta är den svenska översättningen av undertiteln", "Language": "swe"}
    title=data_dict.get('Title', None)
    if title:
        form_dict['Titel']=title.get('Main title', None)
        language=title.get('Language', None)
        if language is None:
            language='eng'
            print("no language specied, guessing English")

        form_dict['Underrubrik']=title.get('Subtitle', None)
    else:
        print("Cannot figure out title information")
        return

    if Verbose_Flag:
        print("language={}".format(language))
        
    author_names=list()
    for i in range(1, 10):
        which_author="Author{}".format(i)
        author=data_dict.get(which_author, None)
        if author:
            last_name=author.get('Last name', None)
            first_name=author.get('First name', None)
            if first_name and last_name:
                author_name=first_name+' '+last_name
            elif not first_name and last_name:
                author_name=last_name
            elif first_name and not last_name:
                author_name=first_name
            else:
                print("Author name is unknown: {}".format(author))
            author_names.append(author_name)
        else:		# if there was no such author, then stop looping
            break

    if Verbose_Flag:
        print("author_names={}".format(author_names))

    if len(author_names) == 1:
        form_dict['Namn på författare']=author_names[0]
    elif len(author_names) == 2:
        if language == 'swe':
            form_dict['Namn på författare']=author_names[0] + ' och ' + author_names[1]
        else:
            form_dict['Namn på författare']=author_names[0] + ' and ' + author_names[1]
    else:
        print("Error cannot handle more than two authors")
        return

    other_info=data_dict.get('Other information', None)
    if other_info:
        year=other_info.get('Year', None)
    else:
        # if np year present, then use the current year
        now = datetime.datetime.now()
        year=now.year

    if language == 'swe':
        form_dict['Sverige, 2021']= "Stockholm, Sverige, {}".format(year)
    else:
        form_dict['Sverige, 2021']= "Stockholm, Sweden, {}".format(year)

    x=args['trita']
    if x:
        trita_string=x
    else:
        print("TRITA string is not specified")

    form_dict['TRITA - XXX-XXX 2021:XX']=trita_string

    #     'Examensarbete inom ämnesområde': "Degree Project in Media Technology",
    #     'Grundnivå/avancerad': "Second cycle, 30 Credits",
    degree=data_dict.get('Degree', None)
    if degree:
        ep=degree.get('Educational program', None)

        cycle=degree.get('Level', None)
        if cycle:
            cycle = int(cycle)
        else:
            print("Unable to determine cycle number")
            return

        number_of_credits=degree.get('Credits', None)
        if number_of_credits:
            number_of_credits=float(number_of_credits)
        else:
            if cycle == 1:
                number_of_credits=15.0
            elif cycle == 2:
                number_of_credits=30.0
            else:
                number_of_credits=None
                print("Cannot guess number_of_credits")
                return

        area = degree.get('subjectArea', None)
        if not area:
            print("Sunject area is not specified")
            return

    #     'Examensarbete inom ämnesområde': "Degree Project in Media Technology",
    #     'Grundnivå/avancerad': "Second cycle, 30 Credits",
    # if the number of credits is an integer, then turn it into an int from a float
    i_number_of_credits=int(number_of_credits)
    if (float(i_number_of_credits) - number_of_credits) == 0.0:
        number_of_credits=i_number_of_credits
    if language == 'swe':
        if cycle == 1:
            form_dict['Grundnivå/avancerad']="Grundnivå nivå {} HP".format(number_of_credits)
        elif cycle == 2:
            form_dict['Grundnivå/avancerad']="Avancerad nivå {} HP".format(number_of_credits)
    else:
        if cycle == 1:
            form_dict['Grundnivå/avancerad']="First cycle, {} Credits".format(number_of_credits)
        elif cycle == 2:
            form_dict['Grundnivå/avancerad']="Second cycle, {} Credits".format(number_of_credits)

    if language == 'swe':
        if cycle == 1:
            form_dict['Examensarbete inom ämnesområde']="Examensarbete inom {}".format(area)
        elif cycle == 2:
            form_dict['Examensarbete inom ämnesområde']="Examensarbete inom {}".format(area)
    else:
        if cycle == 1:
            form_dict['Examensarbete inom ämnesområde']="Degree project in {}".format(area)
        elif cycle == 2:
            form_dict['Examensarbete inom ämnesområde']="Degree project in {}".format(area)

    print("form_dict={}".format(form_dict))

    template_pdf = pdfrw.PdfReader(pdf_template)

    pdf_fields_modify(template_pdf)
    
    status=fill_pdf(template_pdf,pdf_output, form_dict)
    print("status={}".format(status))

    #pdf_fields(template_pdf)

    return

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
