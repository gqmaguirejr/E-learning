#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./create_customized_JSON_file.py     [-c CANVAS_COURSE_ID]
#                                      [-j JSON]
#                                      [--language LANGUAGE]
#                                      [--author AUTHOR]
#                                      [--author2 AUTHOR2]
#                                      [--school SCHOOL]
#                                      [--courseCode COURSECODE]
#                                      [--programCode PROGRAMCODE]
#                                      [--cycle CYCLE]
#                                      [--credits CREDITS]
#                                      [--area AREA]
#                                      [--area2 AREA2]
#                                      [--numberOfSupervisors NUMBEROFSUPERVISORS]
#                                      [--Supervisor SUPERVISOR]
#                                      [--Supervisor2 SUPERVISOR2]
#                                      [--Supervisor3 SUPERVISOR3]
#                                      [--Examiner EXAMINER]
#                                      [--trita TRITA]
#
#
# LANGUAGE is eng or swe -- this is to the language of the body of the thesis
# AUTHOR, AUTHOR2, SUPERVISOR, SUPERVISOR2, SUPERVISOR3, and EXAMINER should be the user's username (i.e., their login_id)
# SCHOOL is one of ABE, CBH, EECS, ITM, or SCI
#
#
# Purpose: The program creates a JSON file of customization information
#          At least one autor's name has to be provided.
#          The program will try to guess as much information as it can based upon the Canvas course information and
#          the KTH Profile API (used to get the examiner and supervisor address information).
#
# Output: a JSON file with customized content: by default: customize.json
#
#
# Example:
# ./create_customized_JSON_file.py -c canvas_course_id --author xxxxx
#
#
# Case for a student with 3 supervisors (one of whom happens to be a teacher in the course) and with a TRITA number
# The program will generate placeholders for supervisors 2 and 3.
# ./create_customized_JSON_file.py --canvas_course_id 22156 --author xxxxx --language eng --programCode TCOMK  --numberOfSupervisors 3 --trita 'TRITA-EECS-EX-2021:00'
#
# Note that you can generate entries for additional superviors by adding a valid login name (such as xxxx) or an invalid username such as yyyy - in the later case a placeholder will be generated for the third supervisor
# ./create_customized_JSON_file.py --canvas_course_id 22156 --author aaaaa --language eng --programCode TCOMK --Supervisor2 xxxx --Supervisor3 yyyy
#
# If the examiner and supervisor are known in the course, then the input could be as simple as:
# ./create_customized_JSON_file.py --canvas_course_id 22156 --author aaaaaa --language eng --programCode TCOMK  
# In the above case, the actual student behind the obscured user name 'aaaaaa' was in a two person first cycle degree project
# and the code will correctly find the other student (if they are in a project group together in the course).

# Notes:
#    Only limited testing has been done thus far.
#
#    The program assumes that only 1st cycle degree projects can have two authors.
#    Moreover, the authors are assumed to be in the same degree project course, same program, and same school.
#    Unless the option --school is specified, the school's name for the student author(s) is guessed from the course code.
#
#    There is an assumption that there is only a single examiner.
#    The first supervisor is assumed to be a teacher in the course
#    If the examiner is specified via the --Examiner xxxx command line argument and xxxx is a login ID for a examiner in the course,
#    then this examiner will be used. Otherwise,  if the student is in a section for an examiner, this is the examiner that will be used.
#    Otherwise, if the "Examiner" assignment lissts this examiner's sortable name as the grade for this student, then this examiner will be used.
#
#    There is an assumption that there are upto three supervisors.
#    If the supervisor is specified via the --Supervisor xxxx command line argument and xxxx is login ID for a teacher in the course,
#    then this supervisor will be used. Otherwise,  if the student is in a section for an supervisor, this is the examiner that will be used.
#    Otherwise, if the "Supervisor" assignment lissts this supervisor's sortable name as the grade for this student, then this supervisor will be used.
#    Supervisor2 and Supervisor3 are treated similar to the Supervisor.
#    Note that --numberOfSupervisors d can be used to specify that there are d supervisors. Currently, d is assumed to be 1, 2, or 3.
#
#
#    If a TRITA string is supplied, it is assumed to be of the form: --trita 'TRITA-xxx-EX-yyyy:dd'
#
# The code assumes that students are in a section in the course with the course
# code in the section name. The code will also take advantage of students being
# in project groups, so you only have to give the user name for one of the
# students.
#
# If the Examiner and Supervisor "assignments" exist the code will use
# the examiner/superviors name from the "grade" of these assignments to get the
# data for the examiner and supervisor(s). Note that this code only supports
# getting information for KTH supervisors, for industrial supervisors you can
# just use a user name such as xxx - that does not exist as a KTH user name
# and the code will generate fake informaiton as a place holder for the external supervisor.

# The code uses the course code to guess what national subject catergory
# the thesis will fall into. Note that in some cases, the course name suggests
# multiple categories - so these are added and then there is a note about
# which category codes correspond to what - so that a human can edit the
# resulting JSON file to have a suitable list of category codes in it.

# If you specify a value, such as --courseCode COURSECODE it will override
# the course code detected from the section that the student is in.
# This is both for testing purposes and can be used if the student is not yet in the Canvas course.
#
# The dates from Canvas are in ISO 8601 format.
# 
# For DiVA's National Subject Category information - one should enter one or more 3 or 5 digit codes.
# These codes are defined in the following documents:
#   https://www.scb.se/contentassets/3a12f556522d4bdc887c4838a37c7ec7/standard-for-svensk-indelning--av-forskningsamnen-2011-uppdaterad-aug-2016.pdf
#   https://www.scb.se/contentassets/10054f2ef27c437884e8cde0d38b9cc4/oversattningsnyckel-forskningsamnen.pdf
#
#
#
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

import requests

import time

import pprint

from collections import defaultdict


import datetime
import isodate                  # for parsing ISO 8601 dates and times
import pytz                     # for time zones
from dateutil.tz import tzlocal

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests
global kth_host, kth_header, kth_payload

global cortina_baseUrl
global cortina_seminarlist_base_Url
global cortina_header 

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(args):
    global baseUrl, header, payload
    global Verbose_Flag
    global kth_host, kth_header, kth_payload
    
    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    config_file=args["config"]
    if Verbose_Flag:
        print("config_file={}".format(config_file))

    try:
        with open(config_file) as json_data_file:
            try:
                configuration = json.load(json_data_file)
            except:
                print("Error in parsing JSON data in config file")
                sys.exit()

            access_token=configuration["canvas"]["access_token"]

            baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}

            # The following are only used in when using get_user_by_kthid(kthid)
            kth_api=configuration.get("KTH_API", None)
            if kth_api:
                kth_key=kth_api["key"]
                kth_host=kth_api["host"]
                kth_header = {'api_key': kth_key, 'Content-Type': 'application/json', 'Accept': 'application/json' }
                kth_payload = {}
            else:
                kth_host=None

    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()

# KTH API related functions
def get_user_by_kthid(kthid):
    global kth_host, kth_header, kth_payload
    # Use the KTH API to get the user information give an orcid
    #"#{$kth_api_host}/profile/v1/kthId/#{kthid}"

    url = "{0}/profile/v1/kthId/{1}".format(kth_host, kthid)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = kth_header)
    if Verbose_Flag:
        print("result of getting profile: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return []

# Currently the address processing in only done for EECS, for the other schools only L1 and L2 addresses are added
def address_from_kth_profile(profile, language, school_acronym):
    address=dict()

    school_key=None
    dept_key=None
    division_key=None
    l2=None
    l3=None

    if not profile:             #  if there is no profile, then use use the name associated with the school_acronym
        address['L1']="{0} ({1})".format(schools_info[school_acronym][language], school_acronym)
        return address

    w=profile.get('worksFor', None)
    if not w:
        address['L1']="{0} ({1})".format(schools_info[school_acronym][language], school_acronym)
        return address
    for item in w['items']:
        path=item['path']
        path_split=path.split('/')
        if len (path_split) >= 1:
            school_key=path_split[0]
        if len(path_split) >= 2:
            dept_key=path_split[1]
        elif len(path_split) >= 3:
            division_key=path_split[2]
        else:
            print("Unexpected depth of path in address_from_kth_profile(), path={}".format(path))

    # convert the path and names to an address
    if school_key == 'a':
        school_acronym='ABE'
        if dept_key == 'ad':
            if language == 'swe':
                l2='Arkitektur'
            else:
                l2='Architecture'
        elif dept_key == 'af':
            if language == 'swe':
                l2='Byggvetenskap'
            else:
                l2='Civil and Architectural Engineering'
        elif dept_key == 'ak':
            if language == 'swe':
                l2='Filosofi och historia'
            else:
                l2='Philosophy and History'
        elif dept_key == 'ai':
            if language == 'swe':
                l2='Fastigheter och byggande'
            else:
                l2='Real Estate and Construction Management'
        elif dept_key == 'al':
            if language == 'swe':
                l2='Hållbar utveckling, miljövetenskap och teknik'
            else:
                l2='Sustainable development, Environmental science and Engineering'
        elif dept_key == 'ag':
            if language == 'swe':
                l2='Samhällsplanering och miljö'
            else:
                l2='Urban Planning and Environment'
    elif school_key == 'c':
        school_acronym='CBH'
        if dept_key == 'cg':
            if language == 'swe':
                l2='Fiber- och polymerteknologi'
            else:
                l2='Fibre- and Polymer Technology'
        elif dept_key == 'ch':
            if language == 'swe':
                l2='Genteknologi'
            else:
                l2='Gene Technology'
        elif dept_key == 'ck':
            if language == 'swe':
                l2='Industriell bioteknologi'
            else:
                l2='Industrial Biotechnology'
        elif dept_key == 'cm':
            if language == 'swe':
                l2='Ingenjörspedagogik'
            else:
                l2='Engineering Pedagogics'
        elif dept_key == 'ce':
            if language == 'swe':
                l2='Kemi'
            else:
                l2='Chemistry'
        elif dept_key == 'cf':
            if language == 'swe':
                l2='Kemiteknik'
            else:
                l2='Chemical Engineering'
        elif dept_key == 'cd':
            if language == 'swe':
                l2='Medicinteknik och hälsosystem'
            else:
                l2='Biomedical Engineering and Health Systems'
        elif dept_key == 'cj':
            if language == 'swe':
                l2='Proteinvetenskap'
            else:
                l2='Protein Science'
        elif dept_key == 'cl':
            if language == 'swe':
                l2='Teoretisk kemi och biologi'
            else:
                l2='Theoretical Chemistry and Biology'
    elif school_key == 'm':
        school_acronym='ITM'
        if dept_key == 'mje':
            if language == 'swe':
                l2='Energiteknik'
            else:
                l2='Energy Technology'
        elif dept_key == 'ml':
            if language == 'swe':
                l2='Hållbar produktionsutveckling (ML)'
            else:
                l2='Sustainable production development'
        elif dept_key == 'me':
            if language == 'swe':
                l2='Industriell ekonomi och organisation (Inst.)'
            else:
                l2='Industrial Economics and Management (Dept.)'
        elif dept_key == 'mg':
            if language == 'swe':
                l2='Industriell produktion'
            else:
                l2='Production Engineering'
        elif dept_key == 'mo':
            if language == 'swe':
                l2='Lärande'
            else:
                l2='Learning'
        elif dept_key == 'mf':
            if language == 'swe':
                l2='Maskinkonstruktion (Inst.)'
            else:
                l2='Machine Design (Dept.)'
        elif dept_key == 'mv':
            if language == 'swe':
                l2='Materialvetenskap'
            else:
                l2='Materials Science and Engineering'
    elif school_key == 's':
        school_acronym='SCI'
        if dept_key == 'sf':
            if language == 'swe':
                l2='Matematik (Inst.)'
            else:
                l2='Mathematics (Dept.)'
        elif dept_key == 'sh':
            if language == 'swe':
                l2='Fysik'
            else:
                l2='Physics'
        elif dept_key == 'sm':
            if language == 'swe':
                l2='Teknisk mekanik'
            else:
                l2='Engineering Mechanics'
        elif dept_key == 'sk':
            if language == 'swe':
                l2='Tillämpad fysik'
            else:
                l2='Applied Physics'
    elif school_key == 'j':     # level 2 and l3 have been done for EECS
        school_acronym='EECS'
        if dept_key == 'jh':
            if language == 'swe':
                l2='Datavetenskap'
            else:
                l2='Computer Science'

            if division_key == 'jhf':
                if language == 'swe':
                    l3='Kommunikationssystem, CoS'
                else:
                    l3='Communication Systems, CoS'
            elif division_key == 'jhk':
                if language == 'swe':
                    l3='Programvaruteknik och datorsystem, SCS'
                else:
                    l3='Software and Computer Systems, SCS'
            elif division_key == 'jhp':
                if language == 'swe':
                    l3='Nätverk och systemteknik'
                else:
                    l3='Network and Systems Engineering	division'
            elif division_key == 'jhs':
                if language == 'swe':
                    l3='Beräkningsvetenskap och beräkningsteknik (CST)'
                else:
                    l3='Computational Science and Technology (CST)'
            elif division_key == 'jht':
                if language == 'swe':
                    l3='Teoretisk datalogi, TCS'
                else:
                    l3='Theoretical Computer Science, TCS'
            else:
                print("Unknown division within {}".format(l2))

        elif dept_key == 'jj':
            if language == 'swe':
                l2='Elektroteknik'
            else:
                l2='Electrical Engineering'

            if division_key == 'jjd':
                if language == 'swe':
                    l3='Fusionsplasmafysik'
                else:
                    l3='Fusion Plasma Physics'
            elif division_key == 'jje':
                if language == 'swe':
                    l3=' och plasmafysik'
                else:
                    l3='Space and Plasma Physics'
            elif division_key == 'jjg':
                if language == 'swe':
                    l3='Elektronik och inbyggda system'
                else:
                    l3='Electronics and Embedded systems'
            elif division_key == 'jji':
                if language == 'swe':
                    l3='Elektroteknisk teori och konstruktion'
                else:
                    l3='Electromagnetic Engineering'
            elif division_key == 'jjn':
                if language == 'swe':
                    l3='Elkraftteknik'
                else:
                    l3='Electric Power and Energy Systems'
            else:
                print("Unknown division within {}".format(l2))

        elif dept_key == 'jm':
            if language == 'swe':
                l2='Människocentrerad teknologi'
            else:
                l2='Human Centered Technology'

            if division_key == 'jma':
                if language == 'swe':
                    l3='Medieteknik och interaktionsdesign, MID'
                else:
                    l3='Media Technology and Interaction Design, MID'
            else:
                print("Unknown division within {}".format(l2))

        elif dept_key == 'jr':
            if language == 'swe':
                l2='Intelligenta system'
            else:
                l2='Intelligent systems'

            if division_key == 'jrc':
                if language == 'swe':
                    l3='Collaborative Autonomous Systems'
                else:
                    l3='Collaborative Autonomous Systems'
            if division_key == 'jrl':
                if language == 'swe':
                    l3='Reglerteknik'
                else:
                    l3='Decision and Control Systems (Automatic Control'

            if division_key == 'jro':
                if language == 'swe':
                    l3='Teknisk informationsvetenskap'
                else:
                    l3='Information Science and Engineering'

            if division_key == 'jrq': # micro nano
                if language == 'swe':
                    l3=''
                else:
                    l3=''
            if division_key == 'jrr':
                if language == 'swe':
                    l3='Robotik, perception och lärande, RPL'
                else:
                    l3='Robotics, Perception and Learning, RPL'

            if division_key == 'jrt':
                if language == 'swe':
                    l3='Tal, musik och hörsel, TMH'
                else:
                    l3='Speech, Music and Hearing, TMH'
            else:
                print("Unknown division within {}".format(l2))


        else:
            print("Unhanded organization={}".format(w))

    if school_key:
        address['L1']="{0} ({1})".format(schools_info[school_acronym][language], school_acronym)
    if l2:
        address['L2']="{0}".format(l2)
    if l3:
        address['L3']="{0}".format(l3)
        
    return address


# Canvas related functions

def list_my_courses():
    courses_found_thus_far=[]
    # Use the Canvas API to get the list of courses for the user making the query
    #GET /api/v1/courses

    url = "{0}/courses".format(baseUrl)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting courses: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            courses_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of courses
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)
            if Verbose_Flag:
                print("result of getting courses for a paginated response: {}".format(r.text))
            page_response = r.json()  
            for p_response in page_response:  
                courses_found_thus_far.append(p_response)

    return courses_found_thus_far

