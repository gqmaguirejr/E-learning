#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./add_dropdows_to_DOCX_file-V2.py [--file cover_template.docx]
#
# Purpose: The program modifies the KTH cover (saved as a DOCX file) by inserting drop-down menus and other configuration for
#          a particular exam and main subject/field of technology/...
#
# This version is for the new cover introduced on 2024-06-05.
#
# Output: outputs a modified DOCX file: <input_filename>-modified.docx
#         More specifically the 'word/document.xml' within the DOCX file is modified.
#
# Example:
# ./add_dropdows_to_DOCX_file-V2.py  --language en --exam civilingenjörsexamen --file Cover_with_picture-e.docx 
#
# produces civilingenjörsexamen-en.docx
#
# Notes:
# It only works with the template file "Cover_with_picture-e.docx".
# This file was produced by the .dotx file saved as a .docx file and then the subject (fields of technology)
# pull down and level & credits pull down were manually added for the civilingenjörsexamen. 
#
# When an exam has only a single number of credits - the credits pull down is not generated.
#
#    Only limited testing - this is a program still under development
#
# There is no longer a option "cycle" - as this is set based on the exam. 
# 
# 2024-06-08 G. Q. Maguire Jr.
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

# This replaces the project name and subject
existing_subject_field='''<w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="en-US"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="en-US"/></w:rPr><w:t xml:space="preserve">Degree project in </w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="Subject area"/><w:tag w:val="subject"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="en-US"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/><w:dropDownList><w:listItem w:value="field_of_technology"/><w:listItem w:displayText="Biotechnology" w:value="Biotechnology"/><w:listItem w:displayText="Civil Engineering and Urban Management" w:value="Civil Engineering and Urban Management"/><w:listItem w:displayText="Computer Science and Engineering" w:value="Computer Science and Engineering"/><w:listItem w:displayText="Design and Product Realisation" w:value="Design and Product Realisation"/><w:listItem w:displayText="Electrical Engineering" w:value="Electrical Engineering"/><w:listItem w:displayText="Energy and Environment" w:value="Energy and Environment"/><w:listItem w:displayText="Engineering Chemistry" w:value="Engineering Chemistry"/><w:listItem w:displayText="Engineering Chemistry, Mid Sweden University – KTH" w:value="Engineering Chemistry, Mid Sweden University – KTH"/><w:listItem w:displayText="Engineering Mathematics" w:value="Engineering Mathematics"/><w:listItem w:displayText="Engineering Physics" w:value="Engineering Physics"/><w:listItem w:displayText="Industrial Engineering and Management" w:value="Industrial Engineering and Management"/><w:listItem w:displayText="Industrial Technology and Sustainability" w:value="Industrial Technology and Sustainability"/><w:listItem w:displayText="Information and Communication Technology" w:value="Information and Communication Technology"/><w:listItem w:displayText="Materials Design and Engineering" w:value="Materials Design and Engineering"/><w:listItem w:displayText="Mechanical Engineering" w:value="Mechanical Engineering"/><w:listItem w:displayText="Media Technology" w:value="Media Technology"/><w:listItem w:displayText="Medical Engineering" w:value="Medical Engineering"/><w:listItem w:displayText="Vehicle Engineering" w:value="Vehicle Engineering"/><w:listItem w:displayText="Open Entrance" w:value="Open Entrance"/></w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="en-US"/></w:rPr><w:t>field of technology</w:t></w:r>'''

def  do_first_replacement(content, r):
    start_marker_1='<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/>'
    end_marker_1='</w:sdtContent></w:sdt></w:sdtContent></w:sdt></w:p>'

    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        end_offset_1=content.find(end_marker_1, start_offset_1)
        if end_offset_1 > 0:
            postfix=content[end_offset_1:]
            content=prefix + r + postfix
    return content

def  do_first_replacement_without_sdt(content, r):
    start_marker_1='<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/>'
    end_marker_1='</w:sdtContent></w:sdt></w:sdtContent></w:sdt></w:p>'

    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        end_offset_1=content.find(end_marker_1, start_offset_1)
        if end_offset_1 > 0:
            postfix=content[end_offset_1+len(end_marker_1):]
            content=prefix + r + postfix
    return content

