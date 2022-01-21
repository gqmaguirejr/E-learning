#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./customize_LaTeX_project.py --json file.json [--file latex_project.zip] [--initialize]
#
# Purpose: The program produces a customized ZIP of a LaTeX project based upon the values in the JSON file
#
# The customied JSON is produced by create_customized_JSON_file.py
#
# Output: outputs a customized LaTeX project ZIP file: <input_filename>-modified.zip
#
# Example:
# ./customize_LaTeX_project.py --json custom_values.json --file zl1a.zip
#    produces zl1a-modified.zip
#
#
# Notes:
#    If the --initialize command line argument is given, then the existing custom content is ignored.
#    Otheriwse, if the length of the existing content is longer thane 0, the new customizeation is added at the end
#    of the existing customization.
#
#    Only limited testing has been done.
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-12-14 G. Q. Maguire Jr.
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

schools_info={'ABE': {'swe': 'Skolan för Arkitektur och samhällsbyggnad',
                      'eng': 'School of Architecture and the Built Environment'},
              'ITM': {'swe': 'Skolan för Industriell teknik och management',
                      'eng': 'School of Industrial Engineering and Management'},
              'SCI': {'swe': 'Skolan för Teknikvetenskap',
                      'eng': 'School of Engineering Sciences'},
              'CBH': {'swe': 'Skolan för Kemi, bioteknologi och hälsa',
                      'eng': 'School of Engineering Sciences in Chemistry, Biotechnology and Health'},
              'EECS': {'swe': 'Skolan för Elektroteknik och datavetenskap',
                      'eng': 'School of Electrical Engineering and Computer Science'}
              }

def lookup_school_acronym(name):
    for s in schools_info:
        if name.find(schools_info[s].get('swe')) >= 0  or name.find(schools_info[s].get('eng')) >= 0:
            return s
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

