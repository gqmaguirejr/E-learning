#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./courses_grades_by_school.py -s school_acronym
#
#
# You have to sent the environment variables KTH_LOGIN and KTH_PASSWD to access LADOK.
#
# Purpose: The program extracts the course information from LADOK for all the students to determine the number of moments and grades that are entered per course.
#
# Output: spreadsheeet with the data, the name of the file is of the form:
# courses-in-SCHOOL-YYYY.xlsx
#
# Example:
#./courses_grades_by_school.py -s EECS
#
# 
# 2021-07-15 G. Q. Maguire Jr.
# Based on earlier thesis_titles_by_school.py
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
#from datetime import datetime

# The following is the structure of a course_roud object
# {'_LadokRemoteData__ladok': <ladok3.LadokSessionKTH object at 0x7f391dd776d0>,
# '_CourseInstance__instance_id': '12370dfa-feba-11e8-ab96-f64de0ad4bfb',
# '_CourseInstance__education_id': '9ae3f161-73d8-11e8-afa7-8e408e694e54',
# '_CourseInstance__code': 'FID3020',
# '_CourseInstance__name': {'sv': 'Avancerad kurs i skalbar maskininlärning och djupinlärning',
# 'en': 'Advanced Course in Large Scale Machine Learning and Deep Learning'},
# '_CourseInstance__version': 2,
# '_CourseInstance__credits': 7.5,
# '_CourseInstance__unit': 'HP',
# '_CourseInstance__grade_scale': [{'_GradeScale__id': 131656,
# 				'_GradeScale__code': 'PF',
# 				'_GradeScale__name': 'PF',
# 				'_GradeScale__grades': [{'_Grade__id': 131658, '_Grade__code': 'P', '_Grade__accepted': True, 'type': 'Grade'},
# 							{'_Grade__id': 131663, '_Grade__code': 'F', '_Grade__accepted': False, 'type': 'Grade'}],
# 				'type': 'GradeScale'}],
# '_CourseInstance__components': [{'_CourseComponent__instance_id': '2ffa8751-feba-11e8-ab96-f64de0ad4bfb',
# 			       '_CourseComponent__education_id': '2ffa8754-feba-11e8-ab96-f64de0ad4bfb',
# 			       '_CourseComponent__code': 'EXA1',
# 			       '_CourseComponent__description': [{'Sprakkod': 'sv',
# 			       					'Text': 'Examination',
# 								'link': []},
# 								{'Sprakkod': 'en',
# 								'Text': 'Examination',
# 								'link': []}],
# 				'_CourseComponent__credits': 7.5,
# 				'_CourseComponent__unit': 'HP',
# 				'_CourseComponent__grade_scale': {'_GradeScale__id': 131656,
# 								 '_GradeScale__code': 'PF',
# 								 '_GradeScale__name': 'PF',
# 								 '_GradeScale__grades': [{'_Grade__id': 131658, '_Grade__code': 'P', '_Grade__accepted': True, 'type': 'Grade'},
# 								 {'_Grade__id': 131663, '_Grade__code': 'F', '_Grade__accepted': False, 'type': 'Grade'}],
# 								 'type': 'GradeScale'},
# 								 'type': 'CourseComponent'}],
# '_CourseRound__round_id': '14f6c945-1432-11eb-8b6e-d59fb0604f75',
# '_CourseRound__round_code': '51484',
# '_CourseRound__start': datetime.date(2020, 10, 26),
# '_CourseRound__end': datetime.date(2021, 1, 15),
# 'type': 'CourseRound'}


# Use Python Pandas to create XLSX files
import pandas as pd

from bs4 import BeautifulSoup

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


################################
######    KOPPS related   ######
################################
KOPPSbaseUrl = 'https://api.kth.se'

English_language_code='en'
Swedish_language_code='sv'