def  do_first_replacement_both(content, r):
    start_marker_1='<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/>'
    end_marker_1='</w:p>'

    start_offset_1=content.find(start_marker_1)
    if start_offset_1 > 0:
        prefix=content[:start_offset_1]
        end_offset_1=content.find(end_marker_1, start_offset_1)
        if end_offset_1 > 0:
            postfix=content[end_offset_1:]
            content=prefix + r + postfix
    return content


existing_cycle_credits='''<w:p w14:paraId="65742EA9" w14:textId="1845AA22" w:rsidR="00B977A8" w:rsidRPr="003E7BE3" w:rsidRDefault="00AB42B2" w:rsidP="003500EE"><w:pPr><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US"/></w:rPr></w:pPr><w:r w:rsidRPr="00AB42B2"><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US"/></w:rPr><w:t xml:space="preserve">Second cycle, </w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US"/></w:rPr><w:alias w:val="credits"/><w:tag w:val="credits"/><w:id w:val="1383295826"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:dropDownList><w:listItem w:displayText="Choose number of credits" w:value=""/><w:listItem w:displayText="30" w:value="30"/><w:listItem w:displayText="15" w:value="15"/></w:dropDownList></w:sdtPr><w:sdtContent><w:r w:rsidR="00AB7341"><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US"/></w:rPr><w:t>30</w:t></w:r></w:sdtContent></w:sdt><w:r><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US"/></w:rPr><w:t xml:space="preserve"> credits</w:t></w:r></w:p>'''

def do_second_replacement(content, r):
    start_marker_1='<w:p w14:paraId="65742EA9" w14:textId="1845AA22" w:rsidR="00B977A8" w:rsidRPr="003E7BE3" w:rsidRDefault="00AB42B2" w:rsidP="003500EE"><w:pPr><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/>'
    end_marker_2='</w:t></w:r></w:p>'

    start_offset_2=content.find(start_marker_1)
    print("start_offset_2={}".format(start_offset_2))
    if start_offset_2 > 0:
        prefix=content[:start_offset_2]
        end_offset_2=content.find(end_marker_2, start_offset_2)
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


# do the replacement in the level and points/credits line
def replacement_level_and_points(content, number_of_credits, lang_attrib, default_level, default_number_of_credits, units):
    if len(number_of_credits) > 1:

        replacement_2a=f'<w:p w14:paraId="65742EA9" w14:textId="1845AA22" w:rsidR="00B977A8" w:rsidRPr="003E7BE3" w:rsidRDefault="00AB42B2" w:rsidP="003500EE"><w:pPr><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00AB42B2"><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{default_level}, </w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:alias w:val="credits"/><w:tag w:val="credits"/><w:id w:val="1383295826"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder>'

        replacement_2b='<w:dropDownList>'
        replacement_2c=''

        for cred in number_of_credits:
            replacement_2c=replacement_2c + f'<w:listItem w:displayText="{cred}" w:value="{cred}"/>'

        replacement_2d=f'</w:dropDownList></w:sdtPr><w:sdtContent><w:r w:rsidR="00AB7341"><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{default_number_of_credits}</w:t></w:r></w:sdtContent></w:sdt><w:r><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve"> {units}'

        replacement_2=replacement_2a + replacement_2b + replacement_2c + replacement_2d
        print(f'In replacement_level_and_points: {replacement_2=}')
        return do_second_replacement(content,replacement_2)
    else:
        replacement_2=f'<w:p w14:paraId="65742EA9" w14:textId="1845AA22" w:rsidR="00B977A8" w:rsidRPr="003E7BE3" w:rsidRDefault="00AB42B2" w:rsidP="003500EE"><w:pPr><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00AB42B2"><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{default_level}, {default_number_of_credits} {units}'

        print(f'In replacement_level_and_points (single number of credits): {replacement_2=}')
        return do_second_replacement(content,replacement_2)
        

# the numeric value is the cycle
all_levels = {1: {'sv': 'Grundnivå', 'en': 'First cycle'},
              2: {'sv': 'Avancerad nivå', 'en': 'Second cycle'}
              }
all_units = {'sv': 'HP', 'en': 'credits'}

number_of_credits =[15, 30]

