#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_ladok.py [-c course_id] --json file.json --code course_code [--which 1|2] [--date 2021-07-14] [--grade [P|F|A|B|C|D|E|Fx|F”] -gradeScale ["PF"|"AF"] [--date YYYY-MM-DD]
#
# Note that which == 3 means both authors, while 1 is hte first author only and 2 is the second author only
# The deault (0) is to report the result for both authors or the only author (if there is just one author).
#
# If the exam date is not specified, it defaults to today.
#
# An assumption is that there is only one moment that requires a project title, i.e., 'KravPaProjekttitel' is True
#
# Purpose: The program makes an entry in LADOK for the indicate course_code and moment
#          using the information from the arguments and a JSON file.
# The JSON file can be produced by extract_pseudo_JSON-from_PDF.py
#
# Output: misc. messages - mostly an error message including "Hinder mot skapa resultat påträffat: Rapporteringsrättighet saknas"
# as I do not have permission to register these course results
#
# Example:
#./JSON_to_ladok.py -c 11   --json experiment.json --code DA213X
#
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-07-14 G. Q. Maguire Jr.
# Based on earlier JSON_to_MODS.py
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
            payload = {}

    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()


#
# routinees for use with Canvas
#
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
def get_all_attested_results_JSON(self, ladok_student_id):
    # get attested results
    r = self.session.get(
        url=self.base_gui_proxy_url +
        '/resultat/studentresultat/attesterade/student/' +
        ladok_student_id,
        headers=self.headers).json()
    return r
            
def get_titles_of_thesis(ladok, ladok_student_id, course_code, moment):
    s1=get_all_attested_results_JSON(ladok,ladok_student_id)
    relevant_course_ID=None
    for course in s1['StudentresultatPerKurs']: # for each of the courses
        course_results=course['Studentresultat']             # look at the course's results
        for module in course_results:
            if module['Utbildningskod'] == 'DA231X': # see if this course has a moment for the course grade
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


def get_grade_scale_by_code(ladok, grade_scale_code):
    return next(grade_scale
      for grade_scale in ladok.get_grade_scales()
        if grade_scale.code == grade_scale_code)

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