def list_users_courses(user_id):
    courses_found_thus_far=[]
    # Use the Canvas API to get the list of courses for the user making the query
    # GET /api/v1/users/:user_id/courses

    url = "{0}/users/{1}/courses".format(baseUrl,user_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting courses: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            courses_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of courses
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)
            if Verbose_Flag:
                print("result of getting courses for a paginated response: {}".format(r.text))
            page_response = r.json()  
            for p_response in page_response:  
                courses_found_thus_far.append(p_response)

    return courses_found_thus_far



def canvas_course_info(course_id):
    # Use the Canvas API to get the course info for a single course
    # GET /api/v1/courses/:id

    url = "{0}/courses/{1}".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting course info: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        return r.json()
    return None


def students_in_course(course_id):
    global Verbose_Flag
    global testing
    users_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    if testing: # for testing purposes include the teachers in the list of students, so a teacher can try the "self" code paths
        extra_parameters={'per_page': '100',
                          'type': ['StudentEnrollment', 'TeacherEnrollment']
                          }
    else:
        extra_parameters={'per_page': '100',
                          'type': ['StudentEnrollment']
                          }
    r = requests.get(url, params=extra_parameters, headers = header)
    if Verbose_Flag:
        print("result of getting enrollments: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            users_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)
            page_response = r.json()  
            for p_response in page_response:  
                users_found_thus_far.append(p_response)

    return users_found_thus_far


def teachers_in_course(course_id):
    global Verbose_Flag
    global testing
    users_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100',
                      'type': ['TeacherEnrollment']
                      }
    r = requests.get(url, params=extra_parameters, headers = header)
    if Verbose_Flag:
        print("result of getting enrollments: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            users_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)
            page_response = r.json()  
            for p_response in page_response:  
                users_found_thus_far.append(p_response)

    return users_found_thus_far

def examiners_in_course(teachers):
    examiners=[]
    for t in teachers:
        
        if t['role'] == 'Examiner':
            examiners.append(t)
    #
    return examiners

def examiner_by_login_id(examiner_login_id, examiners):
    for e in examiners:
        if e['user']['login_id'] == examiner_login_id:
            return e
    return None

def examiner_by_name(sortable_name, examiners):
    for e in examiners:
        if e['user']['sortable_name'] == sortable_name:
            return e
    return None

def teacher_section_id_by_name(sortable_name, sections):
    for s in sections:
        if s['name'] == sortable_name:
            return s['id']
    #
    return None

def examiner_by_section_id(section_ids, sections, examiners):
    if not section_ids:
        return None
    for si in section_ids:
        for s in sections:
            if s['id'] == si:
                for e in examiners:
                    if e['user']['sortable_name'] == s['name']:
                        return e
    #
    return None

def supervisor_by_login_id(supervisor_login_id, supervisors):
    for e in supervisors:
        if e['user']['login_id'] == supervisor_login_id:
            return e
    return None

def supervisor_by_name(sortable_name, supervisors):
    for e in supervisors:
        if e['user']['sortable_name'] == sortable_name:
            return e
    return None

def supervisor_by_section_id(section_ids, sections, supervisors):
    if not section_ids:
        return None
    for si in section_ids:
        for s in sections:
            if s['id'] == si:
                for e in supervisors:
                    if e['user']['sortable_name'] == s['name']:
                        return e
    #
    return None

def user_profile(user_id):
    # Use the Canvas API to get the profile of a user
    #GET /api/v1/users/:user_id/profile
    url = "{0}/users/{1}/profile".format(baseUrl, user_id)
    if Verbose_Flag:
        print("user url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting profile: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return []


def members_of_groups(group_id):
    members_found_thus_far=[]

    # Use the Canvas API to get the list of members of group
    # GET /api/v1/groups/:group_id/users

    url = "{0}/groups/{1}/users".format(baseUrl, group_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting group info: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            members_found_thus_far.append(p_response['id'])

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            page_response = r.json()  
            for p_response in page_response:  
                members_found_thus_far.append(p_response['id'])
    return members_found_thus_far



def list_groups_in_course(course_id):
    groups_found_thus_far=[]

    # Use the Canvas API to get the list of groups in this course
    # GET /api/v1/courses/:course_id/groups

    url = "{0}/courses/{1}/groups".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting groups: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            groups_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            page_response = r.json()  
            for p_response in page_response:  
                groups_found_thus_far.append(p_response)
    return groups_found_thus_far

def sections_in_course(course_id):
    sections_found_thus_far=[]
    # Use the Canvas API to get the list of sections for this course
    #GET /api/v1/courses/:course_id/sections

    url = "{0}/courses/{1}/sections".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting sections: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            sections_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            page_response = r.json()  
            for p_response in page_response:  
                sections_found_thus_far.append(p_response)

    return sections_found_thus_far

def assignment_id_from_assignment_name(assignments_info, assignment_name): 
    for i in assignments_info:
        if i['name'] == assignment_name:
            return i['id']
    return False

def list_assignments(course_id):
    assignments_found_thus_far=[]
    # Use the Canvas API to get the list of assignments for the course
    #GET /api/v1/courses/:course_id/assignments

    url = "{0}/courses/{1}/assignments".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting assignments: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            assignments_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of assignments
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            if Verbose_Flag:
                print("result of getting assignments for a paginated response: {}".format(r.text))
            page_response = r.json()  
            for p_response in page_response:  
                assignments_found_thus_far.append(p_response)

    return assignments_found_thus_far

def get_grade_for_assignment(course_id, assignment_id, user_id):
    global Verbose_Flag
    # Use the Canvas API to assign a grade for an assignment
    #GET /api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id

    # Request Parameters:
    # include[] string	Associations to include with the group.
    #                   Allowed values: submission_history, submission_comments, rubric_assessment, visibility, course, user

    url = "{0}/courses/{1}/assignments/{2}/submissions/{3}".format(baseUrl, course_id, assignment_id, user_id)

    if Verbose_Flag:
        print("url: " + url)

    payload={'include[]': 'submission_comments'}

    r = requests.get(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of getting assignment: {}".format(r.text))
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return None


def get_course_info(course_id):
    global Verbose_Flag
    # Use the Canvas API to get a grading standard
    #GET /api/v1/courses/:id
    url = "{0}/courses/{1}".format(baseUrl, course_id)

    if Verbose_Flag:
        print("url: " + url)

    r = requests.get(url, headers = header)
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return None

# ----------------------------------------------------------------------
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

#EECS degree project course codes
#[DA231X, DA232X, DA233X, DA234X, DA235X, DA236X, DA239X, DA240X, DA246X, DA248X, DA250X, DA256X, DA258X, DM250X, EA236X, EA238X, EA246X, EA248X, EA249X, EA250X, EA256X, EA258X, EA260X, EA270X, EA275X, EA280X, IA249X, IA250X]

# return school acronym
def guess_school_from_course_code(course_code):
    if course_code.startswith('DA') or course_code.startswith('EA') or course_code.startswith('IA') or course_code.startswith('II'):
        return 'EECS'

    # add cases for other schools

    return None

def guess_school_from_course_name(course_name):
    for s in schools_info:
        if course_name.find(s) >= 0:
            return s
    return None


def cycle_from_course_code(course_code):
    if course_code[2] == '2':
        return 2
    elif course_code[2] == '1':
        return 1
    else:
        print("In cycle_from_course_code could not figure out cycle from course code: {}".format(course_code ))
    return None

programcodes={
    'ARKIT': {'cycle': 2,
	      'swe': 'Arkitektutbildning',
              'eng': 'Degree Programme in Architecture'},
    
    'CBIOT': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i bioteknik',
              'eng': 'Degree Programme in Biotechnology'},
    
    'CDATE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i datateknik',
              'eng': 'Degree Programme in Computer Science and Engineering'},
    
    'CDEPR': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i design och produktframtagning',
              'eng': 'Degree Programme in Design and Product Realisation'},
    
    'CELTE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i elektroteknik',
              'eng': 'Degree Programme in Electrical Engineering'},
    
    'CENMI': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i energi och miljö',
              'eng': 'Degree Programme in Energy and Environment'},
    
    'CFATE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i farkostteknik',
              'eng': 'Degree Programme in Vehicle Engineering'},
    
    'CINEK': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i industriell ekonomi',
              'eng': 'Degree Programme in Industrial Engineering and Management'},
    
    'CINTE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i informationsteknik',
              'eng': 'Degree Programme in Information and Communication Technology'},
    
    'CITEH': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i industriell teknik och hållbarhet',
              'eng': 'Degree Programme in Industrial Technology and Sustainability'},
    
    'CLGYM': {'cycle': 2,
	      'swe': 'Civilingenjör och lärare',
              'eng': 'Master of Science in Engineering and in Education'},
    'CMAST': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i maskinteknik',
              'eng': 'Degree Programme in Mechanical Engineering'},
    'CMATD': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i materialdesign',
              'eng': 'Degree Programme in Materials Design and Engineering'},
    'CMEDT': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i medicinsk teknik',
              'eng': 'Degree Programme in Medical Engineering'},
    'CMETE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i medieteknik',
              'eng': 'Degree Programme in Media Technology'},
    'COPEN': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning öppen ingång',
              'eng': 'Degree Programme Open Entrance'},
    'CSAMH': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i samhällsbyggnad',
              'eng': 'Degree Programme in Civil Engineering and Urban Management'},
    'CTFYS': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i teknisk fysik',
              'eng': 'Degree Programme in Engineering Physics'},
    'CTKEM': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i teknisk kemi',
              'eng': 'Degree Programme in Engineering Chemistry'},
    'CTMAT': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i teknisk matematik',
              'eng': 'Degree Programme in Engineering Mathematics'},
    'KPUFU': {'cycle': 2,
	      'swe': 'Kompletterande pedagogisk utbildning för ämneslärarexamen i matematik, naturvetenskap och teknik för forskarutbildade',
              'eng': 'Bridging Teacher Education Programme in Mathematics, Science and Technology for Graduates with a Third Cycle Degree'},
    'KPULU': {'cycle': 2,
	      'swe': 'Kompletterande pedagogisk utbildning',
              'eng': 'Bridging Teacher Education Programme'},
    'KUAUT': {'cycle': 2,
	      'swe': 'Kompletterande utbildning för arkitekter med avslutad utländsk utbildning',
              'eng': 'Bridging programme for architects with foreign qualifications'},
    'KUIUT': {'cycle': 2,
	      'swe': 'Kompletterande utbildning för ingenjörer med avslutad utländsk utbildning',
              'eng': 'Bridging programme for engineers with foreign qualifications'},
    'LÄRGR': {'cycle': 2,
	      'swe': 'Ämneslärarutbildning med inriktning mot teknik, årskurs 7-9',
              'eng': 'Subject Teacher Education in Technology, Secondary Education'},
    'TAEEM': {'cycle': 2,
	      'swe': 'Masterprogram, flyg- och rymdteknik',
              'eng': "Master's Programme, Aerospace Engineering, 120 credits"},
    'TAETM': {'cycle': 2,
	      'swe': 'Masterprogram, aeroelasticitet i turbomaskiner',
              'eng': "Master's Programme, Turbomachinery Aeromechanic University Training, 120 credits"},
    'TARKM': {'cycle': 2,
	      'swe': 'Masterprogram, arkitektur',
              'eng': "Master's Programme, Architecture, 120 credits"},
    'TBASA': {'cycle': 0,
	      'swe': 'Tekniskt basår, KTH Flemingsberg',
              'eng': 'Technical Preparatory Year'},
    'TBASD': {'cycle': 0,
	      'swe': 'Tekniskt basår, KTH Campus',
              'eng': 'Technical Preparatory Year'},
    'TBASE': {'cycle': 0,
	      'swe': 'Tekniskt basår, KTH Södertälje',
              'eng': 'Technical Preparatory Year'},
    'TBTMD': {'cycle': 0,
	      'swe': 'Tekniskt basår, termin 2, KTH Campus',
              'eng': 'Technical Preparatory Semester'},
    'TBTMH': {'cycle': 0,
	      'swe': 'Tekniskt basår, termin 2, KTH Flemingsberg',
              'eng': 'Technical Preparatory Semester'},
    'TBTMS': {'cycle': 0,
	      'swe': 'Tekniskt basår, termin 2, KTH Södertälje',
              'eng': 'Technical Preparatory Semester'},
    'TBYPH': {'cycle': 1,
	      'swe': 'Högskoleutbildning i byggproduktion',
              'eng': 'Degree Progr. in Construction Management'},
    'TCAEM': {'cycle': 2,
	      'swe': 'Masterprogram, husbyggnads- och anläggningsteknik',
              'eng': "Master's Programme, Civil and Architectural Engineering, 120 credits"},
    'TCOMK': {'cycle': 1,
	      'swe': 'Kandidatprogram, informations- och kommunikationsteknik',
              'eng': "Bachelor's Programme in Information and Communication Technology"},
    'TCOMM': {'cycle': 2,
	      'swe': 'Masterprogram, kommunikationssystem',
              'eng': "Master's Programme, Communication Systems, 120 credits"},
    'TCSCM': {'cycle': 2,
	      'swe': 'Masterprogram, datalogi',
              'eng': "Master's Programme, Computer Science, 120 credits"},
    'TDEBM': {'cycle': 2,
	      'swe': 'Magisterprogram, design och byggande i staden',
              'eng': "Master's Programme, Urban Development and Design, 60 credits"},
    'TDSEM': {'cycle': 2,
	      'swe': 'Masterprogram, decentraliserade smarta energisystem',
              'eng': "Master's Programme, Decentralized Smart Energy Systems, 120 credits"},
    'TDTNM': {'cycle': 2,
	      'swe': 'Masterprogram, datorsimuleringar inom teknik och naturvetenskap',
              'eng': "Master's Programme, Computer Simulations for Science and Engineering, 120 credits"},
    'TEBSM': {'cycle': 2,
	      'swe': 'Masterprogram, inbyggda system',
              'eng': "Master's Programme, Embedded Systems, 120 credits"},
    'TEEEM': {'cycle': 2,
	      'swe': 'Masterprogram, teknik och ledning för energi- och miljösystem',
              'eng': "Master's Programme, Management and Engineering of Environment and Energy, 120 credits"},
    'TEEGM': {'cycle': 2,
	      'swe': 'Masterprogram, miljöteknik',
              'eng': "Master's Programme, Environmental Engineering, 120 credits"},
    'TEFRM': {'cycle': 2,
	      'swe': 'Masterprogram, elektromagnetism, fusion och rymdteknik',
              'eng': "Master's Programme, Electromagnetics, Fusion and Space Engineering, 120 credits"},
    'TEILM': {'cycle': 2,
	      'swe': 'Magisterprogram, entreprenörskap och innovationsledning',
              'eng': "Master's Programme, Entrepreneurship and Innovation Management, 60 credits"},
    'TEINM': {'cycle': 2,
	      'swe': 'Masterprogram, innovations- och tillväxtekonomi',
              'eng': "Master's Programme, Economics of Innovation and Growth, 120 credits"},
    'TELPM': {'cycle': 2,
	      'swe': 'Masterprogram, elkraftteknik',
              'eng': "Master's Programme, Electric Power Engineering, 120 credits"},
    'TFAFK': {'cycle': 1,
	      'swe': 'Kandidatprogram, Fastighetsutveckling med fastighetsförmedling',
              'eng': "Bachelor's Programme in Property Development and Agency"},
    'TFAHM': {'cycle': 2,
	      'swe': 'Magisterprogram, fastigheter',
              'eng': "Master's Programme, Real Estate"},
    'TFOBM': {'cycle': 2,
	      'swe': 'Masterprogram, fastigheter och byggande',
              'eng': "Master's Programme, Real Estate and Construction Management, 120 credits"},
    'TFOFK': {'cycle': 1,
	      'swe': 'Kandidatprogram, fastighet och finans',
              'eng': "Bachelor's Programme in Real Estate and Finance"},
    'TFORM': {'cycle': 2,
	      'swe': 'Masterprogram, fordonsteknik',
              'eng': "Master's Programme, Vehicle Engineering, 120 credits"},
    'THSSM': {'cycle': 2,
	      'swe': 'Masterprogram, hållbar samhällsplanering och stadsutformning',
              'eng': "Master's Programme, Sustainable Urban Planning and Design, 120 credits"},
    'TIBYH': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i byggteknik och design',
              'eng': "Degree Programme in Constructional Engineering and Design"},
    'TIDAA': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i datateknik, Flemingsberg',
              'eng': "Degree Programme in Computer Engineering"},
    'TIDAB': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i datateknik, Kista',
              'eng': "Degree Programme in Computer Engineering"},
    'TIDTM': {'cycle': 2,
	      'swe': 'Masterprogram, idrottsteknologi',
              'eng': "Master's Programme, Sports Technology"},
    'TIEDB': {'cycle': 2,
	      'swe': 'Högskoleingenjörsutbildning i elektronik och datorteknik',
              'eng': "Degree Programme in Electronics and Computer Engineering"},
    'TIEEM': {'cycle': 2,
	      'swe': 'Masterprogram, innovativ uthållig energiteknik',
              'eng': "Master's Programme, Innovative Sustainable Energy Engineering, 120 credits"},
    'TIELA': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i elektroteknik, Flemingsberg',
              'eng': "Degree Programme in Electrical Engineering"},
    'TIEMM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell ekonomi',
              'eng': "Master's Programme, Industrial Engineering and Management, 120 credits"},
    'TIETM': {'cycle': 2,
	      'swe': 'Masterprogram, innovativ energiteknik',
              'eng': "Master's Programme, Energy Innovation, 120 credits"},
    'TIHLM': {'cycle': 2,
	      'swe': 'Masterprogram, innovativ teknik för en hälsosam livsmiljö',
              'eng': "Master's Programme, Innovative Technology for Healthy Living"},
    'TIIPS': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i industriell teknik och produktionsunderhåll',
              'eng': "Degree Programme in Industrial Technology and Production Maintenance"},
    'TIKED': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i kemiteknik',
              'eng': "Degree Programme in Chemical Engineering"},
    'TIMAS': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i maskinteknik, Södertälje',
              'eng': "Degree Programme in Mechanical Engineering"},
    'TIMBM': {'cycle': 2,
	      'swe': 'Masterprogram, Industriell och miljöinriktad bioteknologi',
              'eng': "Master's Programme, Industrial and Environmental Biotechnology, 120 credits"},
    'TIMEL': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i medicinsk teknik',
              'eng': "Degree Programme in Medical Technology"},
    'TIMTM': {'cycle': 2,
	      'swe': 'Masterprogram, interaktiv medieteknik',
              'eng': "Master's Programme, Interactive Media Technology, 120 credits"},
    'TINEM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell ekonomi',
              'eng': "Master's Programme, Industrial Management, 120 credits"},
    'TINNM': {'cycle': 2,
	      'swe': 'Masterprogram, information och nätverksteknologi',
              'eng': "Master's Programme, Information and Network Engineering, 120 credits"},
    'TIPDM': {'cycle': 2,
	      'swe': 'Masterprogram, integrerad produktdesign',
              'eng': "Master's Programme, Integrated Product Design, 120 credits"},
    'TIPUM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell produktutveckling',
              'eng': "Master's Programme, Engineering Design, 120 credits"},
    'TITEH': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i teknik och ekonomi',
              'eng': "Degree Programme in Engineering and Economics"},
    'TITHM': {'cycle': 2,
	      'swe': 'Masterprogram, hållbar produktionsutveckling',
              'eng': "Master's Programme, Sustainable Production Development, 120 credits"},
    'TIVNM': {'cycle': 2,
	      'swe': 'Masterprogram, ICT Innovation',
              'eng': "Master's Programme, ICT Innovation, 120 credits"},
    'TJVTM': {'cycle': 2,
	      'swe': 'Masterprogram, järnvägsteknik',
              'eng': "Master's Programme, Railway Engineering, 120 credits"},
    'TKEMM': {'cycle': 2,
	      'swe': 'Masterprogram, kemiteknik för energi och miljö',
              'eng': "Master's Programme, Chemical Engineering for Energy and Environment, 120 credits"},
    'TLODM': {'cycle': 2,
	      'swe': 'Magisterprogram, ljusdesign',
              'eng': "Master's Programme,  Architectural Lighting Design, 60 credits"},
    'TMAIM': {'cycle': 2,
	      'swe': 'Masterprogram, maskininlärning',
              'eng': "Master's Programme, Machine Learning, 120 credits"},
    'TMAKM': {'cycle': 2,
	      'swe': 'Masterprogram, matematik',
              'eng': "Master's Programme, Mathematics, 120 credits"},
    'TMBIM': {'cycle': 2,
	      'swe': 'Masterprogram, medicinsk bioteknologi',
              'eng': "Master's Programme, Medical Biotechnology, 120 credits"},
    'TMEGM': {'cycle': 2,
	      'swe': 'Masterprogram, marinteknik',
              'eng': "Master's Programme, Maritime Engineering, 120 credits"},
    'TMESM': {'cycle': 2,
	      'swe': 'Masterprogram, miljövänliga energisystem',
              'eng': "Master's Programme, Environomical Pathways for Sustainable Energy Systems, 120 credits"},
    'TMHIM': {'cycle': 2,
	      'swe': 'Masterprogram, miljöteknik och hållbar infrastruktur',
              'eng': "Master's Programme, Environmental Engineering and Sustainable Infrastructure, 120 credits"},
    'TMLEM': {'cycle': 2,
	      'swe': 'Masterprogram, medicinsk teknik',
              'eng': "Master's Programme, Medical Engineering, 120 credits"},
    'TMMMM': {'cycle': 2,
	      'swe': 'Masterprogram, makromolekylära material',
              'eng': "Master's Programme, Macromolecular Materials, 120 credits"},
    'TMMTM': {'cycle': 2,
	      'swe': 'Masterprogram, media management',
              'eng': "Master's Programme, Media Management, 120 credits"},
    'TMRSM': {'cycle': 2,
	      'swe': 'Masterprogram, marina system',
              'eng': "Master's Programme, Naval Architecture, 120 credits"},
    'TMTLM': {'cycle': 2,
	      'swe': 'Masterprogram, molekylära tekniker inom livsvetenskaperna',
              'eng': "Master's Programme, Molecular Techniques in Life Science, 120 credits"},
    'TMVTM': {'cycle': 2,
	      'swe': 'Masterprogram, molekylär vetenskap och teknik',
              'eng': "Master's Programme, Molecular Science and Engineering, 120 credits"},
    'TNEEM': {'cycle': 2,
	      'swe': 'Masterprogram, kärnenergiteknik',
              'eng': "Master's Programme, Nuclear Energy Engineering, 120 credits"},
    'TNTEM': {'cycle': 2,
	      'swe': 'Masterprogram, nanoteknik',
              'eng': "Master's Programme, Nanotechnology, 120 credits"},
    'TPRMM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell produktion',
              'eng': "Master's Programme, Production Engineering and Management, 120 credits"},
    'TSCRM': {'cycle': 2,
	      'swe': 'Masterprogram, systemteknik och robotik',
              'eng': "Master's Programme, Systems, Control and Robotics, 120 credits"},
    'TSEDM': {'cycle': 2,
	      'swe': 'Masterprogram, programvaruteknik för distribuerade system',
              'eng': "Master's Programme, Software Engineering of Distributed Systems, 120 credits"},
    'TSUEM': {'cycle': 2,
	      'swe': 'Masterprogram, hållbar energiteknik',
              'eng': "Master's Programme, Sustainable Energy Engineering, 120 credits"},
    'TSUTM': {'cycle': 2,
	      'swe': 'Masterprogram, teknik och hållbar utveckling',
              'eng': "Master's Programme, Sustainable Technology, 120 credits"},
    'TTAHM': {'cycle': 2,
	      'swe': 'Masterprogram, teknik, arbete och hälsa',
              'eng': "Master's Programme, Technology, Work and Health, 120 credits"},
    'TTEMM': {'cycle': 2,
	      'swe': 'Masterprogram, teknisk mekanik',
              'eng': "Master's Programme, Engineering Mechanics, 120 credits"},
    'TTFYM': {'cycle': 2,
	      'swe': 'Masterprogram, teknisk fysik',
              'eng': "Master's Programme, Engineering Physics, 120 credits"},
    'TTGTM': {'cycle': 2,
	      'swe': 'Masterprogram, transport och geoinformatik',
              'eng': "Master's Programme, Transport and Geoinformation Technology, 120 credits"},
    'TTMAM': {'cycle': 2,
	      'swe': 'Masterprogram, tillämpad matematik och beräkningsmatematik',
              'eng': "Master's Programme, Applied and Computational Mathematics, 120 credits"},
    'TTMIM': {'cycle': 2,
	      'swe': 'Masterprogram, transport, mobilitet och innovation',
              'eng': "Master's Programme, Transport, Mobility and Innovation"},
    'TTMVM': {'cycle': 2,
	      'swe': 'Masterprogram, teknisk materialvetenskap',
              'eng': "Master's Programme, Engineering Materials Science, 120 credits"},
    'TURSM': {'cycle': 2,
	      'swe': 'Magisterprogram, urbana studier',
              'eng': "Master's Programme, Urbanism Studies, 60 credits"},
    'TSKKM': {'cycle': 2,
	      'swe': 'Masterprogram, systemkonstruktion på kisel',
              'eng': 'Master’s Programme, System-on-Chip Design'}
}

