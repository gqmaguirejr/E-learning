#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# augment_author_matches_with_canvas_info.py spreadsheet.xlsx
#
# Purpose: To take the result from a Jupyter notebook matching of titles in LADOK with title in DiVA and augment with data from Canvas.
#
# Output: an updated spreadsheet with "-augmented" added to the base filename
#
#
# Example:
# ./augment_author_matches_with_canvas_info.py --file titles-all-EECS-df1-author-matches.xlsx
#   by default it processes the titles-all-EECS-df1-author-matches.xlsx file
#
# 2022-12-07 G. Q. Maguire Jr.
# buids on augment-kth-dept-people-URL.py
#
import re
import sys
import subprocess

import json
import optparse
import os                       # to make OS calls, here to get time zone info

import pprint

import requests, time

import openpyxl
# Use Python Pandas to create XLSX files
import pandas as pd

import datetime

import shlex

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(options):
    global baseUrl, header, payload

    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    if options.config_filename:
        config_file=options.config_filename
    else:
        config_file='config.json'

    if os.path.isfile(config_file):
        if Verbose_Flag:
            print(f"{config_file} exists")
    else:
        print(f"{config_file} does not exist")
        return

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            access_token=configuration["canvas"]["access_token"]
            baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}
    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()


#//////////////////////////////////////////////////////////////////////
# Canvas related routines
#//////////////////////////////////////////////////////////////////////
def users_in_course(course_id):
    users_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100',
                      'type': ['StudentEnrollment'],
                      #'state': ['active', 'completed']
                      #'state': ['active', 'invited', 'creation_pending', 'deleted', 'rejected', 'completed', 'inactive']
    }
    r = requests.get(url, params=extra_parameters, headers = header)
    if Verbose_Flag:
        print("result of getting enrollments: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            users_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)
            page_response = r.json()  
            for p_response in page_response:  
                users_found_thus_far.append(p_response)

    return users_found_thus_far

def students_in_course(course_id):
    users_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

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
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)
            page_response = r.json()  
            for p_response in page_response:  
                users_found_thus_far.append(p_response)

    return users_found_thus_far

def teachers_in_course(course_id):
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
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)
            page_response = r.json()  
            for p_response in page_response:  
                users_found_thus_far.append(p_response)

    return users_found_thus_far