def transform_file(content, dict_of_entries, exam, language):
    global Verbose_Flag

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

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Major'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in main_subjects[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{main_subjects[language][0]}</w:t></w:r>'
        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement(content, replacement_1)


        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])



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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Major'

        replacement_1=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} {main_subjects[language][0]}</w:t></w:r></w:p>'

        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement_without_sdt(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])



    elif exam == 'arkitektexamen':
        cycle=2
        main_subjects={ 'sv': ['arkitektur'],
                        'en': ['Architecture']
                        }

        number_of_credits = [30]

        # deal with the subject line
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'


        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Major'

        replacement_1=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} {main_subjects[language][0]}</w:t></w:r></w:p>'

        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement_without_sdt(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])

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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='teknikområde'
        else:
            heading='field_of_technology'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in field_of_technology[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{field_of_technology[language][0]}</w:t></w:r>'

        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])



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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='teknikområde'
        else:
            heading='field of technology'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in field_of_technology[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{field_of_technology[language][0]}</w:t></w:r>'

        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")

        # do the replacement in the level and points line
        replacement_2a=f'<w:p w14:paraId="65742EA9" w14:textId="1845AA22" w:rsidR="00B977A8" w:rsidRPr="003E7BE3" w:rsidRDefault="00AB42B2" w:rsidP="003500EE"><w:pPr><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00AB42B2"><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{all_levels[cycle][language]}, </w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:alias w:val="credits"/><w:tag w:val="credits"/><w:id w:val="1383295826"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder>'

        replacement_2b='<w:dropDownList>'
        replacement_2c=''

        for cred in number_of_credits:
            replacement_2c=replacement_2c + f'<w:listItem w:displayText="{cred}" w:value="{cred}"/>'

        replacement_2d=f'</w:dropDownList></w:sdtPr><w:sdtContent><w:r w:rsidR="00AB7341"><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{number_of_credits[0]}</w:t></w:r></w:sdtContent></w:sdt><w:r><w:rPr><w:rFonts w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve"> {all_units[language]}'

        replacement_2=replacement_2a + replacement_2b + replacement_2c + replacement_2d

        print(f"{replacement_2=}")
        
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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Major'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in main_subjects[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{main_subjects[language][0]}</w:t></w:r>'
        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])
        
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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Major'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in main_subjects[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{main_subjects[language][0]}</w:t></w:r>'
        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])
        
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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='ämnesområde'
        else:
            heading='Subject area'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in main_subjects[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{main_subjects[language][0]}</w:t></w:r>'
        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])

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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='ämnesområde'
        else:
            heading='Subject area'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in main_subjects[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{main_subjects[language][0]}</w:t></w:r>'
        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])

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
        if language == 'sv':
            project_name='Examensarbete inom'
        else:
            project_name='Degree project in'

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='ämnesområde'
        else:
            heading='Subject area'

        replacement_1=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} {main_subjects[language][0]}</w:t></w:r></w:p>'

        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement_without_sdt(content, replacement_1)

        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])

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

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='teknikområde'
        else:
            heading='field of technology'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in field_of_technology[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{field_of_technology[language][0]}</w:t></w:r></w:sdtContent></w:sdt></w:sdtContent></w:sdt>'

        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")

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

        #        replacement_3d='''</w:dropDownList></w:sdtPr><w:sdtEndPr><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr></w:sdtEndPr><w:sdtContent><w:r><w:rPr><w:rStyle w:val="Normal"/></w:rPr>'''
        # To have the gray placeholder text
        replacement_3d='''</w:dropDownList></w:sdtPr><w:sdtContent><w:r><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr>'''
        replacement_3e='<w:t>{}</w:t></w:r></w:sdtContent></w:sdt>'.format(main_subjects[language][0])

        replacement_3=replacement_3a + replacement_3b + replacement_3c + replacement_3d + replacement_3e
        print(f"{replacement_3=}")

        if language == 'sv':
            replacement_1=replacement_1 + replacement_3
        else:
            #replacement_1=replacement_1 + replacement_3
            replacement_1=replacement_1 + replacement_3

        print(f"Combined replacement: c{replacement_1=}")
        # do first replacement
        content=do_first_replacement_both(content, replacement_1)


        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])



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

        if language == 'sv':
            lang_attrib='sv-SE'
        else:
            lang_attrib='en-US'

        if language == 'sv':
            heading='Huvudområde'
        else:
            heading='Major'

        replacement_1a=f'<w:p w14:paraId="25FC91DA" w14:textId="4EA0CF79" w:rsidR="005040DF" w:rsidRPr="00643E55" w:rsidRDefault="00B57F52" w:rsidP="003E7BE3"><w:pPr><w:spacing w:before="160"/><w:jc w:val="center"/><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr></w:pPr><w:r w:rsidRPr="00B57F52"><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t xml:space="preserve">{project_name} '

        replacement_1b=f'</w:t></w:r><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/></w:rPr><w:alias w:val="{heading}"/><w:tag w:val="{heading}"/><w:id w:val="6960501"/><w:placeholder><w:docPart w:val="FAD190DAA0D045A0B6C94871742ED82F"/></w:placeholder></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:sdt><w:sdtPr><w:rPr><w:rFonts w:cs="Arial"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:id w:val="1814749854"/><w:placeholder><w:docPart w:val="DefaultPlaceholder_-1854013438"/></w:placeholder><w:showingPlcHdr/>'

        #replacement_1c=f'<w:dropDownList><w:listItem w:displayText="{heading}" w:value=""/>'
        replacement_1c=f'<w:dropDownList>'

        replacement_1d=''
        for sub in main_subjects[language]:
            replacement_1d=replacement_1d + f'<w:listItem w:displayText="{sub}" w:value="{sub}"/>'

        replacement_1e=f'</w:dropDownList></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="002B3807" w:rsidRPr="00B57F52"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="{lang_attrib}"/></w:rPr><w:t>{main_subjects[language][0]}</w:t></w:r>'
        replacement_1=replacement_1a + replacement_1b + replacement_1c + replacement_1d + replacement_1e
        print(f"{replacement_1=}")
        # do first replacement
        content=do_first_replacement(content, replacement_1)


        # do the replacement in the level and points line
        content=replacement_level_and_points(content, number_of_credits, lang_attrib, all_levels[cycle][language], number_of_credits[0], all_units[language])



    else:
        print("Do not know how to handle an exam of type {}".format(exam))
    return content

