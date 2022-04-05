#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./add_subject_credits_title_etc_to_cover.py [--file cover_template.docx]
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
# 2022-04-04 G. Q. Maguire Jr.
# Base on earlier add_dropdows_to_DOCX_file.py
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

def  do_first_replacement(content, r):
    start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
    end_marker_1='</w:sdtContent></w:sdt></w:p>'

    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        end_offset_1=content.find(end_marker_1)
        if end_offset_1 > 0:
            postfix=content[end_offset_1:]
            content=prefix + r + postfix
    return content

def do_second_replacement(content, r):
    start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
    end_marker_2='</w:sdtContent></w:sdt><w:r w:rsidR'

    start_offset_2=content.find(start_marker_1)
    print("start_offset_2={}".format(start_offset_2))
    if start_offset_2 > 0:
        prefix=content[:start_offset_2]
        end_offset_2=content.find(end_marker_2)
        if end_offset_2 > 0:
            print("end_offset_2={}".format(end_offset_2))
            postfix=content[end_offset_2:]
            content=prefix + r + postfix
    return content

# From English template
# <w:placeholder><w:docPart w:val="5754E78FAA3547E690B6F86ACE31506E"/></w:placeholder><w:showingPlcHdr/>
# <w:placeholder><w:docPart w:val="C14E00FD463348788D1BB7328469EF1C"/></w:placeholder><w:showingPlcHdr/>
# From Swedish template
# <w:placeholder><w:docPart w:val="3B317945923C481B9F5903B92E839E1E"/></w:placeholder><w:showingPlcHdr/>
# <w:placeholder><w:docPart w:val="276F62D9284D4835BE181771EADBAE35"/></w:placeholder><w:showingPlcHdr/>
# This placeholder text means that you cannot turn of Developer->Dsign mode if you turn it on
def removed_unneded_placeholder_text(content):
    start_marker_1='<w:placeholder><w:docPart w:val="5754E78FAA3547E690B6F86ACE31506E"/></w:placeholder><w:showingPlcHdr/>'
    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        postfix=content[(start_offset_1+len(start_marker_1)):]
        content=prefix + postfix

    start_marker_1='<w:placeholder><w:docPart w:val="C14E00FD463348788D1BB7328469EF1C"/></w:placeholder><w:showingPlcHdr/>'
    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        postfix=content[(start_offset_1+len(start_marker_1)):]
        content=prefix + postfix

    start_marker_1='<w:placeholder><w:docPart w:val="3B317945923C481B9F5903B92E839E1E"/></w:placeholder><w:showingPlcHdr/>'
    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        postfix=content[(start_offset_1+len(start_marker_1)):]
        content=prefix + postfix

    start_marker_1='<w:placeholder><w:docPart w:val="276F62D9284D4835BE181771EADBAE35"/></w:placeholder><w:showingPlcHdr/>'
    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        postfix=content[(start_offset_1+len(start_marker_1)):]
        content=prefix + postfix

    return content


# the numeric value is the cycle
all_levels = {1: {'sv': 'Grundnivå', 'en': 'First cycle'},
              2: {'sv': 'Avancerad nivå', 'en': 'Second cycle'}
              }
all_units = {'sv': 'HP', 'en': 'credits'}

number_of_credits =[15, 30]