KTH_Schools = {
    'ABE':  ['ABE'],
    'CBH':  ['BIO', 'CBH', 'CHE', 'STH'],
    'EECS': ['CSC', 'EES', 'ICT', 'EECS'], # corresponds to course codes starting with D, E, I, and J
    'ITM':  ['ECE', 'ITM'],
    'SCI':  ['SCI']
}
# returns a list of elements of the form: {"code":"IF","name":"ICT/Kommunikationssystem"}
def get_dept_codes(language_code):
    global Verbose_Flag
    # GET https://www.kth.se/api/kopps/v2/departments.en.json
    # GET https://www.kth.se/api/kopps/v2/departments.sv.json
    url = "{0}/api/kopps/v2/departments.{1}.json".format(KOPPSbaseUrl, language_code)
    if Verbose_Flag:
        print("url: {}".format(url))
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting department codes: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    #
    return None

def dept_codes_in_a_school(school_acronym, all_dept_codes):
    dept_codes=[]
    for dept in KTH_Schools[school_acronym]:
        for d in all_dept_codes:
            if d['name'].find(dept) == 0:
                dept_codes.append(d['code'])
    return dept_codes

def get_dept_courses(dept_code, language_code):
    global Verbose_Flag
    # Use the KOPPS API to get the data
    # GET /api/kopps/v2/courses/dd.json
    url = "{0}/api/kopps/v2/courses/{1}.json".format(KOPPSbaseUrl, dept_code)
    if language_code == 'en':
        url = url +'?l=en'    
    if Verbose_Flag:
        print("url: {}".format(url))
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting courses for a department: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    #
    return None

def convert_course_name_to_subject(name_of_course):
    working_str=name_of_course.rsplit(",")[0]
    #
    # if name_of_course begins with "Examensarbete inom ", skip this part
    prefix="Examensarbete inom "
    offset=working_str.find(prefix)
    if offset >= 0:
        working_str=working_str[(offset+len(prefix)):]
        return working_str
    #
    prefix2="Examensarbete i "
    offset2=name_of_course.find(prefix2)
    if offset2 >= 0:
        working_str=working_str[(offset2+len(prefix2)):]
        return working_str
    #
    return working_str


def non_degree_project_courses(requested_dept_codes, language_code):
    global Verbose_Flag
    courses=[]                  # initialize the list of courses
    if len(requested_dept_codes) > 0:
        for d in requested_dept_codes:
            courses_d_all=get_dept_courses(d, language_code)
            
            courses_d=courses_d_all['courses']
            if len(courses_d) == 0: # nothing to do - so skip
                continue
            if Verbose_Flag:
                print("length of courses_d in dept {0} is {1}".format(d, len(courses_d)))
            # extend course information with department and dept_code
            for c in courses_d:
                # do not include cancelled courses by default
                if c['state'].find('CANCELLED') >=0:
                    continue
                c['dept_code']=d
                c['department']=courses_d_all['department']
                c['cycle'] = c['code'][2]
                name_of_course=c['title'][:] # name a copy of the string - so that changes to it do not propagate elsewhere
                c['subject']=convert_course_name_to_subject(name_of_course)
                if c['code'].endswith('x') or c['code'].endswith('X'):
                    continue
                else:
                    courses.append(c)
    else:
        return []
    return courses

def all_non_cancelled_courses(requested_dept_codes, language_code):
    global Verbose_Flag
    courses=[]                  # initialize the list of courses
    if len(requested_dept_codes) > 0:
        for d in requested_dept_codes:
            courses_d_all=get_dept_courses(d, language_code)
            
            courses_d=courses_d_all['courses']
            if len(courses_d) == 0: # nothing to do - so skip
                continue
            if Verbose_Flag:
                print("length of courses_d in dept {0} is {1}".format(d, len(courses_d)))
            # extend course information with department and dept_code
            for c in courses_d:
                # do not include cancelled courses by default
                if c['state'].find('CANCELLED') >=0:
                    continue
                c['dept_code']=d
                c['department']=courses_d_all['department']
                c['cycle'] = c['code'][2]
                name_of_course=c['title'][:] # name a copy of the string - so that changes to it do not propagate elsewhere
                c['subject']=convert_course_name_to_subject(name_of_course)
                courses.append(c)
    else:
        return []
    return courses

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