exams=['arkitektexamen',
       'civilingenjörsexamen',
       'högskoleingenjörsexamen',
       'högskoleexamen',
       'kandidatexamen',
       'masterexamen',
       'magisterexamen',
       'CLGYM', # Civilingenjör och lärare (CLGYM)
       'ämneslärarexamen',  # Ämneslärarutbildning med inriktning mot teknik, årskurs 7-9
       'KPULU', # Kompletterande pedagogisk utbildning
       'KPUFU', # Kompletterande pedagogisk utbildning för ämneslärarexamen i matematik, naturvetenskap och teknik för forskarutbildade
       'KUAUT', # Kompletterande utbildning för arkitekter med avslutad utländsk utbildning
       'KUIUT', # Kompletterande utbildning för ingenjörer med avslutad utländsk utbildning
       'both',   # Både civilingenjörsexamen och masterexamen
       'same'   # Både civilingenjörsexamen och masterexamen om dessa områden har samma benämnin
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


    # json_filename=args["json"]
    # if not json_filename:
    #     print("Unknown source for the JSON information: {}".format(json_filename))
    #     return

    # # extras contains information from the command line options
    # with open(json_filename, 'r') as json_FH:
    #     try:
    #         json_string=json_FH.read()
    #         dict_of_entries=json.loads(json_string)
    #     except:
    #         print("Error in reading={}".format(json_string))
    #         return

    # if Verbose_Flag:
    #     print("read JSON: {}".format(dict_of_entries))
    dict_of_entries=dict()

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
        print("Unknown exam {0}, choose one of {1}".format(exam, exams))        
        return

    language=args["language"]
    if language not in ['sv', 'en']:
        print("Unknown language use 'sv' for Swedish or 'en' for English")
        return

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
                file_contents = transform_file(xml_content, dict_of_entries, exam, language)
                file_contents = removed_unneded_placeholder_text(file_contents )
            else:
                print("Unknown file {}".format(fn))
        # in any case write the file_contents out
        zipOut.writestr(fn, file_contents,  compress_type=compression)

    zipOut.close()

    document.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