def transform_file(content, dict_of_entries):
    global Verbose_Flag
    global initialize_flag

    if initialize_flag:
        new_content=''
    elif len(content) > 0:
        new_content=content
    else:
        new_content=''

    new_content=new_content+'%% Information for inside title page\n'
    #"Author1": {"Last name": "Student", "First name": "Fake A.", "Local User Id": "u100001", "E-mail": "a@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science" }},
    author1=dict_of_entries.get('Author1')
    if author1:
        x=author1.get('Last name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\authorsLastname{"+value+'}\n'
        x=author1.get('First name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\authorsFirstname{"+value+'}\n'
        x=author1.get('E-mail')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\email{"+value+'}\n'
        x=author1.get('Local User Id')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\kthid{"+value+'}\n'
        org=author1.get('organisation')
        if org:
            school=org.get('L1')
            if school:
                school_acronym=lookup_school_acronym(school)
                value="{}".format(school_acronym)
                new_content=new_content+"\\authorsSchool{\\schoolAcronym{"+value+'}}\n'

    # possible second author
    new_content=new_content+"\n%second author information\n"
    author2=dict_of_entries.get('Author2')
    if author2:
        x=author2.get('Last name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\secondAuthorsLastname{"+value+'}\n'
        x=author2.get('First name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\secondAuthorsFirstname{"+value+'}\n'
        x=author2.get('E-mail')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\secondemail{"+value+'}\n'
        x=author2.get('Local User Id')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\secondkthid{"+value+'}\n'
        org=author2.get('organisation')
        if org:
            school=org.get('L1')
            if school:
                school_acronym=lookup_school_acronym(school)
                value="{}".format(school_acronym)
                new_content=new_content+"\\secondAuthorsSchool{\\schoolAcronym{"+value+'}}\n'

    #"Cooperation": {"Partner_name": "Företaget AB"}, 
    external_cooperation=dict_of_entries.get('Cooperation')
    if external_cooperation:
        partner_name=external_cooperation.get('Partner_name')
        if partner_name:
            value="{}".format(partner_name)
            new_content=new_content+"\n%External cooperation information\n"
            new_content=new_content+"\\hostcompany{"+value+'}\n'
            new_content=new_content+"%\\hostorganization{CERN}   \% if there was a host organization\n"

    new_content=new_content+"\n%Supervisor(s) information\n"

    #"Supervisor1": {"Last name": "Supervisor", "First name": "A. Busy", "Local User Id": "u100003", "E-mail": "sa@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science" ,"L2": "Computer Science" }}, 
    #"Supervisor2": {"Last name": "Supervisor", "First name": "Another Busy", "Local User Id": "u100003", "E-mail": "sb@kth.se", "organisation": {"L1": "School of Architecture and the Built Environment" ,"L2": "Architecture" }}, 
    #"Supervisor3": {"Last name": "Supervisor", "First name": "Third Busy", "E-mail": "sc@tu.va", "Other organisation": "Timbuktu University, Department of Pseudoscience" }, 
    supervisor1=dict_of_entries.get('Supervisor1')
    if supervisor1:
        x=supervisor1.get('Last name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorAsLastname{"+value+'}\n'
        x=supervisor1.get('First name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorAsFirstname{"+value+'}\n'
        x=supervisor1.get('E-mail')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorAsEmail{"+value+'}\n'
        x=supervisor1.get('Local User Id')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorAsKTHID{"+value+'}\n'
        org=supervisor1.get('organisation')
        if org:
            school=org.get('L1')
            if school:
                school_acronym=lookup_school_acronym(school)
                value="{}".format(school_acronym)
                new_content=new_content+"\\supervisorAsSchool{\\schoolAcronym{"+value+'}}\n'
            dept=org.get('L2')
            if dept:
                value="{}".format(dept)
                new_content=new_content+"\\supervisorAsDepartment{"+value+'}\n'
        else:
            otherorg=supervisor1.get('Other organisation')
            if otherorg:
                value="{}".format(x)
                new_content=new_content+"\\supervisorAsOrganization{"+value+'}\n'



    supervisor2=dict_of_entries.get('Supervisor2')
    if supervisor2:
        x=supervisor2.get('Last name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorBsLastname{"+value+'}\n'
        x=supervisor2.get('First name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorBsFirstname{"+value+'}\n'
        x=supervisor2.get('E-mail')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorBsEmail{"+value+'}\n'
        x=supervisor2.get('Local User Id')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorBsKTHID{"+value+'}\n'
        org=supervisor2.get('organisation')
        if org:
            school=org.get('L1')
            if school:
                school_acronym=lookup_school_acronym(school)
                value="{}".format(school_acronym)
                new_content=new_content+"\\supervisorBsSchool{\\schoolAcronym{"+value+'}}\n'
            dept=org.get('L2')
            if dept:
                value="{}".format(dept)
                new_content=new_content+"\\supervisorBsDepartment{"+value+'}\n'
        else:
            otherorg=supervisor2.get('Other organisation')
            if otherorg:
                value="{}".format(otherorg)
                new_content=new_content+"\\supervisorBsOrganization{"+value+'}\n'


    supervisor3=dict_of_entries.get('Supervisor3')
    if supervisor3:
        x=supervisor3.get('Last name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorCsLastname{"+value+'}\n'
        x=supervisor3.get('First name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorCsFirstname{"+value+'}\n'
        x=supervisor3.get('E-mail')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorCsEmail{"+value+'}\n'
        x=supervisor3.get('Local User Id')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\supervisorCsKTHID{"+value+'}\n'
        org=supervisor3.get('organisation')
        if org:
            school=org.get('L1')
            if school:
                school_acronym=lookup_school_acronym(school)
                value="{}".format(school_acronym)
                new_content=new_content+"\\supervisorCsSchool{\\schoolAcronym{"+value+'}}\n'
            dept=org.get('L2')
            if dept:
                value="{}".format(dept)
                new_content=new_content+"\\supervisorCsDepartment{"+value+'}\n'
        else:
            otherorg=supervisor3.get('Other organisation')
            if otherorg:
                value="{}".format(otherorg)
                new_content=new_content+"\\supervisorCsOrganization{"+value+'}\n'

    new_content=new_content+"\n%Examiner information\n"
    # "Examiner1": {"Last name": "Maguire Jr.", "First name": "Gerald Q.", "Local User Id": "u1d13i2c", "E-mail": "maguire@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science" ,"L2": "Computer Science" }}, 
    examiner1=dict_of_entries.get('Examiner1')
    if examiner1:
        x=examiner1.get('Last name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\examinersLastname{"+value+'}\n'
        x=examiner1.get('First name')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\examinersFirstname{"+value+'}\n'
        x=examiner1.get('E-mail')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\examinersEmail{"+value+'}\n'
        x=examiner1.get('Local User Id')
        if x:
            value="{}".format(x)
            new_content=new_content+"\\examinersKTHID{"+value+'}\n'
        org=examiner1.get('organisation')
        if org:
            school=org.get('L1')
            if school:
                school_acronym=lookup_school_acronym(school)
                value="{}".format(school_acronym)
                new_content=new_content+"\\examinersSchool{\\schoolAcronym{"+value+'}}\n'
            dept=org.get('L2')
            if dept:
                value="{}".format(dept)
                new_content=new_content+"\\examinersDepartment{"+value+'}\n'

    new_content=new_content+"\n%Date\n"
    new_content=new_content+"\n\\date{\\today}\n"

    new_content=new_content+"\n%course and program information\n"
    #"Cycle": "1", "Course code": "IA150X", "Credits": "15.0", 
    cycle=dict_of_entries.get('Cycle')
    if cycle:
        value="{}".format(cycle)
        new_content=new_content+"\\courseCycle{"+value+'}\n'
    course_code=dict_of_entries.get('Course code')
    if course_code:
        value="{}".format(course_code)
        new_content=new_content+"\\courseCode{"+value+'}\n'
    credits=dict_of_entries.get('Credits')
    if credits:
        value="{}".format(credits)
        new_content=new_content+"\\courseCredits{"+value+'}\n'

    #"Degree1": {"Educational program": "Bachelor's Programme in Information and Communication Technology","programcode": "TCOMK" ,"Degree": "Bachelors degree" ,"subjectArea": "Information and Communication Technology" }, 
    degree1=dict_of_entries.get('Degree1')
    if degree1:
        program=degree1.get('Educational program')
        if program:
            value="{}".format(program)
            new_content=new_content+"\\edprogram{"+value+'}\n'
        programcode=degree1.get('programcode')
        if programcode:
            value="{}".format(programcode)
            new_content=new_content+"\\programcode{"+value+'}\n'
        degree=degree1.get('Degree')
        if degree:
            value="{}".format(degree)
            new_content=new_content+"\\degreeName{"+value+'}\n'
        subjectArea=degree1.get('subjectArea')
        if subjectArea:
            value="{}".format(subjectArea)
            new_content=new_content+"\\subjectArea{"+value+'}\n'

    degree2=dict_of_entries.get('Degree2')
    if degree2:
        program=degree2.get('Educational program')
        if program:
            value="{}".format(program)
            new_content=new_content+"\\secondedProgram{"+value+'}\n'
        programcode=degree2.get('programcode')
        if programcode:
            value="{}".format(programcode)
            new_content=new_content+"\\secondProgramcode{"+value+'}\n'
        degree=degree2.get('Degree')
        if degree:
            value="{}".format(degree)
            new_content=new_content+"\\secondDegreeName{"+value+'}\n'
        subjectArea=degree2.get('subjectArea')
        if subjectArea:
            value="{}".format(subjectArea)
            new_content=new_content+"\\secondSubjectArea{"+value+'}\n'

    new_content=new_content+"%%%%% for DiVA's National Subject Category information\n"
    new_content=new_content+"%%% Enter one or more 3 or 5 digit codes\n"
    new_content=new_content+"%%% See https://www.scb.se/contentassets/3a12f556522d4bdc887c4838a37c7ec7/standard-for-svensk-indelning--av-forskningsamnen-2011-uppdaterad-aug-2016.pdf\n"
    new_content=new_content+"%%% See https://www.scb.se/contentassets/10054f2ef27c437884e8cde0d38b9cc4/oversattningsnyckel-forskningsamnen.pdf\n"
    new_content=new_content+"%%%%\n"
    new_content=new_content+"%%%% Some examples of these codes are shown below:\n"
    new_content=new_content+"% 102 Data- och informationsvetenskap (Datateknik)    Computer and Information Sciences\n"
    new_content=new_content+"% 10201 Datavetenskap (datalogi) Computer Sciences\n"
    new_content=new_content+"% 10202 Systemvetenskap, informationssystem och informatik (samhällsvetenskaplig inriktning under 50804)\n"
    new_content=new_content+"% Information Systems (Social aspects to be 50804)\n"
    new_content=new_content+"% 10203 Bioinformatik (beräkningsbiologi) (tillämpningar under 10610)\n"
    new_content=new_content+"% Bioinformatics (Computational Biology) (applications to be 10610)\n"
    new_content=new_content+"% 10204 Människa-datorinteraktion (interaktionsdesign) (Samhällsvetenskapliga aspekter under 50803) Human Computer Interaction (Social aspects to be 50803)\n"
    new_content=new_content+"% 10205 Programvaruteknik Software Engineering\n"
    new_content=new_content+"% 10206 Datorteknik Computer Engineering\n"
    new_content=new_content+"% 10207 Datorseende och robotik (autonoma system) Computer Vision and Robotics (Autonomous Systems)\n"
    new_content=new_content+"% 10208 Språkteknologi (språkvetenskaplig databehandling) Language Technology (Computational Linguistics)\n"
    new_content=new_content+"% 10209 Medieteknik Media and Communication Technology\n"
    new_content=new_content+"% 10299 Annan data- och informationsvetenskap Other Computer and Information Science\n"
    new_content=new_content+"%%%\n"
    new_content=new_content+"% 202 Elektroteknik och elektronik Electrical Engineering, Electronic Engineering, Information Engineering\n"
    new_content=new_content+"% 20201 Robotteknik och automation Robotics\n"
    new_content=new_content+"% 20202 Reglerteknik Control Engineering\n"
    new_content=new_content+"% 20203 Kommunikationssystem Communication Systems\n"
    new_content=new_content+"% 20204 Telekommunikation Telecommunications\n"
    new_content=new_content+"% 20205 Signalbehandling Signal Processing\n"
    new_content=new_content+"% 20206 Datorsystem Computer Systems\n"
    new_content=new_content+"% 20207 Inbäddad systemteknik Embedded Systems\n"
    new_content=new_content+"% 20299 Annan elektroteknik och elektronik Other Electrical Engineering, Electronic Engineering, Information Engineering\n"
    new_content=new_content+"%% Example for a thesis in Computer Science and Computer Systems\n"

    new_content=new_content+"\n%National Subject Categories information\n"
    #"National Subject Categories": "10201, 10206", 
    natsub=dict_of_entries.get('National Subject Categories')
    if natsub:
        value="{}".format(natsub)
        new_content=new_content+"\\nationalsubjectcategories{"+value+'}\n'

    natsub_augmented=dict_of_entries.get('National Subject Categories Augmented')
    if natsub_augmented:
        new_content=new_content+"# Modify the above national subject catergory information using the information below (remove those that are not relevant):"+'\n'        
        for category in natsub_augmented:
            category="{}".format(category)
            description="{}".format(natsub_augmented[category])
            new_content=new_content+"# national subject catergory "+category+' is '+description+'\n'


    #"Series": {"Title of series": "TRITA-EECS-EX" , "No. in series": "2021:00" }, 
    #% for entering the TRITA number for a thesis
    series=dict_of_entries.get('Series')
    if series:
        x=series.get('Title of series')
        if x:
            value1="{}".format(x)
        x=series.get('No. in series')
        if x:
            value2="{}".format(x)
        new_content=new_content+"\\trita{"+value1+'}{'+value2+'}\n'

    #\{TRITA-EECS-EX}{2021:00}


    print("new_content={}".format(new_content))
    return new_content

def main(argv):
    global Verbose_Flag
    global testing
    global initialize_flag


    argp = argparse.ArgumentParser(description="customize_LaTeX_project.py: to customize a LaTeX thesis template project")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing', required=False,
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-j', '--json',
                      type=str,
                      default="event.json",
                      help="JSON file for extracted data"
                      )

    argp.add_argument('--file',
                      type=str,
                      help="DOCX template"
                      )

    argp.add_argument('-i', '--initialize', required=False,
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    initialize_flag=args['initialize']

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
            json_string=json_string.replace('\&','&')
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

    config_file_name='custom_configuration.tex'
    if config_file_name not in file_names:
        print("Missing file: {}".format(config_file_name))
        return

    output_filename="{}-modfied.zip".format(input_filename[:-4])
    print("outputting modified data to {}".format(output_filename))

    zipOut = zipfile.ZipFile(output_filename, 'w')
    for fn in file_names:
        if Verbose_Flag:
            print("processing file: {}".format(fn))
        # copy existing file to archive
        if fn not in [config_file_name]:
            file_contents = document.read(fn)
        else:
            if Verbose_Flag:
                print("processing {}".format(fn))
            file_contents = document.read(fn).decode('utf-8')
            file_contents = transform_file(file_contents, dict_of_entries)

        # in any case write the file_contents out
        zipOut.writestr(fn, file_contents,  compress_type=compression)

    zipOut.close()

    document.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