def get_grades_non_degree_projects(ladok, ladok_student_id):
    s1=get_all_attested_results_JSON(ladok,ladok_student_id)
    results=list()
    for course in s1['StudentresultatPerKurs']: # for each of the courses
        course_code=None
        course_results=course['Studentresultat']             # look at the course's results
        for module1 in course_results:
            if not module1.get('Utbildningskod'): #  if no 'Utbildningskod', skip this entry
                continue
            if not module1['Utbildningskod'].endswith("X"): #  look for degree projects and skip them
                course_code=module1['Utbildningskod']
                for module in course_results: # rescan the course results to find the momement with the project title
                    if module.get('Projekttitel'):
                        results.append ({'course_code': course_code,
                                        'moment': module['Utbildningskod'],
                                        'Examinationsdatum': module['Examinationsdatum'],
                                        'Examiner': module['Beslutsfattare'],
                                        'Grade':    module['Betygsgradskod']
                                        })
    return results

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

######
def lookup_dept_info(course_code, courses_English):
    for c in courses_English:
        if c['code'] == course_code:
            dept_code=c.get('dept_code', "Unknown")
            dept_name=c.get('department', "Unknown")
            return {'dept_code': dept_code, 'department': dept_name}
    return None

def main(argv):
    global Verbose_Flag
    global testing
    global course_id


    argp = argparse.ArgumentParser(description="courses_grades_by_school.py: to collect course round data")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-s', '--school', type=str, default='EECS',
                      help="acronyms for a school within KTH")

    argp.add_argument('-y', '--year', type=int, default='2020',
                      help="starting year")

    args = vars(argp.parse_args(argv))
    Verbose_Flag=args["verbose"]

    initialize(args)
    if Verbose_Flag:
        print("canvas_baseUrl={}".format(canvas_baseUrl))

    starting_year_int=args['year']
    starting_year=datetime.date(starting_year_int, 1, 1)
    print("starting_year={}".format(starting_year))
    ending_year=datetime.date(starting_year_int+1, 1, 1)

    school_acronym=args["school"]
    if Verbose_Flag:
        print("school_acronym={}".format(school_acronym))
    # compute the list of degree project course codes
    all_dept_codes=get_dept_codes(Swedish_language_code)
    if Verbose_Flag:
        print("all_dept_codes={}".format(all_dept_codes))

    dept_codes=dept_codes_in_a_school(school_acronym, all_dept_codes)
    if Verbose_Flag:
        print("dept_codes={}".format(dept_codes))

    courses_English=all_non_cancelled_courses(dept_codes, English_language_code)
    courses_Swedish=all_non_cancelled_courses(dept_codes, Swedish_language_code)
    if Verbose_Flag:
        print("courses English={0} and Swedish={1}".format(courses_English, courses_Swedish))

    collected_course_codes=set()
    for c in courses_English:
        collected_course_codes.add(c['code'])

    if Verbose_Flag:
        print("collected_course_codes={}".format(collected_course_codes))
    print("total number of course codes={0}".format(len(collected_course_codes)))

    ladok = ladok3.LadokSessionKTH( # establish as session with LADOK
        os.environ["KTH_LOGIN"], os.environ["KTH_PASSWD"],
        test_environment=True) # for experiments

    list_of_student_info=list()
    students_already_processed=set()
    course_rounds_already_processed=set()
    number_found=0

    course_round_info_list=[]

    if args['testing']:
        collected_course_codes=['IK1552']

    for course_code in collected_course_codes:
        course_rounds=None      # set it to None so that if the LADOK search fails it has a value
        print("course_code={}".format(course_code))
        try:
            course_rounds=ladok.search_course_rounds(code=course_code)
        except:
            print("Error for course code={}".format(course_code))

        if Verbose_Flag:
            print("course_rounds={}".format(course_rounds))

        if not course_rounds:   # if there is no course round information, skip to the next course code
            continue
    
        for course_round in course_rounds:
            course_start = course_round.start
            if course_start < starting_year: # skip courses rounds that started prior to the indicated starting year
                continue
            if course_start > ending_year:   # skip courses rounds that started after the indicated starting year
                continue
            course_length = course_round.end - course_start
            print("course_round.round_id={}".format(course_round.round_id))

            collected_components={}
            for j, comp in enumerate(course_round.components()):
                #print("comp={}".format(comp))
                desc=comp.__dict__['_CourseComponent__description']
                en_name=''
                sv_name=''
                for d in desc:
                    if d.get('Sprakkod') == 'en':
                        en_name=d['Text']
                    if d.get('Sprakkod') == 'sv':
                        sv_name=d['Text']

                #print("gradescale={}".format(comp.__dict__['_CourseComponent__grade_scale']))
                gs=comp.__dict__['_CourseComponent__grade_scale']
                #print("gs={0} name={1}".format(gs, gs.name))

                key='component{}_code'.format(j)
                collected_components[key]=comp.__dict__['_CourseComponent__code']
                key='component{}_description_en'.format(j)
                collected_components[key]=en_name
                key='component{}_description_sv'.format(j)
                collected_components[key]=sv_name
                key='component{}_grade_scale'.format(j)
                collected_components[key]=gs.name
                key='component{}_credits'.format(j)
                collected_components[key]=comp.__dict__['_CourseComponent__credits']

            number_of_students=0
            for student in ladok.participants_JSON(course_round.round_id):
                number_of_students=number_of_students+1

            di=lookup_dept_info(course_code, courses_English)
            di_sv=lookup_dept_info(course_code, courses_Swedish)
            course_round_info_list.append(
                {'code': course_round.code,
                 'name': course_round.name,
                 'instance_id': course_round.instance_id,
                 'version': course_round.version,
                 'credits': course_round.credits,
                 'grade_scale_name': course_round.grade_scale[0].name,
                 'start': course_round.start,
                 'end': course_round.end,
                 'dept_code': di['dept_code'],
                 'department_en': di['department'],
                 'department_sv': di_sv['department'],
                 'components': collected_components,
                 'number_of_students': number_of_students
                }
            )
        
            if course_round.round_id in course_rounds_already_processed:
                continue

            course_rounds_already_processed.add(course_round.round_id)



    print("Total number of course codes={0}, total number of course rounds={1}".format(len(collected_course_codes), len(course_round_info_list)))
    #users_info_df=pd.json_normalize(list_of_student_info) 
    output_filename="courses-in-{0}-{1}.xlsx".format(school_acronym, starting_year_int)

    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    # We need to drop duplicate rows since a student can have been registered in more than one course round for their degree project
    # If so, they will appear in the list as many times as there were course rounds.
    #users_info_df.drop_duplicates(ignore_index=True, inplace=True, keep='last')
    #users_info_df.to_excel(writer, sheet_name='Results')

    course_code_info=[]
    for c in collected_course_codes:
        di=lookup_dept_info(c, courses_English)
        di_sv=lookup_dept_info(c, courses_Swedish)
        course_code_info.append({'course_code': c,
                                 'dept_code': di['dept_code'],
                                 'department_en': di['department'],
                                 'department_sv': di_sv['department']
                                 })

    course_codes_df=pd.json_normalize(course_code_info)

    course_codes_df.to_excel(writer, sheet_name='course codes used')

    course_round_info_df=pd.json_normalize(course_round_info_list)
    course_round_info_df.to_excel(writer, sheet_name='Rounds')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    # to logout and close the session
    status=ladok.logout()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