def transform_file(content, dict_of_entries, exam, language, cycle):
    global Verbose_Flag

    # remove unnecessary bookmark
    unnecessary_bookmark='<w:bookmarkStart w:id="0" w:name="_GoBack"/><w:bookmarkEnd w:id="0"/>'
    content=content.replace(unnecessary_bookmark, '')


    # # <property fmtid="xxxx" pid="2" name="property_name"><vt:lpwstr>property_value</vt:lpwstr>
    # #
    # for k in dict_of_entries:
    #     for name in dict_of_entries[k].keys():
    #         new_value=lookup_value_for_name(name, dict_of_entries)
    #         content=replace_value_for_name(name, new_value, content)
    if exam == 'kandidatexamen':
        cycle=1
        main_subjects={ 'sv': ['teknik', 'arkitektur'], #  change the order so most frequen is first
                        'en': ['Technology', 'Architecture']
                        }

        number_of_credits = [15]

        # deal with the subject line
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
            heading='Major'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam == 'högskoleexamen':
        cycle=1
        main_subjects={ 'sv': ['teknik'],
                        'en': ['Technology']
                        }

        if language == 'sv':
            number_of_credits = ['7,5']
        else:
            number_of_credits = [7.5]

        # deal with the subject line
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
            heading='Major'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)


    elif exam == 'arkitektexamen':
        cycle=2
        main_subjects={ 'sv': ['arkitektur'],
                        'en': ['Architecture']
                        }

        number_of_credits = [30]

        # deal with the subject line
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
            heading='Major'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam == 'högskoleingenjörsexamen':
        cycle = 1
        field_of_technology={
            'sv': [
                'byggteknik och design', # TIBYH
                'datateknik', # TIDAA - Flemingsberg and  TIDAB - Kista
                'elektronik och datorteknik', # TIEDB
                'elektroteknik', # TIELA - Flemingsberg
                'industriell teknik och produktionsunderhåll', # TIIPS
                'kemiteknik', # TIKED
                'maskinteknik', # TIMAS - Södertälje
                'medicinsk teknik', # TIMEL
                'teknik och ekonomi', # TITEH
            ],
            'en': [
                'Chemical Engineering', # TIKED
                'Computer Engineering', # TIDAA and TIDAB
                'Constructional Engineering and Design',  # TIBYH
                'Electrical Engineering', # TIELA
                'Electronics and Computer Engineering', # TIEDB
                'Engineering and Economics', # TITEH
                'Industrial Technology and Production Maintenance', # TIIPS
                'Mechanical Engineering', # TIMAS
                'Medical Technology', # TIMEL
            ]
            }

        number_of_credits = [15]

        # deal with the subject line
        start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
        end_marker_1='</w:sdtContent></w:sdt></w:p>'
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='teknikområde'
        else:
            heading='field_of_technology'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
	<w:dropDownList>'''
        replacement_1b=replacement_1b1+replacement_1b2+replacement_1b3

        replacement_1c='<w:listItem w:value="{0}"/>'.format(heading)
        for sub in field_of_technology[language]:
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
        replacement_1e='<w:t>{}</w:t></w:r></w:sdtContent></w:sdt>'.format(field_of_technology[language][0])

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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam == 'civilingenjörsexamen':
        cycle = 2
        field_of_technology={
            'sv': [
                # Civilingenjör och lärare (CLGYM)
                'bioteknik', # CBIOT
                'datateknik', # CDATE
                'design och produktframtagning', # CDEPR
                'elektroteknik', # CELTE
                'energi och miljö', # CENMI
                'farkostteknik', # CFATE
                'industriell ekonomi', # CINEK
                'industriell teknik och hållbarhet', # CITEH
                'informationsteknik', # CINTE
                'maskinteknik', # CMAST
                'materialdesign', # CMATD
                'medicinsk teknik', # CMEDT
                'medieteknik', # CMETE
                'samhällsbyggnad', # CSAMH
                'teknisk fysik', # CTFYS
                'teknisk kemi', # CTKEM
                'teknisk kemi, Mittuniversitet – KTH', # CTKMK
                'teknisk matematik',  # CTMAT
                'öppen ingång' # COPEN
            ],
            'en': [
                'Biotechnology', # CBIOT
                'Civil Engineering and Urban Management', # CSAMH
                'Computer Science and Engineering', #CDATE
                'Design and Product Realisation', # CDEPR
                'Electrical Engineering', # CELTE
                'Energy and Environment', # CENMI
                'Engineering Chemistry', # CTKEM
                'Engineering Chemistry, Mid Sweden University – KTH', # CTKMK
                'Engineering Mathematics', # CTMAT
                'Engineering Physics', # CTFYS
                'Industrial Engineering and Management', # CINEK
                'Industrial Technology and Sustainability', # CITEH
                'Information and Communication Technology', # CINTE
                'Materials Design and Engineering', # CMATD
                'Mechanical Engineering', # CMAST
                'Media Technology', # CMETE
                'Medical Engineering', # CMEDT
                'Vehicle Engineering', # CFATE
                'Open Entrance', # COPEN
                # 'Master of Science in Engineering and in Education' #CLGYM
            ]
            }

        number_of_credits = [30, 15] #  change th order in the list

        # deal with the subject line
        start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
        end_marker_1='</w:sdtContent></w:sdt></w:p>'
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='teknikområde'
        else:
            heading='field_of_technology'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
	<w:dropDownList>'''
        replacement_1b=replacement_1b1+replacement_1b2+replacement_1b3

        replacement_1c='<w:listItem w:value="{0}"/>'.format(heading)
        for sub in field_of_technology[language]:
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
        replacement_1e='<w:t>{}</w:t></w:r></w:sdtContent></w:sdt>'.format(field_of_technology[language][0])

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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam == 'masterexamen': #
        cycle = 2
        main_subjects={
            'sv': [
                'arkitektur', 
                'bioteknik',
                'datalogi och datateknik',
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
                'teknik och management',
                'teknisk fysik'
            ],
            'en': [
                'Architecture',
                'Biotechnology',
	        'Computer Science and Engineering',
                'Electrical Engineering',
                'Industrial Management',
	        'Information and Communication Technology',
                'Chemical Science and Engineering',
                'Mechanical Engineering',
                'Mathematics',
                'Materials Science and Engineering',
                'Medical Engineering',
                'Environmental Engineering'
                'The Built Environment',
                'Technology and Economics',
                'Technology and Health',
                'Technology and Learning',
                'Technology and Management',
                'Engineering Physics'
            ]
        }

        number_of_credits = [30, 15] #  change th order in the list

        # deal with the subject line
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
            heading='Major'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)
        
    elif exam == 'magisterexamen': #
        cycle = 2
        main_subjects={
            'sv': [
                'samhällsbyggnad',     # Magisterprogram, design och byggande i staden (TDEBM) and Magisterprogram, fastigheter (TFAHM)
                'industriell ekonomi', # Magisterprogram, entreprenörskap och innovationsledning (TEILM)
                'arkitektur',          # Magisterprogram, ljusdesign (TLODM) - Arkitektur, Samhällsbyggnad, Teknik och hälsa
                'teknik och hälsa'
            ],
            'en': [
                'Architecture',
                'Industrial Management',
                'The Built Environment',
                'Technology and Health'
            ]
        }

        number_of_credits = [15] # all are only 15 points

        # deal with the subject line
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
            heading='Major'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)
        
    elif exam == 'CLGYM':
        cycle=2
        main_subjects={
            'sv': [
                'teknik och lärande',
                'matematik och lärande',
                'fysik och lärande',
                'kemi och lärande'
            ],
            'en': [
                'Technology and Learning',
                'Mathematics and Learning',
                'Physics and Learning',
                'Chemistry and Learning'
            ]
        }

        number_of_credits = [30]

        # deal with the subject line
        start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
        end_marker_1='</w:sdtContent></w:sdt></w:p>'
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='ämnesområde'
        else:
            heading='Subject area'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam == 'ämneslärarexamen': # note that the students have to do two 15 credit exjobbs pne in the 3 and the other in the 4th year
        cycle=1
        main_subjects={
            'sv': [
                'teknik och lärande',
                'matematik och lärande',
                'fysik och lärande',
                'kemi och lärande',
                'teknik'
            ],
            'en': [
                'Technology and Learning',
                'Mathematics and Learning',
                'Physics and Learning',
                'Chemistry and Learning',
                'Technology'
            ]
        }

        number_of_credits = [15]

        # deal with the subject line
        start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
        end_marker_1='</w:sdtContent></w:sdt></w:p>'
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='ämnesområde'
        else:
            heading='Subject area'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam in ['KPULU', 'KPUFU']:
        cycle=2
        main_subjects={
            'sv': [
                'ämnesdidaktik'
            ],
            'en': [
                'Subject-Based Teaching and Learning'
            ]
        }

        number_of_credits = [15, 30]

        # deal with the subject line
        start_marker_1='<w:rPr><w:rStyle w:val="PlaceholderText"/>'
        end_marker_1='</w:sdtContent></w:sdt></w:p>'
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='ämnesområde'
        else:
            heading='Subject area'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam == 'both':
        # Examensarbete inom teknikområdet <teknikområde> och huvudområdet <huvudområde>
        # Degree Project in the Field of Technology <teknikområde> and the Main Field of Study <huvudområde>
        cycle = 2
        field_of_technology={
            'sv': [
                # Civilingenjör och lärare (CLGYM)
                'bioteknik', # CBIOT
                'datateknik', # CDATE
                'design och produktframtagning', # CDEPR
                'elektroteknik', # CELTE
                'energi och miljö', # CENMI
                'farkostteknik', # CFATE
                'industriell ekonomi', # CINEK
                'industriell teknik och hållbarhet', # CITEH
                'informationsteknik', # CINTE
                'maskinteknik', # CMAST
                'materialdesign', # CMATD
                'medicinsk teknik', # CMEDT
                'medieteknik', # CMETE
                'samhällsbyggnad', # CSAMH
                'teknisk fysik', # CTFYS
                'teknisk kemi', # CTKEM
                'teknisk kemi, Mittuniversitet – KTH', # CTKMK
                'teknisk matematik',  # CTMAT
                'öppen ingång' # COPEN
            ],
            'en': [
                'Biotechnology', # CBIOT
                'Civil Engineering and Urban Management', # CSAMH
                'Computer Science and Engineering', #CDATE
                'Design and Product Realisation', # CDEPR
                'Electrical Engineering', # CELTE
                'Energy and Environment', # CENMI
                'Engineering Chemistry', # CTKEM
                'Engineering Chemistry, Mid Sweden University – KTH', # CTKMK
                'Engineering Mathematics', # CTMAT
                'Engineering Physics', # CTFYS
                'Industrial Engineering and Management', # CINEK
                'Industrial Technology and Sustainability', # CITEH
                'Information and Communication Technology', # CINTE
                'Materials Design and Engineering', # CMATD
                'Mechanical Engineering', # CMAST
                'Media Technology', # CMETE
                'Medical Engineering', # CMEDT
                'Vehicle Engineering', # CFATE
                'Open Entrance', # COPEN
                # 'Master of Science in Engineering and in Education' #CLGYM
            ]
            }

        main_subjects={
            'sv': [
                'arkitektur', 
                'bioteknik',
                'datalogi och datateknik',
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
                'teknik och management',
                'teknisk fysik'
            ],
            'en': [
                'Architecture',
                'Biotechnology',
	        'Computer Science and Engineering',
                'Electrical Engineering',
                'Industrial Management',
	        'Information and Communication Technology',
                'Chemical Science and Engineering',
                'Mechanical Engineering',
                'Mathematics',
                'Materials Science and Engineering',
                'Medical Engineering',
                'Environmental Engineering'
                'The Built Environment',
                'Technology and Economics',
                'Technology and Health',
                'Technology and Learning',
                'Technology and Management',
                'Engineering Physics'
            ]
        }


        number_of_credits = [30, 15] #  change th order in the list

        # deal with the subject line
        if language == 'sv':
            project_name='Examensarbete inom teknikområdet'
        else:
            project_name='Degree Project in the Field of Technology'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='teknikområde'
        else:
            heading='field of technology'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
	<w:dropDownList>'''
        replacement_1b=replacement_1b1+replacement_1b2+replacement_1b3

        replacement_1c='<w:listItem w:value="{0}"/>'.format(heading)
        for sub in field_of_technology[language]:
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
        replacement_1e='<w:t>{}</w:t></w:r></w:sdtContent></w:sdt>'.format(field_of_technology[language][0])

        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e

        # handle the main field of study
        if language == 'sv':
            project_name2=' och huvudområdet'
        else:
            project_name2=' and the Main Field of Study'

        # note the extra <w:r> to start a new run of text
        replacement_3a='<w:r><w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name2)
        if language == 'sv':
            heading2='Huvudområde'
        else:
            heading2='Major'

        replacement_3b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_3b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading2)
        replacement_3b3='''<w:id w:val="-1853569748"/>
	<w:dropDownList>'''
        replacement_3b=replacement_3b1+replacement_3b2+replacement_3b3

        replacement_3c='<w:listItem w:value="{0}"/>'.format(heading2)
        for sub in main_subjects[language]:
            replacement_3c=replacement_3c+'<w:listItem w:displayText="{0}" w:value="{0}"/>'.format(sub)
        replacement_3d='''
	</w:dropDownList>
      </w:sdtPr>
      <w:sdtEndPr>
	<w:rPr>
	  <w:rStyle w:val="DefaultParagraphFont"/>
	</w:rPr>
      </w:sdtEndPr>
      <w:sdtContent>
	<w:r>
	  <w:rPr>
	    <w:rStyle w:val="Normal"/>
	  </w:rPr>'''
        replacement_3e='<w:t>{}</w:t></w:r></w:sdtContent></w:sdt>'.format(main_subjects[language][0])

        replacement_3=replacement_3a + replacement_3b + replacement_3c + replacement_3d + replacement_3e

        if language == 'sv':
            replacement_1=replacement_1 + replacement_3
        else:
            #replacement_1=replacement_1 + replacement_3
            replacement_1=replacement_1 + replacement_3



        # do the replacement in the level and points line
        replacement_2a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}, </w:t></w:r><w:sdt>'.format(all_levels[cycle][language])
        replacement_2b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_2b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(all_units[language])
        replacement_2b3='''
	<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do the replacement in the level and points line
        replacement_2a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}, </w:t></w:r><w:sdt>'.format(all_levels[cycle][language])
        replacement_2b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_2b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(all_units[language])
        replacement_2b3='''
	<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    elif exam == 'same':
        # both degrees are in the same subject
        # Examensarbete inom teknikområdet och huvudområdet <huvudområde>
        # Degree Project in the Field of Technology and the Main Field of Study <huvudområde>
        cycle = 2

        main_subjects={
            'sv': [
                'bioteknik',
                'elektroteknik',
                'industriell ekonomi',
                'kemiteknik',
                'maskinteknik',
                'medicinsk teknik',
                'miljöteknik',
                'samhällsbyggnad',
                'teknisk fysik'
            ],
            'en': [
                'Biotechnology',
                'Electrical Engineering',
                'Industrial Management',
                'Chemical Science and Engineering',
                'Mechanical Engineering',
                'Medical Engineering',
                'Environmental Engineering',
                'The Built Environment',
                'Engineering Physics'
            ]
        }

        number_of_credits = [30, 15] #  change th order in the list

        # deal with the subject line
        if language == 'sv':
            project_name='Examensarbete inom teknikområdet och huvudområdet'
        else:
            project_name='Degree Project in the Field of Technology and the Main Field of Study'

        replacement_1a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{} </w:t></w:r><w:sdt>'.format(project_name)
        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Major'

        replacement_1b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_1b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(heading)
        replacement_1b3='''<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do the replacement in the level and points line
        replacement_2a='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}, </w:t></w:r><w:sdt>'.format(all_levels[cycle][language])
        replacement_2b1='''<w:sdtPr>
	<w:rPr>
	  <w:rStyle w:val="Normal"/>
	</w:rPr>'''
        replacement_2b2='<w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(all_units[language])
        replacement_2b3='''
	<w:id w:val="-1853569748"/>
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
        replacement_2b6='<w:t>{0}</w:t></w:r></w:sdtContent>'.format(number_of_credits[0])
        replacement_2b=replacement_2b1+replacement_2b2+replacement_2b3+replacement_2b4+replacement_2b5+replacement_2b6

        replacement_2c='</w:sdt><w:r><w:t xml:space="preserve"> {0}</w:t></w:r>'.format(all_units[language])

        replacement_2=replacement_2a + replacement_2b + replacement_2c

        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do second replacement
        content=do_second_replacement(content, replacement_2)

    else:
        print("Do not know how to handle an exam of type {}".format(exam))

    # add title, subtitle, and author(s)
    title=dict_of_entries.get('Title', None)
    if title: 
        main_title=title.get('Main title', None)
        subtitle=title.get('Subtitle', None)

    if main_title:
        title_xml='<w:pStyle w:val="Titel"/><w:spacing w:before="800"/></w:pPr><w:r w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>Click here to enter your title</w:t></w:r></w:p>'
        new_title_xml='<w:pStyle w:val="Titel"/><w:spacing w:before="800"/></w:pPr><w:r w:rsidRPr="00A15578"><w:t>{}</w:t></w:r></w:p>'.format(main_title)
        content=content.replace(title_xml, new_title_xml)

    if subtitle:
        subtitle_xml='w:val="Subtitle"/><w:spacing w:before="120"/></w:pPr><w:r w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your </w:t></w:r><w:r><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>sub</w:t></w:r><w:r w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>title</w:t></w:r></w:p>'
        new_subtitle_xml='w:val="Subtitle"/><w:spacing w:before="120"/></w:pPr><w:r w:rsidRPr="00A15578"><w:t>{}</w:t></w:r></w:p>'.format(subtitle)
        content=content.replace(subtitle_xml, new_subtitle_xml)

        # {"Author1": {"Last name": "Student", "First name"
    author1=dict_of_entries.get('Author1', None)
    author1_first_name=author1.get('First name', None)
    author1_last_name=author1.get('Last name', None)
    author_name="{0} {1}".format(author1_first_name, author1_last_name)

    author_xml='w:val="Frfattare"/><w:spacing w:before="560" w:after="120"/></w:pPr><w:r w:rsidRPr="00217644"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>Click here to enter the name of the author (first and last name)</w:t></w:r></w:p>'
    new_author_xml='w:val="Frfattare"/><w:spacing w:before="560" w:after="120"/></w:pPr><w:r w:rsidRPr="00217644"><w:t>{}</w:t></w:r></w:p>'.format(author_name)

    author2=dict_of_entries.get('Author2', None)
    if author2:
        author2_first_name=author2.get('First name', None)
        author2_last_name=author2.get('Last name', None)
        author_name2="{0} {1}".format(author2_first_name, author2_last_name)
        new_author_xml=new_author_xml+'<w:p w:rsidR="006A18DB" w:rsidRPr="00A15578" w:rsidRDefault="006A18DB" w:rsidP="00882929"><w:pPr><w:pStyle w:val="Frfattare"/><w:spacing w:before="120" w:after="120"/></w:pPr><w:r><w:t xml:space="preserve">{}</w:t></w:r></w:p>'.format(author_name2)

    content=content.replace(author_xml, new_author_xml)

    # "Other information": {"Year": "2022"
    other_information=dict_of_entries.get('Other information', None)
    if other_information:
        year=other_information.get('Year', None)
        if year:
            year_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="en-US"/></w:rPr><w:t>Click here to enter year</w:t></w:r>'
            new_year_xml='<w:t>{}</w:t></w:r>'.format(year)
            content=content.replace(year_xml, new_year_xml)

    # "Series": {"Title of series": "TRITA-EECS-EX", "No. in series": "2022:00"}
    series=dict_of_entries.get('Series', None)
    if series:
        title_of_series=series.get('Title of series', None)
        number_in_series=series.get('No. in series', None)

        trita_xml='w:val="TRITA-nummer"/><w:rPr><w:lang w:val="pt-PT"/></w:rPr></w:pPr><w:r w:rsidRPr="00E014A5"><w:rPr><w:lang w:val="pt-PT"/></w:rPr><w:t xml:space="preserve">TRITA – </w:t></w:r><w:sdt><w:sdtPr><w:id w:val="-246959913"/><w:showingPlcHdr/></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="005C767E" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>XXX-XXX 20XX</w:t></w:r><w:r w:rsidR="00BF2CC2" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>:XX</w:t>'
        new_trita_xml='w:val="TRITA-nummer"/><w:rPr><w:lang w:val="pt-PT"/></w:rPr></w:pPr><w:r w:rsidRPr="00E014A5"><w:rPr><w:lang w:val="pt-PT"/></w:rPr><w:t xml:space="preserve">{0}–{1} </w:t></w:r><w:sdt><w:sdtPr><w:id w:val="-246959913"/><w:showingPlcHdr/></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="005C767E" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t></w:t></w:r><w:r w:rsidR="00BF2CC2" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t></w:t>'.format(title_of_series,number_in_series)
        content=content.replace(trita_xml, new_trita_xml)

    return content

exams={'arkitektexamen': 'Degree of Master of Architecture',
       'civilingenjörsexamen': 'Degree of Master of Science in Engineering',
       'högskoleingenjörsexamen': 'Degree of Bachelor of Science in Engineering',
       'högskoleexamen': 'Higher Education Diploma',
       'kandidatexamen': 'Bachelors degree',
       'masterexamen': 'Degree of Master of Science',
       'magisterexamen': 'Magister',
       'clgym': 'clgym', # Civilingenjör och lärare (CLGYM)
       'ämneslärarexamen': 'Degree of Master of Science in Secondary Education',  # Ämneslärarutbildning med inriktning mot teknik, årskurs 7-9
       'kpulu': 'KPU (supplementary pedagogical education', # Kompletterande pedagogisk utbildning
       'kpufu': 'KPUFU', # Kompletterande pedagogisk utbildning för ämneslärarexamen i matematik, naturvetenskap och teknik för forskarutbildade
       'kuaut': 'KUAUT', # Kompletterande utbildning för arkitekter med avslutad utländsk utbildning
       'kuiut': 'KUIUT', # Kompletterande utbildning för ingenjörer med avslutad utländsk utbildning
       'both': 'both',   # Både civilingenjörsexamen och masterexamen
       'same': 'same'   # Både civilingenjörsexamen och masterexamen om dessa områden har samma benämnin
}

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
                      default="calendar_event.json",
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
    degree1=dict_of_entries.get('Degree1', None)
    if not degree1:
        exam=args["exam"]
    exam=degree1.get('Degree', None)

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
            if exl == exams[el].lower(): #  look at English name
                exam=e
                break
    if exam not in exams:
        print("Unknown exam {0}, choose one of {1}".format(exam, exams))        
        return

    print("exam={}".format(exam))

    title=dict_of_entries.get('Title', None)
    if title:
        language=title.get('Language', None)
    else:
        language=args["language"]

    if language == 'eng':
        language = 'en'
    elif language == 'swe':
        language = 'sv'
    else:
        print("Unknown language={}".format(language))
            
    if language not in ['sv', 'en']:
        print("Unknown language use 'sv' for Swedish or 'en' for English")
        return

    print("language={}".format(language))

    cycle=dict_of_entries.get('Cycle', None)
    if not cycle:
        cycle=args['cycle']
    if not cycle:
        cycle=1

    print("cycle={}".format(cycle))
    
    input_filename=args['file']
    if not input_filename:
        print("File name must be specified")
        return

    print("input_filename={}".format(input_filename))

    document = zipfile.ZipFile(input_filename)
    file_names=document.namelist()
    if Verbose_Flag:
        print("File names in ZIP zip file: {}".format(file_names))

    word_document_file_name='word/document.xml'
    word_docprop_custom_file_name='docProps/custom.xml'
    if word_document_file_name not in file_names:
        print("Missing file: {}".format(word_document_file_name))
        return
    
    if Verbose_Flag:
        output_filename="{0}-{1}-{2}.docx".format(input_filename[:-5], exam, language)
    else:
        output_filename="{0}-{1}.docx".format(exam, language)
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
                file_contents = removed_unneded_placeholder_text(file_contents )
            else:
                print("Unknown file {}".format(fn))
        # in any case write the file_contents out
        zipOut.writestr(fn, file_contents,  compress_type=compression)

    zipOut.close()

    document.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