def cycle_of_program(s):
    # replace ’ #x2019 with ' #x27
    s=s.replace(u"\u2019", "'")
    for p in programcodes:
        pname_eng=programcodes[p]['eng']
        pname_swe=programcodes[p]['swe']
        e_offset=s.find(pname_eng)
        s_offset=s.find(pname_swe)
        if (e_offset >= 0) or (s_offset >= 0):
            return programcodes[p]['cycle']
    # secondary check
    if s.find("Magisterprogram") >= 0 or s.find("Masterprogram") >= 0 or s.find("Master's") >= 0 or s.find("Master of Science") >= 0 or s.find("Civilingenjör") >= 0:
        return 2
    if s.find("Kandidatprogram") >= 0 or s.find("Bachelor's") >= 0 or s.find("Högskoleingenjör") >= 0:
        return 1
    print("cycle_of_program: Error in program name - did not match anything")
    return None

def programcode_from_degree(s):
    # replace ’ #x2019 with ' #x27
    s=s.replace(u"\u2019", "'")
    for p in programcodes:
        pname_eng=programcodes[p]['eng']
        pname_swe=programcodes[p]['swe']
        e_offset=s.find(pname_eng)
        s_offset=s.find(pname_swe)
        if (e_offset >= 0) or (s_offset >= 0):
            return p
    return None

# helper functions
def add_word_to_dictionary(d, language, word):
    global Verbose_Flag
    if Verbose_Flag:
        print("d={0}, language={1}, word={2}".format(d, language, word))
    lang_dict=d.get(language, None)
    if lang_dict is None:
        d[language]=[word]
    else:
        d[language].append(word)
    return d

def expand_school_name(school):
    si=schools_info.get(school, None)
    if si:
        return schools_info[school]['eng']
    else:
        return "Unknown"
    
#         <!-- Degree -->
#         <fieldset>
#           <div class="clearfix" id="degree_field">
#             <label for="degree">Cycle and credits of the degree project</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="degree" name="degree">
#                   <option value="tech-label" disabled="" selected="">Choose degree project</option>
#                   <option value="first-level-7">Degree project, first cycle (7.5 credits)</option>
#                   <option value="first-level-10">Degree project, first cycle (10 credits)</option>
#                   <option value="first-level-15">Degree project, first cycle (15 credits)</option>
#                   <option value="second-level-15">Degree project, second cycle (15 credits)</option>
#                   <option value="second-level-30">Degree project, second cycle (30 credits)</option>
#                   <option value="second-level-60">Degree project, second cycle (60 credits)</option>
#                 </select>
#               </div>
#             </div>
#           </div>

#           <!-- Exam -->
#           <div class="clearfix" id="exam_field">
#             <label for="exam">Degree</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="exam" name="exam" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Choose degree</option>
#                   <option class="firstLevel" value="1">Bachelors degree</option>
#                   <option class="firstLevel" value="1">Higher Education Diploma</option>
#                   <option class="firstLevel" value="2">Degree of Bachelor of Science in Engineering</option>
#                   <option class="firstLevel" value="8">Degree of Master of Science in Secondary Education</option>
#                   <option class="secondLevel" value="3">Degree of Master (60 credits)</option>
#                   <option class="secondLevel" value="3">Degree of Master (120 credits)</option>
#                   <option class="secondLevel" value="4">Degree of Master of Science in Engineering</option>
#                   <option class="secondLevel" value="5">Degree of Master of Architecture</option>
#                   <option class="secondLevel" value="6">Degree of Master of Science in Secondary Education</option>
#                   <option class="secondLevel" value="7">Both Master of science in engineering and Master</option>
#                 </select>
#               </div>
#             </div>
#           </div>
#           <!-- Major, tech or subject area -->
#           <div class="clearfix" id="area_field">
#             <label id="area_field_label_normal" for="area">Main field or subject of your degree</label>
#             <label id="area_field_label_mix" for="area">Field of technology (Master of science in engineering)</label>
#               <div class="input">
#               <div class="selectContainer">
#                 <select id="area" name="area" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Choose field of study</option>
#                   <!-- Major areas -->
#                   <option class="area-1 area-3 area-5" value="Architecture">Architecture</option>
#                   <option class="area-3" value="Biotechnology">Biotechnology</option>
#                   <option class="area-3" value="Computer Science and Engineering">Computer Science and Engineering</option>
#                   <option class="area-3" value="Electrical Engineering">Electrical Engineering</option>
#                   <option class="area-3" value="Industrial Management">Industrial Management</option>
#                   <option class="area-3" value="Information and Communication Technology">Information and Communication Technology</option>
#                   <option class="area-3" value="Chemical Science and Engineering">Chemical Science and Engineering</option>
#                   <option class="area-3" value="Mechanical Engineering">Mechanical Engineering</option>
#                   <option class="area-3" value="Mathematics">Mathematics</option>
#                   <option class="area-3" value="Materials Science and Engineering">Materials Science and Engineering</option>
#                   <option class="area-3" value="Medical Engineering">Medical Engineering</option>
#                   <option class="area-3" value="Environmental engineering">Environmental engineering</option>
#                   <option class="area-3" value="The Built Environment">The Built Environment</option>
#                   <option class="area-3" value="Technology and Economics">Technology and Economics</option>
#                   <option class="area-3" value="Technology and Health">Technology and Health</option>
#                   <option class="area-3" value="Technology and Learning">Technology and Learning</option>
#                   <option class="area-3" value="Technology and Management">Technology and Management</option>
#                   <option class="area-3" value="Engineering Physics">Engineering Physics</option>
#                   <option class="area-1 area-8" value="Technology">Technology</option>
#                   <!-- Tech areas -->
#                   <option class="area-2" value="Constructional Engineering and Design">Constructional Engineering and Design</option>
#                   <option class="area-2" value="Computer Engineering">Computer Engineering</option>
#                   <option class="area-2" value="Electronics and Computer Engineering">Electronics and Computer Engineering</option>
#                   <option class="area-2" value="Electrical Engineering">Electrical Engineering</option>
#                   <option class="area-2" value="Chemical Engineering">Chemical Engineering</option>
#                   <option class="area-2" value="Mechanical Engineering">Mechanical Engineering</option>
#                   <option class="area-2" value="Medical Technology">Medical Technology</option>
#                   <option class="area-2 area-3" value="Engineering and Economics">Engineering and Economics</option>
#                   <option class="area-4 area-7" value="Technology and Learning">Technology and Learning</option>
#                   <option class="area-4 area-7" value="Biotechnology">Biotechnology</option>
#                   <option class="area-4 area-7" value="Computer Science and Engineering">Computer Science and Engineering</option>
#                   <option class="area-4 area-7" value="Design and Product Realisation">Design and Product Realisation</option>
#                   <option class="area-4 area-7" value="Electrical Engineering">Electrical Engineering</option>
#                   <option class="area-4 area-7" value="Energy and Environment">Energy and Environment</option>
#                   <option class="area-4 area-7" value="Vehicle Engineering">Vehicle Engineering</option>
#                   <option class="area-4 area-7" value="Industrial Engineering and Management">Industrial Engineering and Management</option>
#                   <option class="area-4 area-7" value="Information and Communication Technology">Information and Communication Technology</option>
#                   <option class="area-4 area-7" value="Mechanical Engineering">Mechanical Engineering</option>
#                   <option class="area-4 area-7" value="Materials Design and Engineering">Materials Design and Engineering</option>
#                   <option class="area-4 area-7" value="Medical Engineering">Medical Engineering</option>
#                   <option class="area-4 area-7" value="Media Technology">Media Technology</option>
#                   <option class="area-4 area-7" value="Civil Engineering and Urban Management">Civil Engineering and Urban Management</option>
#                   <option class="area-4 area-7" value="Engineering Physics">Engineering Physics</option>
#                   <option class="area-4 area-7" value="Engineering Chemistry">Engineering Chemistry</option>
#                   <option class="area-4 area-7" value="Chemical Science and Engineering">Chemical Science and Engineering</option>
#                   <option class="area-4 area-7" value="Microelectronics">Microelectronics</option>
#                   <!-- Subject areas -->
#                   <option class="area-6 area-8" value="Technology and Learning">Technology and Learning</option>
#                   <option class="area-6 area-8" value="Mathematics and Learning">Mathematics and Learning</option>
#                   <option class="area-6 area-8" value="Chemistry and Learning">Chemistry and Learning</option>
#                   <option class="area-6 area-8" value="Physics and Learning">Physics and Learning</option>
#                   <option class="area-6 area-8" value="Subject-Based Teaching">Subject-Based Teaching</option>
#                 </select>
#               </div>
#             </div>
#           </div>