def users_in_accounts(account_id, user_id):
    users_found_thus_far=[]
    # Use the Canvas API to get the list of users in this account
    #GET /api/v1/accounts/:account_id/users

    url = "{0}/accounts/{1}/users".format(baseUrl, account_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100',
                      #'type': ['StudentEnrollment']
    }
    r = requests.get(url, params=extra_parameters, headers = header)
    if Verbose_Flag:
        print("result of getting users in account: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            users_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # while r.links.get('next', False):
        #     r = requests.get(r.links['next']['url'], headers=header)
        #     page_response = r.json()  
        #     for p_response in page_response:  
        #         users_found_thus_far.append(p_response)

    return users_found_thus_far



def user_info(user_id):
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/users/:id

    url = "{0}/users/{1}".format(baseUrl, user_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting user: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        return r.json()
    return None

def user_profile_info(user_id):
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/users/:id/profile

    url = "{0}/users/{1}/profile".format(baseUrl, user_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting user profile: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        return r.json()
    return None


def lookup_user_in_canvas_with_ladok_id(ladok_id):
    user_id="sis_integration_id:{}".format(ladok_id)
    ui=user_info(user_id)
    return ui

def lookup_user_by_ladok_id(ladok_id, all_users):
    user_id="sis_integration_id:{}".format(ladok_id)
    ui=user_info(user_id)
    if ui:
        canvas_user_id= ui['id']
        kthid=ui.get('sis_user_id', None)
        login_id=ui.get('login_id', None)
        canvas_sortable_name=ui.get('sortable_name', None)
        return { 'id':         canvas_user_id,
                 'kthid':      kthid,
                 'login_id':   login_id,
                 'name':       canvas_sortable_name
                }
    print("doing the lookup by the courses for ladok_id: {}".format(ladok_id))

    for u in all_users:
        integration_id=u['user'].get('integration_id', None)
        if integration_id and integration_id == ladok_id:
            canvas_user_id= u['user']['id']
            kthid=u['user'].get('sis_user_id', None)
            login_id=u['user'].get('login_id', None)
            canvas_sortable_name=u['user'].get('sortable_name', None)
            return { 'id':         canvas_user_id,
                     'kthid':      kthid,
                     'login_id':   login_id,
                     'name':       canvas_sortable_name
                    }
    return None

def main(argv):
    global Verbose_Flag
    global testing

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )
    parser.add_option("--config", dest="config_filename",
                      help="read configuration from FILE", metavar="FILE")

    parser.add_option('-t', '--testing',
                      dest="testing",
                      default=False,
                      action="store_true",
                      help="execute test code"
    )

    parser.add_option('--file',
                      type=str,
                      default="titles-all-EECS-df1-author-matches.xlsx file",
                      help="XSLX file to process",
                      metavar="FILE"
                      )

    options, remainder = parser.parse_args()
    
    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))
        print("Configuration file : {}".format(options.config_filename))

    initialize(options)

    testing=options.testing
    if Verbose_Flag:
        print("testing={}".format(testing))

    if testing:
        Verbose_Flag=True
        lookup_user_in_canvas_with_ladok_id('e8dee006-5a94-11e8-9dae-241de8ab435c') #Johannes	Olegård	2020-12-14 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('ec38dd2b-b59a-11e7-96e6-896ca17746d1') #Spyridon') #Karastamatis	2020-10-28 00:00:00	EF226X
        lookup_user_in_canvas_with_ladok_id('4c4e0074-5a94-11e8-9dae-241de8ab435c') #Sandra	Grosz	2020-01-19 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('209ab74e-5a94-11e8-9dae-241de8ab435c') #Wissem	Chouk	2019-11-05 00:00:00	EP240X
        lookup_user_in_canvas_with_ladok_id('cfc16343-5a93-11e8-9dae-241de8ab435c') #Yue	Wang	2019-11-04 00:00:00	EQ275X
        lookup_user_in_canvas_with_ladok_id('cdc8d2c8-5a94-11e8-9dae-241de8ab435c') #Henrik') #Karlsson	2019-06-27 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('3bd81f16-b5a5-11e7-96e6-896ca17746d1') #Vien	Hò	2019-06-20 00:00:00	EN191X
        lookup_user_in_canvas_with_ladok_id('4f7395ab-01c5-11e8-ad82-65c986724815') #Axel	Kelsey	2019-06-20 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('dfa88e63-5a96-11e8-9dae-241de8ab435c') #Malin') #Häggström	2019-06-20 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('d459d07c-5a96-11e8-9dae-241de8ab435c') #Vidar') #Greinsmark	2019-06-20 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('b9134a97-ce0f-11e7-ab7e-c364338b4317') #Daniel') #Arrhénius	2019-06-20 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('98375f89-5a96-11e8-9dae-241de8ab435c') #Kristiyan Yordanov') #Lazarov	2019-06-20 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('13cff972-5a8f-11e8-9dae-241de8ab435c') #Tommy') #Lundberg	2019-06-20 00:00:00	EK112X
        lookup_user_in_canvas_with_ladok_id('88569e8f-4dd9-11e8-b65e-241af9924772') #Daniel Nils Olof') #Nee	2019-06-20 00:00:00	EK112X
        lookup_user_in_canvas_with_ladok_id('ef53983d-5a95-11e8-9dae-241de8ab435c') #Mahan') #Tourkaman	2019-06-20 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('b8c4a081-e1c9-11e8-ab83-f1faf50d4a06') #Albert') #Jiménez Tauste	2019-06-20 00:00:00	EQ112X
        lookup_user_in_canvas_with_ladok_id('3f2052d9-5c19-11e7-82f8-4a99985b4246') #Elvis Didier') #Rodas Jaramillo	2019-06-20 00:00:00	ED112X
        lookup_user_in_canvas_with_ladok_id('accd62f6-ce0c-11e7-ab7e-c364338b4317') #Oscar') #Barreira Petersson	2019-06-20 00:00:00	EI130X
        lookup_user_in_canvas_with_ladok_id('1cca5c48-5c37-11e7-b483-338b13a746f9') #Rasmus') #Antonsson	2019-06-20 00:00:00	EN191X
        lookup_user_in_canvas_with_ladok_id('d0eb7df0-5a8e-11e8-9dae-241de8ab435c') #Jaafar') #Al Zubaidi	2019-06-20 00:00:00	EN191X
        lookup_user_in_canvas_with_ladok_id('5674274e-5c19-11e7-82f8-4a99985b4246') #Damir	Vrabac	2019-06-20 00:00:00	EF112X
        lookup_user_in_canvas_with_ladok_id('35b99d46-b599-11e7-96e6-896ca17746d1') #Mohammadali') #Madadi	2019-01-14 00:00:00	EL201X
        lookup_user_in_canvas_with_ladok_id('fb12ef87-b5a6-11e7-96e6-896ca17746d1') #Aisan	Rasouli	2019-01-14 00:00:00	EI255X
        lookup_user_in_canvas_with_ladok_id('e33471ba-b59c-11e7-96e6-896ca17746d1') #Axel') #Lewenhaupt	2019-01-05 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('4cbf7cc5-5a93-11e8-9dae-241de8ab435c') #Gustaf	Lindstedt	2018-12-30 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('4718f554-4dfe-11e8-a562-6ec76bb54b9f') #Philip	Sköld	2018-12-20 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('3bb6f88b-5a8f-11e8-9dae-241de8ab435c') #Zihan	Zhang	2018-12-10 00:00:00	EH231X
        lookup_user_in_canvas_with_ladok_id('40e72cda-b5a6-11e7-96e6-896ca17746d1') #Daniel') #Hedencrona	2018-11-01 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('304a5ea3-5a94-11e8-9dae-241de8ab435c') #Alexandros') #Krontiris	2018-10-03 00:00:00	DA221X
        lookup_user_in_canvas_with_ladok_id('d5bfb3ea-5a94-11e8-9dae-241de8ab435c') #Thomas') #Vanacker	2018-08-30 00:00:00	DA223X
        lookup_user_in_canvas_with_ladok_id('10b4e170-5a90-11e8-9dae-241de8ab435c') #Matts Karl-Ingvar') #Höglund	2018-07-17 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('6fbe7f8c-a868-11e7-8dbf-78e86dc2470c') #Maxim	Wolpher	2018-06-19 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('68a94204-5a95-11e8-9dae-241de8ab435c') #Martin') #Gomez Gonzalez	2018-06-14 00:00:00	EH231X
        lookup_user_in_canvas_with_ladok_id('80f51317-b5a7-11e7-96e6-896ca17746d1') #Karl Johannes') #Jondell	2018-06-05 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('58321631-b5a8-11e7-96e6-896ca17746d1') #Vlad Ovidiu') #Chelcea	2018-06-05 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('6b14eae0-5a95-11e8-9dae-241de8ab435c') #Björn	Ståhl	2018-06-05 00:00:00	EL115X
        lookup_user_in_canvas_with_ladok_id('3e1042e7-5a95-11e8-9dae-241de8ab435c') #Fredrik	Krantz	2018-06-05 00:00:00	EP112X
        lookup_user_in_canvas_with_ladok_id('8be091b3-5a94-11e8-9dae-241de8ab435c') #Toni	Hinas	2018-06-05 00:00:00	EQ112X
        lookup_user_in_canvas_with_ladok_id('7cc7e806-5a96-11e8-9dae-241de8ab435c') #Isabelle	Ton	2018-06-05 00:00:00	EQ112X
        lookup_user_in_canvas_with_ladok_id('2c2e3513-5a96-11e8-9dae-241de8ab435c') #Erik') #Gåvermark	2018-06-05 00:00:00	ED112X
        lookup_user_in_canvas_with_ladok_id('a1656132-5a96-11e8-9dae-241de8ab435c') #Wera	Mauritz	2018-06-05 00:00:00	EF112X
        lookup_user_in_canvas_with_ladok_id('427dd8f2-4df5-11e8-a562-6ec76bb54b9f') #Mikko Erik') #Kjellberg	2018-06-05 00:00:00	EI130X
        lookup_user_in_canvas_with_ladok_id('a2a3e5fc-5a94-11e8-9dae-241de8ab435c') #Mikael	Hug	2018-06-05 00:00:00	EN191X
        lookup_user_in_canvas_with_ladok_id('242288f4-5a95-11e8-9dae-241de8ab435c') #Fredrik') #Wallin Forsell	2018-06-05 00:00:00	EN191X
        lookup_user_in_canvas_with_ladok_id('abc01e78-12b3-11e7-afc1-27c55ac24396') #Johan	Hagman	2018-06-05 00:00:00	EN191X
        lookup_user_in_canvas_with_ladok_id('66594a5c-5a93-11e8-9dae-241de8ab435c') #Seloan	Saleh	2018-06-05 00:00:00	EN191X
        lookup_user_in_canvas_with_ladok_id('90bb7a65-5a96-11e8-9dae-241de8ab435c') #Andreu') #Salcedo Bosch	2018-06-05 00:00:00	EI130X
        lookup_user_in_canvas_with_ladok_id('e31ce730-01c4-11e8-ad82-65c986724815') #Hampus') #Bäckström	2018-05-18 00:00:00	EI252X
        lookup_user_in_canvas_with_ladok_id('62903a4f-b5a5-11e7-96e6-896ca17746d1') #Daniel	Kruczek	2018-03-24 00:00:00	DA225X
        lookup_user_in_canvas_with_ladok_id('1c5a35fe-b573-11e7-96e6-896ca17746d1') #Sai Man	Wong	2018-03-12 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('9c856eb1-5a94-11e8-9dae-241de8ab435c') #Robert	Alnesjö	2018-02-23 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('b86c7d7e-b59d-11e7-96e6-896ca17746d1') #David') #Lindström	2018-02-22 00:00:00	DA222X
        lookup_user_in_canvas_with_ladok_id('23a3fc71-5a90-11e8-9dae-241de8ab435c') #Andreas	Kokkalis	2018-01-29 00:00:00	II246X
        lookup_user_in_canvas_with_ladok_id('ceb3f1dc-b5a5-11e7-96e6-896ca17746d1') #Daniil	Bogdanov	2018-01-21 00:00:00	DA222X
        return



    input_filename=options.file
    output_filename=input_filename[:-5]+'-augmented-a.xlsx'
    print("input_filename={0}, output_filename={1}".format(input_filename, output_filename))
    if not testing:
        writer = pd.ExcelWriter(f'{output_filename}', engine='xlsxwriter')

    working_df = pd.read_excel(input_filename, engine='openpyxl', index_col=0)

    working_df.reset_index(drop=True, inplace=True)

    # get the data from the degree project course rooms
    # Use the program get_degree_project_course_ids.py to get the list below
    degree_project_course_rooms= [
        493, # DM128X VT17 (61176)
        586, # DD152X VT17 (60353)
        647, # DM129X VT17 (60393)
        827, # DD142X VT17 (61103)
        961, # DA221X VT17 (60332)
        963, # DD151X VT17 (60354)
        991, # DA226X VT17 (60336)
        1072, # DA222X VT17 (60331)
        1074, # DD143X VT17 (60347)
        1101, # DA225X VT17 (60335)
        1221, # DA224X VT17 (60334)
        1268, # DA223X VT17 (60333)
        2379, # DA221X HT17 (50844)
        2380, # DA222X HT17 (50845)
        3085, # DA223X HT17 (50846)
        3214, # DA225X HT17 (51294)
        4125, # DD142X VT18 (60478)
        4138, # DM129X VT18 (60631)
        4157, # DA221X VT18 (60642)
        4315, # DD152X VT18 (60523)
        4653, # DA223X VT18 (60644)
        4656, # DA222X VT18 (60643)
        4929, # DM128X VT18 (61101)
        5279, # DA221X VT18 (61157)
        5399, # DA226X VT18 (61225)
        5565, # DA223X VT18 (61159)
        5568, # DA222X VT18 (61158)
        5756, # DA221X HT17 (51471)
        5757, # DA222X HT17 (51472)
        5758, # DA223X HT17 (51476)
        5759, # DA225X HT17 (51480)
        5760, # DA225X VT18 (61232)
        7248, # DA231X HT18 (51273)
        7249, # DA231X HT18 (51272)
        7250, # DA232X HT18 (51274)
        7251, # DA232X HT18 (51275)
        7252, # DA233X HT18 (51276)
        7253, # DA233X HT18 (51277)
        7254, # DA234X HT18 (51278)
        7255, # DA234X HT18 (51279)
        7258, # DA235X HT18 (51280)
        7259, # DA235X HT18 (51281)
        8537, # DA223X HT18 (51437)
        9094, # DA223X HT18 (51626)
        7529, # DM129X VT19 (60947)
        7546, # ED225X VT19 (60817)
        7547, # ED226X VT19 (60818)
        7559, # EF231X VT19 (60773)
        7560, # EF232X VT19 (60774)
        7561, # EF233X VT19 (60775)
        7581, # EI270X VT19 (60797)
        7586, # EK212X VT19 (60799)
        7587, # EK213X VT19 (60800)
        7589, # EL201X VT19 (60756)
        7590, # EL205X VT19 (60757)
        7594, # EP111X VT19 (60781)
        7597, # EP241X VT19 (60784)
        7598, # EP242X VT19 (60785)
        7599, # EP243X VT19 (60786)
        7603, # EQ274X VT19 (60808)
        7604, # EQ276X VT19 (60809)
        7680, # II142X VT19 (60952)
        7681, # II143X VT19 (60831)
        7692, # IL142X VT19 (60953)
        8199, # DM128X VT19 (60946)
        8239, # ED112X VT19 (60813)
        8240, # EF112X VT19 (61020)
        8241, # EI130X VT19 (60955)
        8242, # EK112X VT19 (60798)
        8243, # EL115X VT19 (60755)
        8244, # EQ112X VT19 (60803)
        8303, # DA231X VT19 (61010)
        8304, # DA231X VT19 (61015)
        8305, # DA232X VT19 (61011)
        8306, # DA232X VT19 (61016)
        8307, # DA233X VT19 (61012)
        8308, # DA233X VT19 (61017)
        8309, # DA234X VT19 (61013)
        8310, # DA234X VT19 (61018)
        8312, # DA235X VT19 (61014)
        8313, # DA235X VT19 (61019)
        11182, # IF226X VT19 (61288)
        11183, # II226X VT19 (61286)
        11184, # IT245X VT19 (61285)
        11185, # II245X VT19 (61289)
        11186, # II246X VT19 (61283)
        11187, # IL226X VT19 (61287)
        11188, # IL246X VT19 (61118)
        11189, # IL248X VT19 (61290)
        11190, # IF245X VT19 (61291)
        11193, # IF246X VT19 (61284)
        11199, # EG230X VT19 (61267)
        11213, # ED225X HT19 (50959)
        11215, # ED226X HT19 (51355)
        11281, # EI270X HT19 (50021)
        11300, # EF231X HT19 (50655)
        11303, # EF232X HT19 (50792)
        11306, # EF233X HT19 (50697)
        11537, # EQ272X VT19 (61296)
        12532, # EL205X HT19 (50700)
        12537, # EQ275X HT19 (50686)
        12540, # EQ276X HT19 (50925)
        12543, # EQ276X HT19 (50936)
        12568, # EQ272X HT19 (50122)
        12572, # EQ272X HT19 (50089)
        12576, # EQ274X HT19 (50483)
        12580, # EQ274X HT19 (50469)
        12584, # EQ275X HT19 (50473)
        16487, # DA226X VT19 (61315)
        16786, # DA236X VT19 (61207)
        16787, # DA236X VT19 (61209)
        16788, # DA239X VT19 (61210)
        16789, # DA239X VT19 (61264)
        16800, # DA236X HT19 (51211)
        16801, # DA236X HT19 (51210)
        16802, # DA239X HT19 (51181)
        16803, # DA239X HT19 (51208)
        16812, # EJ212X VT19 (61331)
        16814, # EN191X VT19 (61329)
        16815, # EP112X VT19 (61332)
        17083, # DD142X VT20 (60298)
        17086, # DD152X VT20 (60537)
        17124, # ED225X VT20 (60522)
        17128, # ED226X VT20 (60523)
        17142, # EQ275X VT20 (60374)
        17146, # EQ276X VT20 (60318)
        17148, # EI270X VT20 (60508)
        17159, # EL205X VT20 (60477)
        17167, # EF231X VT20 (60216)
        17169, # EF232X VT20 (60208)
        17172, # EF233X VT20 (60209)
        17192, # EQ272X VT20 (60370)
        17195, # EQ274X VT20 (60314)
        17205, # II142X VT20 (60907)
        17208, # II142X VT20 (60570)
        17211, # II143X VT20 (60159)
        17218, # II246X VT20 (60682)
        17254, # IF246X VT20 (60913)
        17261, # IL142X VT20 (60577)
        17277, # IL246X VT20 (60650)
        17638, # ED112X VT20 (60832)
        17640, # EL115X VT20 (60274)
        17641, # EQ112X VT20 (60334)
        17657, # DM128X VT20 (60201)
        17746, # DA231X VT20 (60886)
        17750, # DA232X VT20 (60625)
        17753, # DA233X VT20 (60735)
        17757, # DA234X VT20 (60278)
        17783, # DA236X VT20 (60772)
        17786, # DA236X VT20 (60014)
        17790, # DA239X VT20 (60177)
        17793, # DA239X VT20 (60206)
        17919, # EQ275X VT19 (61380)
        18073, # EP248X VT19 (61388)
        18110, # II122X VT19 (61403)
        18112, # II225X VT19 (61405)
        18118, # II123X VT19 (61407)
        18171, # EH241X VT19 (61417)
        18172, # IL122X VT19 (61418)
        18184, # EF226X VT19 (61423)
        18451, # EJ210X VT19 (61479)
        18540, # II249X VT19 (61499)
        18576, # EG201X VT19 (61523)
        18617, # DA232X HT19 (51343)
        18796, # EH241X HT19 (51408)
        19203, # EG230X HT19 (51451)
        19204, # EJ212X HT19 (51450)
        19218, # IL246X HT19 (51467)
        19219, # II226X HT19 (51473)
        19220, # II246X HT19 (51463)
        19221, # DA233X HT19 (51465)
        19231, # IL226X HT19 (51476)
        19233, # DA235X HT19 (51466)
        19274, # II142X HT19 (51524)
        19300, # IF246X HT19 (51539)
        19307, # II249X HT19 (51541)
        19321, # DA231X HT19 (51338)
        19322, # DA231X HT19 (51553)
        19343, # EP248X HT19 (51562)
        19382, # IL142X HT19 (51568)
        19453, # IL122X HT19 (51581)
        19525, # EK213X HT19 (51617)
        19526, # IT245X HT19 (51621)
        19588, # DA236X HT19 (51635)
        19589, # DA236X HT19 (51636)
        19606, # EF226X HT19 (51650)
        19656, # DA233X HT19 (51672)
        19662, # IL248X HT19 (51668)
        19666, # EP242X HT19 (51678)
        19735, # II143X HT19 (51707)
        19764, # DA235X VT20 (61200)
        19765, # EA260X VT20 (61202)
        19766, # DA250X VT20 (61171)
        19767, # EA236X VT20 (61201)
        19775, # DA231X VT20 (61170)
        19780, # EA270X VT20 (61175)
        19781, # EA280X VT20 (61187)
        19782, # EA275X VT20 (61176)
        19870, # EA256X VT20 (61184)
        19871, # DA240X VT20 (61179)
        19872, # DA256X VT20 (61181)
        19873, # DA246X VT20 (61180)
        19874, # EA246X/DA246XVT20
        19875, # DA248X VT20 (61190)
        19876, # EA249X VT20 (61192)
        19877, # IA250X VT20 (61186)
        19878, # IA249X VT20 (61191)
        19879, # DA258X VT20 (61083)
        19880, # EA248X VT20 (61189)
        19881, # EA258X VT20 (61082)
        19884, # IA150X VT20 (61185)
        19885, # IA150X VT20 (60636)
        19886, # DM250X VT20 (61178)
        19887, # EA238X VT20 (61188)
        19893, # DA233X VT20 (61235)
        19894, # DA232X VT20 (61240)
        19895, # DA234X VT20 (61241)
        19896, # DA235X VT20 (61242)
        19897, # EA260X VT20 (61230)
        19898, # EA236X VT20 (61238)
        19899, # EA256X VT20 (61234)
        19900, # DA246X VT20 (61223)
        19901, # DA248X VT20 (61225)
        19902, # IA249X VT20 (61237)
        19903, # EA249X VT20 (61236)
        19904, # EA248X VT20 (61226)
        19905, # EA275X VT20 (61227)
        19906, # EA270X VT20 (61228)
        19907, # EA280X VT20 (61229)
        19908, # DA258X VT20 (61232)
        19909, # DA240X VT20 (61239)
        19910, # EA258X VT20 (61233)
        19911, # DA256X VT20 (61231)
        19912, # EA246X VT20 (61224)
        19972, # II245X HT19 (51336)
        20635, # DA231X HT20 (50506)
        20637, # DA231X HT20 (50509)
        20641, # DA239X HT20 (50635)
        20643, # DA239X HT20 (50756)
        20647, # DA250X HT20 (50758)
        20653, # DA225X VT20 (61281)
        20654, # DA226X VT20 (61270)
        20655, # EH241X VT20 (61288)
        20656, # EG230X VT20 (61283)
        20657, # EJ212X VT20 (61282)
        20658, # EK213X VT20 (61284)
        20659, # EL201X VT20 (61287)
        20660, # IF226X VT20 (61290)
        20661, # EP241X VT20 (61285)
        20662, # EP242X VT20 (61286)
        20663, # IL226X VT20 (61293)
        20664, # II226X VT20 (61289)
        20665, # EP248X VT20 (61146)
        20666, # IT245X VT20 (61292)
        20667, # II245X VT20 (61291)
        21379, # DD152X VT21 (60799)
        21478, # IF246X VT21 (60730)
        21497, # II142X VT21 (60335)
        21501, # II142X VT21 (61016)
        21506, # II143X VT21 (60988)
        21511, # II143X VT21 (61005)
        21531, # IL142X VT21 (60188)
        21538, # IL246X VT21 (60741)
        21992, # DM128X VT21 (60268)
        22047, # EF112X VT21 (60218)
        22072, # DA231X VT21 (60509)
        22074, # DA231X VT21 (60330)
        22078, # DA232X VT21 (60291)
        22082, # DA233X VT21 (60506)
        22087, # DA234X VT21 (60288)
        22128, # DA250X VT21 (60440)
        22130, # DA239X VT21 (60408)
        22132, # DA150X VT21 (61282)
        22134, # DA239X VT21 (60419)
        22152, # DA240X VT21 (60129)
        22156, # IA150X VT21 (60203)
        22309, # II143X VT20 (61265)
        22476, # IL142X VT20 (61406)
        22506, # DA248X VT21 (60465)
        22507, # IA249X VT21 (60471)
        22508, # EA248X VT21 (60468)
        22524, # DA258X VT21 (60478)
        22525, # EA256X VT21 (60474)
        22526, # EA258X VT21 (60475)
        22527, # DA246X VT21 (60472)
        22528, # DA256X VT21 (60477)
        22529, # EA246X VT21 (60473)
        22535, # IA150X VT21 (60479)
        22546, # DA236X VT21 (60458)
        22547, # EA260X VT21 (60486)
        22548, # EA270X VT21 (60485)
        22549, # EA275X VT21 (60483)
        22550, # EA236X VT21 (60481)
        22564, # EF226X VT20 (61438)
        23821, # DA233X HT20 (50244)
        23828, # DA233X HT20 (50672)
        23829, # DA235X HT20 (50009)
        23830, # DA235X HT20 (50079)
        23831, # DA236X HT20 (50679)
        23832, # DA236X HT20 (50691)
        23833, # EA260X HT20 (50710)
        23834, # EA260X HT20 (50713)
        23835, # EA236X HT20 (50693)
        23836, # EA236X HT20 (50702)
        24231, # EA238X HT20 (50833)
        24354, # DA258X HT20 (50922)
        24677, # EA280X HT20 (51064)
        24691, # DA240X HT20 (51077)
        24693, # IL246X HT20 (51086)
        24708, # EA270X HT20 (51092)
        24730, # EA249X HT20 (51137)
        24731, # DA248X HT20 (51125)
        24742, # EK213X HT20 (51159)
        24743, # IA249X HT20 (51155)
        24763, # DA232X HT20 (51178)
        24781, # EA246X HT20 (51211)
        24788, # DA246X HT20 (51216)
        24789, # EA248X HT20 (51215)
        24794, # II142X HT20 (51219)
        24805, # EJ212X HT20 (51228)
        24836, # EA275X HT20 (51270)
        24914, # IA150X HT20 (51273)
        24951, # DA256X HT20 (51327)
        25067, # IL142X HT20 (51353)
        25421, # II143X HT20 (51369)
        25435, # IA150X HT20 (51376)
        25550, # DA235X VT21 (60028)
        25551, # DA235X VT21 (60036)
        25553, # EA238X VT21 (61042)
        25561, # II246X HT20 (51500)
        25563, # EA258X HT20 (51502)
        25573, # DA225X HT20 (51507)
        25577, # IF246X HT20 (51509)
        25578, # DA248X HT20 (51512)
        25579, # DA240X HT20 (51511)
        25580, # EA275X HT20 (51508)
        25817, # DA232X HT20 (51545)
        26377, # II143X HT20 (51551)
        26393, # II143X HT20 (51557)
        27123, # DA231X HT21 (50029)
        27124, # DA231X HT21 (50037)
        27131, # EA280X VT21 (61045)
        27189, # DM250X HT21 (50274)
        28346, # EA249X VT21 (61131)
        28693, # IA250X VT21 (60681)
        29024, # EG230X VT21 (61269)
        30157, # DA233X VT21 (61490)
        30158, # DA258X VT21 (61491)
        30159, # EA258X VT21 (61494)
        30187, # EA246X VT21 (61510)
        30246, # II226X VT21 (61530)
        30249, # DA246X VT21 (61534)
        30334, # DA256X VT21 (61545)
        30373, # DA248X VT21 (61559)
        30375, # EA250X HT21 (50691)
        30383, # DA250X HT21 (50692)
        30440, # DM250X HT21 (50695)
        31167, # II142X VT22 (60668)
        31171, # IL142X VT22 (60647)
        31399, # DA231X VT22 (60129)
        31496, # DD152X VT22 (60547)
        31587, # II142X VT22 (61127)
        31588, # II143X VT22 (60626)
        31871, # DM128X VT22 (60518)
        31891, # EF112X VT22 (60065)
        31923, # DA231X VT22 (60132)
        31924, # DA232X VT22 (60555)
        31925, # DA233X VT22 (60554)
        31926, # DA234X VT22 (60726)
        31959, # DA236X VT22 (60156)
        31971, # EA260X VT22 (60245)
        31972, # EA236X VT22 (60162)
        31977, # EA256X VT22 (60708)
        31978, # DA246X VT22 (61073)
        31979, # DA248X VT22 (61057)
        31980, # DA150X VT22 (60508)
        31981, # IA249X VT22 (61108)
        31982, # EA248X VT22 (61038)
        31983, # EA270X VT22 (60182)
        31986, # DA240X VT22 (61113)
        31987, # DA256X VT22 (60707)
        31988, # EA246X VT22 (61074)
        31989, # IA150X VT22 (60608)
        31990, # EA275X VT22 (60101)
        31991, # DM250X VT22 (60233)
        31992, # DA258X VT22 (60705)
        31993, # EA258X VT22 (60706)
        32033, # DA236X VT21 (61581)
        32083, # IA250X VT22 (60437)
        32089, # DA246X HT21 (50846)
        32115, # DA258X HT21 (50894)
        32560, # IA250X HT21 (51010)
        32664, # EQ276X HT21 (51135)
        32668, # DA234X HT21 (51128)
        32672, # DA232X HT21 (51127)
        32673, # DA233X HT21 (51126)
        32674, # DA234X HT21 (51129)
        32675, # EA260X HT21 (51132)
        32676, # DA240X HT21 (51123)
        32677, # EA275X HT21 (51133)
        32678, # EA238X HT21 (51131)
        32711, # EA246X HT21 (51166)
        32716, # EG230X HT21 (51073)
        32721, # DA236X HT21 (51174)
        32722, # DA239X HT21 (51182)
        32723, # EA236X HT21 (51187)
        32726, # EA256X HT21 (51196)
        32727, # DA248X HT21 (51183)
        32728, # IA249X HT21 (51201)
        32729, # EA248X HT21 (51194)
        32730, # EA270X HT21 (51199)
        32731, # EA280X HT21 (51200)
        32732, # DA256X HT21 (51184)
        32733, # IA150X/II143X HT21/VT22
        32734, # EA249X HT21 (51195)
        32735, # EA258X HT21 (51197)
        32755, # IA150X HT21 (51234)
        32836, # DA152X VT22 (60785)
        33079, # II142X HT21 (51319)
        33445, # IL142X HT21 (51362)
        33446, # IL142X HT21 (51363)
        33521, # DA235X VT22 (60820)
        33522, # DA239X VT22 (60822)
        33523, # DA250X VT22 (60825)
        33524, # EA280X VT22 (60834)
        33525, # EA249X VT22 (60830)
        33526, # EA238X VT22 (60827)
        33527, # EA250X VT22 (60832)
        33528, # DA235X VT22 (60821)
        33529, # DA233X HT21 (51393)
        33530, # DA239X VT22 (60823)
        33532, # DA250X VT22 (60824)
        33533, # EA280X VT22 (60833)
        33534, # EA249X VT22 (60828)
        33536, # EA238X VT22 (60826)
        33537, # EA250X VT22 (60831)
        33574, # EA256X HT21 (51427)
        33575, # DA246X HT21 (51428)
        33576, # DA256X HT21 (51426)
        33577, # EA246X HT21 (51439)
        33578, # DA258X HT21 (51425)
        33579, # EA258X HT21 (51424)
        33780, # DA151X VT22 (60842)
        33837, # EA248X HT21 (51582)
        34053, # DA236X HT21 (51601)
        34054, # DA239X HT21 (51603)
        34415, # EA270X HT21 (51615)
        34809, # DA231X HT22 (50978)
        34812, # DA239X HT22 (51010)
        34815, # DA250X HT22 (51034)
        35051, # DA240X VT22 (60964)
        35081, # DA240X VT21 (60909)
        35581, # DA233X VT22 (61031)
        35711, # EG230X VT22 (61070)
        35712, # DA258X VT22 (61075)
        35945, # DA239X HT22 (50979)
        35955, # DA250X HT22 (51033)
        36216, # DA231X HT22 (50906)
        36451, # IA150X VT22 (61129)
        36619, # II143X VT22 (61140)
        36987, # EA246X VT22 (61187)
        37041, # DA256X VT22 (61192)
        37085, # IL142X VT22 (61291)
        37089, # EA248X VT22 (61290)
        37092, # IA250X HT22 (50551)
        37093, # EA238X HT22 (50552)
        37094, # EA250X HT22 (50553)
        37102, # DA248X VT22 (61313)
        37556, # DD152X VT23 (60178)
        37642, # II142X VT23 (60621)
        37643, # II143X VT23 (60606)
        37905, # DM128X VT23 (61080)
        37924, # EF112X VT23 (60051)
        37951, # DA231X VT23 (61086)
        37952, # DA232X VT23 (61096)
        37953, # DA233X VT23 (61090)
        37954, # DA234X VT23 (60658)
        37987, # DA236X VT23 (60791)
        37988, # DA239X VT23 (60458)
        37998, # EA260X VT23 (60753)
        37999, # EA236X VT23 (60801)
        38006, # EA256X VT23 (60500)
        38007, # DA246X VT23 (60417)
        38008, # DA248X VT23 (60483)
        38009, # DA250X VT23 (60655)
        38010, # DA150X VT23 (60631)
        38011, # IA249X VT23 (60385)
        38012, # EA248X VT23 (60485)
        38013, # EA270X VT23 (60685)
        38016, # DA240X VT23 (60492)
        38017, # DA256X VT23 (60499)
        38018, # EA246X VT23 (60416)
        38019, # IA150X VT23 (60587)
        38020, # EA275X VT23 (60647)
        38023, # DA258X VT23 (60497)
        38024, # EA258X VT23 (60498)
        38051, # DA151X VT23 (60261)
        38113, # DA246X VT22 (61359)
        38466, # DA233X HT22 (50695)
        38525, # EA236X HT22 (50812)
        38526, # EA236X HT22 (50813)
        38527, # EA248X HT22 (50811)
        38932, # DA231X VT23 (60277)
        38972, # DA239X VT23 (60447)
        38989, # DA250X VT23 (60469)
        39065, # II142X VT23 (60287)
        39069, # IL142X VT23 (60260)
        39239, # II143X HT21 (51656)
        39486, # DA236X HT22 (51102)
        39487, # DA236X HT22 (51110)
        39582, # DA248X HT22 (51133)
        39720, # DA240X HT22 (51178)
        39721, # DA256X HT22 (51182)
        39722, # EA275X HT22 (51173)
        39724, # II143X HT22 (51203)
        39726, # DA232X HT22 (51181)
        39727, # EA270X HT22 (51155)
        39746, # II142X/II143X/IA150X HT22/VT23
        39749, # DA234X HT22 (51212)
        39757, # IA249X HT22 (51216)
        39762, # EA258X HT22 (51213)
        39898, # DA233X HT22 (51242)
        39927, # DA258X HT22 (51246)
        39988, # EA260X HT22 (51248)
        40063, # DA246X HT22 (51272)
        40202, # EA246X HT22 (51295)
        40224, # IA150X HT22 (51299)
        40318, # DA258X HT22 (51335)
        40409, # DA235X VT23 (60610)
        40411, # EA238X VT23 (60611)
        40412, # EA250X VT23 (60613)
        40575, # IL142X HT22 (51390)
        40590, # DA240X HT22 (51407)
        40634, # DA256X HT22 (51419)
        41000, # EA249X VT23 (60673)
        41001, # EA249X VT23 (60674)
        41056, # EA249X HT22 (51436)
        41104, # EA248X HT22 (51451)
        41211, # IA250X VT23 (60746)
        41212, # DM250X VT23 (60747)
        7496, # DD142X VT19 (60510)
        7497, # DD152X VT19 (60889)
        17639, # EF112X VT20 (60151)
        19582, # Degree Project at the Department of Intelligent Systems
        19619, # HCT Degree Projects 2020
        25434, # Degree Projects at EECS, 2021
        33514, # Degree Projects at EECS, 2022
        40135, # Degree Projects at EECS, 2023
        877, # EI270X VT17 (60499)
        878, # EI254X VT17 (60497)
        902, # EH111X VT17 (60469)
        903, # EH231X VT17 (60470)
        905, # EH241X VT17 (60472)
        923, # EF111X VT17 (60448)
        927, # EQ276X VT17 (60532)
        983, # ED226X VT17 (60436)
        984, # EQ175X VT17 (60517)
        1004, # EJ111X VT17 (60500)
        1005, # EJ212X VT17 (60503)
        1034, # EL111X VT17 (60165)
        1035, # EL205X VT17 (60167)
        1046, # EQ111X VT17 (60515)
        1048, # EQ174X VT17 (60516)
        1082, # EP242X VT17 (61016)
        1087, # EH253X VT17 (60477)
        1092, # EF226X VT17 (60457)
        1093, # EG230X VT17 (60462)
        1127, # EK211X VT17 (60509)
        1128, # EK213X VT17 (60511)
        1130, # EQ272X VT17 (60529)
        1148, # EK212X VT17 (60510)
        1179, # EQ275X VT17 (60531)
        1185, # EP241X VT17 (61184)
        1208, # EH251X VT17 (60474)
        1209, # EH257X VT17 (60476)
        1210, # EH259X VT17 (60468)
        1228, # EI111X VT17 (60481)
        1239, # EF225X VT17 (60456)
        1247, # EP111X VT17 (61164)
        1249, # EI252X VT17 (60492)
        1255, # EJ210X VT17 (60501)
        1256, # EJ211X VT17 (60502)
        1259, # EF227X VT17 (60458)
        1281, # EL201X VT17 (60166)
        1304, # EH252X VT17 (60478)
        1305, # EH258X VT17 (60475)
        1333, # EQ274X VT17 (60530)
        1340, # EI253X VT17 (60493)
        1341, # EI255X VT17 (60498)
        1367, # ED225X VT17 (60435)
        1387, # ED111X VT17 (61165)
        1393, # EP243X VT17 (61185)
        1402, # EK111X VT17 (61168)
        1406, # EG111X VT17 (61169)
        1416, # EF232X VT17 (61237)
        1474, # EF233X VT17 (61275)
        1477, # EF112X VT17 (61283)
        1479, # EI130X VT17 (61278)
        1481, # EL115X VT17 (61285)
        1482, # EP112X VT17 (61284)
        1484, # EK112X VT17 (61286)
        1553, # ED112X VT17 (61290)
        1554, # EN191X VT17 (61291)
        1555, # EQ112X VT17 (61289)
        1556, # EF231X VT17 (61300)
        2038, # EP248X VT17 (61382)
        2694, # EL111X HT17 (50010)
        2695, # EL205X HT17 (50012)
        2793, # ED225X HT17 (50017)
        2798, # ED226X HT17 (50018)
        2799, # EL201X HT17 (50011)
        2802, # EP241X HT17 (50780)
        2830, # EI270X HT17 (50755)
        2954, # EF225X HT17 (50729)
        2955, # EF226X HT17 (50730)
        2956, # EF227X HT17 (50731)
        2958, # EF231X HT17 (50732)
        2959, # EF232X HT17 (50733)
        2960, # EF233X HT17 (50734)
        3065, # EK211X HT17 (50764)
        3066, # EK212X HT17 (50765)
        3067, # EK213X HT17 (50766)
        3906, # EG230X HT17 (51358)
        3915, # EQ274X HT17 (51353)
        3916, # EQ274X HT17 (51357)
        3917, # EQ276X HT17 (51354)
        3918, # EQ276X HT17 (51356)
        3934, # EJ212X HT17 (51379)
        3944, # EP242X HT17 (51388)
        3948, # EP243X HT17 (51389)
        3949, # EP248X HT17 (51390)
        4158, # EP242X VT18 (60719)
        4299, # EL205X VT18 (60008)
        4376, # ED226X VT18 (60556)
        4382, # EL111X VT18 (60006)
        4383, # EL201X VT18 (60007)
        4386, # EP241X VT18 (60602)
        4423, # EI270X VT18 (60588)
        4471, # EK213X VT18 (60595)
        4516, # ED112X VT18 (60353)
        4548, # EF225X VT18 (60568)
        4549, # EF226X VT18 (60569)
        4550, # EF227X VT18 (60570)
        4551, # EF232X VT18 (60571)
        4584, # EN191X VT18 (60354)
        4619, # EF112X
        4620, # EF233X VT18 (60572)
        4634, # ED225X VT18 (60555)
        4639, # EK211X VT18 (60593)
        4640, # EK212X VT18 (60594)
        4776, # EK112X VT18 (61039)
        4783, # EQ274X VT18 (61049)
        4784, # EQ276X VT18 (61048)
        4885, # EJ210X HT17 (51430)
        4894, # EI253X HT17 (51451)
        4907, # EQ112X VT18 (61111)
        4930, # EI253X VT18 (61102)
        4932, # EP112X VT18 (61110)
        4933, # EL115X VT18 (61112)
        4937, # EI130X VT18 (61114)
        5086, # EJ212X VT18 (61171)
        5095, # EP247X VT18 (61180)
        5396, # EJ210X VT18 (61226)
        5502, # EF231X VT18 (61217)
        5613, # EI111X VT18 (61221)
        5621, # EH251X VT18 (61219)
        5622, # EH111X VT18 (61218)
        5623, # EP111X VT18 (61220)
        5624, # EG230X VT18 (61223)
        5784, # EH115X VT18 (61275)
        5785, # EH231X VT18 (61257)
        5786, # EH241X VT18 (61235)
        5787, # EH253X VT18 (61251)
        5788, # EH258X VT18 (61239)
        5795, # EP240X VT18 (61322)
        5796, # EP248X VT18 (61324)
        5799, # EQ275X VT18 (61240)
        6212, # ED225X HT18 (51067)
        6213, # ED226X HT18 (51068)
        6241, # EF231X HT18 (51012)
        6242, # EF232X HT18 (51013)
        6243, # EF233X HT18 (51015)
        6253, # EH253X HT18 (51286)
        6269, # EI270X HT18 (51038)
        6277, # EK212X HT18 (51040)
        6278, # EK213X HT18 (51041)
        6282, # EL111X HT18 (50980)
        6283, # EL201X HT18 (50985)
        6284, # EL205X HT18 (50986)
        6310, # EQ274X HT18 (51056)
        6311, # EQ274X HT18 (51057)
        6312, # EQ276X HT18 (51058)
        6313, # EQ276X HT18 (51059)
        8619, # EG230X HT18 (51444)
        8629, # EJ212X HT18 (51473)
        8829, # EP242X HT18 (51526)
        8853, # EH241X HT18 (51546)
        8934, # EP247X HT18 (51565)
        8942, # EP248X HT18 (51564)
        9049, # EF226X HT18 (51608)
        9090, # EH258X HT18 (51618)
        9146, # EQ272X HT18 (51602)
        9268, # EH251X HT18 (51721)
        9264, # Degree Project Supervision Group HT2018-P2
        25029, # HCT Degree Projects 2021
        1418, # IF227X VT17 (61272)
        1419, # IL122X VT17 (61254)
        1421, # IF225X VT17 (61262)
        1422, # II123X VT17 (61255)
        1423, # IL142X VT17 (61241)
        1424, # IL226X VT17 (61257)
        1425, # IL249X VT17 (61268)
        1426, # II226X VT17 (61256)
        1427, # IL227X VT17 (61271)
        1429, # II147X VT17 (61264)
        1434, # IF249X VT17 (61269)
        1448, # IF226X VT17 (61258)
        1449, # IF245X VT17 (61249)
        1450, # IF246X VT17 (61245)
        1451, # II142X VT17 (61240)
        1452, # II143X VT17 (61242)
        1453, # II225X VT17 (61259)
        1454, # II245X VT17 (61246)
        1455, # II246X VT17 (61243)
        1458, # IL247X VT17 (61265)
        1459, # II122X VT17 (61273)
        1461, # IL246X VT17 (61244)
        1462, # IL248X VT17 (61247)
        1463, # IF247X VT17 (61266)
        1464, # II227X VT17 (61270)
        1465, # II247X VT17 (61263)
        1466, # II249X VT17 (61267)
        1467, # IL228X VT17 (61260)
        1468, # IT225X VT17 (61261)
        1469, # IT245X VT17 (61248)
        2078, # II147X VT17 (61369)
        2920, # II142X HT17 (51306)
        2921, # II147X HT17 (51326)
        2922, # IL228X HT17 (51323)
        2924, # IT225X HT17 (51324)
        2969, # II247X HT17 (51327)
        3019, # IL247X HT17 (51328)
        3034, # II227X HT17 (51333)
        3035, # IL122X HT17 (51310)
        3044, # IF249X HT17 (51332)
        3045, # II123X HT17 (51311)
        3138, # IF227X HT17 (51334)
        3173, # IL246X HT17 (51313)
        3179, # IL227X HT17 (51235)
        3187, # IF246X HT17 (51314)
        3197, # IF226X HT17 (51317)
        3202, # II245X HT17 (51318)
        3207, # IL248X HT17 (51319)
        3208, # IF245X HT17 (51321)
        3209, # IT245X HT17 (51320)
        3213, # II225X HT17 (51322)
        3218, # IF225X HT17 (51325)
        3219, # IF247X HT17 (51329)
        3220, # II122X HT17 (51309)
        3221, # II143X HT17 (51308)
        3222, # II226X HT17 (51315)
        3223, # II246X HT17 (51312)
        3224, # II249X HT17 (51330)
        3225, # IL142X HT17 (51307)
        3226, # IL226X HT17 (51316)
        3227, # IL249X HT17 (51331)
        4908, # II143X VT18 (61121)
        4909, # II147X VT18 (61128)
        4910, # II225X VT18 (61141)
        4911, # IL122X VT18 (61136)
        4914, # II245X VT18 (61125)
        4915, # II247X VT18 (61129)
        4916, # II249X VT18 (61132)
        4917, # IL142X VT18 (61120)
        4918, # IL226X VT18 (61139)
        4919, # IL227X VT18 (61146)
        4920, # IL228X VT18 (61142)
        4921, # IL246X VT18 (61123)
        4922, # IL247X VT18 (61130)
        4923, # IL248X VT18 (61126)
        4924, # IT225X VT18 (61143)
        4925, # IT245X VT18 (61127)
        4938, # IL249X VT18 (61133)
        4939, # IF249X VT18 (61134)
        4940, # II122X VT18 (61135)
        4941, # IF225X VT18 (61144)
        4942, # IF226X VT18 (61140)
        4943, # IF227X VT18 (61147)
        4944, # IF246X VT18 (61124)
        4945, # IF247X VT18 (61131)
        4946, # II123X VT18 (61137)
        4947, # II142X VT18 (61119)
        4948, # II226X VT18 (61138)
        4949, # II227X VT18 (61145)
        4950, # II246X VT18 (61122)
        8681, # II226X HT18 (51491)
        8780, # IF246X HT18 (51506)
        8781, # II142X HT18 (51507)
        8782, # II143X HT18 (51509)
        8783, # II246X HT18 (51504)
        8784, # IL142X HT18 (51508)
        8785, # IL246X HT18 (51505)
        8804, # II245X HT18 (51522)
        8805, # IL248X HT18 (51521)
        8929, # IL226X HT18 (51562)
        9091, # IL122X HT18 (51627)
        11151, # IT245X HT18 (51575)
        # supplementary data
        8360, # KEXE HT19
        17640, # EL115X VT20 (60274) Degree Project in Electrical Engineering, First Cycle

        
    ]
    all_users=[]

    for course_id in sorted(degree_project_course_rooms):
        print("working on course room {}".format(course_id))
        # look for user - then check for integration_id
        users=users_in_course(course_id)
        if Verbose_Flag:
            print("users={}".format(users))
        all_users.extend(users)
        
    #pprint.pprint(all_users)

    if testing:
        test_user=lookup_user_by_ladok_id('725d9640-d24a-11ea-a4db-82cca4dd4b3e', all_users)
        pprint.pprint(test_user)

        test_user=lookup_user_by_ladok_id('75a4aa93-5a96-11e8-9dae-241de8ab435c', all_users)
        pprint.pprint(test_user)

    for idx, row in working_df.iterrows():
        integration_id=row['integration_id']
        if Verbose_Flag:
            print("integration_id={}".format(integration_id))
        canvas_user_info=lookup_user_by_ladok_id(integration_id, all_users)
        
        if Verbose_Flag:
            print("canvas_user_info={}".format(canvas_user_info))

        if canvas_user_info:
            working_df.at[idx, 'canvas_id']=canvas_user_info['id']
            working_df.at[idx, 'kthid']=canvas_user_info['kthid']
            working_df.at[idx, 'login_id']=canvas_user_info['login_id']
            working_df.at[idx, 'canvas_sortable_name']=canvas_user_info['name']

    # Eliminate the index pseudo column
    working_df.reset_index(drop=True, inplace=True)

    #
    if not testing:
        working_df.to_excel(writer, sheet_name='augmented')

    # Close the Pandas Excel writer and output the Excel file.
    if not testing:
        writer.close()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
