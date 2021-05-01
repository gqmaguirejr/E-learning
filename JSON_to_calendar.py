#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_calendar.py -c course_id 
#
# Example:
# ./JSON_to_calendar.py -c 11
# ./JSON_to_calendar.py -t -v -c 11 --config config-test.json
# ./JSON_to_calendar.py -t -v -c 11 --config config-test.json --mods theses.mods
#
# The program creates an entry (from fixed data), modifies the English language "lead" and the uses PUT to modify the entry, then it get the final entry.
#
# I will work at extending it to also generate an announcement in a Canvas course room and create a calendar entry in the Canvas calendar for this course room.
#
# Once I get the above working, then my plan is to make several programs that can feed it data:
# 1. to take data from DiVA for testing with earlier presentations (so I can generate lots of tests)
# 2. to extract data from my augmented PDF files (which have some of the JSON at the end)
# 3. to extract data from a Overleaf ZIP file that uses my thesis template
# 4. to extract data from a DOCX file that uses my thesis tempalte
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-04-22 G. Q. Maguire Jr.
#
import re
import sys

import json
import argparse
import os			# to make OS calls, here to get time zone info

import requests, time

# Use Python Pandas to create XLSX files
import pandas as pd

import pprint

# for dealing with MODS file
from bs4 import BeautifulSoup

# for dealing with XML
from eulxml import xmlmap
from eulxml.xmlmap import load_xmlobject_from_file, mods
import lxml.etree as etree

from collections import defaultdict


import datetime
import isodate                  # for parsing ISO 8601 dates and times
import pytz                     # for time zones
from dateutil.tz import tzlocal

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

def local_to_utc(LocalTime):
    EpochSecond = time.mktime(LocalTime.timetuple())
    utcTime = datetime.datetime.utcfromtimestamp(EpochSecond)
    return utcTime

def datetime_to_local_string(canvas_time):
    global Use_local_time_for_output_flag
    t1=isodate.parse_datetime(canvas_time)
    if Use_local_time_for_output_flag:
        t2=t1.astimezone()
        return t2.strftime("%Y-%m-%d %H:%M")
    else:
        return t1.strftime("%Y-%m-%d %H:%M")



#############################
###### EDIT THIS STUFF ######
#############################

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests
global cortina_baseUrl
global cortina_header 

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(args):
    global baseUrl, header, payload
    global cortina_baseUrl, cortina_header

    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    config_file=args["config"]

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            access_token=configuration["canvas"]["access_token"]

            if args["containers"]:
                baseUrl="http://"+configuration["canvas"]["host"]+"/api/v1"
                print("using HTTP for the container environment")
            else:
                baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}

            cortina_baseUrl=configuration["KTH_Calendar_API"]["host"]+"/v1/seminar"
            api_key=configuration["KTH_Calendar_API"]["key"]
            cortina_header={'api_key': api_key, 'Content-Type': 'application/json'}

    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()