#             <!-- Subject area (magister) for type 7 (master of science and master-->
#             <div class="double_field" id="master_field">
#                 <label for="master">Main field of study (Degree of master)</label>
#                 <div class="input">
#                     <div class="selectContainer">
#                         <select id="master" name="master">
#                             <option class="firstLevel secondLevel" value="" disabled="" selected="">Choose field of study</option>
#                             <!-- Major areas -->
#                             <option class="area-1 area-3 area-5" value="Architecture">Architecture</option>
#                             <option class="area-3" value="Biotechnology">Biotechnology</option>
#                             <option class="area-3" value="Computer Science and Engineering">Computer Science and Engineering</option>
#                             <option class="area-3" value="Electrical Engineering">Electrical Engineering</option>
#                             <option class="area-3" value="Industrial Management">Industrial Management</option>
#                             <option class="area-3" value="Information and Communication Technology">Information and Communication Technology</option>
#                             <option class="area-3" value="Chemical Science and Engineering">Chemical Science and Engineering</option>
#                             <option class="area-3" value="Mechanical Engineering">Mechanical Engineering</option>
#                             <option class="area-3" value="Mathematics">Mathematics</option>
#                             <option class="area-3" value="Materials Science and Engineering">Materials Science and Engineering</option>
#                             <option class="area-3" value="Medical Engineering">Medical Engineering</option>
#                             <option class="area-3" value="Environmental engineering">Environmental engineering</option>
#                             <option class="area-3" value="The Built Environment">The Built Environment</option>
#                             <option class="area-3" value="Technology and Economics">Technology and Economics</option>
#                             <option class="area-3" value="Technology and Health">Technology and Health</option>
#                             <option class="area-3" value="Technology and Learning">Technology and Learning</option>
#                             <option class="area-3" value="Technology and Management">Technology and Management</option>
#                             <option class="area-3" value="Engineering Physics">Engineering Physics</option>
#                         </select>
#                     </div>
#                 </div>
#             </div>
# 					<div class="clearfix" id="year_field">
# 						<label for="year">Year</label>
# 						<div class="input">
# 							<input type="text" id="year" name="year" value="" required="">
# 						</div>
# 					</div>


# Swedish version of form:
# <div class="form">
#     		<a href="https://intra.kth.se"><img src="/kth-cover/assets/images/logotype.jpg" class="logotype"></a>

# 			<h2 class="site">KTH Intranät</h2>

# 			<div class="breadcrums" id="breadcrums">
# 				<a href="https://intra.kth.se/en">KTH INTRANÄT</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration">ADMINISTRATIVT STÖD</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation">KOMMUNIKATION - RÅD OCH VERKTYG</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation/mallar">MALLAR</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation/mallar/avhandlingarochexamensarbeten">MALLAR FÖR AVHANDLINGAR OCH EXAMENSARBETEN</a> <span class="separator">/</span>
# 				SKAPA OMSLAG TILL EXAMENSARBETE
# 			</div>

#       <h1>Skapa omslag till examensarbete</h1>
# 			<div class="langSwitcher">
				
# 					<a href="/kth-cover?l=en" title="">In English <img src="/kth-cover/assets/images/en_UK.png" class="logotype"></a>
				
# 			</div>
#       <p>Detta formulär genererar ett svenskspråkigt omslag. Om du vill ha ett engelskspråkigt omslag ska du följa länken In English till höger.</p>
#       <p>När du fyllt i examensarbetets nivå och poäng samt den examen som examenarbetet ingår i kommer möjliga alternativ för huvud-, teknik- eller ämnesområde för din examen att komma upp i rullgardinsmenyn.</p>
#       <p>För högskoleingenjörsexamen och civilingenjörsexamen ska teknikområdet anges, vilket du känner igen från namnet på ditt program. För masterexamen hittar du huvudområdet genom att slå upp kursplanen för examensarbetskursen i kurs- och programkatalogen. Om kursen har flera huvudområden så behöver du fråga någon ansvarig för programmet eller inspektera huvudområdena för de fördjupande kurser på avancerad nivå som du läst och välja det huvudområde där du läst minst 30 hp.</p>
       

# <form action="/kth-cover/kth-cover.pdf" method="POST" enctype="multipart/form-data" onsubmit="return validate()">
    

#         <!-- Degree -->
#         <fieldset>
#           <div class="clearfix" id="degree_field">
#             <label for="degree">Examensarbetets nivå och poäng</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="degree" name="degree">
#                   <option value="tech-label" disabled="" selected="">Välj examensarbete</option>
#                   <option value="first-level-7">Examensarbete, grundnivå (7,5 hp)</option>
#                   <option value="first-level-10">Examensarbete, grundnivå (10 hp)</option>
#                   <option value="first-level-15">Examensarbete, grundnivå (15 hp)</option>
#                   <option value="second-level-15">Examensarbete, avancerad nivå (15 hp)</option>
#                   <option value="second-level-30">Examensarbete, avancerad nivå (30 hp)</option>
#                   <option value="second-level-60">Examensarbete, avancerad nivå (60 hp)</option>
#                 </select>
#               </div>
#             </div>
#           </div>

#           <!-- Exam -->
#           <div class="clearfix" id="exam_field">
#             <label for="exam">Examen</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="exam" name="exam" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj examen</option>
#                   <option class="firstLevel" value="1">Kandidatexamen</option>
#                   <option class="firstLevel" value="1">Högskoleexamen</option>
#                   <option class="firstLevel" value="2">Högskoleingenjörsexamen</option>
#                   <option class="firstLevel" value="8">Ämneslärarexamen</option>
#                   <option class="secondLevel" value="3">Magisterexamen</option>
#                   <option class="secondLevel" value="3">Masterexamen</option>
#                   <option class="secondLevel" value="4">Civilingenjörsexamen</option>
#                   <option class="secondLevel" value="5">Arkitektexamen</option>
#                   <option class="secondLevel" value="6">Ämneslärarexamen</option>
#                   <option class="secondLevel" value="7">Civilingenjörs- och masterexamen</option>
#                 </select>
#               </div>
#             </div>
#           </div>

#           <!-- Major, tech or subject area -->
#           <div class="clearfix" id="area_field">
#             <label id="area_field_label_normal" for="area">Huvud-, teknik- eller ämnesområde för din examen</label>
#             <label id="area_field_label_mix" for="area">Teknikområde för civilingenjörsexamen</label>
#               <div class="input">
#               <div class="selectContainer">
#                 <select id="area" name="area" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj område</option>
#                   <!-- Major areas -->
#                   <option class="area-1 area-3 area-5" value="Arkitektur">Arkitektur</option>
#                   <option class="area-3" value="Bioteknik">Bioteknik</option>
#                   <option class="area-3" value="Datalogi och datateknik">Datalogi och datateknik</option>
#                   <option class="area-3" value="Elektroteknik">Elektroteknik</option>
#                   <option class="area-3" value="Industriell ekonomi">Industriell ekonomi</option>
#                   <option class="area-3" value="Informations- och kommunikationsteknik">Informations- och kommunikationsteknik</option>
#                   <option class="area-3" value="Kemiteknik">Kemiteknik</option>
#                   <option class="area-3" value="Maskinteknik">Maskinteknik</option>
#                   <option class="area-3" value="Matematik">Matematik</option>
#                   <option class="area-3" value="Materialteknik">Materialteknik</option>
#                   <option class="area-3" value="Medicinsk teknik">Medicinsk teknik</option>
#                   <option class="area-3" value="Miljöteknik">Miljöteknik</option>
#                   <option class="area-3" value="Samhällsbyggnad">Samhällsbyggnad</option>
#                   <option class="area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
#                   <option class="area-3" value="Teknik och hälsa">Teknik och hälsa</option>
#                   <option class="area-3" value="Teknik och lärande">Teknik och lärande</option>
#                   <option class="area-3" value="Teknik och management">Teknik och management</option>
#                   <option class="area-3" value="Teknisk fysik">Teknisk fysik</option>
#                   <option class="area-1 area-8" value="Teknik">Teknik</option>
#                   <!-- Tech areas -->
#                   <option class="area-2" value="Byggteknik och design">Byggteknik och design</option>
#                   <option class="area-2" value="Datateknik">Datateknik</option>
#                   <option class="area-2" value="Elektronik och datorteknik">Elektronik och datorteknik</option>
#                   <option class="area-2" value="Elektroteknik">Elektroteknik</option>
#                   <option class="area-2" value="Kemiteknik">Kemiteknik</option>
#                   <option class="area-2" value="Maskinteknik">Maskinteknik</option>
#                   <option class="area-2" value="Medicinsk teknik">Medicinsk teknik</option>
#                   <option class="area-2 area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
#                   <option class="area-4 area-7" value="Teknik och lärande">Teknik och lärande</option>
#                   <option class="area-4 area-7" value="Bioteknik">Bioteknik</option>
#                   <option class="area-4 area-7" value="Datateknik">Datateknik</option>
#                   <option class="area-4 area-7" value="Design och produktframtagning">Design och produktframtagning</option>
#                   <option class="area-4 area-7" value="Elektroteknik">Elektroteknik</option>
#                   <option class="area-4 area-7" value="Energi och miljö">Energi och miljö</option>
#                   <option class="area-4 area-7" value="Farkostteknik">Farkostteknik</option>
#                   <option class="area-4 area-7" value="Industriell ekonomi">Industriell ekonomi</option>
#                   <option class="area-4 area-7" value="Informationsteknik">Informationsteknik</option>
#                   <option class="area-4 area-7" value="Maskinteknik">Maskinteknik</option>
#                   <option class="area-4 area-7" value="Materialdesign">Materialdesign</option>
#                   <option class="area-4 area-7" value="Medicinsk teknik">Medicinsk teknik</option>
#                   <option class="area-4 area-7" value="Medieteknik">Medieteknik</option>
#                   <option class="area-4 area-7" value="Samhällsbyggnad">Samhällsbyggnad</option>
#                   <option class="area-4 area-7" value="Teknisk fysik">Teknisk fysik</option>
#                   <option class="area-4 area-7" value="Teknisk kemi">Teknisk kemi</option>
#                   <option class="area-4 area-7" value="Kemivetenskap">Kemivetenskap</option>
#                   <option class="area-4 area-7" value="Mikroelektronik">Mikroelektronik</option>
#                   <!-- Subject areas -->
#                   <option class="area-6 area-8" value="Teknik och lärande">Teknik och lärande</option>
#                   <option class="area-6 area-8" value="Matematik och lärande">Matematik och lärande</option>
#                   <option class="area-6 area-8" value="Kemi och lärande">Kemi och lärande</option>
#                   <option class="area-6 area-8" value="Fysik och lärande">Fysik och lärande</option>
#                   <option class="area-6 area-8" value="Ämnesdidaktik">Ämnesdidaktik</option>
#                 </select>
#               </div>
#             </div>
#           </div>


#             <!-- Subject area (magister) for type 7 (master of science and master-->
#             <div class="double_field" id="master_field">
#                 <label for="master">Huvudområde för masterexamen</label>
#                 <div class="input">
#                     <div class="selectContainer">
#                         <select id="master" name="master">
#                             <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj område</option>
#                             <!-- Major areas -->
#                             <option class="area-1 area-3 area-5" value="Arkitektur">Arkitektur</option>
#                             <option class="area-3" value="Bioteknik">Bioteknik</option>
#                             <option class="area-3" value="Datalogi och datateknik">Datalogi och datateknik</option>
#                             <option class="area-3" value="Elektroteknik">Elektroteknik</option>
#                             <option class="area-3" value="Industriell ekonomi">Industriell ekonomi</option>
#                             <option class="area-3" value="Informations- och kommunikationsteknik">Informations- och kommunikationsteknik</option>
#                             <option class="area-3" value="Kemiteknik">Kemiteknik</option>
#                             <option class="area-3" value="Maskinteknik">Maskinteknik</option>
#                             <option class="area-3" value="Matematik">Matematik</option>
#                             <option class="area-3" value="Materialteknik">Materialteknik</option>
#                             <option class="area-3" value="Medicinsk teknik">Medicinsk teknik</option>
#                             <option class="area-3" value="Miljöteknik">Miljöteknik</option>
#                             <option class="area-3" value="Samhällsbyggnad">Samhällsbyggnad</option>
#                             <option class="area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
#                             <option class="area-3" value="Teknik och hälsa">Teknik och hälsa</option>
#                             <option class="area-3" value="Teknik och lärande">Teknik och lärande</option>
#                             <option class="area-3" value="Teknik och management">Teknik och management</option>
#                             <option class="area-3" value="Teknisk fysik">Teknisk fysik</option>
#                         </select>
#                     </div>
#                 </div>
#             </div>

#             <div class="clearfix" id="title_field">
#                 <label for="title">Titel</label>

#                 <div class="input">
#                     <input type="text" id="title" name="title" value="" class="title">
#                 </div>
#                 <span class="titleHint">Du kan ange plats för radbrytningar i detta fält med &lt;br/&gt;. Övriga tillåtna taggar är de för &lt;i&gt;kursiv&lt;/i&gt;, &lt;sup&gt;upphöjd&lt;/sup&gt; eller &lt;sub&gt;nedsänkt&lt;/sub&gt; text.</span>
#             </div>

#             <div class="clearfix" id="secondaryTitle_field">
#                 <label for="title">Undertitel</label>

#                 <div class="input">
#                     <input type="text" id="secondaryTitle" name="secondaryTitle" value="" class="subtitle">
#                 </div>
#                 <span class="titleHint">Du kan ange plats för radbrytningar i detta fält med &lt;br/&gt;. Övriga tillåtna taggar är de för &lt;i&gt;kursiv&lt;/i&gt;, &lt;sup&gt;upphöjd&lt;/sup&gt; eller &lt;sub&gt;nedsänkt&lt;/sub&gt; text.</span>
#             </div>

#             <div class="clearfix" id="author_field">
#                 <label for="author">Författare</label>

#                 <div class="input">
#                     <input type="text" id="author" name="author" value="">
#                 </div>
#             </div>

#             <div class="clearfix" id="author_2_field">
#                 <label for="author_2">Författare (om ytterligare författare)</label>

#                 <div class="input">
#                     <input type="text" id="author_2" name="author_2" value="">
#                 </div>
#             </div>

#             <div id="image_field" class="clearfix">
#                 <label for="image">Här kan du ladda upp en bild till omslaget (png eller jpg)</label>

#                 <div class="input">
#                     <input type="file" name="image" id="image" class="image">
#                 </div>
#             </div>
#         </fieldset>

