#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_DOCX_cover.py [--file cover_template.docx]
#
# Purpose: The program modifies the KTH cover (saved as a DOCX file) by inserting the different values specified either on the command line for based upon the values in a JSON file.
# Note that the coomand lines override the values in the JSON file.
#
# Command line options:
#
#  -h, --help            show this help message and exit
#  -v, --verbose         Print lots of output to stdout
#  -t, --testing         execute test code
#  -j JSON, --json JSON  JSON file for extracted data
#  --cycle CYCLE         cycle of degree project
#  --credits CREDITS     number_of_credits of degree project
#  --exam EXAM           type of exam
#  --language LANGUAGE   language sv or en for Swedish or English
#  --area AREA           area of thesis
#  --area2 AREA2         area of thesis for combined Civing. and Master's
#  --trita TRITA         trita string for thesis
#  --file FILE           DOCX template
#  -p, --picture         keep the optional picture
#  --title TITLE         title of thesis
#  --subtitle SUBTITLE   subtitle of thesis
#  --year YEAR           year
#
# Note that in the case of a combined Civing. and Master's,
# the AREA is the field of technology, while AREA2 is the main subject
#
# Output: outputs a DOCX file for the specified type of cover
#         More specifically the 'word/document.xml' within the DOCX file is modified.
#
# Example:
# ./JSON_to_DOCX_cover.py --file  Omslag_Exjobb_Eng_en-20220325.docx --exam kandidatexamen -v
#   produces kandidatexamen-en.docx
#
# ./JSON_to_DOCX_cover.py --file  Omslag_Exjobb_Eng_en-20220325.docx --exam kandidatexamen --json calendar-sv.json
#   produces kandidatexamen-sv.docx
#
# ./JSON_to_DOCX_cover.py --file  Omslag_Exjobb_Eng_en-20220325.docx --cycle 2 --credits 30.0 --area "bioteknik" --area2 "kemiteknik" --exam both --language sv  --json calendar-sv.json
#   produces both-sv.docx
#
# ./JSON_to_DOCX_cover.py --file  Omslag_Exjobb_Eng_en-20220325.docx --cycle 1 --credits 15.0 --area "Engineering and Economics" --exam högskoleingenjörsexamen --language en
#   produces högskoleingenjörsexamen-en.docx
#
# ./JSON_to_DOCX_cover.py --file  Omslag_Exjobb_Eng_en-20220325.docx --exam kandidatexamen --title "What is this title for?" --subtitle " "
#   kandidatexamen-en.docx
#   This sets the title and subtitle from the command line.
# Note that you have to pass a " " to the subtitle to override the subtitle in the calendar.json file and to remove the default subtitle placeholder text.
# 
# ./JSON_to_DOCX_cover.py --file  Omslag_Exjobb_Eng_en-20220325.docx --exam kandidatexamen --title "What is this title for?" --subtitle " " --year 2023
# produces kandidatexamen-en.docx
# the --year option sets the year shown on the cover
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

def format_credits(credits, language):
    fcredits=float(credits)
    if fcredits == round(fcredits,0):
        cred="{}".format(int(fcredits))
    else:
        cred="{}".format(round(fcredits,1))
        
    if language == 'sv' and cred.find('.') > 0:
        cred=cred.replace('.', ',')
    return cred


