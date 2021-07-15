#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./thesis_titles.py -c course_id
#
# An assumption is that there is only one moment that requires a project title, i.e., 'KravPaProjekttitel' is True
#
# Purpose: The program extracts the thesis title from LADOK for all the students in the canvas_course.
#
# Output: spreadsheeet with the data
#
# Example:
#./thesis_titles.py -c 25434
#
#
# 
# 2021-07-15 G. Q. Maguire Jr.
# Based on earlier JSON_to_ladok.py
#

import ladok3
import pprint
import requests, time
import json
import argparse
import sys
import re
import os                       # to make OS calls, here to get time zone info
import datetime
from datetime import datetime

# Use Python Pandas to create XLSX files
import pandas as pd


global canvas_baseUrl	# the base URL used for access to Canvas
global canvas_header	# the header for all HTML requests
global canvas_payload	# place to store additionally payload when needed for options to HTML requests

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(args):
    global canvas_baseUrl, canvas_header, canvas_payload
    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    config_file=args["config"]

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            access_token=configuration["canvas"]["access_token"]

            canvas_baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

            canvas_header = {'Authorization' : 'Bearer ' + access_token}
            canvas_payload = {}

    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()


#
# routinees for use with Canvas
#
def students_in_course(course_id):
    user_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(canvas_baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100',
                      'type': ['StudentEnrollment']}
    
    r = requests.get(url, params=extra_parameters, headers = canvas_header)
    if Verbose_Flag:
        print("result of getting enrollments: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            user_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=canvas_header)
            page_response = r.json()  
            for p_response in page_response:  
                user_found_thus_far.append(p_response)
    return user_found_thus_far

def user_info(user_id):
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/users/:id

    url = "{0}/users/{1}".format(canvas_baseUrl, user_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = canvas_header)
    if Verbose_Flag:
        print("result of getting user: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        return r.json()
    return None


def user_profile_info(user_id):
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/users/:id/profile

    url = "{0}/users/{1}/profile".format(canvas_baseUrl, user_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = canvas_header)
    if Verbose_Flag:
        print("result of getting user profile: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        return r.json()
    return None



#
# routinees for use with LADOK
#
def get_all_results(student_id):
    r = ladok.session.get(url=ladok.base_gui_proxy_url + '/resultat/studentresultat/attesterade/student/' + student_id, headers=ladok.headers).json()
    return r

def get_student_course_moments_JSON(ladok, course_round_id, student_id):
    r = ladok.session.get(
        url=ladok.base_gui_proxy_url +
        '/resultat/kurstillfalle/' + str(course_round_id) +
        '/student/' + str(student_id) + '/moment',
        headers=ladok.headers).json()
    
    return r
#####################################################################
#
# get_results
#
# person_nr          - personnummer, siffror i strängformat
#            t.ex. 19461212-1212
# course_code          - kurskod t.ex. DD1321
#
# RETURNERAR JSON
#
def get_all_results_JSON(self, person_nr_raw, course_code):
    person_nr_raw = str(person_nr_raw)
    person_nr =  format_personnummer(person_nr_raw)
    if not person_nr: raise Exception('Invalid person nr ' + person_nr_raw)
    
    student_data = self.__get_student_data(person_nr)

    student_course = next(x
                          for x in self.__get_student_courses(student_data['id'])
                          if x['code'] == course_code)

    # get attested results
    r = self.session.get(
        url=self.base_gui_proxy_url +
        '/resultat/studentresultat/attesterade/student/' +
        student_data['id'],
        headers=self.headers).json()
    
    results_attested_current_course = None
    results = {}  # return value
    
    for course in r['StudentresultatPerKurs']:
        if course['KursUID'] == student_course['education_id']:
            results_attested_current_course = course['Studentresultat']
            break


    if results_attested_current_course:
        for result in results_attested_current_course:
            try:
                d = { 'grade' : result['Betygsgradskod'],
                      'status': 'attested',
                      'date'  : result['Examinationsdatum'] }
                results[ result['Utbildningskod'] ] = d
            except:
                pass  # tillgodoräknanden har inga betyg och då är result['Utbildningskod'] == None

    # get pending results
    r = self.session.get(
        url=self.base_gui_proxy_url + '/resultat/resultat/resultat/student/' +
        student_data['id'] + '/kurs/' + student_course['education_id'] +
        '?resultatstatus=UTKAST&resultatstatus=KLARMARKERAT',
        headers=self.headers).json()
    
    for result in r['Resultat']:
        r = self.session.get(
            url=self.base_gui_proxy_url + '/resultat/utbildningsinstans/' +
            result['UtbildningsinstansUID'],
            headers=self.headers).json()
        d_grade = result['Betygsgradsobjekt']['Kod']
        d_status = "pending(" + str(result['ProcessStatus']) + ")"
        # utkast har inte datum tydligen ...
        d_date = "0" if 'Examinationsdatum' not in result \
            else result['Examinationsdatum']
        d = { 'grade' : d_grade ,
              'status': d_status,
              'date'  : d_date      } 
        results[ r['Utbildningskod'] ] = d
    return results

######################################################################
######################################################################
# get_all_results_JSON(self, ladok_student_id)
# ladok_student_id is a LADOK Uid for a student
#
# returns a value of the form:
# {'StudentresultatPerKurs': [{'KursUID': 'xxx', 'Studentresultat': [] }]
def get_all_attested_results_JSON(ladok, ladok_student_id):
    # get attested results
    r = ladok.session.get(
        url=ladok.base_gui_proxy_url +
        '/resultat/studentresultat/attesterade/student/' +
        ladok_student_id,
        headers=ladok.headers).json()
    return r
            
def get_titles_of_thesis(ladok, ladok_student_id, course_code, moment):
    s1=get_all_attested_results_JSON(ladok,ladok_student_id)
    relevant_course_ID=None
    for course in s1['StudentresultatPerKurs']: # for each of the courses
        course_results=course['Studentresultat']             # look at the course's results
        for module in course_results:
            if module['Utbildningskod'] == course_code: # see if this course has a moment for the course grade
                relevant_course_ID=course['KursUID']
                print("relevant_course_ID={}".format(relevant_course_ID))
                break
        if relevant_course_ID:      # if so, get the moment PRO3 as this has the titles in it
            for module in course_results:
                if module['Utbildningskod'] == 'PRO3':
                    print("Projekttitel={}".format(module['Projekttitel']))
                    return module['Projekttitel']

# produces: Projekttitel={'AlternativTitel': 'Adapting to the new remote work era', 'Titel': 'Adapting to the new remote work era', 'link': []}

#t1=get_titles_of_thesis(ladok, 'eda96a1a-5a95-11e8-9dae-241de8ab435c', "DA231X", "PRO3")
#Projekttitel={'AlternativTitel': 'Adapting to the new remote work era', 'Titel': 'Adapting to the new remote work era', 'link': []}

def get_titles_of_all_thesis(ladok, ladok_student_id):
    s1=get_all_attested_results_JSON(ladok,ladok_student_id)
    relevant_course_ID=None
    course_code=None
    for course in s1['StudentresultatPerKurs']: # for each of the courses
        course_results=course['Studentresultat']             # look at the course's results
        for module in course_results:
            if module['Utbildningskod'].endswith("X"): #  look for degree projects
                course_code=module['Utbildningskod']
                relevant_course_ID=course['KursUID']
                if Verbose_Flag:
                    print("relevant_course_ID={}".format(relevant_course_ID))
                break
        if relevant_course_ID:      # if so, get the moment PRO3 as this has the titles in it
            for module in course_results:
                if module.get('Projekttitel'):
                    return {'course_code': course_code, 'moment': module['Utbildningskod'], 'titles': module['Projekttitel']}

def get_student_courses(ladok, student_id):
    r = ladok.session.get(
        url=ladok.base_gui_proxy_url +
        '/studiedeltagande/tillfallesdeltagande/kurstillfallesdeltagande/student/'
        + student_id,
        headers=ladok.headers).json()
    return r

def get_all_pending_results_JSON(ladok, ladok_student_id, course_code):
    tresults=get_student_courses(ladok, ladok_student_id)
    for course in tresults['Tillfallesdeltaganden']:
        if not course['Nuvarande'] or \
           'Utbildningskod' not in course['Utbildningsinformation']:
            continue
        if course['Utbildningsinformation']['Utbildningskod'] == course_code:
            education_id=course['Utbildningsinformation']['UtbildningUID'] # ett Ladok-ID för något annat som rör kursen
            instance_id=course['Utbildningsinformation']['UtbildningsinstansUID']
            print("education_id={0}, instance_id={1}".format(education_id, instance_id))
            # get pending results
            r = ladok.session.get(
                url=ladok.base_gui_proxy_url +
                '/resultat/resultat/resultat/student/' +
                ladok_student_id + '/kurs/' + education_id +
                '?resultatstatus=UTKAST&resultatstatus=KLARMARKERAT',
                headers=ladok.headers).json()
            return r
    return None

# returns a response of the form: {'Tillfallesdeltaganden': [ course ]}
#t2=get_all_pending_results_JSON(ladok, 'eda96a1a-5a95-11e8-9dae-241de8ab435c', "DA231X")

 
def instance_id_given_course_code(courses, course_code):
    for course in courses['Tillfallesdeltaganden']:
        if not course['Nuvarande'] or \
           'Utbildningskod' not in course['Utbildningsinformation']:
            continue
      
        if course['Utbildningsinformation']['Utbildningskod'] == course_code:
            result={'id': course['Uid'],
                    'round_id': course['Utbildningsinformation']['UtbildningstillfalleUID'], # ett Ladok-ID för kursomgången
                    'education_id': course['Utbildningsinformation']['UtbildningUID'], # ett Ladok-ID för något annat som rör kursen
                    'instance_id': course['Utbildningsinformation']['UtbildningsinstansUID'], # ett Ladok-ID för att rapportera in kursresultat
                    'swe_name': course['Utbildningsinformation']['Benamning']['sv'],
                    'eng_name': course['Utbildningsinformation']['Benamning']['en']
                    }
            return result
    return None

def get_student_course_moments(ladok, course_round_id, student_id):
    r = ladok.session.get(
        url=ladok.base_gui_proxy_url +
        '/resultat/kurstillfalle/' + str(course_round_id) +
        '/student/' + str(student_id) + '/moment',
        headers=ladok.headers).json()
    
    return [{
        'course_moment_id': moment['UtbildningsinstansUID'],
        'code': moment['Utbildningskod'],
        'education_id': moment['UtbildningUID'],
        'name': moment['Benamning']['sv']
    } for moment in r['IngaendeMoment']]

#m1=get_student_course_moments(ladok, '8e15ae14-1d86-11ea-a622-3565135944de', 'fe5c5c77-5a96-11e8-9dae-241de8ab435c')
# returns: [{'course_moment_id': '3742e13f-73d8-11e8-b4e0-063f9afb40e3', 'code': 'PRO1', 'education_id': '3743560c-73d8-11e8-afa7-8e408e694e54', 'name': 'Projekt'}, {'course_moment_id': '373ee99c-73d8-11e8-b4e0-063f9afb40e3', 'code': 'PRO2', 'education_id': '373ee8cf-73d8-11e8-afa7-8e408e694e54', 'name': 'Projekt'}, {'course_moment_id': '374a826c-73d8-11e8-b4e0-063f9afb40e3', 'code': 'PRO3', 'education_id': '374a818c-73d8-11e8-afa7-8e408e694e54', 'name': 'Projekt'}]

def get_student_course_results(ladok, course_round_id, student_id):
    r = ladok.session.get(
        url=ladok.base_gui_proxy_url +
        '/resultat/studieresultat/student/' + student_id +
        '/utbildningstillfalle/' + course_round_id,
        headers=ladok.headers).json()
    
    return {
        'id': r['Uid'],
        'results': [{
            'education_id': result['UtbildningUID'],
            'pending': {
                'id': result['Arbetsunderlag']['Uid'],
                'moment_id': result['Arbetsunderlag']['UtbildningsinstansUID'],
                'grade': self.__get_grade_by_id(result['Arbetsunderlag']['Betygsgrad']),
                'date': result['Arbetsunderlag']['Examinationsdatum'],
                'grade_scale': self.__get_grade_scale_by_id(result['Arbetsunderlag']['BetygsskalaID']),
                # behövs vid uppdatering av betygsutkast
                'last_modified': result['Arbetsunderlag']['SenasteResultatandring']
            } if 'Arbetsunderlag' in result else None,
            'attested': {
                'id': result['SenastAttesteradeResultat']['Uid'],
                'moment_id': result['SenastAttesteradeResultat']['UtbildningsinstansUID'],
                'grade': self.__get_grade_by_id(result['SenastAttesteradeResultat']['Betygsgrad']),
                'date': result['SenastAttesteradeResultat']['Examinationsdatum'],
                'grade_scale': self.__get_grade_scale_by_id(result['SenastAttesteradeResultat']['BetygsskalaID'])
            } if 'SenastAttesteradeResultat' in result else None
        } for result in r['ResultatPaUtbildningar']]
    }

def validate_date(ladok, date_raw):
    datregex = re.compile("(\d\d)?(\d\d)-?(\d\d)-?(\d\d)")
    dat = datregex.match(date_raw)
    if dat:
        if dat.group(1) == None: # add 20, ladok3 won't survive till 2100
            return "20" + dat.group(2) + "-" + dat.group(3) + "-" + dat.group(4)
        else:
            return dat.group(1) + dat.group(2) + \
                "-" + dat.group(3) + "-" + dat.group(4)
    else:
        return None

def get_integration_id_from_email_address(email_address):
    if Verbose_Flag:
        print("email_address={}".format(email_address))

    info=user_info('sis_login_id:'+email_address)
    user_id=info['id']
    print("sortable name={}".format(info['sortable_name']))
    print("Canvas user_id={}".format(user_id))

    user_profile=user_profile_info(user_id)
    integration_id=user_profile.get('integration_id', None)
    return integration_id

def main(argv):
    global Verbose_Flag
    global testing
    global course_id


    argp = argparse.ArgumentParser(description="thesis_titles.py: to collect thesis titles")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")

    argp.add_argument("-c", "--canvas_course_id", type=int,
                      # required=True,
                      help="canvas course_id")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    initialize(args)
    if Verbose_Flag:
        print("canvas_baseUrl={}".format(canvas_baseUrl))

    # If there is a course number argument, then initializae in prepartion for Canvas API calls
    course_id=args["canvas_course_id"]
    if Verbose_Flag:
        print("course_id={}".format(course_id))
        print("baseUrl={}".format(baseUrl))

    if not course_id:
        print("No course_id was specified, therefore quitting")
        return

    # get the list of students in the course
    students=students_in_course(course_id)
    set_of_student_canvas_ids=set()
    for s in students:
        set_of_student_canvas_ids.add(s['user_id'])

    print("Number of students={}".format(len(set_of_student_canvas_ids)))

    list_of_student_info=list()

    testing=args["testing"]
    print("testing={}".format(testing))

    ladok = ladok3.LadokSessionKTH( # establish as session with LADOK
        os.environ["KTH_LOGIN"], os.environ["KTH_PASSWD"],
        test_environment=False) # for experiments

    number_found=0
    for id in set_of_student_canvas_ids:
        print("Canvas user_id={}".format(id))
        user_profile=user_profile_info(id)
        integration_id=user_profile.get('integration_id', None)
        if Verbose_Flag:
            print("integration_id={}".format(integration_id))

        info=get_titles_of_all_thesis(ladok, integration_id)
        if info:
            student_info=dict()
            student_info['user_id']=id
            student_info['sname']=user_profile['sortable_name']
            course_code=info.get('course_code')
            if course_code:
                student_info['course_code']=course_code
            title=info['titles'].get('Titel')
            if title:
                student_info['title']=title
            alt_title=info['titles'].get('AlternativTitel')
            if alt_title:
                student_info['alt_title']=alt_title
            list_of_student_info.append(student_info)
            number_found=number_found+1
        if testing and number_found > 10:
            print("list_of_student_info={}".format(list_of_student_info))
            break

    users_info_df=pd.json_normalize(list_of_student_info) 
    output_filename="titles-{}.xlsx".format(course_id)                            
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    users_info_df.to_excel(writer, sheet_name='Titles')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    # to logout and close the session
    status=ladok.logout()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