#         <fieldset>
#           <div class="clearfix" id="school_field">
#             <label for="school">Skola vid KTH där examensarbetet examinerades</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="school" name="school">
#                   <option value="Skolan för arkitektur och samhällsbyggnad">Skolan för arkitektur och samhällsbyggnad</option>
#                   <option value="Skolan för industriell teknik och management">Skolan för industriell teknik och management</option>
#                   <option value="Skolan för teknikvetenskap">Skolan för teknikvetenskap</option>
#                   <option value="Skolan för kemi, bioteknologi och hälsa">Skolan för kemi, bioteknologi och hälsa</option>
#                   <option value="Skolan för elektroteknik och datavetenskap">Skolan för elektroteknik och datavetenskap</option>
#                 </select>
#               </div>
#             </div>
#           </div>

# 					<div class="clearfix" id="year_field">
# 						<label for="year">År</label>
# 						<div class="input">
# 							<input type="text" id="year" name="year" value="" required="">
# 						</div>
# 					</div>
# 				</fieldset>
				
# 				<fieldset>
# 					<div class="clearfix" id="trita_field">
# 						<label for="trita">TRITA</label>
# 						<div class="input">
# 							<input type="text" id="trita" name="trita" value="">
# 						</div>
#           </div>
# 				</fieldset>
# ...

def check_for_cover_keys(data):
    required_keys=['degree', 'exam', 'area', 'title', 'author', 'year']
    print("Checking for cover keys")
    num_keys=0
    for key, value in data.items():
        if key in required_keys:
            num_keys=num_keys+1
    if num_keys < len(required_keys):
        print("misisng a required key for cover")
        return False
    return True


# Areas
program_areas = {
    'ARKIT': {'cycle': 2,
              'eng': 'Architecture', 'swe': 'Arkitektur'},
    'CBIOT': {'cycle': 2,
              'eng': 'Biotechnology', 'swe': 'Bioteknik'},
    'CDATE': {'cycle': 2,
              'eng': 'Computer Science and Engineering', 'swe': 'Datalogi och datateknik'},
    'CDEPR': {'cycle': 2,
              'eng': 'Design and Product Realisation', 'swe': 'Design och produktframtagning'},
    'CELTE': {'cycle': 2,
              'eng': 'Electrical Engineering', 'swe': 'Elektroteknik'},
    'CENMI': {'cycle': 2,
              'eng': 'Energy and Environment', 'swe': 'Energi och miljö'},
    'CFATE': {'cycle': 2,
              'eng': 'Vehicle Engineering', 'swe': 'Farkostteknik'},
    'CINEK': {'cycle': 2,
              'eng': 'Industrial Management', 'swe': 'Industriell ekonomi'},
    'CINTE': {'cycle': 2,
              'eng': 'Information and Communication Technology', 'swe': 'Informations- och kommunikationsteknik'},
    'CITEH': {'cycle': 2,
              'eng': '', 'swe': ''}, # 'Civilingenjörsutbildning i industriell teknik och hållbarhet', 'Degree Programme in Industrial Technology and Sustainability'
    'CTKEM': {'cycle': 2,
              'eng': 'Engineering Chemistry', 'swe': 'Teknisk kemi'},
    'CLGYM': {'cycle': 2,
              'eng': 'Technology and Learning', 'swe': 'Teknik och lärande'},
    'CMAST': {'cycle': 2,
              'eng': 'Mechanical Engineering', 'swe': 'Maskinteknik'},
    'CMATD': {'cycle': 2,
              'eng':'Materials Science and Engineering', 'swe': 'Materialteknik'},
    'CMEDT': {'cycle': 2,
              'eng': 'Medical Engineering', 'swe': 'Medicinsk teknik'},
    'CMETE': {'cycle': 2,
              'eng': 'Media Technology', 'swe': 'Medieteknik'},
    'COPEN': {'cycle': 2, # 'Civilingenjörsutbildning öppen ingång', 'Degree Programme Open Entrance'
	      'swe': '',
              'eng': ''},
    'CSAMH': {'cycle': 2,
              'eng': 'Civil Engineering and Urban Management', 'swe': 'Samhällsbyggnad'},
    'CTFYS': {'cycle': 2,
              'eng': 'Engineering Physics', 'swe': 'Teknisk fysik'},
    'CTMAT': {'cycle': 2,
              'eng': 'Mathematics', 'swe': 'Matematik'},
    'KPUFU': {'cycle': 2, # 'Kompletterande pedagogisk utbildning för ämneslärarexamen i matematik, naturvetenskap och teknik för forskarutbildade', 'Bridging Teacher Education Programme in Mathematics, Science and Technology for Graduates with a Third Cycle Degree'
              'eng': 'Subject-Based Teaching', 'swe':'Ämnesdidaktik'},
    'KPULU': {'cycle': 2, # 'Kompletterande pedagogisk utbildning', 'Bridging Teacher Education Programme'
              'eng': '', 'swe': ''},
    'KUAUT': {'cycle': 2, # 'Kompletterande utbildning för arkitekter med avslutad utländsk utbildning', 'Bridging programme for architects with foreign qualifications'
              'eng': 'Architecture', 'swe': 'Arkitektur'},
    'KUIUT': {'cycle': 2, # 'Kompletterande utbildning för ingenjörer med avslutad utländsk utbildning', 'Bridging programme for engineers with foreign qualifications'
              'eng': 'Architecture', 'swe': 'Arkitektur'},
    'LÄRGR': {'cycle': 2, # 'Ämneslärarutbildning med inriktning mot teknik, årskurs 7-9', 'Subject Teacher Education in Technology, Secondary Education'
              'eng': 'Subject-Based Teaching', 'swe':'Ämnesdidaktik'},
    'TAEEM': {'cycle': 2, # 'Masterprogram, flyg- och rymdteknik', "Master's Programme, Aerospace Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TAETM': {'cycle': 2, # 'Masterprogram, aeroelasticitet i turbomaskiner', "Master's Programme, Turbomachinery Aeromechanic University Training, 120 credits"
              'eng': '', 'swe': ''},
    'TARKM': {'cycle': 2, # 'Masterprogram, arkitektur', "Master's Programme, Architecture, 120 credits"
              'eng': 'Architecture', 'swe': 'Arkitektur'},
              # there are not theses for cycle 0, so skip the subject areas of these programs
    'TBYPH': {'cycle': 1, # 'Högskoleutbildning i byggproduktion', 'Degree Progr. in Construction Management'
              'eng': '', 'swe': ''},
    'TCAEM': {'cycle': 2, # 'Masterprogram, husbyggnads- och anläggningsteknik', "Master's Programme, Civil and Architectural Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TCOMK': {'cycle': 1, # 'Kandidatprogram, informations- och kommunikationsteknik', "Bachelor's Programme in Information and Communication Technology"
              'eng':  'Information and Communication Technology', 'swe': 'Informationsteknik'},
    'TCOMM': {'cycle': 2, # 'Masterprogram, kommunikationssystem', "Master's Programme, Communication Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TCSCM': {'cycle': 2, # 'Masterprogram, datalogi', "Master's Programme, Computer Science, 120 credits"
              'eng': '', 'swe': ''},
    'TDEBM': {'cycle': 2, #'Magisterprogram, design och byggande i staden',  "Master's Programme, Urban Development and Design, 60 credits"
              'eng': '', 'swe': ''},
    'TDSEM': {'cycle': 2, # 'Masterprogram, decentraliserade smarta energisystem', "Master's Programme, Decentralized Smart Energy Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TDTNM': {'cycle': 2, # 'Masterprogram, datorsimuleringar inom teknik och naturvetenskap', "Master's Programme, Computer Simulations for Science and Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TEBSM': {'cycle': 2, # 'Masterprogram, inbyggda system', "Master's Programme, Embedded Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TEEEM': {'cycle': 2, # 'Masterprogram, teknik och ledning för energi- och miljösystem', "Master's Programme, Management and Engineering of Environment and Energy, 120 credits"
              'eng': '', 'swe': ''},
    'TEEGM': {'cycle': 2, # 'Masterprogram, miljöteknik', "Master's Programme, Environmental Engineering, 120 credits"
              'eng': 'Environmental engineering', 'swe': 'Miljöteknik'},
    'TEFRM': {'cycle': 2, # 'Masterprogram, elektromagnetism, fusion och rymdteknik', "Master's Programme, Electromagnetics, Fusion and Space Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TEILM': {'cycle': 2, # 'Magisterprogram, entreprenörskap och innovationsledning', "Master's Programme, Entrepreneurship and Innovation Management, 60 credits"
              'eng': '', 'swe': ''},
    'TEINM': {'cycle': 2, # 'Masterprogram, innovations- och tillväxtekonomi', "Master's Programme, Economics of Innovation and Growth, 120 credits"
              'eng': '', 'swe': ''},
    'TELPM': {'cycle': 2, # 'Masterprogram, elkraftteknik', "Master's Programme, Electric Power Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TFAFK': {'cycle': 1, # 'Kandidatprogram, Fastighetsutveckling med fastighetsförmedling', "Bachelor's Programme in Property Development and Agency"
              'eng': '', 'swe': ''},
    'TFAHM': {'cycle': 2, # 'Magisterprogram, fastigheter', "Master's Programme, Real Estate"
              'eng': '', 'swe': ''},
    'TFOBM': {'cycle': 2, # 'Masterprogram, fastigheter och byggande', "Master's Programme, Real Estate and Construction Management, 120 credits"
              'eng': '', 'swe': ''},
    'TFOFK': {'cycle': 1, # 'Kandidatprogram, fastighet och finans', "Bachelor's Programme in Real Estate and Finance"
              'eng': '', 'swe': ''},
    'TFORM': {'cycle': 2, # 'Masterprogram, fordonsteknik', "Master's Programme, Vehicle Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'THSSM': {'cycle': 2, # 'Masterprogram, hållbar samhällsplanering och stadsutformning', "Master's Programme, Sustainable Urban Planning and Design, 120 credits"
              'eng': '', 'swe': ''},
    'TIBYH': {'cycle': 1, #  'Högskoleingenjörsutbildning i byggteknik och design', "Degree Programme in Constructional Engineering and Design"
              'eng': 'Constructional Engineering and Design', 'swe': 'Byggteknik och design'},
    'TIDAA': {'cycle': 1, # 'Högskoleingenjörsutbildning i datateknik, Flemingsberg', "Degree Programme in Computer Engineering"
              'eng': 'Computer Science and Engineering', 'swe': 'Datateknik'},
    'TIDAB': {'cycle': 1, # 'Högskoleingenjörsutbildning i datateknik, Kista', "Degree Programme in Computer Engineering"
              'eng': 'Computer Science and Engineering', 'swe': 'Datateknik'},
    'TIDTM': {'cycle': 2, # 'Masterprogram, idrottsteknologi', "Master's Programme, Sports Technology"
              'eng': '', 'swe': ''},
    'TIEDB': {'cycle': 2, # 'Högskoleingenjörsutbildning i elektronik och datorteknik', "Degree Programme in Electronics and Computer Engineering"
              'eng': 'Electronics and Computer Engineering', 'swe': 'Elektronik och datorteknik'},
    'TIEEM': {'cycle': 2, # 'Masterprogram, innovativ uthållig energiteknik', "Master's Programme, Innovative Sustainable Energy Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TIELA': {'cycle': 1, # 'Högskoleingenjörsutbildning i elektroteknik, Flemingsberg', "Degree Programme in Electrical Engineering"
              'eng': '', 'swe': ''},
    'TIEMM': {'cycle': 2, # 'Masterprogram, industriell ekonomi', "Master's Programme, Industrial Engineering and Management, 120 credits"
              'eng': '', 'swe': ''},
    'TIETM': {'cycle': 2, # 'Masterprogram, innovativ energiteknik',  "Master's Programme, Energy Innovation, 120 credits"
              'eng': '', 'swe': ''},
    'TIHLM': {'cycle': 2, # 'Masterprogram, innovativ teknik för en hälsosam livsmiljö', "Master's Programme, Innovative Technology for Healthy Living"
              'eng': '', 'swe': ''},
    'TIIPS': {'cycle': 1, # 'Högskoleingenjörsutbildning i industriell teknik och produktionsunderhåll', "Degree Programme in Industrial Technology and Production Maintenance"
              'eng': '', 'swe': ''},
    'TIKED': {'cycle': 1, # 'Högskoleingenjörsutbildning i kemiteknik', "Degree Programme in Chemical Engineering"
              'eng': '', 'swe': ''},
    'TIMAS': {'cycle': 1, # 'Högskoleingenjörsutbildning i maskinteknik, Södertälje', "Degree Programme in Mechanical Engineering"
              'eng': 'Mechanical Engineering', 'swe': 'Maskinteknik'},
    'TIMBM': {'cycle': 2, # 'Masterprogram, Industriell och miljöinriktad bioteknologi', "Master's Programme, Industrial and Environmental Biotechnology, 120 credits"
              'eng': '', 'swe': ''},
    'TIMEL': {'cycle': 1, # 'Högskoleingenjörsutbildning i medicinsk teknik', "Degree Programme in Medical Technology"
              'eng': '', 'swe': ''},
    'TIMTM': {'cycle': 2, # 'Masterprogram, interaktiv medieteknik', "Master's Programme, Interactive Media Technology, 120 credits"
              'eng': '', 'swe': ''},
    'TINEM': {'cycle': 2, # 'Masterprogram, industriell ekonomi', "Master's Programme, Industrial Management, 120 credits"
              'eng': '', 'swe': ''},
    'TINNM': {'cycle': 2, # 'Masterprogram, information och nätverksteknologi', "Master's Programme, Information and Network Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TIPDM': {'cycle': 2, # 'Masterprogram, integrerad produktdesign', "Master's Programme, Integrated Product Design, 120 credits"
              'eng': '', 'swe': ''},
    'TIPUM': {'cycle': 2, # 'Masterprogram, industriell produktutveckling', "Master's Programme, Engineering Design, 120 credits"
              'eng': '', 'swe': ''},
    'TITEH': {'cycle': 1, # 'Högskoleingenjörsutbildning i teknik och ekonomi', "Degree Programme in Engineering and Economics"
              'eng': '', 'swe': ''},
    'TITHM': {'cycle': 2, # 'Masterprogram, hållbar produktionsutveckling', "Master's Programme, Sustainable Production Development, 120 credits"
              'eng': '', 'swe': ''},
    'TIVNM': {'cycle': 2, # 'Masterprogram, ICT Innovation', "Master's Programme, ICT Innovation, 120 credits"
              'eng':  'Information and Communication Technology', 'swe': 'Informationsteknik'},
    'TJVTM': {'cycle': 2, # 'Masterprogram, järnvägsteknik', "Master's Programme, Railway Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TKEMM': {'cycle': 2, # 'Masterprogram, kemiteknik för energi och miljö', "Master's Programme, Chemical Engineering for Energy and Environment, 120 credits"
              'eng': '', 'swe': ''},
    'TLODM': {'cycle': 2, # 'Magisterprogram, ljusdesign', "Master's Programme,  Architectural Lighting Design, 60 credits"
              'eng': '', 'swe': ''},
    'TMAIM': {'cycle': 2, # 'Masterprogram, maskininlärning', "Master's Programme, Machine Learning, 120 credits"
              'eng': '', 'swe': ''},
    'TMAKM': {'cycle': 2, # 'Masterprogram, matematik', "Master's Programme, Mathematics, 120 credits"
              'eng': '', 'swe': ''},
    'TMBIM': {'cycle': 2, # 'Masterprogram, medicinsk bioteknologi', "Master's Programme, Medical Biotechnology, 120 credits"
              'eng': '', 'swe': ''},
    'TMEGM': {'cycle': 2, # 'Masterprogram, marinteknik', "Master's Programme, Maritime Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TMESM': {'cycle': 2, # 'Masterprogram, miljövänliga energisystem', "Master's Programme, Environomical Pathways for Sustainable Energy Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TMHIM': {'cycle': 2, # 'Masterprogram, miljöteknik och hållbar infrastruktur', "Master's Programme, Environmental Engineering and Sustainable Infrastructure, 120 credits"
              'eng': '', 'swe': ''},
    'TMLEM': {'cycle': 2, # 'Masterprogram, medicinsk teknik', "Master's Programme, Medical Engineering, 120 credits"
              'eng': 'Medical Technology', 'swe': 'Medicinsk teknik'},
    'TMMMM': {'cycle': 2, # 'Masterprogram, makromolekylära material', "Master's Programme, Macromolecular Materials, 120 credits"
              'eng': '', 'swe': ''},
    'TMMTM': {'cycle': 2, # 'Masterprogram, media management', "Master's Programme, Media Management, 120 credits"
              'eng': '', 'swe': ''},
    'TMRSM': {'cycle': 2, # 'Masterprogram, marina system', "Master's Programme, Naval Architecture, 120 credits"
              'eng': '', 'swe': ''},
    'TMTLM': {'cycle': 2, # 'Masterprogram, molekylära tekniker inom livsvetenskaperna', "Master's Programme, Molecular Techniques in Life Science, 120 credits"
              'eng': '', 'swe': ''},
    'TMVTM': {'cycle': 2, # 'Masterprogram, molekylär vetenskap och teknik', "Master's Programme, Molecular Science and Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TNEEM': {'cycle': 2, # 'Masterprogram, kärnenergiteknik', "Master's Programme, Nuclear Energy Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TNTEM': {'cycle': 2, # 'Masterprogram, nanoteknik', "Master's Programme, Nanotechnology, 120 credits"
              'eng': '', 'swe': ''},
    'TPRMM': {'cycle': 2, # 'Masterprogram, industriell produktion', "Master's Programme, Production Engineering and Management, 120 credits"
              'eng': '', 'swe': ''},
    'TSCRM': {'cycle': 2, # 'Masterprogram, systemteknik och robotik', "Master's Programme, Systems, Control and Robotics, 120 credits"
              'eng': '', 'swe': ''},
    'TSEDM': {'cycle': 2, # 'Masterprogram, programvaruteknik för distribuerade system', "Master's Programme, Software Engineering of Distributed Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TSUEM': {'cycle': 2, # 'Masterprogram, hållbar energiteknik', "Master's Programme, Sustainable Energy Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TSUTM': {'cycle': 2, # 'Masterprogram, teknik och hållbar utveckling', "Master's Programme, Sustainable Technology, 120 credits"
              'eng': '', 'swe': ''},
    'TTAHM': {'cycle': 2, # 'Masterprogram, teknik, arbete och hälsa', "Master's Programme, Technology, Work and Health, 120 credits"
              'eng': 'Technology and Health', 'swe': 'Teknik och hälsa'},
    'TTEMM': {'cycle': 2, # 'Masterprogram, teknisk mekanik', "Master's Programme, Engineering Mechanics, 120 credits"
              'eng': '', 'swe': ''},
    'TTFYM': {'cycle': 2, # 'Masterprogram, teknisk fysik', "Master's Programme, Engineering Physics, 120 credits"
              'eng': 'Engineering Physics', 'swe': 'Teknisk fysik',},
    'TTGTM': {'cycle': 2, # 'Masterprogram, transport och geoinformatik', "Master's Programme, Transport and Geoinformation Technology, 120 credits"
              'eng': '', 'swe': ''},
    'TTMAM': {'cycle': 2, # 'Masterprogram, tillämpad matematik och beräkningsmatematik', "Master's Programme, Applied and Computational Mathematics, 120 credits"
              'eng': '', 'swe': ''},
    'TTMIM': {'cycle': 2, # 'Masterprogram, transport, mobilitet och innovation', "Master's Programme, Transport, Mobility and Innovation"
              'eng': '', 'swe': ''},
    'TTMVM': {'cycle': 2, # 'Masterprogram, teknisk materialvetenskap', "Master's Programme, Engineering Materials Science, 120 credits"
              'eng': '', 'swe': ''},
    'TURSM': {'cycle': 2, # 'Magisterprogram, urbana studier', "Master's Programme, Urbanism Studies, 60 credits
              'eng': '', 'swe': ''},
    #

    # 'eng': 'Electrical Engineering', 'swe': 'Elektroteknik',
    # 'eng': 'Engineering and Economics'. 'swe': '',
    # 'eng': 'Industrial Engineering and Management', 'swe': 'Industriell ekonomi',
    # 'eng': 'Materials Design and Engineering', 'swe': 'Materialdesign',
    # 'eng': 'Microelectronics', 'swe': 'Mikroelektronik',
    # 'eng': 'The Built Environment', 'swe': 'Samhällsbyggnad',

    # 'eng': 'Chemistry and Learning', 'swe': 'Kemi och lärande',
    # 'eng': 'Mathematics and Learning', 'swe': 'Matematik och lärande',
    # 'eng': 'Physics and Learning', 'swe': 'Fysik och lärande',
    # 'eng': 'Technology and Economics', 'swe': 'Teknik och ekonomi',
    # 'eng': 'Technology and Learning', 'swe': 'Teknik och lärande',
    # 'eng': 'Technology and Management', 'swe': 'Teknik och management',
    # 'eng': 'Technology', 'swe': 'Teknik',

}