def transform_file(content, dict_of_entries, exam, language, cycle, keep_picture):
    global Verbose_Flag

    # remove unnecessary bookmark
    unnecessary_bookmark='<w:bookmarkStart w:id="0" w:name="_GoBack"/><w:bookmarkEnd w:id="0"/>'
    content=content.replace(unnecessary_bookmark, '')

    # remove optional picture
    if not keep_picture:
        start_marker_1='<w:pStyle w:val="Frfattare"/><w:spacing w:before="680"/><w:ind w:left="-658"/><w:jc w:val="center"/></w:pPr>'
        end_marker_1='</w:sdt>'

        start_offset_1=content.find(start_marker_1)
        if start_offset_1 > 0:
            prefix=content[:start_offset_1+len(start_marker_1)]
            end_offset_1=content.find(end_marker_1, start_offset_1+len(start_marker_1))
            if end_offset_1 > 0:
                postfix=content[end_offset_1+len(end_marker_1):]
                content=prefix + postfix

    # if te language is 'sv' then change the country from "Sweden" to "Sverige"
    sweden_xml='<w:lang w:val="en-US"/></w:rPr><w:t>Sweden</w:t>'
    sverige_xml='<w:lang w:val="sv-SE"/></w:rPr><w:t>Sverige</w:t>'
    content=content.replace(sweden_xml, sverige_xml)
    
    # if this is a Swedish language cover, then remove the English KTH logo
    english_KTH_logo='<w:r w:rsidRPr="00A15578"><w:rPr><w:noProof/><w:lang w:val="en-US"/></w:rPr><w:drawing><wp:anchor distT="0" distB="0" distL="114300" distR="114300" simplePos="0" relativeHeight="251667456" behindDoc="1" locked="0" layoutInCell="1" allowOverlap="1" wp14:anchorId="6EB69F10" wp14:editId="7BEE6404"><wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="leftMargin"><wp:posOffset>5736178</wp:posOffset></wp:positionH><wp:positionV relativeFrom="topMargin"><wp:posOffset>417830</wp:posOffset></wp:positionV><wp:extent cx="1331595" cy="240665"/><wp:effectExtent l="0" t="0" r="1905" b="6985"/><wp:wrapNone/><wp:docPr id="3" name="Bildobjekt 3" descr="English logotype for KTH Royal Institute of Technology."/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="3" name="Bildobjekt 3" descr="English logotype for KTH Royal Institute of Technology."/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId8" cstate="print"><a:extLst><a:ext uri="{28A0092B-C50C-407E-A947-70E740481C1C}"><a14:useLocalDpi xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" val="0"/></a:ext></a:extLst></a:blip><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1331595" cy="240665"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic><wp14:sizeRelH relativeFrom="page"><wp14:pctWidth>0</wp14:pctWidth></wp14:sizeRelH><wp14:sizeRelV relativeFrom="page"><wp14:pctHeight>0</wp14:pctHeight></wp14:sizeRelV></wp:anchor></w:drawing></w:r>'

    if language == 'sv':
        content=content.replace(english_KTH_logo, '')

    if exam == 'kandidatexamen':
        cycle=1
        main_subjects={ 'sv': ['teknik', 'arkitektur'], #  change the order so most frequen is first
                        'en': ['Technology', 'Architecture']
                        }

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        # "Degree1": {"Educational program": "Bachelor’s Programme in Information and Communication Technology", "programcode": "TCOMK", "Degree": "Bachelors degree", "subjectArea": "Technology"}

        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="15.0"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

    elif exam == 'högskoleexamen':
        cycle=1
        main_subjects={ 'sv': ['teknik'],
                        'en': ['Technology']
                        }

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'
        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="7.5"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)


    elif exam == 'arkitektexamen':
        cycle=2
        main_subjects={ 'sv': ['arkitektur'],
                        'en': ['Architecture']
                        }

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="30.0"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

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

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in field_of_technology[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="15.0"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

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

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in field_of_technology[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="30.0"  #  might in some cases be 15

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)


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

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="30.0" # also might be 15

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

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

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="15.0"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

    elif exam == 'clgym':
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

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'

        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="30.0"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

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

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'

        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="15.0"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)


    elif exam in ['kpulu', 'kpufu']:
        cycle=2
        main_subjects={
            'sv': [
                'ämnesdidaktik'
            ],
            'en': [
                'Subject-Based Teaching and Learning'
            ]
        }

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'

        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="15.0" # could also be 30

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

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


        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'

        field=args['area']
        if not field:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                field=degree1.get('subjectArea', None)

        # check that the subject is valid
        if field not in field_of_technology[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(field, exam))

        subjectArea=args['area2']
        if not subjectArea:
            degree2=dict_of_entries.get('Degree2', None)
            if degree2:
                subjectArea=degree1.get('subjectArea', None)


        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom teknikområdet {0} och huvudområdet {1}'.format(field, subjectArea)
        else:
            project_name='Degree Project in the Field of Technology {0} and the Main Field of Study {1}'.format(field, subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="30.0" # could also be 15

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)



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

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom teknikområdet och huvudområdet {}'.format(subjectArea)
        else:
            project_name='Degree Project in the Field of Technology and the Main Field of Study {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'

        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="30.0"  # might also be 15

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)

    elif exam == 'högskoleexamen':
        cycle=1
        main_subjects={ 'sv': ['teknik'],
                        'en': ['Technology']
                        }

        # deal with the subject line
        subject_line_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your subject area. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Degree P</w:t></w:r><w:r w:rsidR="00A15578" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>roject in Information and Communication Technology</w:t></w:r><w:r w:rsidR="001D0C1B" w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve"> </w:t>'
        
        subjectArea=args['area']
        if not subjectArea:
            degree1=dict_of_entries.get('Degree1', None)
            if degree1:
                subjectArea=degree1.get('subjectArea', None)

        # check that the subject is valid
        if subjectArea not in main_subjects[language]:
            print("An invalid subjectArea of {0} has been entered for an exam of type {1}".format(subjectArea, exam))

        if language == 'sv':
            project_name='Examensarbete inom {}'.format(subjectArea)
        else:
            project_name='Degree project in {}'.format(subjectArea)

        new_subject_line_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{}</w:t>'.format(project_name)
        content=content.replace(subject_line_xml, new_subject_line_xml, 1)

        # do the replacement in the level and points line
        leveL_points_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter first or second cycle and credits. For example. </w:t></w:r><w:r w:rsidR="005C4F74"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>First cycle 15 credits</w:t>'
        
        credits=args['credits']
        if not credits:
            credits=dict_of_entries.get('Credits', None)
            if not credits:
                credits="7.5"

        cred=format_credits(credits, language)

        level_credits_txt='{0}, {1} {2}'.format(all_levels[cycle][language], cred, all_units[language])

        new_leveL_points_xml='<w:rPr><w:rStyle w:val="Normal"/></w:rPr><w:t xml:space="preserve">{0}</w:t>'.format(level_credits_txt)
        content=content.replace(leveL_points_xml, new_leveL_points_xml, 1)


    else:
        print("Do not know how to handle an exam of type {}".format(exam))

    # add title, subtitle, and author(s)
    title_option=args['title']
    if not title_option:
        title=dict_of_entries.get('Title', None)
        if title: 
            main_title=title.get('Main title', None)
            subtitle=args['subtitle']
            if not subtitle:
                subtitle=title.get('Subtitle', None)
    else:  
        main_title=title_option            
        subtitle=args['subtitle']
        if not subtitle:
            title=dict_of_entries.get('Title', None)
            if title:
                subtitle=title.get('Subtitle', None)


    if main_title:
        title_xml='<w:pStyle w:val="Titel"/><w:spacing w:before="800"/></w:pPr><w:r w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>Click here to enter your title</w:t></w:r></w:p>'
        new_title_xml='<w:pStyle w:val="Titel"/><w:spacing w:before="800"/></w:pPr><w:r w:rsidRPr="00A15578"><w:t>{}</w:t></w:r></w:p>'.format(main_title)
        content=content.replace(title_xml, new_title_xml)

    # If there is no subtitle or it is simply a space, then delete the whole vreical to prevent the loss of vertical space
    if not subtitle or subtitle == " ":
        complete_subtitle_xml='<w:sdt><w:sdtPr><w:id w:val="-1971594218"/><w:placeholder><w:docPart w:val="4BAA847A82F14FE19642931C4B768D6D"/></w:placeholder><w:showingPlcHdr/></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:p w:rsidR="00FF3FD9" w:rsidRPr="00A15578" w:rsidRDefault="00A15578" w:rsidP="00480A58"><w:pPr><w:pStyle w:val="Subtitle"/><w:spacing w:before="120"/></w:pPr><w:r w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">Click here to enter your </w:t></w:r><w:r><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>sub</w:t></w:r><w:r w:rsidRPr="00A15578"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>title</w:t></w:r></w:p></w:sdtContent></w:sdt>'
        content=content.replace(complete_subtitle_xml, '')
    else:
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
    year=args['year']
    if not year:
        if other_information:
            year=other_information.get('Year', None)
    if year:
        year_xml='<w:rPr><w:rStyle w:val="PlaceholderText"/><w:lang w:val="en-US"/></w:rPr><w:t>Click here to enter year</w:t></w:r>'
        new_year_xml='<w:t>{}</w:t></w:r>'.format(year)
        content=content.replace(year_xml, new_year_xml)

    trita=args['trita']
    if not trita:
        # "Series": {"Title of series": "TRITA-EECS-EX", "No. in series": "2022:00"}
        series=dict_of_entries.get('Series', None)
        if series:
            title_of_series=series.get('Title of series', None)
            number_in_series=series.get('No. in series', None)
            trita="{0}–{1}".format(title_of_series,number_in_series)

        trita_xml='w:val="TRITA-nummer"/><w:rPr><w:lang w:val="pt-PT"/></w:rPr></w:pPr><w:r w:rsidRPr="00E014A5"><w:rPr><w:lang w:val="pt-PT"/></w:rPr><w:t xml:space="preserve">TRITA – </w:t></w:r><w:sdt><w:sdtPr><w:id w:val="-246959913"/><w:showingPlcHdr/></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="005C767E" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>XXX-XXX 20XX</w:t></w:r><w:r w:rsidR="00BF2CC2" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>:XX</w:t>'
        new_trita_xml='w:val="TRITA-nummer"/><w:rPr><w:lang w:val="pt-PT"/></w:rPr></w:pPr><w:r w:rsidRPr="00E014A5"><w:rPr><w:lang w:val="pt-PT"/></w:rPr><w:t xml:space="preserve">{0}</w:t></w:r><w:sdt><w:sdtPr><w:id w:val="-246959913"/><w:showingPlcHdr/></w:sdtPr><w:sdtEndPr/><w:sdtContent><w:r w:rsidR="005C767E" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t></w:t></w:r><w:r w:rsidR="00BF2CC2" w:rsidRPr="00637386"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t></w:t>'.format(trita)
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
    global args

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
                      default=None,
                      help="language sv or en for Swedish or English"
                      )

    argp.add_argument('--area',
                      type=str,
                      help="area of thesis"
                      )

    argp.add_argument('--area2',
                      type=str,
                      help="area of thesis for combined Civing. and Master's"
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

    argp.add_argument('--title',
                      type=str,
                      help="title of thesis"
                      )

    argp.add_argument('--subtitle',
                      type=str,
                      help="subtitle of thesis"
                      )

    argp.add_argument('--year',
                      type=int,
                      help="year"
                      )


    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

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
    if not exam:
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

    language=args["language"]
    if not language:
        title=dict_of_entries.get('Title', None)
        if title:
            language=title.get('Language', None)
            if language == 'eng':
                language = 'en'
            elif language == 'swe':
                language = 'sv'
            else:
                language = None

    if language not in ['sv', 'en']:
        print("Unknown language use 'sv' for Swedish or 'en' for English")
        return

    print("language={}".format(language))

    cycle=args['cycle']
    if not cycle:
        cycle=dict_of_entries.get('Cycle', None)
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
                file_contents = transform_file(xml_content, dict_of_entries, exam, language, cycle, args['picture'])
                file_contents = removed_unneded_placeholder_text(file_contents )
            else:
                print("Unknown file {}".format(fn))
        # in any case write the file_contents out
        zipOut.writestr(fn, file_contents,  compress_type=compression)

    zipOut.close()

    document.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