# Canvas API related functions
def list_of_accounts():
    global Verbose_Flag
    
    entries_found_thus_far=[]

    # Use the Canvas API to get the list of accounts this user can see
    # GET /api/v1/accounts
    url = "{0}/accounts".format(baseUrl)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100'}
    r = requests.get(url, params=extra_parameters, headers = header)

    if Verbose_Flag:
        print("result of getting accounts: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            entries_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            if Verbose_Flag:
                print("result of getting accounts for a paginated response: {}".format(r.text))
            page_response = r.json()  
            for p_response in page_response:  
                entries_found_thus_far.append(p_response)

    return entries_found_thus_far

# Announcements
# Announcements are a special type of discussion in Canvas
# The GUI to create and announcement is of the form ttps://canvas.kth.se/courses/:course_id/discussion_topics/new?is_announcement=true
#

def post_canvas_announcement(course_id, title, message):
    global Verbose_Flag
    
    # Use the Canvas API to Create a new discussion topic
    # POST /api/v1/courses/:course_id/discussion_topics
    url = "{0}/courses/{1}/discussion_topics".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    # title		string	no description
    # message		string	no description
    # is_announcement		boolean	If true, this topic is an announcement. It will appear in the announcement's section rather than the discussions section. This requires announcment-posting permissions.
    # specific_sections		string	A comma-separated list of sections ids to which the discussion topic should be made specific to. If it is not desired to make the discussion topic specific to sections, then this parameter may be omitted or set to “all”. Can only be present only on announcements and only those that are for a course (as opposed to a group).

    extra_parameters={'is_announcement': True,
                      'title':           title,
                      'message':	 message
                      }
    r = requests.post(url, params=extra_parameters, headers = header)

    if Verbose_Flag:
        print("result of posting an announcement: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    else:
        return r.status_code

# Cortina
type_of_seminars=['dissertation', 'licentiate', 'thesis']
schools=['ABE', 'EECS', 'ITM', 'CBH', 'SCI']
departments={"EECS":
             {'CS':  "Datavetenskap",
              'EE':  "Elektroteknik",
              'IS':  "Intelligenta system",
              'MKT': "Människocentrerad teknologi"}}

def post_to_Cortina(seminartype, school, data):
    global Verbose_Flag

    # Use the Cortina Calendar API - to create a new seminar event
    # POST ​/v1​/seminar​/{seminartype}​/{school}
    url = "{0}/{1}/{2}".format(cortina_baseUrl, seminartype, school)
    if Verbose_Flag:
        print("url: {}".format(url))
    r = requests.post(url, headers = cortina_header, json=data)

    if Verbose_Flag:
        print("result of post_to_Cortina: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return r.status_code

def put_to_Cortina(seminartype, school, content_id, data):
    global Verbose_Flag

    # Use the Cortina Calendar API - to create a new seminar event
    # POST ​/v1​/seminar​/{seminartype}​/{school}
    url = "{0}/{1}/{2}/{3}".format(cortina_baseUrl, seminartype, school, content_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    r = requests.put(url, headers = cortina_header, json=data)

    if Verbose_Flag:
        print("result of put_to_Cortina: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return r.status_code

def get_from_Cortina(seminartype, school, content_id):
    global Verbose_Flag

    # Use the Cortina Calendar API - to Get seminar event
    # GET ​/v1​/seminar​/{seminartype}​/{school}​/{contentId}
    url = "{0}/{1}/{2}/{3}".format(cortina_baseUrl, seminartype, school, content_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    r = requests.get(url, headers = cortina_header)

    if Verbose_Flag:
        print("result of get_from_Cortina: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return r.status_code

def create_calendar_event(course_id, start, end, title, description, location_name, location_address):
    # Use the Canvas API to get the calendar event
    # POST /api/v1/calendar_events
    url = "{0}/calendar_events".format(baseUrl)
    if Verbose_Flag:
        print("url: " + url)

    context_code="course_{}".format(course_id) # note that this established the course content
    print("context_code={}".format(context_code))

    payload={'calendar_event[context_code]': context_code,
             'calendar_event[title]': title,
             'calendar_event[description]': description,
             'calendar_event[start_at]': start,
             'calendar_event[end_at]':   end
    }

    # calendar_event[location_name]		string	Location name of the event.
    # calendar_event[location_address]		string	Location address

    if location_name:
        payload['location_name']=location_name
    if location_address:
        payload['location_address']=location_address

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of creating a calendar event: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    else:
        print("status code={}".format(r.status_code))
    return None
    
def get_calendar_event(calendar_event_id):
       # Use the Canvas API to get the calendar event
       #GET /api/v1/calendar_events/:id
       url = "{0}/calendar_events/{1}".format(baseUrl, calendar_event_id)
       if Verbose_Flag:
              print("url: " + url)

       r = requests.get(url, headers = header)
       if Verbose_Flag:
              print("result of getting a single calendar event: {}".format(r.text))

       if r.status_code == requests.codes.ok:
              page_response=r.json()
              return page_response

       return None

required_keys=['advisor',
                'contentId',
                'contentName',
                'dates_endtime',
                'dates_starttime',
                'lead',
                'lecturer',
                'location',
                'opponent',
                'organisation',
                'respondent',
                'respondentUrl',
                'respondentDepartment',
                'seminartype',
                'subjectarea',
                'paragraphs_text',
                'uri']
    
swagger_keys=["contentId",
              "seminartype",
              "organisation",
              "dates_starttime",
              "dates_endtime",
              "contentName",
              "lead",
              "paragraphs_text",
              "advisor",
              "lecturer",
              "opponent",
              "respondent",
              "respondentDepartment",
              "location",
              "uri",
              "subjectarea"]


# processing of MODS data:
def extract_list_of_dicts_from_mods(tree):
    global testing
    json_records=list()
    current_subject_language=''
    list_of_topics_English=list()
    list_of_topics_Swedish=list()
    thesis_abstract_language=list()

    for i in range(0, len(tree.node)):
        if testing and i > 10:   # limit the number of theses to process when testing
            break
        print("processing node={}".format(i))
        if tree.node[i].tag.count("}modsCollection") == 1:
            # case of a modsCollection
            if Verbose_Flag:
                print("Tag: " + tree.node[i].tag)
                print("Attribute: ")
                print(tree.node[i].attrib)
                # case of a mods
        elif tree.node[i].tag.count("}mods") == 1:
            if Verbose_Flag:
                print("new mods Tag: " + tree.node[i].tag)
                #  print "Attribute: " + etree.tostring(tree.node[i].attrib, pretty_print=True) 
                print("Attribute: {}".format(tree.node[i].attrib))
                
            # extract information about the publication
            pub_info=dict()


            #
            current_mod=tree.node[i]
            pub_info['node']=[i]

            pub_info['thesis_title']=dict()
            authors=list()
            supervisors=list()
            examiners=list()
            opponents=list()
            list_of_topics=dict()
            list_of_HSV_subjects=dict()
            list_of_HSV_codes=set()
            current_subject_language=None

            # note types
            level=dict()
            universityCredits=dict()
            venue=None
            cooperation=None

            if Verbose_Flag:
                print("Length of mod: {0}".format(len(current_mod)))
            for mod_element in range(0, len(current_mod)):
                current_element=current_mod[mod_element]
                if Verbose_Flag:
                    print("current element {0}".format(current_element))
                if current_element.tag.count("}genre") == 1:
                    if Verbose_Flag:
                        print("attribute={}".format(current_element.attrib))
                        print("text={}".format(current_element.text))
                    attribute=current_element.attrib
                    type=attribute.get('type', None)
                    if type and (type == 'publicationTypeCode'):
                        if current_element.text == 'studentThesis':
                            pub_info['genre_publicationTypeCode']=current_element.text
                        elif current_element.text in ['comprehensiveDoctoralThesis',
                                                      'comprehensiveLicentiateThesis',
                                                      'monographDoctoralThesis',
                                                      'monographLicentiateThesis']:
                            pub_info['genre_publicationTypeCode']=current_element.text
                        else:
                            print("Unexpected genre publicationTypeCode = {}".format(current_element.text))

                elif current_element.tag.count("}name") == 1:
                    name_given=None
                    name_family=None
                    corporate_name=''
                    affiliation=''
                    role=None
                    kthid=None

                    name_type=current_element.attrib.get('type', 'Unknown')
                    if Verbose_Flag:
                        print("name_type={}".format(name_type))
                        print("current_element.attrib={}".format(current_element.attrib))
                    # note the line below is based on the manual expansion of the xlink name space
                    kthid=current_element.attrib.get('{http://www.w3.org/1999/xlink}href', None)
                    if Verbose_Flag:
                        print("kthid={}".format(kthid))

                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}namePart") == 1:
                            if name_type == 'personal':
                                #   name_family, name_given, name_type, affiliation
                                if Verbose_Flag:
                                    print("namePart: {}".format(elem.text))
                                if len(elem.attrib) > 0 and Verbose_Flag:
                                    print(elem.attrib)
                                namePart_type = elem.attrib.get('type', None)
                                if namePart_type and namePart_type == 'family':
                                    name_family=elem.text
                                    if Verbose_Flag:
                                        print("name_family: {}".format(name_family))
                                elif namePart_type and namePart_type == 'given':
                                    name_given=elem.text
                                    if Verbose_Flag:
                                        print("name_given: {}".format(name_given))
                                elif namePart_type and namePart_type == 'date':
                                    name_date=elem.text
                                    if Verbose_Flag:
                                        print("name_date: {}".format(name_date))
                                elif namePart_type and Verbose_Flag:
                                    print("Cannot parse namePart {0} {1}".format(elem.attrib['type'], elem.text))
                                else:
                                    print("here is no namePart_type")
                            elif name_type == 'corporate':
                                if len(corporate_name) > 0:
                                    corporate_name = corporate_name + "," + elem.text
                                else:
                                    corporate_name = elem.text
                            else:
                                print("dont' know what do do about a namePart")

                        elif elem.tag.count("}role") == 1:
                            if Verbose_Flag and elem.text is not None:
                                print("role: elem {0} {1}".format(elem.attrib, elem.text))
                                print("role length is {}".format(len(elem)))
                            for j in range(0, len(elem)):
                                rt=elem[j]
                                if rt.tag.count("}roleTerm") == 1:
                                    # role, affiliation, author_affiliation, supervisor_affiliation, examiner_affiliation
                                    #  name_family, name_given, author_name_family, author_name_given, supervisor_name_family, supervisor_name_given
                                    #  examiner_name_family, examiner_name_given, corporate_name, publisher_name
                                    #
                                    if len(rt.attrib) > 0 and Verbose_Flag:
                                        print("roleTerm: {}".format(rt.attrib))
                                    if rt.text is not None:
                                        if Verbose_Flag:
                                            print(rt.text)
                                        if rt.text.count('aut') == 1:
                                            author_name_family = name_family
                                            author_name_given = name_given
                                            role = 'aut'
                                            if Verbose_Flag:
                                                print("author_name_family: {}".format(name_family))
                                                print("author_name_given: {}".format(name_given))
                                        elif rt.text.count('ths') == 1:
                                            role = 'ths'
                                            if Verbose_Flag:
                                                print("supervisor_name_family: {}".format(name_family))
                                                print("supervisor_name_given: {}".format(name_given))
                                        elif rt.text.count('mon') == 1:
                                            role = 'mon'
                                            if Verbose_Flag:
                                                print("examiner_name_family: {}".format(name_family))
                                                print("examiner_name_given: {}".format(name_given))
                                        elif rt.text.count('opn') == 1:
                                            role = 'opn'
                                            if Verbose_Flag:
                                                print("examiner_name_family: {}".format(name_family))
                                                print("examiner_name_given: {}".format(name_given))
                                        elif rt.text.count('pbl') == 1:
                                            publisher_name = corporate_name
                                            role = 'pbl'
                                            if Verbose_Flag:
                                                print("publisher_name: {}".format(publisher_name))
                                        elif rt.text.count('oth') == 1:
                                            # clear the corporate_name if this is a "oth" role
                                            corporate_name=''
                                            if Verbose_Flag:
                                                print("name_family: {}".format(name_family))
                                                print("name_given: {}".format(name_given))
                                        else:
                                            if Verbose_Flag:
                                                print("rt[{0}]={1}".format(j, rt))
                        elif elem.tag.count("}affiliation") == 1:
                            # Extract
                            # affiliation, author_affiliation, supervisor_affiliation, examiner_affiliation
                            if Verbose_Flag:
                                print("affiliation :")
                            if len(elem.attrib) > 0:
                                if Verbose_Flag:
                                    print(elem.attrib)
                            if elem.text is not None:
                                if len(affiliation) > 0:
                                    affiliation = affiliation + ' ,' + elem.text
                                else:
                                    affiliation=elem.text
                                    if Verbose_Flag:
                                        print(elem.text)

                        elif elem.tag.count("}description") == 1:
                            if Verbose_Flag:
                                if len(elem.attrib) > 0:
                                    if Verbose_Flag and elem.text is not None:
                                        print("description: {0} {1}".format(elem.attrib, elem.text))

                        else:
                            if Verbose_Flag:
                                print("mod_emem[{0}]={1}".format(n, elem))

                    if  name_given and name_family:
                        full_name=name_given+' '+name_family
                    elif name_given:
                        full_name=name_given
                    elif name_family:
                        full_name=name_family
                    else:
                        full_name=None

                    if full_name:
                        if role == 'aut':
                            author={'name': full_name}
                            if kthid:
                                author['kthid']=kthid
                            if affiliation:
                                author['affiliation']=affiliation
                            authors.append(author)
                        elif role == 'ths':
                            supervisor={'name': full_name}
                            if kthid:
                                supervisor['kthid']=kthid
                            if affiliation:
                                supervisor['affiliation']=affiliation
                            supervisors.append(supervisor)
                        elif role == 'mon':
                            examiner={'name': full_name}
                            if kthid:
                                examiner['kthid']=kthid
                            if affiliation:
                                examiner['affiliation']=affiliation
                            examiners.append(examiner)
                        elif role == 'opn':
                            opponent={'name': full_name}
                            if kthid:
                                opponent['kthid']=kthid
                            if affiliation:
                                opponent['affiliation']=affiliation
                            opponents.append(opponent)
                        elif role == 'pbl':
                            # publisher_name
                            print("publisher_name={}".format(publisher_name))
                        elif role == 'oth':
                            # clear the corporate_name if this is a "oth" role
                            print("role is oth")
                        else:
                            if name_given and name_family:
                                print("Unknown role for {0} {1}".format(name_given, name_family))
                # end of processing a name
                elif current_element.tag.count("}titleInfo") == 1:
                    if Verbose_Flag:
                        print("TitleInfo: ")
                    if len(current_element.attrib) > 0:
                        if Verbose_Flag:
                            print("current_element.attrib={}".format(current_element.attrib))
                        titleInfo_type=current_element.attrib.get('type', None)
                        titleInfo_lang=current_element.attrib.get('lang', None)
                        if current_element.text is not None:
                            if Verbose_Flag:
                                print("{}".format(current_element.text))
                        for j in range(0, len(current_element)):
                            elem=current_element[j]
                            if elem.tag.count("}title") == 1:
                                if len(elem.attrib) > 0:
                                    if Verbose_Flag:
                                        print("{}".format(elem.attrib))
                                if elem.text is not None:
                                    if titleInfo_type == 'alternative':
                                        if pub_info['thesis_title'].get('alternative', None):
                                            pub_info['thesis_title']['alternative'][titleInfo_lang]=elem.text
                                        else:
                                            pub_info['thesis_title']['alternative']=dict()
                                            pub_info['thesis_title']['alternative'][titleInfo_lang]=elem.text
                                    else:
                                        pub_info['thesis_title'][titleInfo_lang]=elem.text
                            else:
                                if Verbose_Flag:
                                    print("mod_emem[{0}]={1}".format(i, elem))

                # skip this:
                elif current_element.tag.count("}language") == 1:
                    objectPart=current_element.attrib.get('objectPart', None)
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}languageTerm") == 1:
                            type=elem.attrib.get('type', None)
                            if type == 'code' and objectPart == 'defence':
                                pub_info['defence_language']=elem.text
                            if type == 'code' and objectPart is None:
                                pub_info['thesis_language']=elem.text

                
                elif current_element.tag.count("}originInfo") == 1:
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}dateIssued") == 1:
                            if elem.text is not None:
                                pub_info['dateIssued']=elem.text
                        elif elem.tag.count("}dateOther") == 1:
                            if elem.text is not None:
                                if Verbose_Flag:
                                    print("dateOther: {0} {1}".format(elem.attrib, elem.text))
                                if pub_info.get('dateOther', None) is None:
                                    pub_info['dateOther']=dict()
                                dateOther_type=elem.attrib.get('type', None)
                                pub_info['dateOther'][dateOther_type]=elem.text
                        else:
                            if Verbose_Flag:
                                print("mod_emem[{0}]={1}".format(i, elem))

                elif current_element.tag.count("}physicalDescription") == 1:
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if pub_info.get('physicalDescription', None) is None:
                            pub_info['physicalDescription']=dict()
                        if elem.tag.count("}form") == 1:
                            if elem.text is not None:
                                pub_info['physicalDescription']['form']=elem.text
                        elif elem.tag.count("}extent") == 1:
                            if elem.text is not None:
                                pub_info['physicalDescription']['extent']=elem.text
                        else:
                            if Verbose_Flag:
                                print("physicalDescription elem[{0}]={1}".format(i, elem))


                elif current_element.tag.count("}identifier") == 1:
                    if current_element.text is not None:
                        identifier_type=current_element.attrib.get('type', None)
                        if identifier_type == 'uri':
                            pub_info['thesis_uri']=current_element.text
                        elif identifier_type == 'isbn':
                            pub_info['thesis_isbn']=current_element.text
                        else:
                            print("Unhandled identifier: {0} of type {1}".format(current_element.text, identifier_type))

                elif current_element.tag.count("}abstract") == 1:
                    abstract_lang=current_element.attrib.get('lang', None)
                    if abstract_lang is None:
                        print("No language for abstract={}".format(current_element.text))
                    else:
                        if pub_info.get('abstract', None) is None:
                            pub_info['abstract']=dict()
                        if current_element.text is not None:
                            pub_info['abstract'][abstract_lang]=current_element.text
                            if Verbose_Flag:
                                print("Abstract: {0} {1}".format(abstract_lang, current_element.text))


                elif current_element.tag.count("}subject") == 1:
                    if len(current_element.attrib) > 0:
                        if Verbose_Flag:
                            print("subject attributes={}".format(current_element.attrib))
                        current_subject_language=current_element.attrib.get('lang', None)
                        authority=current_element.attrib.get('authority', None)
                        xlink=current_element.attrib.get('{http://www.w3.org/1999/xlink}href', None)
                        if xlink:
                            if Verbose_Flag:
                                print("xlink={}".format(xlink))
                            list_of_HSV_codes.add(xlink) # the codes are the same independent of the language
                        if Verbose_Flag:
                            print("current_subject_language={}".format(current_subject_language))
                        if Verbose_Flag:
                            if len(current_element.attrib) > 0:
                                if Verbose_Flag:
                                    print("subject: {0} {1} {2}".format(current_element.tag, current_element.text, current_element.attrib))
                            else:
                                print("subject: {0} {1}".format(current_element.tag, current_element.text))

                        for j in range(0, len(current_element)):
                            elem=current_element[j]
                            if elem.tag.count("}topic") == 1:
                                if elem.text is not None:
                                    if current_subject_language:
                                        if authority == 'hsv':
                                            add_word_to_dictionary(list_of_HSV_subjects, current_subject_language, elem.text)
                                        else:
                                            add_word_to_dictionary(list_of_topics, current_subject_language, elem.text)
                                    else:
                                        print("no language specified for subject, topic is: {}".format(elem.text))

                                    if Verbose_Flag:
                                        print("topic: {0} {1}".format(elem.tag, elem.text))

                            else:
                                if Verbose_Flag:
                                    print("mod_emem[{0}]={1}".format(i, elem))

                elif current_element.tag.count("}recordInfo") == 1:
                    if Verbose_Flag:
                        print("recordInfo: {}".format(current_element))
                        for j in range(0, len(current_element)):
                            elem=current_element[j]
                            if elem.tag.count("}recordOrigin") == 1:
                                if elem.text is not None:
                                    thesis_recordOrigin=elem.text
                                    pub_info['recordOrigin']=elem.text
                            elif elem.tag.count("}recordContentSource") == 1:
                                if elem.text is not None:
                                    pub_info['recordContentSource']=elem.text
                            elif elem.tag.count("}recordCreationDate") == 1:
                                if elem.text is not None:
                                    pub_info['recordCreationDate']=elem.text
                            elif elem.tag.count("}recordChangeDate") == 1:
                                if elem.text is not None:
                                    pub_info['recordChangeDate']=elem.text
                            elif elem.tag.count("}recordIdentifier") == 1:
                                if elem.text is not None:
                                    pub_info['recordIdentifier']=elem.text
                            else:
                                if Verbose_Flag:
                                    print("mod_emem[{0}]={1}".format(i, elem))
                

                elif current_element.tag.count("}note") == 1:
                    type=current_element.attrib.get('type', None)
                    lang=current_element.attrib.get('lang', None)
                    if type == 'level':
                        add_word_to_dictionary(level, lang, current_element.text)
                    elif type == 'universityCredits':
                        add_word_to_dictionary(universityCredits, lang, current_element.text)
                    elif type == 'venue':
                        pub_info['venue']=current_element.text
                    elif type == 'cooperation':
                        pub_info['cooperation']=current_element.text
                    elif type == 'degree':
                        pub_info['degree']=current_element.text
                    elif type == 'funder':
                        pub_info['funder']=current_element.text
                    elif type == 'thesis':
                        pub_info['thesis_note']=current_element.text
                    elif type == 'papers':
                        pub_info['papers_note']=current_element.text
                    elif type == 'project':
                        pub_info['project']=current_element.text
                    elif type == 'publicationChannel':
                        pub_info['publicationChannel']=current_element.text
                    elif type == None:
                        if Verbose_Flag:
                            print("note type of None")
                    else:
                        print("unknown note type={0} {1}".format(type, current_element.text))

                elif current_element.tag.count("}typeOfResource") == 1:
                    if Verbose_Flag:
                        print("typeOfResource: {0} {1}".format(current_element.tag, current_element.text))
                    pub_info['typeOfResource']=current_element.text

                elif current_element.tag.count("}relatedItem") == 1:
                    relatedItem=current_element.attrib.get('type', None)
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}titleInfo") == 1:
                            for k in range(0, len(elem)):
                                relatedItem_titleInfo=elem[k]
                                if relatedItem_titleInfo.tag.count("}title") == 1:
                                    if relatedItem_titleInfo.text is not None:
                                        if pub_info.get('relatedItem', None) is None:
                                            pub_info['relatedItem']=dict()
                                        pub_info['relatedItem']['title']=relatedItem_titleInfo.text
                        elif elem.tag.count("}identifier") == 1:
                            relatedItem_id_type=elem.attrib.get('type', None)
                            if pub_info.get('relatedItem', None) is None:
                                pub_info['relatedItem']=dict()
                            if pub_info['relatedItem'].get('identifier', None) is None:
                                pub_info['relatedItem']['identifier']=dict()
                            pub_info['relatedItem']['identifier'][relatedItem_id_type]=elem.text
                            if Verbose_Flag:
                                print("relatedItem {0} {1}".format(relatedItem_id_type, elem.text))
                        else:
                            if Verbose_Flag:
                                print("Unknown relatedItem elem{0}]={1}".format(i, elem))

            if authors:
                pub_info['authors']=authors
            if supervisors:
                pub_info['supervisors']=supervisors
            if examiners:
                pub_info['examiners']=examiners
            if opponents:
                pub_info['opponents']=opponents

            if list_of_topics:
                pub_info['keywords']=list_of_topics

            if list_of_HSV_subjects:
                pub_info['HSV_subjects']=list_of_HSV_subjects

            if list_of_HSV_codes:
                pub_info['HSV_codes']=list_of_HSV_codes

            if level:
                pub_info['level']=level
            if universityCredits:
                pub_info['universityCredits']=universityCredits

            if Verbose_Flag:
                print("pub_info is {}".format(pub_info))
            #df2 = pd.DataFrame(record) 
            #print("df for record is {}".format(df2))

        json_records.append(pub_info)
    return json_records

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
    if school == 'ABE':
        return "Arkitektur och samhällsbyggnad"
    elif school == 'EECS':
        return "Elektroteknik och datavetenskap"
    elif school == 'ITM':
        return "Industriell teknik och management"
    elif school == 'CBH':
        return "Kemi, bioteknologi och hälsa"
    elif school == 'SCI':
        return "Teknikvetenskap"
    else:
        return "Unknown"
    

def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing

    Use_local_time_for_output_flag=True

    timestamp_regex = r'(2[0-3]|[01][0-9]|[0-9]):([0-5][0-9]|[0-9]):([0-5][0-9]|[0-9])'

    argp = argparse.ArgumentParser(description="II2202-grades_to_report.py: look for students who have passed the 4 assignments and need a grade assigned")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")

    argp.add_argument("-c", "--canvas_course_id", type=int, required=True,
                      help="canvas course_id")

    argp.add_argument('-C', '--containers',
                      default=False,
                      action="store_true",
                      help="for the container enviroment in the virtual machine, uses http and not https")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-m', '--mods',
                      type=str,
                      default="theses.mods",
                      help="read mods formatted information from file"
                      )



    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    initialize(args)
    if Verbose_Flag:
        print("baseUrl={}".format(baseUrl))
        print("cortina_baseUrl={0}".format(cortina_baseUrl))

    course_id=args["canvas_course_id"]
    print("course_id={}".format(course_id))

    testing=args["testing"]
    print("testing={}".format(testing))

    mods_filename=args["mods"]
    try:
        with open(mods_filename, "rb") as mods_data_file:
            tree=load_xmlobject_from_file(mods_data_file, mods.MODS)
            xml=BeautifulSoup(mods_data_file, 'lxml-xml')

    except:
        print("Unable to open mods file named {}".format(mods_filename))
        print("Please create a suitable mods file, the default name is theses.mods")
        sys.exit()


    if mods_filename:
        #tree.node
        #<Element {http://www.loc.gov/mods/v3}modsCollection at 0x34249b0>
        #>>> tree.node[1]
        #<Element {http://www.loc.gov/mods/v3}mods at 0x3d46aa0>
        json_records=extract_list_of_dicts_from_mods(tree)
        if Verbose_Flag:
            print("json_records={}".format(json_records))

        for i in range(0, len(json_records)):
            record=json_records[i]

            data=dict()
            data['contentId']=''

            typeOfDocument=record.get('genre_publicationTypeCode', None)
            
            if typeOfDocument == 'studentThesis':
                data['seminartype']='thesis'
            elif typeOfDocument in ['comprehensiveDoctoralThesis',
                                                      'comprehensiveLicentiateThesis',
                                                      'monographDoctoralThesis',
                                                      'monographLicentiateThesis']:
                continue
            else:
                print("Unexpected type of document={}".format(typeOfDocument))
                continue

            # 2021-01-28T13:00:00
            dateother=record.get('dateOther', None)
            if dateother:
                oral_presentation_date_time=dateother.get('defence', None)
                if oral_presentation_date_time:
                    local_start=datetime.datetime.fromisoformat(oral_presentation_date_time)
                    utc_datestart=local_to_utc(local_start).isoformat()+'.000Z'
                    local_end=local_start+datetime.timedelta(hours = 1.0)
                    utc_dateend=local_to_utc(local_end).isoformat()+'.000Z'
                    data['dates_starttime']=utc_datestart
                    data['dates_endtime']=utc_dateend
                else:
                    continue    # If there is no date, then there is no point in trying to put an entry in the calendar
            else:
                continue        # If there is no date, then there is no point in trying to put an entry in the calendar

            series=record['relatedItem']['title']
            if series.find('ABE') > 0:
                school='ABE'
            elif series.find('CBH') > 0:
                school='CBH'
            elif series.find('EECS') > 0:
                school='EECS'
            elif series.find('ITM') > 0:
                school='ITM'
            elif series.find('SCI') > 0:
                school='SCI'
            else:
                school='Unknown'
                print("Unknown series={}".format(series))

            authors_names=[x['name'] for x in record['authors']]
            data['lecturer']='&'.join(authors_names)
            data['respondent']="" 			# must be present but empty
            data['respondentDepartment']=""		# must be present but empty

            if record.get('opponents', None):
                opponents_names=[x['name'] for x in record['opponents']]
                data['opponent']='&'.join(opponents)
            else:
                data['opponent']="TBA"   		# we do not know the opponents from the DiVA record

            # 'supervisors': [{'name': 'Anders Västberg', 'kthid': 'u1ft3a12', 'affiliation': 'KTH, ...}]
            supervisr_names=[x['name'] for x in record['supervisors']]
            data['advisor']='&'.join(supervisr_names)

            examiners_names=[x['name'] for x in record['examiners']]
            # for the momement do not add examiner - until the API supports it
            # data['examiner']='&'.join(examiners_names)

            # take organisation from examiner's affiliation
            examiners_affiliation=[x['affiliation'] for x in record['examiners']]
            if examiners_affiliation:
                examiners_affiliation_text='&'.join(examiners_affiliation)
                print("examiners_affiliation_text={}".format(examiners_affiliation_text))
                if examiners_affiliation_text == 'KTH, Kommunikationssystem, CoS':
                    department='Datavetenskap'
                elif examiners_affiliation_text == 'KTH, Tal-kommunikation':
                    department='Datavetenskap'
                else:
                    department='Unknown'
               
                data['organisation']= { "school": school,
                                        "department": department }
            else:
                data['organisation']={"school": school,
                                      "department": "Unknown" }

                    

            # 'thesis_title': {'eng': '2D object detection and semantic segmentation in the Carla simulator', 'alternative': {'swe': '2D-objekt detektering och semantisk segmentering i Carla-simulatorn'}}
            # "contentName": {
            # "en_GB": "UAV Navigation using Local Computational Resources: Keeping a target in sight",
            # "sv_SE": "UAV Navigering med Lokala Beräkningsresurser: Bevara ett mål i sensorisk räckvidd"
            # },
            
            thesis_title=record['thesis_title']
            thesis_main_title_lang=None
            thesis_secondary_title_lang=None
            thesis_secondary_title=None

            # note that here were are only supporting a main or secondary language of eng or swe
            # as the Cortina Calendar API is only supporting thwse two languages (as  en_GB and sv_SE
            # case of an English primary title and possible Swedish alternative title
            thesis_main_title=thesis_title.get('eng', None)
            if thesis_main_title:
                thesis_main_title_lang='eng'
                thesis_secondary_title_alternative=thesis_title.get('alternative', None)
                if thesis_secondary_title_alternative:
                    thesis_secondary_title=thesis_secondary_title_alternative.get('swe', None)
                    if thesis_secondary_title:
                        thesis_secondary_title_lang='swe'
            else:
                # case of an Swedish primary title and possible English alternative title
                thesis_main_title=thesis_title.get('swe', None)
                if thesis_main_title:
                    thesis_main_title_lang='swe'
                    thesis_secondary_title_alternative=thesis_title.get('alternative', None)
                    if thesis_secondary_title_alternative:
                        thesis_secondary_title=thesis_secondary_title_alternative.get('eng', None)
                        if thesis_secondary_title:
                            thesis_secondary_title_lang='eng'

            # If no secondary title, use the primary title
            if not thesis_secondary_title:
                thesis_secondary_title=thesis_main_title

            if not thesis_main_title_lang:
                print("language of main title is not eng or swe, I'm dazed and confused")
            else:
                if thesis_main_title_lang == 'eng':
                    data['contentName']={'en_GB': thesis_main_title,
                                         'sv_SE': thesis_secondary_title
                                         }
                else:
                    data['contentName']={'en_GB': thesis_secondary_title,
                                         'sv_SE': thesis_main_title
                                         }

            # from level and credits we can determine if it is a 1st or 2nd cycle thesis
            # 'level': {'swe': ['Självständigt arbete på avancerad nivå (masterexamen)']}, 'universityCredits': {'swe': ['20 poäng / 30 hp']}}, {'node': [1], 'thesis_title': {'eng': '3D Human Pose and Shape-aware Modelling', 'alternative': {'swe': 'Modellering av mänskliga poser och former i 3D'}}
            # "Level": {
            #     // Level field:
            #     // <option value="H1">Independent thesis Advanced level (degree of Master (One Year))</option>
            #     // <option value="H2">Independent thesis Advanced level (degree of Master (Two Years))</option>
            #     // <option value="H3">Independent thesis Advanced level (professional degree)</option>
            #     // <option value="M2">Independent thesis Basic level (degree of Bachelor)</option>
            #     // <option value="M3">Independent thesis Basic level (professional degree)</option>
            #     // <option value="M1">Independent thesis Basic level (university diploma)</option>
            #     // <option value="L1">Student paper first term</option>
            #     // <option value="L3">Student paper other</option>
            #     // <option value="L2">Student paper second term</option>
            #     'Independent thesis Advanced level (degree of Master (One Year))': 'H1',
            #     'Independent thesis Advanced level (degree of Master (Two Years))': 'H2',
            #     'Independent thesis Advanced level (professional degree)': 'H3',
            #     'Independent thesis Basic level (degree of Bachelor)': 'M2',
            #     'Independent thesis Basic level (professional degree)': 'M3',
            #     'Independent thesis Basic level (university diploma)': 'M1',
            #     'Student paper first term': 'L1',
            #     'Student paper other': 'L3',
            #     'Student paper second term': 'L2'
            # },
            # "University credits": {
            #     '7,5 HE credits':	'5',
            #     '10 HE credits':	'7',
            #     '12 HE credits':	'8',
            #     '15 HE credits':	'10',
            #     '18 HE credits':	'12',
            #     '22,5 HE credits':	'15',
            #     '16 HE credits':	'16',
            #     '20 HE credits':	'17',
            #     '30 HE credits': 	'20',
            #     '37,5 HE credits':	'25',
            #     '45 HE credits':	'30',
            #     '60 HE credits':	'40',
            #     '90 HE credits':	'60',
            #     '120 HE credits':	'80',
            #     '180 HE credits':	'120',
            #     '210 HE credits':	'140',
            #     '240 HE credits':	'160',
            #     '300 HE credits':	'200',
            #     '330 HE credits':	'220',
            # },
            # "lead": {
            #     "en_GB": "Master's thesis presentation",
            #     "sv_SE": "Examensarbete presentation"
            # }

            level=record.get('level', None)
            universityCredits=record.get('universityCredits', None)
            if level:
                print("level={}".format(level))
            if universityCredits:
                print("universityCredits={}".format(universityCredits))

            level_swedish=level.get('swe', None)
            if level_swedish:
                if len(level_swedish) > 0:
                    if level_swedish[0].find('grundnivå') > 0:
                        data['lead']={
                            'en_GB': "Bachelor's thesis presentation",
                            'sv_SE': "Kandidate Examensarbete presentation"
                        }
                    else:
                        data['lead']={
                            'en_GB': "Master's thesis presentation",
                            'sv_SE': "Examensarbete presentation"
                        }
                else:
                    if level_swedish.find('grundnivå') > 0:
                        if level_swedish.find('grundnivå') > 0:
                            data['lead']={
                                'en_GB': "Bachelor's thesis presentation",
                                'sv_SE': "Kandidate Examensarbete presentation"
                            }
                        else:
                            data['lead']={
                                'en_GB': "Master's thesis presentation",
                                'sv_SE': "Examensarbete presentation"
                            }
                        
            venue=record.get('venue', None)
            if venue:
                print("venue={}".format(venue))
                data['location']=venue
            else:
                data['location']="Unknown location"


            # pub_info['keywords']=list_of_topics
            # pub_info['HSV_subjects']=list_of_HSV_subjects
            # pub_info['HSV_codes']=list_of_HSV_codes

            keywords_eng_text=''
            keywords_swe_text=''

            list_of_topics=record.get('keywords', None)
            if Verbose_Flag:
                print("list_of_topics={}".format(list_of_topics))
            if list_of_topics:
                keywords_eng=list_of_topics.get('eng', None)
                if keywords_eng:
                    keywords_eng_text=', '.join(keywords_eng)

                keywords_swe=list_of_topics.get('swe', None)
                if keywords_swe:
                    keywords_swe_text=', '.join(keywords_swe)

            #"subjectarea": {
            #"en_GB": "networking",
            #"sv_SE": "nät"
            #}
            data['subjectarea']=dict()
            data['subjectarea']['en_GB']=keywords_eng_text
            data['subjectarea']['sv_SE']=keywords_swe_text


            # "paragraphs_text": {
            #  "en_GB": "<p></p><p><strong>Keywords:</strong> <em>Unmanned aerial vehicle, Path planning, On-board computation, Autonomy</em></p>",
            #  "sv_SE": "<p></p><p><b>Nyckelord:</b> <em>Obemannade drönare, Vägplanering, Lokala beräkningar, Autonomi&#8203;</em></p>"
            # }
            abstracts=record.get('abstract', None)
            if abstracts:
                abstracts_eng=abstracts.get("eng", '')
                abstracts_swe=abstracts.get("swe", '')

            data['paragraphs_text']={
                'en_GB': abstracts_eng,
                'sv_SE': abstracts_swe
                }
            

            data['uri']="https://www.kth.se"

            print("data={}".format(data))
            with open('event.json', 'w') as outfile:
                json.dump(data, outfile, sort_keys = True, indent = 4, ensure_ascii = False)

            print("Checking for extra keys")
            for key, value in data.items():
                if key not in required_keys:
                    print("extra key={0}, value={1}".format(key, value))

            print("Checking for extra keys from Swagger")
            for key, value in data.items():
                if key not in swagger_keys:
                    print("extra key={0}, value={1}".format(key, value))

            response=post_to_Cortina(data['seminartype'], school, data)
            if isinstance(response, int):
                print("response={0}".format(response))
            elif isinstance(response, dict):
                content_id=response['contentId']
            else:
                print("problem in entering the calendar entry")


    if testing:                 #  when testing the parsing of the file and construction of the JSON - just stop here
        return

    if mods_filename:           # if processing a mods file, do not do the following - as this is for manually entering one event
        return

    seminartype='thesis'
    school='EECS'

    presentation_date="2021-01-19"
    local_startTime="16:00"
    local_endTime="17:00"
    utc_datestart=local_to_utc(datetime.datetime.fromisoformat(presentation_date+'T'+local_startTime)).isoformat()+'.000Z'
    utc_dateend=local_to_utc(datetime.datetime.fromisoformat(presentation_date+'T'+local_endTime)).isoformat()+'.000Z'
    data={
        "advisor": "Anders Västberg",
        "contentId": "",
        "contentName": {
            "en_GB": "UAV Navigation using Local Computational Resources: Keeping a target in sight",
            "sv_SE": "UAV Navigering med Lokala Beräkningsresurser: Bevara ett mål i sensorisk räckvidd"
        },
        #"dates_starttime": "2021-01-19T15:00:00.000Z",
        "dates_starttime": utc_datestart,
        #"dates_endtime": "2021-01-19T16:00:00.000Z",
        "dates_endtime": utc_dateend,
        "lead": {
            "en_GB": "Master's thesis presentation",
            "sv_SE": "Examensarbete presentation"
        },
        "lecturer": "M C Hammer",
        "location": "Zoom via https://kth-se.zoom.us/j/xxxxx",
        "opponent": "xxxxxx",
        "organisation": { "school": "EECS", "department": "Datavetenskap" },
        "respondent": "",
        "respondentDepartment": "",
        #"respondentUrl": "",
        "seminartype": "thesis",
        "subjectarea": {
            "en_GB": "networking",
            "sv_SE": "nät"
        },
        "paragraphs_text": {
            "en_GB": "<p>When tracking a moving target, an Unmanned Aerial Vehicle (UAV) must keep the target within its sensory range while simultaneously remaining aware of its surroundings. However, small flight computers must have sufficient environmental knowledge and computational capabilities to provide real-time control to function without a ground station connection. Using a Raspberry Pi 4 model B, this thesis presents a practical implementation for evaluating path planning generators in the context of following a moving target.</p><p>The practical model integrates two waypoint generators for the path planning scenario: A*and 3D Vector Field Histogram* (3DVFH*). The performances of the path planning algorithms are evaluated in terms of the required processing time, distance from the target, and memory consumption. The simulations are run in two types of environments. One is modelled by hand with a target walking a scripted path. The other is procedurally generated with a random walker. The study shows that 3DVFH* produces paths that follow the moving target more closely when the actor follows the scripted path. With a random walker, A* consistently achieves the shortest distance. Furthermore, the practical implementation shows that the A* algorithm’s persistent approach to detect and track objects has a prohibitive memory requirement that the Raspberry Pi 4 with a 2 GB RAM cannot handle. Looking at the impact of object density, the 3DVFH* implementation shows no impact on distance to the moving target, but exhibits lower execution speeds at an altitude with fewer obstacles to detect. The A* implementation has a marked impact on execution speeds in the form of longer distances to the target at altitudes with dense obstacle detection.</p><p>This research project also realized a communication link between the path planning implementations and a Geographical Information System (GIS) application supported by the Carmenta Engine SDK to explore how locally stored geospatial information impact path planning scenarios. Using VMap geospatial data, two levels of increasing geographical resolution were compared to show no performance impact on the planner processes, but a significant addition in memory consumption. Using geospatial information about a region of interest, the waypoint generation implementations are able to query the map application about the legality of its current position.</p><p><strong>Keywords:</strong> <em>Unmanned aerial vehicle, Path planning, On-board computation, Autonomy</em></p>",
            "sv_SE": "<p>När en obemannade luftfarkost, även kallad drönare, spårar ett rörligt mål, måste drönaren behålla målet inom sensorisk räckvidd medan den håller sig uppdaterad om sin omgivning. Små flygdatorer måste dock ha tillräckligt med information om sin omgivning och nog med beräkningsresurser för att erbjuda realtidskontroll utan kommunikation med en markstation. Genom att använda en Raspberry Pi 4 modell B presenterar denna studie en praktisk applicering utav vägplanerare som utvärderas utifrån deras lämplighet att följa ett rörligt mål.</p><p>Den praktiska implementationen jämför två vägplaneringsalgoritmer: A* och 3D Vector Field Histogram* (3DVFH*). Vägplaneringsalgoritmernas prestanda utvärderas genom att studera deras hastighet, avstånd från målet, och minnesresurser. Vägplaneringsalgoritmerna utvärderas i två situationer. Den första är en simulationsvärld som är gjord för hand där målet rör sig efter en fördefinierad väg. Den andra är en procedurellt genererad värld där målet rör sig slumpmässigt. Studien visar att 3DVFH* producerar vägar som håller drönaren närmare målet när målet rör sig efter en fördefinierad väg. Med en slumpvandring i en procedurell värld är A* närmast målet. Resultaten från Raspberry Pi visar också att A* algoritmen sätter prohibitivt höga minneskrav på Raspberry Pi 4 som har 2 GB RAM. Studerar man påverkan av synbara objekt på avståndet till målet, så ser man ingen för 3DVFH* algoritmens egenskap att hålla sig nära, men man ser snabbare bearbetningshastighet när det är färre objekt att upptäcka. A* algoritmen ser en påverkan på dess distans från målet när fler objekt finns att upptäcka.</p><p>Denna studie visar också hur en kommunikationslänk mellan vägplaneringsalgoritmer och kartapplikationer som stöds utav Carmenta Engine SDK skall implementeras. Detta används för att studera hur lokal geografisk information kan användas i ett spårningssammanhang. Genom att använda två nivåer av geografisk upplösning från VMap data, jämförs påverkan på vägplaneringarnas prestanda. Studien visar att ingen påverkan på prestandan kan ses, men att kartapplikationen kräver mer minnesresurser. Genom att använda geografisk information om en region av intresse, visar denna applikation hur vägplaneringsalgoritmerna kan fråga kartapplikationen om legaliteten om sin nuvarande position.</p><p><b>Nyckelord:</b> <em>Obemannade drönare, Vägplanering, Lokala beräkningar, Autonomi&#8203;</em></p>"
        },
        "uri": "https://www.kth.se"
    }

    if Verbose_Flag:
        print("advisor={}".format(data['advisor']))
        print("contentId={}".format(data['contentId']))
        print("contentName={}".format(data['contentName']))
        print("dates_endtime={}".format(data['dates_endtime']))
        print("dates_starttime={}".format(data['dates_starttime']))
        print("lead={}".format(data['lead']))
        print("lecturer={}".format(data['lecturer']))
        print("location={}".format(data['location']))
        print("opponent={}".format(data['opponent']))
        print("organisation={}".format(data['organisation']))
        print("respondent={}".format(data['respondent']))
        #print("respondentUrl={}".format(data['respondentUrl']))
        print("respondentDepartment={}".format(data['respondentDepartment']))
        print("seminartype={}".format(data['seminartype']))
        print("subjectarea={}".format(data['subjectarea']))
        print("paragraphs_text={}".format(data['paragraphs_text']))
        print("uri={}".format(data['uri']))
    
    print("Checking for extra keys")
    for key, value in data.items():
        if key not in required_keys:
            print("extra key={0}, value={1}".format(key, value))
 
    print("Checking for extra keys from Swagger")
    for key, value in data.items():
        if key not in swagger_keys:
            print("extra key={0}, value={1}".format(key, value))

    if not testing:
        response=post_to_Cortina(seminartype, school, data)
        if isinstance(response, int):
            print("response={0}".format(response))
        elif isinstance(response, dict):
            content_id=response['contentId']

            data['lead']['en_GB']="Master's thesis presentation"
            print("updated lead={}".format(data['lead']))

            # must add the value for the contentId to the data
            data['contentId']=content_id
            response2=put_to_Cortina(seminartype, school, content_id, data)
            print("response2={0}".format(response2))

            event=get_from_Cortina(seminartype, school, content_id)
            print("event={0}".format(event))
        else:
            print("unexpected response={0}".format(response))
        

    event_date_time=utc_to_local(isodate.parse_datetime(data['dates_starttime']))
    print("event_date_time={}".format(event_date_time))

    event_date=event_date_time.date()
    event_time=event_date_time.time().strftime("%H:%M")
    title="{0}/{1} on {2} at {3}".format(data['lead']['en_GB'], data['lead']['sv_SE'], event_date, event_time)
    print("title={}".format(title))


    # <pre>Student:   Karim Kuvaja Rabhi
    # Title:     Automatisering av aktiv lyssnare processen inom examensarbetesseminarium
    # Time:      Monday 3 June 2019 at 17:00
    # Place:     Seminar room Grimeton at COM (Kistag&aring;ngen 16), East, Floor 4, Kista
    # Examiner:  Professor Gerald Q. Maguire Jr.
    # Academic Supervisor: Anders V&auml;stberg
    # Opponent: Sebastian Forsmark and Martin Brisfors
    # Language: Swedish 
    # </pre>


    pre_formatted0="Student:\t{0}\n".format(data['lecturer'])
    pre_formatted1="Title:\t{0}\nTitl:\t{1}\n".format(data['contentName']['en_GB'], data['contentName']['sv_SE'])
    pre_formatted2="Place:\t{0}\n".format(data['location'])

    examiner="Professor Gerald Q. Maguire Jr."
    pre_formatted3="Examiner:\t{0}\n".format(examiner)
    pre_formatted4="Academic Supervisor:\t{0}\n".format(data['advisor'])
    pre_formatted5="Opponent:\t{0}\n".format(data['opponent'])

    language_of_presentation='Swedish'
    pre_formatted6="Language:\t{0}\n".format(language_of_presentation)

    pre_formatted="<pre>{0}{1}{2}{3}{4}{5}{6}</pre>".format(pre_formatted0, pre_formatted1, pre_formatted2, pre_formatted3, pre_formatted4, pre_formatted5, pre_formatted6)
    print("pre_formatted={}".format(pre_formatted))

    # need to use the contentID to find the URL in the claendar
    see_also="<p>See also: <a href='https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842'>https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842</a></p>".format()

    body_html="<div style='display: flex;'><div><h2 lang='en'>Abstract</h2>{0}</div><div><h2 lang='sv'>Sammanfattning</h2>{1}</div></div>".format(data['paragraphs_text']['en_GB'], data['paragraphs_text']['sv_SE'])

    print("body_html={}".format(body_html))

    message="{0}{1}".format(pre_formatted, body_html)
    canvas_announcement_response=post_canvas_announcement(course_id, title, message)
    print("canvas_announcement_response={}".format(canvas_announcement_response))



    start=data['dates_starttime']
    end=data['dates_endtime']

    if language_of_presentation == 'Swedish':
        title=data['lead']['sv_SE']
    else:
        title=data['lead']['en_GB']

    if language_of_presentation == 'Swedish':
        description=data['contentName']['sv_SE']
    else:
        description=data['contentName']['en_GB']
    
    location_name=None
    location_address=None
    print("course_id={0}, start={1}, end={2}, title={3}, description={4}, location_name={5}, location_address={6}".format(course_id, start, end, title, description, location_name, location_address))

    canvas_calender_event=create_calendar_event(course_id, start, end, title, message, location_name, location_address)
    print("canvas_calender_event={}".format(canvas_calender_event))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