# for combined Civing. and Master's
# <!-- Subject area (magister) for type 7 (master of science and master-->
program_areas2 = {
    'Architecture': {'eng': 'Architecture', 'swe': 'Arkitektur'},
    'Biotechnology':  {'eng': 'Biotechnology', 'swe': 'Bioteknik'},
    'Computer Science and Engineering': {'eng': 'Computer Science and Engineering', 'swe': 'Datalogi och datateknik'},
    'Electrical Engineering': {'eng':  'Electrical Engineering', 'swe': 'Elektroteknik'},
    'Industrial Management': { 'eng': 'Industrial Management', 'swe': 'Industriell ekonomi'},
    'Information and Communication Technology': { 'eng': 'Information and Communication Technology', 'swe': 'Informations- och kommunikationsteknik'},
    'Chemical Science and Engineering': {'eng': 'Chemical Science and Engineering', 'swe': 'Kemiteknik'},
    'Mechanical Engineering': {'eng': 'Mechanical Engineering', 'swe': 'Maskinteknik'},
    'Mathematics': {'eng' 'Mathematics', 'Matematik'},
    'Materials Science and Engineering': {'eng': 'Materials Science and Engineering', 'swe': 'Materialteknik'},
    'Medical Engineering': {'eng': 'Medical Engineering', 'swe': 'Medicinsk teknik'},
    'Environmental engineering': {'eng': 'Environmental engineering', 'swe': 'Miljöteknik'},
    'The Built Environment': {'eng': 'The Built Environment', 'swe': 'Samhällsbyggnad'},
    'Technology and Economics': {'eng': 'Technology and Economics', 'swe': 'Teknik och ekonomi'},
    'Technology and Health': {'eng': 'Technology and Health', 'swe': 'Teknik och hälsa'},
    'Technology and Learning': {'eng': 'Technology and Learning', 'swe': 'Teknik och lärande'},
    'Technology and Management': {'eng': 'Technology and Management', 'swe': 'Teknik och management'},
    'Engineering Physics': {'eng': 'Engineering Physics', 'swe': 'Teknisk fysik'},
}

def transform_file(content, dict_of_entries):
    global Keep_picture_flag

    for control_box in dict_of_entries:
        # 'language' is a pseudo control box, it reflects the language of the thesis title
        # We use it to change the language for the address on the cover
        if control_box == 'language' and  dict_of_entries['language'] != 'swe':
            content=content.replace('Stockholm, Sverige', 'Stockholm, Sweden')
        else:
            value=dict_of_entries[control_box]
            content=enter_field(content, control_box, value)
    if not Keep_picture_flag:
        # remove the optional picture
        content=remove_optionalPicture(content)
    return content

def guess_degree_project_course(courses):
    # compute a dict of course ids (as integers) and corresponding course name
    course_id_and_names=dict()
    for c in courses:
        course_id_and_names[int(c['id'])]=c['name']
 
    clist=sorted(course_id_and_names.keys())
    clist.reverse()             #  note that reverse reversees the list in place and returns None
    for c in clist:
        # look for latest degree project course 'Degree Projects at'
        if course_id_and_names[c].startswith('Degree Projects at'):
            return c

        elif course_id_and_names[c][2].isdigit() and course_id_and_names[c][3].isdigit() and course_id_and_names[c][4].isdigit() and course_id_and_names[c][5] == 'X': # or a course name of hte form lldddX*
            return c
        else:
            continue
    return None

# Note that this will return one of the enrollments in the course for the user
def student_from_students_by_id(canvas_user_id, students):
    for student in students:
        if student['user_id'] == canvas_user_id:
            return student
    return None

# Note that this will return one of the enrollments in the course for the user
def student_from_students_by_login_id(login_id, students):
    for student in students:
        if login_id == student['user']['login_id']:
            return student
    return None

# A given student can be enrolled in many sections, but one will have a 'section_integration_id'
# and for that enrollment we wanted the 'sis_section_id'
def sis_section_id_from_students_by_id(canvas_user_id, students):
    for student in students:
        if student['user_id'] == canvas_user_id and student['section_integration_id']:
            return student['sis_section_id']
    return None

def section_ids_for_students_by_id(canvas_user_id, students):
    section_ids=[]
    for student in students:
        #print("student={}".format(student))
        if student['user_id'] == canvas_user_id and not student['section_integration_id']:
            section_ids.append(student['course_section_id'])
    return section_ids

def guess_area_from_section_name(cycle, section_name):
    if not cycle or not section_name:
        return None

    if cycle == 1 and section_name.endswith('grundnivå'):
        area=section_name.replace('grundnivå', '')
    elif cycle == 1 and section_name.endswith('First Cycle'):
        area=section_name.replace('First Cycle', '')
    elif cycle == 2 and section_name.endswith('avancerad nivå'):
        area=section_name.replace('avancerad nivå', '')
    elif cycle == 2 and section_name.endswith('Second Cycle'):
        area=section_name.replace('Second Cycle', '')
    else:
        print("Unexpected sis_section string")
        return None

    area=area.strip()      # trim off leading and trailing spaces
    if area.endswith(','): # trim off trailing comma
        area=area[:-1]

    # list of patterns to apply in order
    patterns=['Degree Project in',
              'Examensarbete inom',
              'Examensarbete i'
              ]
              
    for pattern in patterns:
        pattern_offset=area.find(pattern)
        if pattern_offset >= 0:
            area=area[pattern_offset+len(pattern):]
            return area.strip()
    return None

#
#  Architecture
#  Biotechnology
# Computer Science and Engineering
# Electrical Engineering
# Industrial Management
# Information and Communication Technology
# Chemical Science and Engineering
# Mechanical Engineering
# Mathematics
# Materials Science and Engineering
# Medical Engineering
# Environmental engineering
# The Built Environment
# Technology and Economics
# Technology and Health
# Technology and Learning
# Technology and Management
# Engineering Physics
# Technology
# -- Tech areas -
# Constructional Engineering and Design
# Computer Engineering
# Electronics and Computer Engineering
# Electrical Engineering
# Chemical Engineering
# Mechanical Engineering
# Medical Technology
# Engineering and Economics
# Technology and Learning
# Biotechnology
# Computer Science and Engineering
# Design and Product Realisation
# Electrical Engineering
# Energy and Environment
# Vehicle Engineering
# Industrial Engineering and Management
# Information and Communication Technology
# Mechanical Engineering
# Materials Design and Engineering
# Medical Engineering
# Media Technology
# Civil Engineering and Urban Management
# Engineering Physics
# Engineering Chemistry
# Chemical Science and Engineering
# Microelectronics
# -- Subject areas (for teaching) --
# Technology and Learning
# Mathematics and Learning
# Chemistry and Learning
# Physics and Learning
# Subject-Based Teaching

def add_national_subject_category(category):
    global national_subject_category
    if len(national_subject_category) == 0:
        national_subject_category=category
    else:
        national_subject_category=national_subject_category+', '+category
    return national_subject_category

def add_national_subject_category_augmented(category, description):
    global national_subject_category_augmented
    if not national_subject_category_augmented:
        national_subject_category_augmented=dict()

    existing_description=national_subject_category_augmented.get(category)
    if existing_description and existing_description != description:
        print("Existing national_subject_category_augmented entry for category {0}  with definition {1} and new definition {2}".format(category,existing_description, description))
    else:
        national_subject_category_augmented[category]=description
    return national_subject_category_augmented


