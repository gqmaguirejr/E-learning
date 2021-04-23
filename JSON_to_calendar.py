#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_calendar.py -c course_id 
#
# Example:
# ./JSON_to_calendar.py
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


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag

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
        
    requireed_keys=['advisor',
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
    
    print("Checking for extra keys")
    for key, value in data.items():
        if key not in requireed_keys:
            print("extra key={0}, value={1}".format(key, value))
 
    print("Checking for extra keys from Swagger")
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