def save_result_degree_project3(ladok, student_id, course_code, course_moment, result_date_raw, grade_raw, grade_scale, title, alternative_title):
    # set up the headers to be able to do the POST later
    headers = ladok.headers.copy()
    headers['Content-Type'] = 'application/vnd.ladok-resultat+json'
    headers['X-XSRF-TOKEN'] = ladok.xsrf_token
    headers['Referer'] = ladok.base_gui_url
    
    # get the list of student's courses
    courses=get_student_courses(ladok, student_id)
    
    # choose the course with the indicated course_code
    student_course=instance_id_given_course_code(courses, course_code)
    # {'id': '6683207e-5a5d-11eb-9b32-eeb44fb14647', 'round_id': '8e15ae14-1d86-11ea-a622-3565135944de', 'education_id': '374ea085-73d8-11e8-afa7-8e408e694e54', 'instance_id': '8eee8da9-dd0a-11e8-bb7a-19f8cd1a470e', 'swe_name': 'Examensarbete i datalogi och datateknik, avancerad nivå', 'eng_name': 'Degree Project in Computer Science and Engineering, Second Cycle'}

    # get the student's results for the specific course round (i.e., a specific offering of the course for which the student is registered)
    student_course_results = get_student_course_results(ladok, student_course['round_id'], student_id)

    # get the grading scale information and used it to get the information needed to assign the grade
    grade_scale =get_grade_scale_by_code(ladok, grade_scale)
    grade = grade_scale.grades(code=grade_raw)[0]

    # get the moments for this course (and course round) and look for the selected course moment
    course_moements=get_student_course_moments(ladok, student_course['round_id'], student_id)
    for m in course_moements:
        if m['code'] == course_moment:
            course_moment_id=m['course_moment_id']

    # validate the date (ensures it is in the correct format)
    result_date = validate_date(ladok, result_date_raw)

    # create a POST request - note that in addition to the usual fields this includes the project title, a field containing both a title and alternate title
    post_data = {
        'Resultat': [{
            'StudieresultatUID': student_course_results['id'],
            'UtbildningsinstansUID': course_moment_id,
            'Betygsgrad': grade.id,
            'Noteringar': [],
            'Projekttitel': {'AlternativTitel': alternative_title, 'Titel': title, 'link': []},
            'BetygsskalaID': grade_scale.id,
            'Examinationsdatum': result_date
        }]
    }
    r = ladok.session.post(
        url=ladok.base_gui_proxy_url + '/resultat/studieresultat/skapa',
        json=post_data,
        headers=headers)
    #
    if not 'Resultat' in r.json():
        raise Exception("Couldn't register " + course_moment + "=" + grade_raw + " " + result_date_raw + ": " + r.json()["Meddelande"])
    return True


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


    argp = argparse.ArgumentParser(description="JSON_to_LADOK.py: to enter titles for a thesis")

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

    argp.add_argument('-j', '--json',
                      type=str,
                      default="event.json",
                      help="JSON file for extracted data"
                      )

    argp.add_argument('--which',
                      type=int, # 1, 2, or 3
                      default=0,
                      help="if more than one author, which should be processed"
                      )

    argp.add_argument('--code',
                      type=str,
                      required=True,
                      help="course code"
                      )

    argp.add_argument('--date',
                      type=str,
                      help="date of the requirement being completed"
                      )

    argp.add_argument('--grade',
                      type=str,
                      default="P",
                      help="grade to be assigned"
                      )

    argp.add_argument('--gradeScale',
                      type=str,
                      default="PF",
                      help="grading scale"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    initialize(args)
    if Verbose_Flag:
        print("baseUrl={}".format(baseUrl))

    # If there is a course number argument, then initializae in prepartion for Canvas API calls
    course_id=args["canvas_course_id"]
    if course_id:
        if Verbose_Flag:
            print("course_id={}".format(course_id))
            print("baseUrl={}".format(baseUrl))

    testing=args["testing"]
    print("testing={}".format(testing))

    d=None
    json_filename=args["json"]
    if json_filename:
        with open(json_filename, 'r', encoding='utf-8') as json_FH:
            try:
                json_string=json_FH.read()
                d=json.loads(json_string)
            except:
                print("Error in reading={}".format(event_string))
                return

            if Verbose_Flag:
                print("read JSON: {}".format(d))

        if d:
            print("d={}".format(d))

            # get title and alternative title
            #"Title": {"Main title": "HoneyRAN", "Subtitle": "A Radio Access Network Honeypot", "Language": "eng"}, "Alternative title": {"Main title": "HoneyRAN", "Subtitle": "En honeypot för radioaccessnät", "Language": "swe"}
            title_info=d.get('Title', None)
            if title_info:
                main_title=title_info.get('Main title', None)
                alternative_main_title=title_info.get('Alternative title', None)
            else:
                print("Missing title")
                return

            if not main_title:
                print("Missing title")
                return

            degree_info=d.get('Degree', None)
            if not degree_info:
                print("Missing degree information")
                return
            else:
                course_code=degree_info.get('Course code')
                if not course_code:
                    print("Missing course code")
                    return
            print("course_code={}".format(course_code))

            date_of_exam=args["date"]
            if date_of_exam:
                result_date = validate_date(ladok, date_of_exam)
            else:
                # datetime object containing current date and time
                now = datetime.now()
                print("now =", now)
                dt_string = now.strftime("%Y-%m-%d")
                print("date =", dt_string)

                result_date = dt_string
                
                grade=args['grade']
                if not grade:
                    grade = 'P'

                grade_scale=args['gradeScale']
                if not grade_scale:
                    grade_scale="PF"

            ladok = ladok3.LadokSessionKTH( # establish as session with LADOK
                os.environ["KTH_LOGIN"], os.environ["KTH_PASSWD"],
                test_environment=True) # for experiments

            author_names=list()
            for i in range(1, 10):
                which=args['which'] # which author should be processed
                if (which == 0) or (which == i) or (which == 3):
                    which_author="Author{}".format(i)
                    author=d.get(which_author, None)
                    if author:
                        print("author={}".format(author))
                        integration_id=get_integration_id_from_email_address(author['E-mail'])
                        print("integration_id={}".format(integration_id))

                        courses=get_student_courses(ladok, integration_id)
                        ladok_course_info=instance_id_given_course_code(courses, course_code)
                        print("ladok_course_info={}".format(ladok_course_info))
                        ladok_course_moments_info=get_student_course_moments_JSON(ladok, ladok_course_info['round_id'], integration_id)
                        if ladok_course_moments_info:
                            for mom in ladok_course_moments_info['IngaendeMoment']:
                                print("moment code={0}, requires title={1}".format(mom['Utbildningskod'], mom['KravPaProjekttitel']))
                                if mom['KravPaProjekttitel']:
                                    print("trying to store a passing grade for moment={0}".format(mom['Utbildningskod']))
                                    status=save_result_degree_project3(ladok, integration_id, course_code, mom['Utbildningskod'], result_date, grade, grade_scale, main_title, alternative_main_title)
                                    print("status={}".format(status))
                                    #returned: Exception: Couldn't register PRO3=P 2021-07-14: Hinder mot skapa resultat påträffat: Rapporteringsrättighet saknas

            # to logout and close the session
            status=ladok_session.logout()
            
    else:
        print("Unknown source for the JSON: {}".format(json_filename))
        return
    


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