def main(argv):
    global Verbose_Flag
    global testing
    global Keep_picture_flag
    global national_subject_category
    global national_subject_category_augmented

    argp = argparse.ArgumentParser(description="create_customized_JSON_file.py: to make a customized JSON file")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")

    argp.add_argument('-c', '--canvas_course_id',
                      default=0,
                      type=int,
                      help="Canvas course id"
                      )

    argp.add_argument('-j', '--json',
                      type=str,
                      default="customize.json",
                      help="output JSON file"
                      )

    argp.add_argument('--language',
                      type=str,
                      help="code for planned language of the thesis (eng or swe)"
                      )

    argp.add_argument('--author',
                      type=str,
                      help="login ID without the @kth.se"
                      )

    argp.add_argument('--author2',
                      type=str,
                      help="login ID of second without the @kth.se"
                      )

    argp.add_argument('--school',
                      type=str,
                      help="acronyms for school"
                      )

    argp.add_argument('--courseCode',
                      type=str,
                      help="course code"
                      )

    argp.add_argument('--programCode',
                      type=str,
                      help="program code"
                      )

    argp.add_argument('--cycle',
                      type=int,
                      help="cycle of thesis"
                      )

    argp.add_argument('--credits',
                      type=float,
                      help="number_of_credits of thesis"
                      )

    argp.add_argument('--area',
                      type=str,
                      help="area of thesis"
                      )

    argp.add_argument('--area2',
                      type=str,
                      help="area of thesis for combined Cinving. and Master's"
                      )

    argp.add_argument('--numberOfSupervisors',
                      default=1,
                      type=int,
                      help="number of supervisors"
                      )

    argp.add_argument('--Supervisor',
                      type=str,
                      help="login ID of supervisor without the @kth.se"
                      )

    argp.add_argument('--Supervisor2',
                      type=str,
                      help="login ID of second supervisor without the @kth.se"
                      )

    argp.add_argument('--Supervisor3',
                      type=str,
                      help="login ID of third supervisor without the @kth.se"
                      )

    argp.add_argument('--Examiner',
                      type=str,
                      help="login ID of examiner without the @kth.se"
                      )

    argp.add_argument('--trita',
                      type=str,
                      help="trita string for thesis"
                      )


    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    initialize(args)
    
    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))

    canvas_course_id=args['canvas_course_id']
    canvas_course_name=None

    current_profile=None
    current_canvas_user_id=None #  first author
    student1=None
    second_canvas_user_id=None  # second author
    student2=None
    
    students=None

    school_name=None
    school_acronym=None

    canvas_course_name=None
    course_code=None

    sis_section=None
    sections=None

    assignments=None

    teachers=None
    examiners=None

    examiner=None
    examiner_canvas_user_id=None
    examiner_section_id=None

    supervisor=None
    supervisor_canvas_user_id=None

    supervisor2=None
    supervisor2_canvas_user_id=None


    author=args['author']
    if not author:
        print("You have to provude at least one of the auhtor's names")
        return

    if author and canvas_course_id > 0:   # author and canvas_course_id specified on command line, so use them
        # at this point we know a canvas_course_id
        students=students_in_course(canvas_course_id)

        # chack that the author is in this course
        if author:
            if not author.endswith('@kth.se'):
                author=author+'@kth.se'

        student=student_from_students_by_login_id(author, students)
        current_canvas_user_id=student['user']['id']
        if not current_canvas_user_id:
            print("Unable to find author {0} in course {1}".format(author, canvas_course_id))
            return

    elif not author and canvas_course_id > 0:   # canvas_course_id specified on command line, but not author, assume 'self'
        current_profile=user_profile('self')
        current_canvas_user_id=current_profile['id']
        author=current_profile['login_id']
        if Verbose_Flag:
            print("current_profile={0}, current_canvas_user_id={1}".format(current_profile, current_canvas_user_id))

    elif not author and canvas_course_id == 0:   # neither author or course if specified on command line, so look at self's own courses
        current_profile=user_profile('self')
        current_canvas_user_id=current_profile['id']
        author=current_profile['login_id']

        # pick the  highest numbered canvas course that either starts with 'Degree Projects at' or has a lldddX source code
        my_courses=list_my_courses()
        if Verbose_Flag:
            print("my_courses={}".format(my_courses))

        canvas_course_id=guess_degree_project_course(my_courses)
        if canvas_course_id:
            print("Guessing that your degree project course is canvas_course_id={}".format(canvas_course_id))
        else:
            print("Unable to guessing your degree project course, please add --canvas_course_id and course id to command line")
            return
    else:
        print("Don't know how to process your request, consider adding at a minimum the canvas_course_id")
        return

    if Verbose_Flag:
        print("current_canvas_user_id={0}, canvas_course_id={1}".format(current_canvas_user_id, canvas_course_id))

    if not students:
        students=students_in_course(canvas_course_id)
        if not students:
            print("Error in getting enrollments for course: ".format(canvas_course_id))
            return

    # chack that the author is in this course
    student1=student_from_students_by_id(current_canvas_user_id, students)
    if not student1:
        print("Unable to find author {0} in course {1}".format(author, canvas_course_id))
        return

    # Either use the explicitly specified language or try to guess based on author's profile in Canvas
    language=args['language']
    if not language:
        # if no language specified look at the uer's profile - where it is encoded as per RFC 5646
        locale=current_profile['locale']
        if locale:
            if locale[0:2] == 'en':
                language='eng'
            elif locale[0:2] == 'sv':
                language='swe'
        else:
            print("locale={}".format(locale))
            print("please specify the lanaguge of the thesis as eng or swe")
            return
    if language not in ['eng', 'swe']:
        print("Unknown language code={}".format(language))
        return

    if Verbose_Flag:
        print("language={}".format(language))

    customize_data=dict()
    # the student can be in many sections but should be section for their specific course
    # for example: Section for the course DA231X VT21-1 Degree Project in Computer Science and Engineering, Second Cycle
    sis_section=sis_section_id_from_students_by_id(current_canvas_user_id, students)
    if not sis_section:
        print("Could not find the sis:section_if for author")
        return

    if sis_section and len(sis_section) >= 6:
        course_code=sis_section[0:6]
        if not school_name:
            school_acronym=guess_school_from_course_code(course_code)
            if not school_acronym:
                print("Could not figure out school from the course_code {}".format(course_code))
                return
            else:
                school_name=schools_info[school_acronym][language]
    else:
        print("Error in course_code {}".format(course_code))
        return

    cycle=cycle_from_course_code(course_code)

    course_info=canvas_course_info(canvas_course_id)
    if course_info:
        canvas_course_name=course_info['name']

    # get school name
    school_acronym=args['school']
    if school_acronym:
            school_name=schools_info[school_acronym][language]
            print("School acronym {0}, school name is {1}".format(school_acronym, school_name))
    else:
        school_acronym=guess_school_from_course_name(canvas_course_name)
        if school_acronym:
            school_name=schools_info[school_acronym][language]
        else:
            school_acronym=guess_school_from_course_code(course_code)
            if school_acronym:
                school_name=schools_info[school_acronym][language]
            else:
                print("Unable to guess school acronym or shool name")
                return
    if Verbose_Flag:
        print("Found school acronym {0}, school name is {1}".format(school_acronym, school_name))

    sortable_name=student1['user']['sortable_name']
    last_name, first_name=sortable_name.split(',')
    customize_data['Author1']={
        "Last name": last_name.strip(),
        "First name": first_name.strip(),
        "Local User Id": student1['sis_user_id'],
        "E-mail": student1['user']['login_id'],
        "organisation": {"L1": school_name }
    }

    #"Cycle": "1", "Course code": "IA150X", "Credits": "15.0", 
    x=args['cycle']
    if x:
        customize_data['Cycle']=x
    elif cycle:
        customize_data['Cycle']=cycle
    else:
        print("Unable to deterrmined the cycle of the course, please add --cycle 1 or 2 to command line")

    x=args['courseCode']
    if x:
        customize_data['Course code']=x
    elif course_code:
        customize_data['Course code']=course_code
    else:
        print("Unable to deterrmined the course code of the course, please add --courseCode and course code to command line")

    x=args['credits']
    if x:
        customize_data['Credits']=x
    elif course_code and cycle == 1:
        customize_data['Credits']=15
    elif course_code and cycle == 2:
        customize_data['Credits']=30
    else:
        print("Unable to deterrmined the number of credits for the course, please add --credits and value to command line")

    # if cycle == 1 the look for second author who is in the group with the first author
    if cycle == 1:
        author2=args['author2']
        if author2:
            # process second author from command line
            if not author2.endswith('@kth.se'):
                author2=author2+'@kth.se'

            student2=student_from_students_by_login_id(author2, students)
            if student2:
                second_canvas_user_id=student2['user']['id']
            else:
                print("Unable to find second author {0} in course {1}".format(author2, canvas_course_id))
                return
        else:
            # Look for the second author being in a group with the first author; for example, in a group set 'Exjobb grupp'
            groups=list_groups_in_course(canvas_course_id)
            if groups:
                if Verbose_Flag:
                    print("groups={}".format(groups))
                groups_names=dict()
                for g in groups:
                    g_id=g['id']
                    g_members=members_of_groups(g_id)
                    #groups_names[g_id]={'name': g['name'], 'members': g_members}
                    if Verbose_Flag:
                        print("g_id={0}, g_members={1}".format(g_id, g_members))
                    if current_canvas_user_id in g_members:
                        g_members.remove(current_canvas_user_id) # remove first author from list
                        if len(g_members) > 1:
                            print("too many users in group {}".format(g['name']))
                        else:
                            second_canvas_user_id=g_members[0]
                            student2=student_from_students_by_id(second_canvas_user_id, students)

                            sis_section=sis_section_id_from_students_by_id(second_canvas_user_id, students)
                            if Verbose_Flag:
                                print("sis_section of second author={}".format(sis_section))
                            if sis_section and len(sis_section) >= 6:
                                course_code=sis_section[0:6]
                                if not args['school']:
                                    school_acronym=guess_school_from_course_code(course_code)
                                    school_name=schools_info[school_acronym][language]
                                    if Verbose_Flag:
                                        print("Found school acronym {0}, school name is {1}".format(school_acronym, school_name))

                            sortable_name=student2['user']['sortable_name']
                            last_name, first_name=sortable_name.split(',')
                            customize_data['Author2']={
                                "Last name": last_name.strip(),
                                "First name": first_name.strip(),
                                "Local User Id": student2['sis_user_id'],
                                "E-mail": student2['user']['login_id'],
                                "organisation": {"L1": school_name }
                            }
                            break # end loop over groups

    # "Degree1": {"Educational program": "Bachelor's Programme in Information and Communication Technology","programcode": "TCOMK" ,
    #             "Degree": "Bachelors degree" ,"subjectArea": "Information and Communication Technology" }, 

    degree1_data=dict()

    # sis_section may be of the form with
    #   TT is either  HT or VT: Fall (HT) and Spring (VT) semester
    #   yy as the last two digits of the year
    #   d as 1 or 2
    # Section for the course DA231X TTyy-d Degree Project in Computer Science and Engineering, Second Cycle
    # Section for the course DA232X TTyy-d Degree Project in Computer Science and Engineering, specializing in Interactive Media Technology, Second Cycle
    # Section for the course DA233X TTyy-d Degree Project in Computer Science and Engineering, specializing in Machine Learning, Second Cycle
    # Section for the course DA233X TTyy-d Examensarbete i datalogi och datateknik med inriktning mot maskininlärning, avancerad nivå
    # Section for the course DA234X TTyy-d Degree Project in Computer Science and Engineering, specializing in Media Management, Second Cycle
    # Section for the course DA235X TTyy-d Degree Project in Computer Science and Engineering, specializing in Industrial Management, Second Cycle
    # Section for the course DA236X TTyy-d Degree Project in Computer Science and Engineering, specializing in Systems, Control and Robotics, Second Cycle
    # Section for the course DA239X TTyy-d Degree Project in Computer Science and Engineering, Second Cycle
    # Section for the course DA240X TTyy-d Degree Project in Computer Science and Engineering, specializing in Software Engineering for Distributed Systems, Second Cycle
    # Section for the course DA246X TTyy-d Degree Project in Computer Science and Engineering, specialising in Communication Systems, Second Cycle
    # Section for the course DA248X TTyy-d Degree Project in Computer Science and Engineering, specialising in Embedded Systems, Second Cycle
    # Section for the course DA250X TTyy-d Degree Project in Computer Science and Engineering, Second Cycle
    # Section for the course DA250X TTyy-d Examensarbete inom datateknik, avancerad nivå
    # Section for the course DA256X TTyy-d Degree Project in Computer Science and Engineering, specialising in ICT Innovation, Second Cycle
    # Section for the course DA258X TTyy-d Degree Project in Computer Science and Engineering, specialising in ICT Innovation, Second Cycle
    # Section for the course DM250X TTyy-d Degree Project in Media Technology, Second Cycle
    # Section for the course EA236X TTyy-d Degree Project in Electrical Engineering, specializing in Systems, Control and Robotics, Second Cycle
    # Section for the course EA238X TTyy-d Degree Project in Electrical Engineering, Second Cycle
    # Section for the course EA246X TTyy-d Degree Project in Electrical Engineering, specializing in Communication Systems, Second Cycle
    # Section for the course EA248X TTyy-d Degree Project in Electrical Engineering, specialising in Embedded Systems, Second Cycle
    # Section for the course EA249X TTyy-d Degree Project in Electrical Engineering, specialising in Nanotechnology, Second Cycle
    # Section for the course EA250X TTyy-d Degree Project in Electrical Engineering, Second Cycle
    # Section for the course EA256X TTyy-d Degree Project in Electrical Engineering, specialising in ICT Innovation, Second Cycle
    # Section for the course EA258X TTyy-d Degree Project in Electrical Engineering, specialising in ICT Innovation, Second Cycle
    # Section for the course EA260X TTyy-d Degree Project in Electrical Engineering, specializing in Information and Network Engineering , Second Cycle
    # Section for the course EA270X TTyy-d Degree Project in Electrical Engineering, specialising in Electric Power Engineering, Second Cycle
    # Section for the course EA275X TTyy-d Degree Project in Electrical Engineering, specialising in Electromagnetics, Fusion and Space Engineering, Second Cycle
    # Section for the course EA280X TTyy-d Degree Project in Electrical Engineering, specialising in Energy Innovation Second Cycle
    # Section for the course IA249X TTyy-d Degree Project in Engineering Physics, specialising in Nanotechnology, Second Cycle
    # Section for the course IA250X TTyy-d Degree Project in Information and Communication Technology, Second Cycle
    #
    # Section for the course IA150X TTyy-d Examensarbete inom informationsteknik, grundnivå

    if Verbose_Flag:
        print("About to check for area")
    x=args['area']
    if x:
        area=x
    else:
        sections=sections_in_course(canvas_course_id)
        if Verbose_Flag:
            print("sections={}".format(sections))

        print("sis_section={}".format(sis_section))

        section_name=None
        for s in sections:
            if s['sis_section_id'] == sis_section:
                section_name=s['name']
                break
        print("section_name={}".format(section_name))
        if section_name:
            area=guess_area_from_section_name(cycle, section_name)

    if area:
        degree1_data['subjectArea']=area
        if Verbose_Flag:
            print("area={}".format(area))

    program_code=args['programCode']
    if program_code:
        degree1_data['programcode']=program_code
    # alternatively one might try to look this up in LADOK or from custom data in the course

    program_info=programcodes.get(program_code, None)
    if program_info:
        ep=program_info[language]
        if ep:
            degree1_data['Educational program']=ep

    # Degree corresponds to the Exam in the PDF cover generator
    if cycle == 1:
        if language == 'eng':
            if program_code in ['TCOMK', 'TFAFK', 'TFOFK']: #  for EECS
                degree1_data['Degree']="Bachelors degree"
            elif program_code in ['TBYPH', 'TIBYH', 'TIDAA', 'TIDAB', 'TIEDB', 'TIELA', 'TIIPS', 'TIKED', 'TIMAS', 'TIMEL', 'TITEH', ]: #  for EECS
                degree1_data['Degree']="Higher Education Diploma"
            else:
                degree1_data['Degree']="Degree of Bachelor of Science in Engineering"
        elif language == 'swe':
            if program_code in ['TCOMK', 'TFAFK', 'TFOFK']: #  for EECS
                degree1_data['Degree']="kandidatexamen"
            elif program_code in ['TBYPH', 'TIBYH', 'TIDAA', 'TIDAB', 'TIEDB', 'TIELA', 'TIIPS', 'TIKED', 'TIMAS', 'TIMEL', 'TITEH', ]: #  for EECS
                degree1_data['Degree']="Högskoleexamen"

            degree1_data['Degree']="Bachelors degree" # fix Swedish
        else:
            print("Unknown degree")
    elif cycle == 2:
        if language == 'eng':
            if program_code == 'ARKIT':
                degree1_data['Degree']="Degree of Master of Architecture" #
            elif program_code == 'CLGYM':
                degree1_data['Degree']="Master of Science in Engineering and in Education" #
            elif program_code[0] == 'C':
                degree1_data['Degree']="Degree of Master of Science in Engineering"
            elif program_code in ['TDEBM', 'TEILM', 'TFAHM', 'TLODM', 'TURSM']: #  for EECS
                degree1_data['Degree']="Degree of Master (60 credits)"
            else:
                # What about the cases
                # Degree of Master of Science in Secondary Education
                # Both Master of science in engineering and Master
                #
                degree1_data['Degree']="Degree of Master (120 credits)"
        elif language == 'swe':
            if program_code == 'ARKIT':
                degree1_data['Degree']="Arkitektexamen" #
            elif program_code == 'CLGYM':
                degree1_data['Degree']="Civilingenjör och lärare" #
            elif program_code[0] == 'C':
                degree1_data['Degree']="Civilingenjörsexamen"
            elif program_code in ['TDEBM', 'TEILM', 'TFAHM', 'TLODM', 'TURSM']: #  for EECS
                degree1_data['Degree']="Magisterexamen"
            else:
                # What about the cases
                # Degree of Master of Science in Secondary Education
                # Both Master of science in engineering and Master
                #
                degree1_data['Degree']="Masterexamen"
        else:
            print("Unknown degree")

    customize_data['Degree1']=degree1_data

    teachers=teachers_in_course(canvas_course_id)
    if not teachers:
        print("Error in getting teachers for course: ".format(canvas_course_id))
        return
    if Verbose_Flag:
        print("teachers={}".format(teachers))

    examiners=examiners_in_course(teachers)
    if not examiners:
        print("Error in getting examiners for course: ".format(canvas_course_id))
        return

    if Verbose_Flag:
        print("examiners={}".format(examiners))

    if not sections:
        sections=sections_in_course(canvas_course_id)

    #"Examiner1": {"Last name": "Maguire Jr.", "First name": "Gerald Q.", "Local User Id": "u1d13i2c", "E-mail": "maguire@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science" ,"L2": "Computer Science" }}, 

    x=args['Examiner']
    if x:
        if not x.endswith('@kth.se'):
                x=x+'@kth.se'
        examiner=examiner_by_login_id(x, examiners)
        if examiner:
            examiner_canvas_user_id=examiner['user']['id']
            examiner_section_id=teacher_section_id_by_name(examiner['user']['sortable_name'], sections)
    else:
        # Try to identify the examiner based upon the sections that the student is in - one should be that of their examiner
        author1_section_ids=section_ids_for_students_by_id(current_canvas_user_id, students)
        print("before determining examiner: author1_section_ids={}".format(author1_section_ids))
        examiner=examiner_by_section_id(author1_section_ids, sections, examiners)
        if examiner:
            examiner_canvas_user_id=examiner['user']['id']
            examiner_section_id=teacher_section_id_by_name(examiner['user']['sortable_name'], sections)
        else:
            assignments=list_assignments(canvas_course_id)
            examiner_assignment_id=assignment_id_from_assignment_name(assignments, 'Examiner')
            examiner_grade=get_grade_for_assignment(canvas_course_id, examiner_assignment_id, current_canvas_user_id)
            examiner_name=examiner_grade.get('entered_grade', None)
            if examiner_name:
                print("examiner_name={}".format(examiner_name))
                examiner=examiner_by_name(examiner_name, examiners)
                examiner_canvas_user_id=examiner['user']['id']
                examiner_section_id=teacher_section_id_by_name(examiner['user']['sortable_name'], sections)
                if Verbose_Flag:
                    print("examiner_id={0} is {1}".format(examiner_canvas_user_id, examiner))
            else:
                print("Failed To be able to guess the examiner, please add the argument --examiner login ID")

        # if second_canvas_user_id:
        #     author2_section_ids=section_ids_for_students_by_id(second_canvas_user_id, students)

    if examiner and examiner_canvas_user_id:
        school_name=''          # need to calculate the school name, department, etc. for examiner
        examiner_kthid=examiner['sis_user_id']
        kth_profile=get_user_by_kthid(examiner_kthid)
        #print("kth_profile={}".format(kth_profile))
        address=address_from_kth_profile(kth_profile, language, school_acronym)
                       
        examiner_sortable_name=examiner['user']['sortable_name']

        last_name, first_name=examiner_sortable_name.split(',')
        customize_data['Examiner1']={
            "Last name": last_name.strip(),
            "First name": first_name.strip(),
            "Local User Id": examiner['sis_user_id'],
            "E-mail": examiner['user']['login_id'],
            "organisation": address
        }
    else:                       #  Leave a place holder for the examiner
        customize_data['Examiner1']={
            "Last name": 'Examiner last_name',
            "First name": 'Examiner first_name',
            "Local User Id": 'KTHID of examiner',
            "E-mail": 'email address of examiner',
            "organisation": {"L1": 'school name of Examiner' }
        }

    # The supervisor section of code is under development
    #"Supervisor1": {"Last name": "Supervisor", "First name": "A. Busy", "Local User Id": "u100003", "E-mail": "sa@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science" ,"L2": "Computer Science" }}, 
    #"Supervisor2": {"Last name": "Supervisor", "First name": "Another Busy", "Local User Id": "u100003", "E-mail": "sb@kth.se", "organisation": {"L1": "School of Architecture and the Built Environment" ,"L2": "Architecture" }}, 
    ##"Supervisor3": {"Last name": "Supervisor", "First name": "Third Busy", "E-mail": "sc@tu.va", "Other organisation": "Timbuktu University, Department of Pseudoscience" }, 

    # We will assume that there is an academic supervisor who is listed as a teacher in the course
    x=args['Supervisor']
    if x:
        if not x.endswith('@kth.se'):
                x=x+'@kth.se'
        supervisor=supervisor_by_login_id(x, teachers)
        if supervisor:
            supervisor_canvas_user_id=supervisor['user']['id']
    else:
        # Try to identify the supervisor based upon the sections that the student is in - one could be that of their supervisor
        author1_section_ids=section_ids_for_students_by_id(current_canvas_user_id, students)
        if examiner_section_id:
            author1_section_ids.remove(examiner_section_id) # remove the examiner's section
        print("before determining supervisor: author1_section_ids={}".format(author1_section_ids))
        supervisor=supervisor_by_section_id(author1_section_ids, sections, teachers)
        if supervisor:
            supervisor_canvas_user_id=supervisor['user']['id']
        else:
            assignments=list_assignments(canvas_course_id)
            supervisor_assignment_id=assignment_id_from_assignment_name(assignments, 'Supervisor')
            supervisor_grade=get_grade_for_assignment(canvas_course_id, supervisor_assignment_id, current_canvas_user_id)
            supervisor_name=supervisor_grade.get('entered_grade', None)
            if supervisor_name:
                print("supervisor_name={}".format(supervisor_name))
                supervisor=supervisor_by_name(supervisor_name, teachers)
                supervisor_canvas_user_id=supervisor['user']['id']
                if Verbose_Flag:
                    print("supervisor_id={0} is {1}".format(supervisor_canvas_user_id, supervisor))
            else:
                print("Failed To be able to guess the supervisor, please add the argument --supervisor login ID")

        # if second_canvas_user_id:
        #     author2_section_ids=section_ids_for_students_by_id(second_canvas_user_id, students)

    if supervisor and supervisor_canvas_user_id:
        supervisor_section_id=teacher_section_id_by_name(supervisor['user']['sortable_name'], sections)

        school_name=''          # need to calculate the school name, department, etc. for supervisor

        supervisor_sortable_name=supervisor['user']['sortable_name']

        last_name, first_name=supervisor_sortable_name.split(',')
        customize_data['Supervisor1']={
            "Last name": last_name.strip(),
            "First name": first_name.strip(),
            "Local User Id": supervisor['sis_user_id'],
            "E-mail": supervisor['user']['login_id'],
            "organisation": {"L1": school_name }
        }
    else:                       #  Leave a place holder for the supervisor
        customize_data['Supervisor1']={
            "Last name": 'Supervisor last_name',
            "First name": 'Supervisor first_name',
            "Local User Id": 'KTHID of supervisor',
            "E-mail": 'email address of supervisor',
            "organisation": {"L1": 'school name of Supervisor' }
        }

    # We will assume that there may be a second academic supervisor who is listed as a teacher in the course
    # If they are not listed as a teacher in the course, we will generate a place holder for them if necessary.
    # In this case necessary is only if there is an explicit second advisor who is a teacher or numberOfSupervisors >= 2.
    numberOfSupervisors=args['numberOfSupervisors']

    x=args['Supervisor2']
    if x:
        if not x.endswith('@kth.se'):
                x=x+'@kth.se'
        supervisor2=supervisor_by_login_id(x, teachers)
        if supervisor2:
            supervisor2_canvas_user_id=supervisor2['user']['id']
    else:
        # Try to identify the supervisor2 based upon the sections that the student is in - one could be that of their supervisor2
        author1_section_ids=section_ids_for_students_by_id(current_canvas_user_id, students)
        if examiner_section_id:
            author1_section_ids.remove(examiner_section_id) # remove the examiner's section
        if supervisor_section_id:
            author1_section_ids.remove(supervisor_section_id) # remove supervisor1's section
        print("before determining supervisor2: author1_section_ids={}".format(author1_section_ids))
        supervisor2=supervisor_by_section_id(author1_section_ids, sections, teachers)
        if supervisor2:
            supervisor2_canvas_user_id=supervisor2['user']['id']
        else:
            if numberOfSupervisors >= 2:
                print("Failed To be able to guess the supervisor2. If they are a teacher in the course, please add the argument --supervisor2 login ID")

        # if second_canvas_user_id:
        #     author2_section_ids=section_ids_for_students_by_id(second_canvas_user_id, students)

    if supervisor2 and supervisor2_canvas_user_id:
        school_name=''          # need to calculate the school name, department, etc. for supervisor2

        supervisor2_sortable_name=supervisor2['user']['sortable_name']

        last_name, first_name=supervisor2_sortable_name.split(',')
        customize_data['Supervisor2']={
            "Last name": last_name.strip(),
            "First name": first_name.strip(),
            "Local User Id": supervisor2['sis_user_id'],
            "E-mail": supervisor2['user']['login_id'],
            "organisation": {"L1": school_name }
        }
    else: #  Leave a place holder for the supervisor2 if necessary. As they are not a teacher in the course, assume an external organization
        if args['Supervisor2'] or numberOfSupervisors >= 2:
            customize_data['Supervisor2']={
                "Last name": 'Supervisor2 last_name',
                "First name": 'Supervisor2 first_name',
                "E-mail": 'email address of supervisor2',
                "Other organisation": 'organization of Supervisor2'
            }

    # We will assume that there may be a third supervisor who is listed as a teacher in the course
    # If they are not listed as a teacher in the course, we will generate a place holder for them if necessary.
    # In this case necessary is only if there is an explicit second advisor who is a teacher or numberOfSupervisors >= 3.
    x=args['Supervisor3']
    if x:
        if not x.endswith('@kth.se'):
                x=x+'@kth.se'
        supervisor3=supervisor_by_login_id(x, teachers)
        if supervisor3:
            supervisor3_canvas_user_id=supervisor3['user']['id']
    else:
        # Try to identify the supervisor3 based upon the sections that the student is in - one could be that of their supervisor3
        author1_section_ids=section_ids_for_students_by_id(current_canvas_user_id, students)
        if examiner_section_id:
            author1_section_ids.remove(examiner_section_id) # remove the examiner's section
        if supervisor_section_id:
            author1_section_ids.remove(supervisor_section_id) # remove supervisor1's section
        print("before determining supervisor3: author1_section_ids={}".format(author1_section_ids))
        supervisor3=supervisor_by_section_id(author1_section_ids, sections, teachers)
        if supervisor3:
            supervisor3_canvas_user_id=supervisor3['user']['id']
        else:
            if numberOfSupervisors >= 2:
                print("Failed To be able to guess the supervisor3. If they are a teacher in the course, please add the argument --supervisor3 login ID")

        # if second_canvas_user_id:
        #     author2_section_ids=section_ids_for_students_by_id(second_canvas_user_id, students)

    if supervisor3 and supervisor3_canvas_user_id:
        school_name=''          # need to calculate the school name, department, etc. for supervisor3

        supervisor3_sortable_name=supervisor3['user']['sortable_name']

        last_name, first_name=supervisor3_sortable_name.split(',')
        customize_data['Supervisor3']={
            "Last name": last_name.strip(),
            "First name": first_name.strip(),
            "Local User Id": supervisor3['sis_user_id'],
            "E-mail": supervisor3['user']['login_id'],
            "organisation": {"L1": school_name }
        }
    else: #  Leave a place holder for the supervisor2 if necessary. As they are not a teacher in the course, assume an external organization
        if args['Supervisor3'] or numberOfSupervisors >= 3:
            customize_data['Supervisor3']={
                "Last name": 'Supervisor3 last_name',
                "First name": 'Supervisor3 first_name',
                "E-mail": 'email address of supervisor3',
                "Other organisation": 'organization of Supervisor3'
            }


    #"Series": {"Title of series": "TRITA-EECS-EX" , "No. in series": "2021:00" }
    x= args['trita']
    if x:
        series, num_in_series = x.split('-EX-')
        customize_data['Series']={"Title of series": series+'-EX' , "No. in series": num_in_series }
                                
    #"Cooperation": {"Partner_name": "Företaget AB"}
    customize_data['Cooperation']={"Partner_name": "To be added here if relevant, otherwise remove this data"}

    #"National Subject Categories": "10201, 10206", 
    national_subject_category=""
    national_subject_category_augmented=None
    if degree1_data:
        subject_area1=degree1_data.get('subjectArea', None)
    # use course_code
    print("course_code (possibly from section info) is: {}".format(course_code))
    course_code=customize_data['Course code']
    print("course_code from command line is: {}".format(course_code))
    if course_code == 'DA231X':	# Computer Science and Engineering
        add_national_subject_category("10201")
    elif course_code == 'DA232X':	# Computer Science and Engineering, specializing in Interactive Media Technology
        add_national_subject_category("10201")
        add_national_subject_category("10209")
    elif course_code == 'DA233X':        # Computer Science and Engineering, specializing in Machine Learning
        add_national_subject_category("10201")
    elif course_code == 'DA234X':        # Computer Science and Engineering, specializing in Media Management
        add_national_subject_category("10201")
        add_national_subject_category("10209")
    elif course_code == 'DA235X':        # Computer Science and Engineering, specializing in Industrial Management
        add_national_subject_category("10201")
    elif course_code == 'DA236X':        # Computer Science and Engineering, specializing in Systems, Control and Robotics
        add_national_subject_category("10201")
        add_national_subject_category("10207")
    elif course_code == 'DA239X':        # Computer Science and Engineering
        add_national_subject_category("10201")
    elif course_code == 'DA240X':        # Computer Science and Engineering, specializing in Software Engineering for Distributed Systems
        add_national_subject_category("10201")
        add_national_subject_category("10205")
    elif course_code == 'DA246X':        # Computer Science and Engineering, specialising in Communication Systems
        add_national_subject_category("10201")
        add_national_subject_category("20203")
    elif course_code == 'DA248X':        # Computer Science and Engineering, specialising in Embedded Systems
        add_national_subject_category("10201")
        add_national_subject_category("20207")
    elif course_code == 'DA250X':        # Computer Science and Engineering/Examensarbete inom datateknik
        add_national_subject_category("10206")
    elif course_code == 'DA256X':        # Computer Science and Engineering, specialising in ICT Innovation
        add_national_subject_category("10202")
    elif course_code == 'DA258X':        # Computer Science and Engineering, specialising in ICT Innovation
        add_national_subject_category("10202")
    elif course_code == 'DM250X':        # Media Technology
        add_national_subject_category("10209")
    elif course_code == 'EA236X':        # Electrical Engineering, specializing in Systems, Control and Robotics
        # the course's aubjects span different national subject categories
        # So we add them all, and then need to remind the user to select the appropriate one
        add_national_subject_category("20201") # for robotics
        add_national_subject_category_augmented("20201", 'robotics')
        add_national_subject_category("20202") # for control
        add_national_subject_category_augmented("20202", 'control')
        add_national_subject_category("Datorsyste") #  for computer systems
        add_national_subject_category_augmented("Datorsyste", 'computer systems')
    elif course_code == 'EA238X':        # Electrical Engineering
        add_national_subject_category("202")
    elif course_code == 'EA246X':        # Electrical Engineering, specializing in Communication Systems
        add_national_subject_category("20203")
    elif course_code == 'EA248X':        # Electrical Engineering, specialising in Embedded Systems
        add_national_subject_category("20207")
    elif course_code == 'EA249X':        #  Electrical Engineering, specialising in Nanotechnology
        add_national_subject_category("202")
        add_national_subject_category("21001") # Nanoteknik
    elif course_code == 'EA250X':        # Electrical Engineering
        add_national_subject_category("202")
    elif course_code == 'EA256X':        # Electrical Engineering, specialising in ICT Innovation
        add_national_subject_category("202")
        add_national_subject_category("10202")
    elif course_code == 'EA258X':        # Electrical Engineering, specialising in ICT Innovation
        add_national_subject_category("202")
        add_national_subject_category("10202")
    elif course_code == 'EA260X':        # Electrical Engineering, specializing in Information and Network Engineering
        add_national_subject_category("202")
        add_national_subject_category("20203") # for Kommunikationssystem Communication Systems
        add_national_subject_category_augmented("20203", 'Communication Systems')
        add_national_subject_category("20204") # for Telekommunikation Telecommunications
        add_national_subject_category_augmented("20204", 'Telecommunications')
    elif course_code == 'EA270X':        #  Electrical Engineering, specialising in Electric Power Engineering
        add_national_subject_category("202")
        add_national_subject_category("20299")
    elif course_code == 'EA275X':        # Electrical Engineering, specialising in Electromagnetics, Fusion and Space Engineering
        add_national_subject_category("202")
        add_national_subject_category("10303") # Fusion, plasma och rymdfysik
        add_national_subject_category_augmented("10303", 'Fusion, Plasma and Space Physics')
        add_national_subject_category("20299")
        add_national_subject_category_augmented("20299", 'Other Electrical Engineering, Electronic Engineering, Information Engineering') # Annan elektroteknik och elektronik/Other Electrical Engineering, Electronic Engineering, Information Engineering
    elif course_code == 'EA280X':        # Electrical Engineering, specialising in Energy Innovation
        add_national_subject_category("202")
        add_national_subject_category("20702") # Energisystem
    elif course_code == 'IA249X':        # Engineering Physics, specialising in Nanotechnology
        add_national_subject_category("103")
        add_national_subject_category("21001")
    elif course_code == 'IA250X':        #  Information and Communication Technology
        add_national_subject_category("10202")
        add_national_subject_category("20203")
    elif course_code == 'IA150X':        # inom informationsteknik
        add_national_subject_category("10202")
    elif course_code == 'II143X':        # Information and Communication Technology
        add_national_subject_category("10202")
        add_national_subject_category("20203")
    else:
        print("Unknown program code ({0}), cannot guess national subject category".format(course_code))
    if national_subject_category and len(national_subject_category) > 0:
        customize_data['National Subject Categories']=national_subject_category

    if national_subject_category_augmented and len(national_subject_category_augmented) > 0:
        customize_data['National Subject Categories Augmented']=national_subject_category_augmented

    print("customize_data={}".format(customize_data))

    # save the results
    output_filename=args["json"]
    if Verbose_Flag:
        print("output_filename={}".format(output_filename))
    with open(output_filename, 'w', encoding='utf-8') as output_FH:
        j_as_string = json.dumps(customize_data, ensure_ascii=False)
        print(j_as_string, file=output_FH)
    return

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

