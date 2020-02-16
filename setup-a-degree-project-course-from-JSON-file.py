#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./setup-a-degree-project-course-from-JSON-file.py cycle_number course_id school_acronym course_code program_code
#
# Output: none (it modifies the state of the course)
#
#
# Input
# reads the course and examiner information from a file whose name is of the form: course-data-{school_acronym}-cycle-{cycle_number}.json
#
# Note that the cycle_number is either 1 or 2 (1st or 2nd cycle)
#
# 
# with the option '-C'or '--containers' use HTTP rather than HTTPS for access to Canvas
# "-m" or "--modules" set up the two basic modules (does nothing in this program)
# "-p" or "--page" set up the two basic pages for the course
# "-s" or "--survey" set up the survey
# "-S" or "--sections" set up the sections for the examiners and programs
# "-c" or "--columns" set up the custom columns
# "-p" or "--pages" set up the pages
# "-a" or "--assignments" set up the assignments (proposal, alpha and beta drafts, etc.)
# "-o" or "--objectives" set up the objectives for the course
#
# "-A" or "--all" set everything up (sets all of the above options to true)
#
# "-t" or "--testing" to enable small tests to be done
# 
#
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./setup-degree-project-course.py --config config-test.json -A 1 19885 EECS IA150X CINTE
#
# Example:
# set up a 1st cycle course:
# ./setup-a-degree-project-course-from-JSON-file.py -A 1 22309 EECS II143X TCOMK
#
# set up a 2nd cycle course:
# ./setup-a-degree-project-course-from-JSON-file.py -o 2 19874 EECS DA246X TCOMM
#
# Create custom colums:
# ./setup-a-degree-project-course-from-JSON-file.py -c 1 19885 EECS IA150X CINTE
#
# Create sections for examiners and programs:
# ./setup-a-degree-project-course-from-JSON-file.py -S 1 19885 EECS IA150X CINTE
# 
# Create assignments:
# ./setup-a-degree-project-course-from-JSON-file.py -a 1 19885 EECS IA150X CINTE
#
# Create pages for the course:
# ./setup-a-degree-project-course-from-JSON-file.py -p 1 19885 EECS IA150X CINTE
#
# Create objectives:
# ./setup-a-degree-project-course-from-JSON-file.py -o 1 19885 EECS IA150X CINTE
# ./setup-a-degree-project-course-from-JSON-file.py -o 1 22309 EECS II143X TCOMK
#
#
# G. Q. Maguire Jr.
#
#
# 2020.01.21 based on setup-degree-project-course-from-JSON-file.py
#
# Note: At present if you use the -A option, you need to run the program again with the -o options to correctly set up the outcomes
#
import requests, time
import pprint
import optparse
import sys
import json

# Use Python Pandas to create XLSX files
import pandas as pd

from bs4 import BeautifulSoup

################################
######    KOPPS related   ######
################################
KOPPSbaseUrl = 'https://www.kth.se'

English_language_code='en'
Swedish_language_code='sv'

KTH_Schools = {
    'ABE':  ['ABE'],
    'CBH':  ['BIO', 'CBH', 'CHE', 'STH'],
    'EECS': ['CSC', 'EES', 'ICT', 'EECS'], # corresponds to course codes starting with D, E, I, and J
    'ITM':  ['ECE', 'ITM'],
    'SCI':  ['SCI']
}


def potential_examiners_answer(examiners):
    examiner_alternatives_list=[]
    #
    for e in sorted(examiners):
        new_element=dict()
        new_element['blank_id']='e1'
        new_element['weight']=100
        new_element['text']=e
        examiner_alternatives_list.append(new_element)

    return examiner_alternatives_list

def potential_examiners_answerv2(course_examiner_dict):
    examiner_alternatives_list=[]
    #
    for e in sorted(examiners):
        new_element=dict()
        new_element['blank_id']='e1'
        new_element['weight']=100
        new_element['text']=e
        examiner_alternatives_list.append(new_element)

    return examiner_alternatives_list

def course_code_alternatives(pf_courses, af_courses):
    course_code_alternatives_list=[]
    for i in sorted(pf_courses):
        new_element=dict()
        new_element['blank_id']='PF'
        new_element['weight']=100
        new_element['text']=i
        course_code_alternatives_list.append(new_element)
    #
    for i in sorted(af_courses):
        new_element=dict()
        new_element['blank_id']='AF'
        new_element['weight']=100
        new_element['text']=i
        course_code_alternatives_list.append(new_element)
    #
    return course_code_alternatives_list

# def credits_for_course(course_code, courses):
#     for c in courses:
#         if c['code'] == course_code:
#             return c['credits']
#     return 0

# def title_for_course(course_code, courses):
#     for c in courses:
#         if c['code'] == course_code:
#             return c['title']
#     return ''

def credits_for_course(course_code, courses):
    credits=0
    course=courses.get(course_code, [])
    if course: 
        credits=course.get('credits', 0)
    return credits

def title_for_course(course_code, courses):
    title=''
    course=courses.get(course_code, [])
    if course: 
        title=course.get('title', 0)
    return title

def course_code_descriptions(pf_courses, af_courses, courses_english, courses_swedish):
    course_code_description='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en"><table border="1" cellspacing="1" cellpadding="1"><tbody>'
    table_heading='<tr><th>Course Code</th><th>Credits</th><th>Name</th></tr>'
    course_code_description=course_code_description+table_heading

    for i in sorted(pf_courses):
        #table_row='<tr><td>'+str(i)+'</td><td>'+credits_for_course(i, courses_english)+'</td><td lang="en">'+title_for_course(i, courses_english)+'</td></tr>'
        table_row='<tr><td>{0}</td><td>{1}</td><td lang="en">{2}</td></tr>'.format(i, credits_for_course(i, courses_english), title_for_course(i, courses_english))
        course_code_description=course_code_description+table_row
    # end of table
    course_code_description=course_code_description+'</tbody></table></div><div id="fragment-sv"><table border="1" cellspacing="1" cellpadding="1"><tbody>'
    table_heading='<tr><th>Kurskod</th><th>Credits</th><th>Namn</th></tr>'
    course_code_description=course_code_description+table_heading
    #
    for i in sorted(af_courses):
        #table_row='<tr><td>'+str(i)+'</td><td>'+credits_for_course(i, courses_swedish)+'</td><td lang="sv">'+title_for_course(i, courses_swedish)+'</td></tr>'
        table_row='<tr><td>{0}</td><td>{1}</td><td lang="sv">{2}</td></tr>'.format(i, credits_for_course(i, courses_swedish), title_for_course(i, courses_swedish))
        course_code_description=course_code_description+table_row
    # end of table
    course_code_description=course_code_description+'</tbody></table></div>'
    #
    return course_code_description

# course_codes_from_url('https://www.kth.se/student/kurser/program/CINTE/20182/arskurs1')
# returns {'II143X', 'II1305', 'IK2206', 'IC1007', 'SF1547', 'ID1217', 'II1307', 'ID2202', 'IE1202', 'ME2063', 'SK1118', 'ID2213', 'ID1206', 'ID1212', 'DD2350', 'SF1546', 'DD1351', 'SF1625', 'ID1354', 'II2202', 'EQ1110', 'SF1912', 'IK1203', 'SF1610', 'IV1350', 'ID1019', 'ID1020', 'EL1000', 'EQ1120', 'IV1013', 'ID2216', 'ME2015', 'IE1206', 'ID1018', 'IE1204', 'DD2352', 'AG1815', 'IH1611', 'II1306', 'SF1689', 'IK1552', 'SG1102', 'ID2201', 'IS1200', 'SH1011', 'IS2202', 'DD2372', 'IV1303', 'SF1686', 'SF1624', 'ID1214', 'IV1351', 'DD2401', 'ME1003'}
def course_codes_from_url(syllabus_url):
    set_of_course_codes=set()
    offset=syllabus_url.find('arskurs')
    course_list_url=syllabus_url[:offset]+'kurslista'
    if Verbose_Flag:
        print("course_list_url: " + course_list_url)
    #
    r = requests.get(course_list_url)
    if Verbose_Flag:
        print("result of getting course list: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        xml=BeautifulSoup(r.text, "html")
        for link in xml.findAll('a'):
            h1=link.get('href')
            if h1:
                if Verbose_Flag:
                    print("h1={}".format(h1))
                offset=h1.find('/student/kurser/kurs/')
                if offset >= 0:
                    course_code=h1[-6:]
                    print("course_code={}".format(course_code))
                    set_of_course_codes.add(course_code)
    return set_of_course_codes

# degree_project_course_codes_in({'II143X', 'II1305', 'IK2206', 'IC1007', 'SF1547', 'ID1217', 'II1307', 'ID2202', 'IE1202', 'ME2063', 'SK1118', 'ID2213', 'ID1206', 'ID1212', 'DD2350', 'SF1546', 'DD1351', 'SF1625', 'ID1354', 'II2202', 'EQ1110', 'SF1912', 'IK1203', 'SF1610', 'IV1350', 'ID1019', 'ID1020', 'EL1000', 'EQ1120', 'IV1013', 'ID2216', 'ME2015', 'IE1206', 'ID1018', 'IE1204', 'DD2352', 'AG1815', 'IH1611', 'II1306', 'SF1689', 'IK1552', 'SG1102', 'ID2201', 'IS1200', 'SH1011', 'IS2202', 'DD2372', 'IV1303', 'SF1686', 'SF1624', 'ID1214', 'IV1351', 'DD2401', 'ME1003'})
# returns {'II143X'}
def degree_project_course_codes_in(set_of_course_codes):
    dp_course_set=set()
    for c in set_of_course_codes:
        if c[-1:] == 'X':
            dp_course_set.add(c)
    return dp_course_set

def compute_equivalence_class_of_teachers_in_courses(ces):
    courses_with_same_examiners=dict()
    set_of_examiners=dict()
    courses_with_no_examiner=list()
    i=0
    for c in ces:
        examiners_for_class=ces[c]
        examiner_set=set(examiners_for_class)
        if Verbose_Flag:
            print("examiners_for_class={0} are {1}".format(c, examiner_set))
        if not examiner_set:
            if Verbose_Flag:
                print("course {0} has no examiners".format(c))
            courses_with_no_examiner.append(c)
            continue
        teacher_set_found = -1
        for j in range(0, len(set_of_examiners)):
            if examiner_set == set_of_examiners[j]:
                if Verbose_Flag:
                    print("already in set of examiners for j={}".format(j))
                teacher_set_found=j
                break
        #
        if teacher_set_found >= 0:
            course_codes=courses_with_same_examiners.get(teacher_set_found, [])
            if not course_codes:
                if Verbose_Flag:
                    print("inserted course code {0} in courses_with_same_examiners[{1}]".format(c, courses_with_same_examiners[teacher_set_found]))
                courses_with_same_examiners[teacher_set_found]=[c]
            else:
                courses_with_same_examiners[teacher_set_found].append(c)
                if Verbose_Flag:
                    print("added {0} to courses_with_same_examiners[{1}] is {2}".format(c, teacher_set_found, examiner_set))
        else:
            next_set=len(set_of_examiners)
            if Verbose_Flag:
                print("new courses_with_same_examiners[{0}] is {1}".format(next_set, examiner_set))
            set_of_examiners[next_set]=examiner_set
            courses_with_same_examiners[next_set]=[c]
    #
    return {'courses': courses_with_same_examiners, 'examiners': set_of_examiners, 'courses_with_no_examiner': courses_with_no_examiner}


def examiners_courses(name, courses):
    list_of_courses=list()
    for c in courses:
        if name in courses[c]:
            #print("course code={0}".format(c))
            list_of_courses.append(c)
            #print("list_of_courses={0}".format(list_of_courses))
    list_of_courses.sort()      # note - this sorts the list in place
    return list_of_courses

def course_examiner_alternatives_table(ecs):
    table_string='<table border="1" cellspacing="1" cellpadding="1"><tbody>'
    courses=ecs['courses']
    set_of_examiners=ecs['examiners']
    courses_with_no_examiner=ecs['courses_with_no_examiner']
    for i in courses:
        table_string="{0}<tr><td>{1}</td><td>{2}</td></tr>".format(table_string, (', '.join(courses[i])), '[e'+str(i)+']')
    #
    table_string="{0}<tr><td>{1}</td><td>Inga examinatorer/No examiners</td></tr>".format(table_string, (', '.join(courses_with_no_examiner)))
    table_string=table_string+'</tbody></table>'
    return table_string

def course_examiner_alternatives_answers(ecs):
    set_of_examiners=ecs['examiners']
    examiner_alternatives_list=[]
    #
    for i in set_of_examiners:
        for e in sorted(set_of_examiners[i]):
            new_element=dict()
            new_element['blank_id']='e'+str(i)
            new_element['weight']=100
            new_element['text']=e
            examiner_alternatives_list.append(new_element)
    return examiner_alternatives_list

def potential_examiners_answerv2(course_examiner_dict):
    examiner_alternatives_list=[]
    #
    for e in sorted(examiners):
        new_element=dict()
        new_element['blank_id']='e1'
        new_element['weight']=100
        new_element['text']=e
        examiner_alternatives_list.append(new_element)

    return examiner_alternatives_list


################################
###### Canvas LMS related ######
################################

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(options):
    global baseUrl, header, payload

    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    if options.config_filename:
        config_file=options.config_filename
    else:
        config_file='config.json'

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            access_token=configuration["canvas"]["access_token"]
            if options.containers:
                baseUrl="http://"+configuration["canvas"]["host"]+"/api/v1"
                print("using HTTP for the container environment")
            else:
                baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}
    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()

def users_in_course(course_id):
       user_found_thus_far=[]
       # Use the Canvas API to get the list of users enrolled in this course
       #GET /api/v1/courses/:course_id/enrollments

       url = "{0}/courses/{1}/enrollments".format(baseUrl,course_id)
       if Verbose_Flag:
              print("url: {}".format(url))

       extra_parameters={'per_page': '100'}
       r = requests.get(url, params=extra_parameters, headers = header)
       if Verbose_Flag:
              print("result of getting enrollments: {}".format(r.text))

       if r.status_code == requests.codes.ok:
              page_response=r.json()

              for p_response in page_response:  
                     user_found_thus_far.append(p_response)

              # the following is needed when the reponse has been paginated
              # i.e., when the response is split into pieces - each returning only some of the list of modules
              # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
              while r.links['current']['url'] != r.links['last']['url']:  
                     r = requests.get(r.links['next']['url'], headers=header)  
                     page_response = r.json()  
                     for p_response in page_response:  
                            user_found_thus_far.append(p_response)
       return user_found_thus_far

def user_profile_url(user_id):
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

def section_name_from_section_id(sections_info, section_id): 
       for i in sections_info:
            if i['id'] == section_id:
                   return i['name']

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
              # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
              while r.links['current']['url'] != r.links['last']['url']:  
                     r = requests.get(r.links['next']['url'], headers=header)  
                     page_response = r.json()  
                     for p_response in page_response:  
                            sections_found_thus_far.append(p_response)

       return sections_found_thus_far

def list_your_courses():
       courses_found_thus_far=[]
       # Use the Canvas API to get the list of all of your courses
       # GET /api/v1/courses

       url = baseUrl+'courses'
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
              # i.e., when the response is split into pieces - each returning only some of the list of modules
              # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
              while r.links['current']['url'] != r.links['last']['url']:  
                     r = requests.get(r.links['next']['url'], headers=header)  
                     if Verbose_Flag:
                            print("result of getting courses for a paginated response: {}".format(r.text))
                     page_response = r.json()  
                     for p_response in page_response:  
                            courses_found_thus_far.append(p_response)

       return courses_found_thus_far

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
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links['current']['url'] != r.links['last']['url']:  
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting assignments for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    assignments_found_thus_far.append(p_response)

    return assignments_found_thus_far

def create_assignment(course_id, name, max_points, grading_type, description, assignment_group_id):
    # Use the Canvas API to create an assignment
    # POST /api/v1/courses/:course_id/assignments

    # Request Parameters:
    #Parameter		Type	Description
    # assignment[name]	string	The assignment name.
    # assignment[position]		integer	The position of this assignment in the group when displaying assignment lists.
    # assignment[submission_types][]		string	List of supported submission types for the assignment. Unless the assignment is allowing online submissions, the array should only have one element.
    # assignment[peer_reviews]	boolean	If submission_types does not include external_tool,discussion_topic, online_quiz, or on_paper, determines whether or not peer reviews will be turned on for the assignment.
    # assignment[notify_of_update] boolean     If true, Canvas will send a notification to students in the class notifying them that the content has changed.
    # assignment[grade_group_students_individually]		integer	 If this is a group assignment, teachers have the options to grade students individually. If false, Canvas will apply the assignment's score to each member of the group. If true, the teacher can manually assign scores to each member of the group.
    # assignment[points_possible]		number	 The maximum points possible on the assignment.
    # assignment[grading_type]		string	The strategy used for grading the assignment. The assignment defaults to “points” if this field is omitted.
    # assignment[description]		string	The assignment's description, supports HTML.
    # assignment[grading_standard_id]		integer	The grading standard id to set for the course. If no value is provided for this argument the current grading_standard will be un-set from this course. This will update the grading_type for the course to 'letter_grade' unless it is already 'gpa_scale'.
    # assignment[published]		boolean	Whether this assignment is published. (Only useful if 'draft state' account setting is on) Unpublished assignments are not visible to students.

    url = "{0}/courses/{1}/assignments".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'assignment[name]': name,
             'assignment[submission_types][]': ["none"],
             'assignment[peer_reviews]': 'false',
             'assignment[notify_of_update]': 'false',
             'assignment[grade_group_students_individually]': 'true',
             'assignment[peer_reviews]': 'false',
             'assignment[points_possible]': max_points,
             'assignment[grading_type]': grading_type,
             'assignment[description]': description,
             'assignment[published]': 'true' # if not published it will not be in the gradebook
    }
    if assignment_group_id:
        payload['assignment[assignment_group_id]']=assignment_group_id

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post making an assignment: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted assignment")
        return page_response['id']
    return False

def create_assignment_with_submission(course_id, name, max_points, grading_type, description, assignment_group_id):
    # Use the Canvas API to create an assignment
    # POST /api/v1/courses/:course_id/assignments

    # Request Parameters:
    #Parameter		Type	Description
    # assignment[name]	string	The assignment name.
    # assignment[position]		integer	The position of this assignment in the group when displaying assignment lists.
    # assignment[submission_types][]		string	List of supported submission types for the assignment. Unless the assignment is allowing online submissions, the array should only have one element.
    # assignment[peer_reviews]	boolean	If submission_types does not include external_tool,discussion_topic, online_quiz, or on_paper, determines whether or not peer reviews will be turned on for the assignment.
    # assignment[notify_of_update] boolean     If true, Canvas will send a notification to students in the class notifying them that the content has changed.
    # assignment[grade_group_students_individually]		integer	 If this is a group assignment, teachers have the options to grade students individually. If false, Canvas will apply the assignment's score to each member of the group. If true, the teacher can manually assign scores to each member of the group.
    # assignment[points_possible]		number	 The maximum points possible on the assignment.
    # assignment[grading_type]		string	The strategy used for grading the assignment. The assignment defaults to “points” if this field is omitted.
    # assignment[description]		string	The assignment's description, supports HTML.
    # assignment[grading_standard_id]		integer	The grading standard id to set for the course. If no value is provided for this argument the current grading_standard will be un-set from this course. This will update the grading_type for the course to 'letter_grade' unless it is already 'gpa_scale'.
    # assignment[published]		boolean	Whether this assignment is published. (Only useful if 'draft state' account setting is on) Unpublished assignments are not visible to students.

    url = "{0}/courses/{1}/assignments".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'assignment[name]': name,
             'assignment[submission_types][]': ['online_upload'],
             'assignment[peer_reviews]': 'false',
             'assignment[notify_of_update]': 'false',
             'assignment[grade_group_students_individually]': 'true',
             'assignment[peer_reviews]': 'false',
             'assignment[points_possible]': max_points,
             'assignment[grading_type]': grading_type,
             'assignment[description]': description,
             'assignment[published]': 'true' # if not published it will not be in the gradebook
    }
    if assignment_group_id:
        payload['assignment[assignment_group_id]']=assignment_group_id

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post making an assignment: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted assignment")
        return page_response['id']
    return False

def create_assignment_with_textual_submission(course_id, name, max_points, grading_type, description, assignment_group_id):
    if Verbose_Flag:
        print("in create_assignment_with_textual_submission assignment_group_id={}".format(assignment_group_id))
    # Use the Canvas API to create an assignment
    # POST /api/v1/courses/:course_id/assignments

    url = "{0}/courses/{1}/assignments".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'assignment[name]': name,
             'assignment[submission_types][]': ['online_text_entry'],
             'assignment[peer_reviews]': 'false',
             'assignment[notify_of_update]': 'false',
             'assignment[grade_group_students_individually]': 'true',
             'assignment[peer_reviews]': 'false',
             'assignment[points_possible]': max_points,
             'assignment[grading_type]': grading_type,
             'assignment[description]': description,
             'assignment[published]': 'true' # if not published it will not be in the gradebook
    }
    if assignment_group_id:
        payload['assignment[assignment_group_id]']=assignment_group_id



    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post making an assignment: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted assignment")
        return page_response['id']
    return False

def create_assignment_with_submission_with_peerreview(course_id, name, max_points, grading_type, description, assignment_group_id):
    # Use the Canvas API to create an assignment
    # POST /api/v1/courses/:course_id/assignments

    # Request Parameters:
    #Parameter		Type	Description
    # assignment[name]	string	The assignment name.
    # assignment[position]		integer	The position of this assignment in the group when displaying assignment lists.
    # assignment[submission_types][]		string	List of supported submission types for the assignment. Unless the assignment is allowing online submissions, the array should only have one element.
    # assignment[peer_reviews]	boolean	If submission_types does not include external_tool,discussion_topic, online_quiz, or on_paper, determines whether or not peer reviews will be turned on for the assignment.
    # assignment[notify_of_update] boolean     If true, Canvas will send a notification to students in the class notifying them that the content has changed.
    # assignment[grade_group_students_individually]		integer	 If this is a group assignment, teachers have the options to grade students individually. If false, Canvas will apply the assignment's score to each member of the group. If true, the teacher can manually assign scores to each member of the group.
    # assignment[points_possible]		number	 The maximum points possible on the assignment.
    # assignment[grading_type]		string	The strategy used for grading the assignment. The assignment defaults to “points” if this field is omitted.
    # assignment[description]		string	The assignment's description, supports HTML.
    # assignment[grading_standard_id]		integer	The grading standard id to set for the course. If no value is provided for this argument the current grading_standard will be un-set from this course. This will update the grading_type for the course to 'letter_grade' unless it is already 'gpa_scale'.
    # assignment[published]		boolean	Whether this assignment is published. (Only useful if 'draft state' account setting is on) Unpublished assignments are not visible to students.
    # assignment[peer_reviews]		boolean	If submission_types does not include external_tool,discussion_topic, online_quiz, or on_paper, determines whether or not peer reviews will be turned on for the assignment.
    # assignment[automatic_peer_reviews]		boolean	Whether peer reviews will be assigned automatically by Canvas or if teachers must 

    url = "{0}/courses/{1}/assignments".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'assignment[name]': name,
             'assignment[submission_types][]': ['online_upload'],
             'assignment[peer_reviews]': 'false',
             'assignment[notify_of_update]': 'false',
             'assignment[grade_group_students_individually]': 'true',
             'assignment[peer_reviews]': 'false',
             'assignment[points_possible]': max_points,
             'assignment[grading_type]': grading_type,
             'assignment[description]': description,
             'assignment[published]': 'true',		 # if not published it will not be in the gradebook
             'assignment[peer_reviews]': 'true',	 # require a peer review
             'assignment[automatic_peer_reviews]': 'false'	# manually assign the peer reviewer(s)
    }
    if assignment_group_id:
        payload['assignment[assignment_group_id]']=assignment_group_id

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post making an assignment: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted assignment")
        return page_response['id']
    return False



def create_module_assignment_item(course_id, module_id, assignment_id, item_name, points):
    # Use the Canvas API to create a module item in the course and module
    #POST /api/v1/courses/:course_id/modules/:module_id/items
    url = "{0}/courses/{1}/modules/{2}/items".format(baseUrl, course_id, module_id)
    if Verbose_Flag:
        print("creating module assignment item for course_id={0} module_id={1} assignment_id={1}".format(course_id, module_id, assignment_id))
    payload = {'module_item[title]': item_name,
               'module_item[type]': 'Assignment',
               'module_item[content_id]': assignment_id,
               'module_item[completion_requirement][type]': 'min_score',
               'module_item[completion_requirement][min_score]': points

    }

    r = requests.post(url, headers = header, data = payload)
    if Verbose_Flag:
        print("result of creating module: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        modules_response=r.json()
        module_id=modules_response["id"]
        return module_id
    return  module_id

def list_modules(course_id):
    modules_found_thus_far=[]
    # Use the Canvas API to get the list of modules for the course
    #GET /api/v1/courses/:course_id/modules

    url = "{0}/courses/{1}/modules".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting modules: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            modules_found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of modules
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links['current']['url'] != r.links['last']['url']:  
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting modules for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    modules_found_thus_far.append(p_response)

    return modules_found_thus_far

def create_module(course_id, module_name, requires_module_id):
    module_id=None              # will contain the module's ID if it exists
    # Use the Canvas API to create a module in the course
    #POST /api/v1/courses/:course_id/modules
    url = "{0}/courses/{1}/modules".format(baseUrl, course_id,module_name)
    if Verbose_Flag:
        print("creating module for course_id={0} module_name={1}".format(course_id,module_name))
    if requires_module_id:
        payload = {'module[name]': module_name,
                   'module[prerequisite_module_ids][]': requires_module_id
        }
    else:
        payload = {'module[name]': module_name
        }
    r = requests.post(url, headers = header, data = payload)
    if Verbose_Flag:
        print("result of creating module: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        modules_response=r.json()
        module_id=modules_response["id"]
        return module_id
    return  module_id

def create_gatekeeper_module(course_id, module_name):
    module_id=None              # will contain the module's ID if it exists
    # Use the Canvas API to create a module in the course
    #POST /api/v1/courses/:course_id/modules
    url = "{0}/courses/{1}/modules".format(baseUrl, course_id)
    if Verbose_Flag:
        print("creating module for course_id={0} module_name={1}".format(course_id,module_name))
    payload = {'module[name]': module_name,
               'module[position]': 1,
               'module[require_sequential_progress]': True
    }
    r = requests.post(url, headers = header, data = payload)
    if Verbose_Flag:
        print("result of creating module: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        modules_response=r.json()
        module_id=modules_response["id"]
        return module_id
    return  module_id

def check_for_module(course_id,  module_name):
    modules_found_thus_far=[]
    module_id=None              # will contain the moudle's ID if it exists
    # Use the Canvas API to get the list of modules for the course
    #GET /api/v1/courses/:course_id/modules

    url = "{0}/courses/{1}/modules".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    # this will do a partial match against the module_name
    # This reducing the number of responses returned

    payload = {'search_term': module_name} 
    r = requests.get(url, headers = header, data = payload)
    if Verbose_Flag:
        print("result of getting modules: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            modules_found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of modules
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links['current']['url'] != r.links['last']['url']:  
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting modules for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    modules_found_thus_far.append(p_response)

    name_to_match="{}".format(module_name)
    if Verbose_Flag:
       print("name \t id\tmatching: {}".format(name_to_match))

    for m in modules_found_thus_far:
        if (m["name"]  ==  name_to_match):
            if Verbose_Flag:
                print("{0}\t{1}\ttrue".format(m["name"], m["id"]))
            module_id=m["id"]
            if Verbose_Flag:
                print("module_id is {}".format(module_id))
            return module_id
        else:
            if Verbose_Flag:
                print("{0}\t{1}".format(m["name"],m["id"]))

    return module_id


def create_basic_modules(course_id):

    module_id=check_for_module(course_id, "Gatekeeper module 1")
    if not module_id:
        module_id=create_gatekeeper_module(course_id, "Gatekeeper module 1")
        if Verbose_Flag:
            print("create_basic_modules: Gatekeeper module 1 module_id={}".format(module_id))

    name="Gatekeeper 1 access control"
    description="This assignment is simply for access control. When the teacher sets the assignment for a student to have 1 point then the student will have access to the pages protected by the module where this assignment is."
    assignment_id=create_assignment(course_id, name, 1, 'points', description, False)
    if Verbose_Flag:
        print("create_basic_modules:assignment_id={}".format(assignment_id))

    item_name="Gatekeeper 1 access control"
    create_module_assignment_item(course_id, module_id, assignment_id, item_name, 1)

    access_controlled_module=check_for_module(course_id,  "Gatekeeper protected module 1")
    if not access_controlled_module:
        access_controlled_module=create_module(course_id, "Gatekeeper protected module 1", module_id)
        if Verbose_Flag:
            print("create_basic_modules: Gatekeeper protected module 1 module_id={}".format(access_controlled_module))

    return access_controlled_module

def create_survey_quiz(course_id):
    # Use the Canvas API to create a quiz
    # POST /api/v1/courses/:course_id/quizzes

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    description='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en">Please answer the following questions about your propose degree project.</p></div><div id="fragment-sv"><p lang="sv">Var snäll och svara på följande frågor om ditt förslag på exjobb.</p></div></div>'
    payload={'quiz[title]': 'Information om exjobbsprojekt/Information for degree project',
             'quiz[description]': description,
             'quiz[quiz_type]': 'survey',
             'quiz[hide_results]': '',
             'quiz[show_correct_answers]': 'false',
             'quiz[allowed_attempts]': -1,
             'quiz[scoring_policy]': 'keep_latest',
             'quiz[published]': True
    }

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post making a quiz: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if (r.status_code == requests.codes.created) or (r.status_code == requests.codes.ok):
        page_response=r.json()
        print("inserted quiz")
        return page_response['id']
    return False

def create_quiz_question_group(course_id, quiz_id, question_group_name):
    # return the quiz_group_id

    global Verbose_Flag

    # quiz_groups will be a dictionary of question_category and corresponding quiz_group_id
    # we learn the quiz_group_id when we put the first question into the question group
    print("course_id={0}, quiz_id={1}, question_group_name={2}".format(course_id, quiz_id, question_group_name))

    # Create a question group
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/groups
    url = "{0}/courses/{1}/quizzes/{2}/groups".format(baseUrl, course_id, quiz_id)

    if Verbose_Flag:
        print("url: " + url)
    payload={'quiz_groups':
             [
                 {
                     'name': question_group_name,
                     'pick_count': 1,
                     'question_points': 1
                 }
             ]
    }

    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)

    print("result of post creating question group: {}".format(r.text))
    print("r.status_code={}".format(r.status_code))
    if (r.status_code == requests.codes.ok) or (r.status_code == 201):
        print("result of creating question group in the course: {}".format(r.text))
        page_response=r.json()
        if Verbose_Flag:
            print("page_response={}".format(page_response))
        # store the new id in the dictionary
        if Verbose_Flag:
            print("inserted question group={}".format(question_group_name))
            # '{"quiz_groups":[{"id":541,"quiz_id":2280,"name":"Newgroup","pick_count":1,"question_points":1.0,"position":2,"assessment_question_bank_id":null}]}')
        quiz_group_id=page_response['quiz_groups'][0]['id']
        if Verbose_Flag:
            print("quiz_group_id={}".format(quiz_group_id))
            return quiz_group_id

    return 0


def create_question_boolean(course_id, quiz_id, index, name, question_text, answers):
    #print("create_question_boolean:answers={}".format(answers))
    # Use the Canvas API to create a question for a quiz
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes/{2}/questions".format(baseUrl, course_id, quiz_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    payload={'question':
             {
                 'question_name': name,
                 'question_text': question_text,
                 'question_type': 'true_false_question',
                 'question_category': 'Unknown',
                 'position': index,
                 'answers': answers,
             }
    }
    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of post making a question: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted question")
        return page_response['id']
    return False

def create_question_multiple_choice(course_id, quiz_id, index, name, question_text, answers):
    #print("create_question_multiple_choice:answers={}".format(answers))
    # Use the Canvas API to create a question for a quiz
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes/{2}/questions".format(baseUrl, course_id, quiz_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    payload={'question':
             {
                 'question_name': name,
                 'question_text': question_text,
                 'question_type': 'multiple_choice_question',
                 'question_category': 'Unknown',
                 'position': index,
                 'answers': answers,
             }
    }
    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of post making a question: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted question")
        return page_response['id']
    return False

def create_question_multiple_choice_with_points(course_id, quiz_id, index, name, question_text, answers, points):
    #print("create_question_multiple_choice:answers={}".format(answers))
    # Use the Canvas API to create a question for a quiz
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes/{2}/questions".format(baseUrl, course_id, quiz_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    payload={'question':
             {
                 'question_name': name,
                 'question_text': question_text,
                 'question_type': 'multiple_choice_question',
                 'question_category': 'Unknown',
                 'position': index,
                 'answers': answers,
                 'points_possible': points
             }
    }
    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of post making a question: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted question")
        return page_response['id']
    return False



def create_question_essay(course_id, quiz_id, index, name, question_text):
    # Use the Canvas API to create a question for a quiz
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes/{2}/questions".format(baseUrl, course_id, quiz_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    payload={'question':
             {
                 'question_name': name,
                 'question_text': question_text,
                 'question_type': 'essay_question',
                 'question_category': 'Unknown',
                 'position': index
             }
    }

    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of post making a question: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted question")
        return page_response['id']
    return False

def create_question_short_answer_question(course_id, quiz_id, index, name, question_text):
    # Use the Canvas API to create a question for a quiz
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes/{2}/questions".format(baseUrl, course_id, quiz_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    payload={'question':
             {
                 'question_name': name,
                 'question_text': question_text,
                 'question_type': 'short_answer_question',
                 'question_category': 'Unknown',
                 'position': index
             }
    }

    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of post making a question: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted question")
        return page_response['id']
    return False


def create_question_multiple_dropdowns(course_id, quiz_id, index, name, question_text, answers):
    if Verbose_Flag:
        print("create_question_multiple_dropdowns:question_text={}".format(question_text))
        print("create_question_multiple_dropdowns:answers={}".format(answers))
    # Use the Canvas API to create a question for a quiz
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes/{2}/questions".format(baseUrl, course_id, quiz_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    payload={'question':
             {
                 'question_name': name,
                 'question_text': question_text,
                 'question_type': 'multiple_dropdowns_question',
                 'question_category': 'Unknown',
                 'position': index,
                 'answers': answers,
             }
    }
    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of post making a question: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted question")
        return page_response['id']
    return False

def create_question_multiple_dropdowns_with_points(course_id, quiz_id, index, name, question_text, answers, points):
    if Verbose_Flag:
        print("create_question_multiple_dropdowns:question_text={}".format(question_text))
        print("create_question_multiple_dropdowns:answers={}".format(answers))
    # Use the Canvas API to create a question for a quiz
    # POST /api/v1/courses/:course_id/quizzes/:quiz_id/questions

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes/{2}/questions".format(baseUrl, course_id, quiz_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    payload={'question':
             {
                 'question_name': name,
                 'question_text': question_text,
                 'question_type': 'multiple_dropdowns_question',
                 'question_category': 'Unknown',
                 'position': index,
                 'answers': answers,
                 'points_possible': points
             }
    }
    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of post making a question: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if r.status_code == requests.codes.created:
        page_response=r.json()
        print("inserted question")
        return page_response['id']
    return False

def create_module_quiz_item(course_id, module_id, quiz_id, item_name, points):
    # Use the Canvas API to create a module item in the course and module
    #POST /api/v1/courses/:course_id/modules/:module_id/items
    url = "{0}/courses/{1}/modules/{2}/items".format(baseUrl, course_id, module_id)
    if Verbose_Flag:
        print("creating module quiz item for course_id={0} module_id={1} quiz_id={1}".format(course_id, module_id, quiz_id))
    payload = {'module_item[title]': item_name,
               'module_item[type]': 'Quiz',
               'module_item[content_id]': quiz_id,
               'module_item[completion_requirement][type]': 'must_submit',
               #'module_item[completion_requirement][min_score]': points

    }

    r = requests.post(url, headers = header, data = payload)
    if Verbose_Flag:
        print("result of creating module: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        modules_response=r.json()
        module_id=modules_response["id"]
        return module_id
    return  module_id

def create_survey(course_id, cycle_number, school_acronym, PF_courses, AF_courses, relevant_courses_English, relevant_courses_Swedish, examiners, all_course_examiners):
    index=1
    survey=create_survey_quiz(course_id)

    # add the quiz to the appropriate module page
    module_id=check_for_module(course_id,  'Gatekeeper protected module 1')
    if Verbose_Flag:
        print("found module to place the quiz in is module_id: {}".format(module_id))
    q_module_id=create_module_quiz_item(course_id, module_id, survey, 'Information om exjobbsprojekt/Information for degree project', 0)
    if Verbose_Flag:
        print("placed the quiz into module as module item id: {}".format(q_module_id))

    graded_or_ungraded='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en">Do you wish an A-F grade, rather than the default P/F (i.e. Pass/Fail) grade for your degree project?</p><p>True: Grade A-F</p><p>False: Pass/Fail (standard)</p></div><div id="fragment-sv"><p lang="sv">Vill du ha ett betygsatt exjobb (A-F), i stället för ett vanligt med bara P/F (Pass/Fail)?</p><p>Sant: Betygsatt exjobb (A-F)</p><p>Falskt: Pass/Fail (standard)</p></div>'

    create_question_boolean(course_id, survey, index,
                            'Graded or ungraded', graded_or_ungraded,
                            [{'answer_comments': '', 'answer_weight': 100, 'answer_text': 'True/Sant'}, {'answer_comments': '', 'answer_weight': 0, 'answer_text': 'False/Falskt'}])
    index += 1

    diva='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en">Do you give KTH permission to make the full text of your final report available via DiVA?</p><p lang="en"><strong>True</strong>: I accept publication via DiVA</p><p lang="en"><strong>False</strong>: I do not accept publication via DiVA</p><p lang="en"><strong>Note that in all cases the report is public and KTH must provide a copy to anyone on request.</strong></p></div><div id="fragment-sv"><p lang="sv">Ger du KTH tillstånd att publicera hela din slutliga exjobbsrapport elektroniskt i databasen DiVA?</p><p lang="sv"><strong>Sant:</strong> Jag godkänner publicering via DiVA</p><p lang="sv"><strong>Falskt:</strong> Jag godkänner inte publicering via DiVA</p><p lang="sv"><strong>Observera att din slutliga exjobbsrapport alltid är offentlig, och att KTH alltid måste tillhandahålla en kopia om någon begär det.</strong></p></div>'
    create_question_boolean(course_id, survey, index, 'Publishing in DiVA', diva, [{'answer_comments': '', 'answer_weight': 100, 'answer_text': 'True/Sant'}, {'answer_comments': '', 'answer_weight': 0, 'answer_text': 'False/Falskt'}])
    index += 1


    course_code='''<p>Kurskod/Course code: Pass/Fail grading (standard): [PF] or Graded A-F/Betygsatt exjobb (A-F): [AF]</p>'''
    course_code_answers=course_code_alternatives(PF_courses, AF_courses)
    course_code_description=course_code_descriptions(PF_courses, AF_courses, relevant_courses_English, relevant_courses_Swedish)
    create_question_multiple_dropdowns(course_id, survey, index, 'Kurskod/Course code', course_code_description+course_code, course_code_answers)
    index += 1
        

    prelim_title='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en">Tentative title</p></div><div id="fragment-sv"><p lang="sv">Preliminär titel</p></div>'
    create_question_essay(course_id, survey, index, 'Preliminär titel/Tentative title', prelim_title)
    index += 1


    # The following was added to provide some information that could be used to identify an appropriate examiner
    prelim_description='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en">Brief description of the proposed project</p></div><div id="fragment-sv"><p lang="sv">Kort beskrivning av det föreslagna projektet</p></div>'
    create_question_essay(course_id, survey, index, 'Project Description/Projekt beskrivning', prelim_description)
    index += 1

    # examiner
    examiner_question='''<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">P&aring; svenska</a></li></ul><div id="fragment-en"><p lang="en">Potential examiner:</p></div><div id="fragment-sv"><p lang="sv">F&ouml;rslag p&aring; examinator:</p></div></div><p> [e1]</p>'''

    course_code_description=course_code_descriptions(PF_courses, AF_courses, relevant_courses_English, relevant_courses_Swedish)
    examiner_answers=potential_examiners_answer(examiners)
    create_question_multiple_dropdowns(course_id, survey, index, 'Examinator/Examiner', examiner_question, examiner_answers)
    index += 1

    # examiner version 2
    #course_examiners_dict=course_examiners(PF_courses + AF_courses)
    #equiv_classes=compute_equivalence_class_of_teachers_in_courses(course_examiners_dict)
    equiv_classes=compute_equivalence_class_of_teachers_in_courses(all_course_examiners)

    examiner_question2='''<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">P&aring; svenska</a></li></ul><div id="fragment-en"><p lang="en">Potential examiner:</p></div><div id="fragment-sv"><p lang="sv">F&ouml;rslag p&aring; examinator:</p></div></div>'''+course_examiner_alternatives_table(equiv_classes)

    examiner_answers2=course_examiner_alternatives_answers(equiv_classes)
    course_code_description=course_code_descriptions(PF_courses, AF_courses, relevant_courses_English, relevant_courses_Swedish)

    #examiner_answers=potential_examiners_answer(examiners)
    create_question_multiple_dropdowns(course_id, survey, index, 'Examinator/Examiner (version 2)', examiner_question2, examiner_answers2)
    index += 1



    start_date='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">P&aring; svenska</a></li></ul><div id="fragment-en"><p lang="en">Planned start:</p></div><div id="fragment-sv"><p lang="sv">Startdatum:</p></div></div><p>[year].[month].[day]</p>' 
    start_date_answers=[{'weight': 100, 'text': '2018', 'blank_id': 'year'},
                        {'weight': 100, 'text': '2019', 'blank_id': 'year'},
                        {'weight': 100, 'text': '2020', 'blank_id': 'year'},
                        {'weight': 100, 'text': '01', 'blank_id': 'month'},
                        {'weight': 100, 'text': '02', 'blank_id': 'month'},
                        {'weight': 100, 'text': '03', 'blank_id': 'month'},
                        {'weight': 100, 'text': '04', 'blank_id': 'month'},
                        {'weight': 100, 'text': '05', 'blank_id': 'month'},
                        {'weight': 100, 'text': '06', 'blank_id': 'month'},
                        {'weight': 100, 'text': '07', 'blank_id': 'month'},
                        {'weight': 100, 'text': '08', 'blank_id': 'month'},
                        {'weight': 100, 'text': '09', 'blank_id': 'month'},
                        {'weight': 100, 'text': '10', 'blank_id': 'month'},
                        {'weight': 100, 'text': '11', 'blank_id': 'month'},
                        {'weight': 100, 'text': '12', 'blank_id': 'month'},
                        {'weight': 100, 'text': '01', 'blank_id': 'day'},
                        {'weight': 100, 'text': '02', 'blank_id': 'day'},
                        {'weight': 100, 'text': '03', 'blank_id': 'day'},
                        {'weight': 100, 'text': '04', 'blank_id': 'day'},
                        {'weight': 100, 'text': '05', 'blank_id': 'day'},
                        {'weight': 100, 'text': '06', 'blank_id': 'day'},
                        {'weight': 100, 'text': '07', 'blank_id': 'day'},
                        {'weight': 100, 'text': '08', 'blank_id': 'day'},
                        {'weight': 100, 'text': '09', 'blank_id': 'day'},
                        {'weight': 100, 'text': '10', 'blank_id': 'day'},
                        {'weight': 100, 'text': '11', 'blank_id': 'day'},
                        {'weight': 100, 'text': '12', 'blank_id': 'day'},
                        {'weight': 100, 'text': '13', 'blank_id': 'day'},
                        {'weight': 100, 'text': '14', 'blank_id': 'day'},
                        {'weight': 100, 'text': '15', 'blank_id': 'day'},
                        {'weight': 100, 'text': '16', 'blank_id': 'day'},
                        {'weight': 100, 'text': '17', 'blank_id': 'day'},
                        {'weight': 100, 'text': '18', 'blank_id': 'day'},
                        {'weight': 100, 'text': '19', 'blank_id': 'day'},
                        {'weight': 100, 'text': '20', 'blank_id': 'day'},
                        {'weight': 100, 'text': '21', 'blank_id': 'day'},
                        {'weight': 100, 'text': '22', 'blank_id': 'day'},
                        {'weight': 100, 'text': '23', 'blank_id': 'day'},
                        {'weight': 100, 'text': '24', 'blank_id': 'day'},
                        {'weight': 100, 'text': '25', 'blank_id': 'day'},
                        {'weight': 100, 'text': '26', 'blank_id': 'day'},
                        {'weight': 100, 'text': '27', 'blank_id': 'day'},
                        {'weight': 100, 'text': '28', 'blank_id': 'day'},
                        {'weight': 100, 'text': '29', 'blank_id': 'day'},
                        {'weight': 100, 'text': '30', 'blank_id': 'day'},
                        {'weight': 100, 'text': '31', 'blank_id': 'day'}]

    create_question_multiple_dropdowns(course_id, survey, index, 'Startdatum/Planned start', start_date, start_date_answers)
    index += 1

    company='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en">At a company, indicate name:</p></div><div id="fragment-sv"><p lang="sv">På företag, ange vilket</p></div>'
    create_question_essay(course_id, survey, index, 'På företag, ange vilket/At a company, indicate name', company)
    index += 1

    country='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en"><p lang="en">Outside Sweden, indic. Country (Enter two character country code)</p></div><div id="fragment-sv"><p lang="sv">Utomlands, ange land (Ange landskod med två tecken)</p></div>'
    create_question_short_answer_question(course_id, survey, index, 'Utomlands, ange land/Outside Sweden, indic. Country', country)
    index += 1

    university='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">P&aring; svenska</a></li></ul><div id="fragment-en"><p lang="en">At another university</p></div><div id="fragment-sv"><p lang="sv">P&aring; annan h&ouml;gskola</p></div></div>'
    create_question_essay(course_id, survey, index, 'På annan högskola/At another university', university)
    index += 1

    contact='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">P&aring; svenska</a></li></ul><div id="fragment-en"><p lang="en">Enter the name and contact details of your contact at a company, other university, etc.</p></div><div id="fragment-sv"><p lang="sv">Ange namn, e-postadress och annan kontaktinformation f&ouml;r din kontaktperson vid f&ouml;retaget, det andra universitetet, eller motsvarande.</p></div></div>'
    create_question_essay(course_id, survey, index, 'Kontaktperson/Contact person', contact)
    index += 1


def insert_column_name(course_id, column_name):
    global Verbose_Flag

    # Use the Canvas API to Create a custom gradebook column
    # POST /api/v1/courses/:course_id/custom_gradebook_columns
    #   Create a custom gradebook column
    # Request Parameters:
    #Parameter		Type	Description
    #column[title]	Required	string	no description
    #column[position]		integer	The position of the column relative to other custom columns
    #column[hidden]		boolean	Hidden columns are not displayed in the gradebook
    # column[teacher_notes]		boolean	 Set this if the column is created by a teacher. The gradebook only supports one teacher_notes column.

    url = "{0}/courses/{1}/custom_gradebook_columns".format(baseUrl,course_id)
    if Verbose_Flag:
       print("url: {}".format(url))
    payload={'column[title]': column_name}
    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post creating custom column: {}".format(r.text))
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        print("inserted column: {}".format(column_name))
        return True
    return False

def list_custom_columns(course_id):
    columns_found_thus_far=[]
    # Use the Canvas API to get the list of custom column for this course
    #GET /api/v1/courses/:course_id/custom_gradebook_columns

    url = "{0}/courses/{1}/custom_gradebook_columns".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting custom_gradebook_columns: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            columns_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links['current']['url'] != r.links['last']['url']:  
            r = requests.get(r.links['next']['url'], headers=header)  
            page_response = r.json()  
            for p_response in page_response:  
                columns_found_thus_far.append(p_response)

    return columns_found_thus_far

def create_custom_columns(course_id, cycle_number):
    existing_columns=list_custom_columns(course_id)
    print("existing_columns={}".format(existing_columns))

    #column_names=['Group', 'Course_code', 'Planned_start_date', 'Tentative_title', 'Prelim_description', 'Examiner', 'Supervisor', 'KTH_unit', 'Place', 'Contact', 'Student_approves_fulltext', 'TRITA', 'DiVA_URN', 'GA_Approval', 'Ladok_Final_grade_entered']
    column_names=['Group', 'Planned_start_date', 'Tentative_title', 'Prelim_description', 'Examiner', 'Supervisor', 'KTH_unit', 'Place', 'Contact', 'Student_approves_fulltext', 'TRITA', 'DiVA_URN', 'GA_Approval', 'Ladok_Final_grade_entered']

    if cycle_number == '2':
        column_names.remove('Group') # as 2nd cycle degree projects can only be done by individual students

    for c in existing_columns:  # no need to insert existing columns
        column_names.remove(c['title'])

    for c in column_names:
        insert_column_name(course_id, c)

def lookup_column_number(column_name, list_of_exiting_columns):
    for column in list_of_exiting_columns:
        if Verbose_Flag:
            print('column: ', column)
        if column['title'] == column_name: 
            return column['id']
    return -1
       
def add_column_if_necessary(course_id, new_column_name, list_of_exiting_columns):
    column_number=lookup_column_number(new_column_name, list_of_exiting_columns)
    if column_number > 0:
        return column_number
    # otherwise insert the new column
    insert_column_name(course_id, new_column_name)
    return lookup_column_number(new_column_name, list_custom_columns(course_id))

def put_custom_column_entries(course_id, column_number, user_id, data_to_store):
    entries_found_thus_far=[]
    # Use the Canvas API to get the list of custom column entries for a specific column for the course
    #PUT /api/v1/courses/:course_id/custom_gradebook_columns/:id/data/:user_id

    url = "{0}/courses/{1}/custom_gradebook_columns/{2}/data/{3}".format(baseUrl,course_id, column_number,user_id)
    if Verbose_Flag:
        print("url: " + url)
        
    payload={'column_data[content]': data_to_store}
    r = requests.put(url, headers = header, data=payload)

    if Verbose_Flag:
        print("result of putting data into custom_gradebook_column: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

    for p_response in page_response:  
        entries_found_thus_far.append(p_response)

    return entries_found_thus_far

def sections_in_course(course_id):
    sections_found_thus_far=[]
    # Use the Canvas API to get the list of sections for this course
    #GET /api/v1/courses/:course_id/section

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
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links['current']['url'] != r.links['last']['url']:  
            r = requests.get(r.links['next']['url'], headers=header)  
            page_response = r.json()  
            for p_response in page_response:  
                sections_found_thus_far.append(p_response)

    return sections_found_thus_far

def create_sections_in_course(course_id, section_names):
    sections_found_thus_far=[]

    # Use the Canvas API to create sections for this course
    #POST /api/v1/courses/:course_id/sections

    url = "{0}/courses/{1}/sections".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    for section_name in section_names:
        #course_section[name]
        payload={'course_section[name]': section_name}
        r = requests.post(url, headers = header, data=payload)

        if Verbose_Flag:
            print("result of creating section: {}".format(r.text))

        if r.status_code == requests.codes.ok:
            page_response=r.json()

            for p_response in page_response:  
                sections_found_thus_far.append(p_response)

    return sections_found_thus_far

def create_sections_for_examiners_and_programs(course_id, examiners, programs):
    if Verbose_Flag:
        print("create_sections_for_examiners_and_programs({0}, {1}, {2}".format(course_id, examiners, programs))
    create_sections_in_course(course_id, sorted(examiners))

    program_names=[]
    for s in programs:
        program_names.append("Program: {0}-{1}".format(s, programs[s]['title_en'] ))

    create_sections_in_course(course_id, program_names)

def create_course_page(course_id, page_title, page_contents):
    #Create page WikiPagesApiController#create
    #POST /api/v1/courses/:course_id/pages

    url = "{0}/courses/{1}/pages".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'wiki_page':
             {
                 'title': page_title,
                 'body': page_contents,
                 'published': 'true'
                 }
    }
    r = requests.post(url, headers = header, json=payload)

    if Verbose_Flag:
        print("result of creating a page: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

    return page_response

def create_module_page_item(course_id, module_id, page_id, item_name, page_url):
    # Use the Canvas API to create a module item in the course and module
    #POST /api/v1/courses/:course_id/modules/:module_id/items
    url = "{0}/courses/{1}/modules/{2}/items".format(baseUrl, course_id, module_id)
    if Verbose_Flag:
        print("creating module assignment item for course_id={0} module_id={1} assignment_id={1}".format(course_id, module_id, page_id))
    payload = {'module_item':
               {
                   'title': item_name,
                   'type': 'Page',
                   'content_id': page_id,
                   'page_url': page_url
               }
    }

    r = requests.post(url, headers = header, json = payload)
    if Verbose_Flag:
        print("result of creating module page item: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        modules_response=r.json()
        module_id=modules_response["id"]
        return module_id
    return  module_id


def create_basic_pages(course_id, cycle_number, existing_modules):
    basic_pages={
        'Introduction': ['Welcome to Degree Project Course / Välkommen till examensprojektkurs',
                         'Grants from KTH Opportunities Fund / Bidrag från KTH Opportunities Fund',
                         'Instructions for degree project / Instruktioner för examensarbete',
                         'Templates/Mallar',
                         'After completing degree project/Efter att ha avslutat examensarbete',
                         'Recover from failed degree project/ Återuppta underkänt examensarbete'],
        'Working Material': ['Material lectures, templates etc/ Material Föreläsningar, Mallar mm',
                             'Blank English-Swedish page'],
        'For Faculty': ['Generate cover/Skapa omslag']
        }
    pages_content={
                  'Welcome to Degree Project Course / Välkommen till examensprojektkurs':
                  '''<p><span style="color: red;"></span><span lang="en">Welcome</span> (<span lang="sv">Välkommen</span>)</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p><strong>Information in English <br></strong></p>
<p>Here follows information about degree projects, at the bachelor and master levels. There is information in both Swedish and English.</p>
<p>No matter the level of the degree project, a project proposal must be created and handed in. Templates for the project proposal are available. These templates are in Swedish and English and the contents are the same irrespective of language and degree project (bachelor or master).</p>
<p>The project proposal is used to aid the search for examiners and supervisors at KTH. The proposal is also used to assess the degree project’s characteristics and scope. Hence, the project proposal serves as a basis for discussion. In the event of lacking a project, the project proposal is still useful as a declaration of interest in a subject, problem, or research area. The declared areas of interest can then be used to find a suitable examiner and/or supervisor.</p>
<p>Fill in the project proposal with the available information. Information that is unknown should be stated as such, rather than being omitted. <span style="font-size: 1rem;">Hand in the project proposal by uploading the file in the appropriate Canvas activity and assignment.</span></p>
</div>
<div id="fragment-sv">
<p lang="sv"><strong>Information på Svenska</strong></p>
<p lang="sv">Här följer information om examensarbeten, på kandidatexamen och masternivåer. Det finns information på både svenska och engelska.
Oavsett graden av examensarbetet måste ett projektförslag skapas och lämnas in. Mallar för projektförslaget finns tillgängliga. Mallarna är på svenska och engelska och innehållet är desamma oavsett språk och examensarbete (kandidatexamen eller master).</p>
<p lang="sv">Projektförslaget används för att hjälpa till att söka examinatorer och handledare vid KTH. Förslaget används också för att bedöma examensprojektets egenskaper och omfattning. Därför fungerar projektförslaget som grund för diskussion. Om det saknas ett projekt är projektförslaget fortfarande användbart som intresseförklaring för ett ämne, problem eller forskningsområde. De deklarerade intressanta områdena kan sedan användas för att hitta en lämplig examinator och / eller handledare.</p>
<p lang="sv">Fyll i projektförslaget med tillgänglig information. Information som är okänd ska anges som sådan snarare än att utelämnas. Lämna in projektförslaget genom att ladda upp filen i lämplig Canvas-aktivitet och uppdrag.</p>
</div>
</div>
                  ''',
                   'Grants from KTH Opportunities Fund / Bidrag från KTH Opportunities Fund':
                   '''
<p><span lang="en">Grants from KTH Opportunities Fund</span> (<span lang="sv">Bidrag från KTH Opportunities Fund</span>)</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<h2 lang="en">Apply for a grant from KTH Opportunities Fund</h2>
<p lang="en">Thanks to donations from alumni and friends of KTH, KTH Opportunities Fund is able to support student projects and initiatives. All KTH students at the undergraduate, master's and doctoral level are able to apply for funding from KTH Opportunities Fund.</p>

<h2 lang="en">Get involved!</h2>
<h3 lang="en">As volunteer or mentor or another function</h3>
<p lang="en">Alumni volunteers who give their time and experience are critical to the continuing success of KTH. Getting involved is not only the chance for you to give something back to your alma mater. It is also a way for you to reconnect with KTH, benefit your organisation, further your professional development and create valuable networking opportunities.</p>
</div>
<div id="fragment-sv">
<h2 lang="sv">Ansöka om ett bidrag från KTH Opportunities Fund</h2>
<p lang="sv">Tack vare donationer från alumner och vänner av KTH, är KTH Opportunities Fund kunna stödja studentprojekt och initiativ. Alla KTH-studenter på grundnivå, master- och forskarnivå kan ansöka om finansiering från KTH Opportunities Fund.</p>
<h2 lang="sv">Bli involverad!</h2>
<h3 lang="sv">Som volontär eller mentor eller en annan funktion</h3>
<p lang="sv">Alumni volontärer som ger sin tid och erfarenhet är avgörande för fortsatt framgång för KTH. Engagera är inte bara en chans för dig att ge något tillbaka till din alma mater. Det är också ett sätt för dig att återansluta med KTH, till nytta för din organisation, ytterligare din professionella utveckling och skapa värdefulla möjligheter till nätverkande.</p>
</div>
</div>
                   ''',
        'Instructions for degree project / Instruktioner för examensarbete':

'''<p><span lang="en">Degree project</span> (<span lang="sv">Examensarbete</span>)</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Please read the information concerning the different degree project courses at <a title="Kurser/Courses" href="https://kth.instructure.com/courses/1586/pages/kurser-slash-courses" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/pages/kurser-slash-courses" data-api-returntype="Page">Kurser/Courses</a>.</p>
<p lang="en">As a first step, a project proposal must be created and handed in. Templates for the project proposal can be found in Mallar/Templates. The templates are in Swedish and English and the contents are the same irrespective of language and degree project.</p>
<p lang="en">The project proposal is used for assigning examiners and supervisors. The proposals are also used for evaluating the degree project’s characteristics and scope. Hence, the project proposals serve as a basis for discussion. Even without a specific project, it is still possible to assign an examiner and a supervisor, thus students should hand in their project proposal to indicate their interest area(s). These interest areas are used to assign the most suitable examiner and/or supervisor.</p>
<p lang="en">Fill in the project proposal with available information. If any pieces of information are unknown, please indicate this in the project proposal. Hand in the project proposal by uploading the file via the Projekt Plan/Project plan assignment.</p>
<p lang="en">A time ordered list of deliverables can be found under Assignments.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Läs informationen som rör det examensarbete ni ska göra (se <a title="Kurser/Courses" href="https://kth.instructure.com/courses/1586/pages/kurser-slash-courses" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/pages/kurser-slash-courses" data-api-returntype="Page">Kurser/Courses</a>).   </p>
<p lang="sv">Oavsett examensarbete ska projektförslag upprättas och lämnas in. Mallar för projektförslag (tidigare kallat projektplan) finns att hämta i Mallar/Templates. Mallarna är på svenska som engelska och har samma innehåll, det vill säga oavsett språk och examensarbete.</p>
<p lang="sv">Projektförslagen används för att tilldela examinator och handledare. Förslagen är även till för att bedöma examensarbetets karaktär och omfång. Således fungerar projektförslagen även som diskussionsunderlag. Även om projekt saknas, går det att tilldela examinator och handledare, så alla studenter ska lämna in ett projektförslag. I dessa fall, sker tilldelning utifrån intresseområden.</p>
<p lang="sv">Fyll i projektförslaget utifrån den information som finns att tillgå. Om det finns oklarheter med examensarbetet, skriv det i projektförslaget. Lämna in projektförslaget genom att ladda upp filen i Projekt Plan/Project plan inlämning.</p>
<p lang="sv">En tid ordnad lista över delresultaten finns under Assignments/Uppgifter.</p>
</div>
</div>''',
        'Material lectures, templates etc/ Material Föreläsningar, Mallar mm':
        '''
<p><a class="instructure_file_link instructure_scribd_file" title="BachelorMaster2019_DegreeProjectFairOct2018.pdf" href="https://kth.instructure.com/courses/1586/files/1340605/download?verifier=I51GxS4aF9OGVgEKPTcmDfG9nzFYRa0T2jRu3w2F&amp;wrap=1" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/files/1340605" data-api-returntype="File">BachelorMaster2019_DegreeProjectFairOct2018.pdf</a></p>
<p><a class="instructure_file_link instructure_scribd_file" title="KandidatMaster2019_ExjobbsmässanOkt2018.pdf" href="https://kth.instructure.com/courses/1586/files/1340606/download?verifier=GeG8l2NDewg9s1lKSPY0GoOMFhPZzzJh23Svr68x&amp;wrap=1" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/files/1340606" data-api-returntype="File">KandidatMaster2019_ExjobbsmässanOkt2018.pdf</a></p>
<p>Lecture Spring 2018: <a class="instructure_file_link instructure_scribd_file" title="Master-degree project-2018 jan 16 - introduction.pdf" href="https://kth.instructure.com/courses/1586/files/711077/download?verifier=UqeKeF9deC5HTkTYarX4w1RH2Re75T0CVfJWQBrA&amp;wrap=1" data-api-returntype="File" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/files/711077">Master-degree project-2018 jan 16 - introduction.pdf</a></p>
        ''',
        'Templates/Mallar':
        '''
<p><span lang="en">Templates</span> (<span lang="sv">Mallar</span>)</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<h3 lang="en">Template Project Proposal</h3>
<p><a title="Project Proposal" href="https://people.kth.se/~maguire/Template-Project_Plan-English-2020.docx">Project Proposal</a></p>
<h3 lang="en">Template thesis</h3>
<p lang="en"><a title="Thesis template" href="https://people.kth.se/~maguire/Template-thesis-English-2020.docx">Thesis template</a></p>
<h3 lang="en">Opposition Template</h3>
<p lang="en"><a title="Opposition template" href="https://people.kth.se/~maguire/Template-opposition-opponeringsmall-2020.docx">Opposition template</a></p>
<h3><span id="mceFileUpload_insertion">Portal of Methods and Methodologies</span></h3>
<ul>
<li><a class="instructure_file_link instructure_scribd_file" title="Research Methods - Methodologies(1)(1).pdf" href="https://kth.instructure.com/courses/1586/files/659671/download?verifier=IF75hoeLSEnZifdZU9RsU8UB9QjDCjjHHOHV47wL&amp;wrap=1" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/files/659671" data-api-returntype="File">Research Methods - Methodologies.pdf</a></li>
</ul>
<p> </p>
</div>
<div id="fragment-sv">
<h3 lang="sv">Projektförslag Mall</h3>
<p><a title="Projektförslag Mall" href="https://people.kth.se/~maguire/Template-Projekt_Förslag_Mall-svensk.docx">Projektförslag Mall</a></p>
<h3 lang="sv">Uppsatsrapport</h3>
<p lang="sv"><a title="Mall för Examensarbeten" href="https://people.kth.se/~maguire/Template-Mall_f%C3%B6r_Examensarbeten-svensk-2020.docx">Mall för Examensarbeten</a></p>
<h3 lang="sv">Oppositionmallar</h3>
<p lang="en"><a title="Oppositionmallar" href="https://people.kth.se/~maguire/Template-opposition-opponeringsmall-2020.docx">Oppositionmallar</a></p>
<h3><span id="mceFileUpload_insertion">Portal of Methods and Methodologies</span></h3>
<ul>
<li><span id="mceFileUpload_insertion"><a class="instructure_file_link instructure_scribd_file" title="Research Methods - Methodologies(1)(1).pdf" href="https://kth.instructure.com/courses/1586/files/659671/download?verifier=IF75hoeLSEnZifdZU9RsU8UB9QjDCjjHHOHV47wL&amp;wrap=1" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/files/659671" data-api-returntype="File">Research Methods - Methodologies.pdf</a></span></li>
</ul>
</div>
</div>
        ''',
        'After completing degree project/Efter att ha avslutat examensarbete':
        '''
<p><span lang="en">After completing degree project</span> (<span lang="sv">Efter att ha avslutat examensarbete</span>)</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en"><em><strong>OBSERVE: </strong></em>After degree project, you should apply for your degree certificate. For more information, see:</p>
<p lang="en"><a href="https://www.kth.se/en/student/program/examen/examen-hur-och-var-ansoker-man-1.2234">Apply for degree certificate</a></p>
<p lang="en">If you do not apply, you will not graduate!</p>
</div>
<div id="fragment-sv">
<p lang="sv"><em><strong>OBSERVERA: </strong></em>Efter examensarbete, bör du ansöka om examensbevis . För mer information, se:</p>
<p lang="sv"><a href="https://www.kth.se/en/student/program/examen/examen-hur-och-var-ansoker-man-1.2234">Ansöka om examensbevis</a></p>
<p lang="sv">Om du inte ansökaa, kommer du inte examen!</p>
</div>
</div>
        ''',
        'Recover from failed degree project/ Återuppta underkänt examensarbete':
        '''
<p><span lang="en"></span>Recover from failed degree project/ Återuppta underkänt examensarbete</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">If you got Fail on the degree project due to a problem, for example, not carried out within time constraint, or lack of quality, you must retake the course and carry out a new degree project. This new degree project must be clearly distinct from the failed degree project. Parts from the already carried out project may, if possible, be reused in the new degree project, such as the literature study and research methods and methodologies but this must be discussed with and decided by your examiner.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Om du har fått Fail på ditt examensarbete av någon orsak, t ex något problem såsom ej slutfört examensarbetet inom utsatt tid, 1 år, eller bristande kvalitet, måste du göra om examensarbetet och utföra ett nytt examensarbetsprojektet. Detta nya examensarbete måste tydligt skilja sig från det tidigare underkända examensarbetsprojektet. Delar från det redan genomförda projektet kan, om möjligt, återanvändas i det nya examensprojektet, såsom litteraturstudien och forskningsmetoder och metodologier men det måste göras i samråd med din examinator.</p>
</div>
</div>
        ''',
        'Blank English-Swedish page':
        '''
<p><span lang="en"></span>English heading / Engelsk rubrik</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Fill in Enlish text</p>
</div>
<div id="fragment-sv">
<p lang="sv">Fyll i svensk text</p>
</div>
</div>
        ''',
        'Generate cover/Skapa omslag':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">P&aring; svenska</a></li>
</ul>
<div id="fragment-en">
<h3 lang="en">Create a KTH Thesis Cover Page as PDF</h3>
<p lang="en"><a href="https://intra.kth.se/kth-cover?l=en">cover generator</a></p>
</div>
<div id="fragment-sv">
<h3 lang="sv">Skapa omslag till examensarbete</h3>
<p lang="sv"><a href="https://intra.kth.se/kth-cover/">omslaggenerator</a></p>
</div>
</div>
        '''
        
    }

    # for m in existing_modules:
    #     if m['name'] == 'Gatekeeper protected module 1':
    #         id_of_protected_module=m['id']

    for bp in basic_pages:
        module_id=check_for_module(course_id,  bp)
        if not module_id:
            module_id=create_module(course_id, bp, False)
        pages_in_module=basic_pages[bp]
        print("pages_in_module={}".format(pages_in_module))

        for p in pages_in_module:
            if Verbose_Flag:
                print("p={}".format(p))
            page_title=p
            page_content=pages_content.get(p, [])
            if Verbose_Flag:
                print("page_content={}".format(page_content))
            if page_content:                 
                cp=create_course_page(course_id, page_title, page_content)
                if Verbose_Flag:
                    print("cp={}".format(cp))
                    print("page title={}".format(cp['title']))
                    print("page url={}".format(cp['url']))
                    print("page id={}".format(cp['page_id']))
                create_module_page_item(course_id, module_id, cp['page_id'], cp['title'], cp['url'])

def create_basic_assignments(course_id, group_name):
    list_of_assignments={
        'Projekt Plan/Project plan':
        '''<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul>
        <div id="fragment-en">
        <p lang="en">Students should submit their initial project proposal.</p>
        <p lang="en">The name of the project proposal should be of the form:</p>
        <ul><li lang="en">DegreeProgram-CourseCode-Author1-ProjectTitle-Keywords-YYYYMMDD</li></ul></div>
        <div id="fragment-sv">
        <p lang="sv">Studenterna ska lämna in sin ursprungliga projektförslag.</p>
        <p lang="sv">Namnet på projektförslaget ska vara enligt formen:</p>
        <ul><li lang="sv">UtbildningsprogramKod-Författare1-ProjektTitel–Nyckelord-YYYYMMDD</li></ul></div></div>''',
        'Förslaget presentationsbilder/Proposal presentation slides':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students can (optionally) submit their proposal presentation slides.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna kan (valfritt) lämna in sina förslag presentationsbilder.</p>
</p>
</div>
</div>
        ''',
        'Litteraturstudie/Literature study':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students should submit their Literature study.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna ska lämna in sin Litteraturstudie.</p>
</div>
</div>
        ''',
        'Alfa utkast/draft':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students should submit their alpha draft</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna ska lämna in sin alfa utkast.</p>
</div>
</div>
        ''',
        'Beta utkast/draft':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students should submit their beta draft</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna ska lämna in sin beta utkast.</p>
</div>
</div>''',
        'Utkast till/Draft for opponent':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students should submit their draft for their opponent. Additionally, the students should notify their examiner of the name of their opponent(s) (at the latest when they submit the draft for the opponent ) - so that the examiner can assign the opponent(s) as a peer reviewer. </p>
<p lang="en">Note that if you are doing your thesis in a company that you must clear your thesis draft with the company for external distribution before submitted it. This enables the company to file patent applications, remove confidential material, remove material that they/you have access to under a non-disclosure agreement, etc.</p>
<p lang="en">Note that the opponent should submit their opposition report as their own opposition report (as a separate assignment), rather than directly in the peer review of the report. However, this peer review of the report is a good is a good way to submit the detailed comments on the manuscript.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna ska lägga fram sina utkast för sin opponent. Dessutom ska studenten meddela sin examinator namnet på sin opponent(er) (senast när de lämnar ett utkast till motståndaren) - så att examinator kan tilldela opponent(er) som peer granskare.</p>
<p lang="sv">Observera att om du gör din avhandling i ett företag som du måste rensa din avhandling utkast med bolaget för extern distribution innan lämnat den. Detta gör det möjligt för företaget att lämna in patentansökningar, avlägsna konfidentiellt material, ta bort material som de / du har tillgång till under ett sekretessavtal, osv.</p>
<p lang="sv">Observera att motståndaren ska lämna sitt motstånd rapport som sina egna oppositionsrapport (som särskilt uppdrag), snarare än direkt i granskningen av rapporten. Detta är dock granskningen av rapporten en bra är ett bra sätt att lämna in detaljerade synpunkter på manuskriptet.</p>
</div>
</div>''',
        'Opponeringsrapport/Opposition report':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students should submit their opposition report. Note that this is an individual, rather than a group assignment.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna ska lämna in sin opponeringsrapport. Observera att detta är en individ, i stället för en gruppuppgift .</p>
</div>
</div>''',
        'Presentationsbilder (utkast)/Presentation slides (draft)':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students can (optionally) submit a draft version of their presentation slides.</p>
<p lang="en">A typical oral presentation addresses the following:</p>
<ul>
<li lang="en">Title slide: Project title[:subtitle], Name of student(s) who conducted the project, Date of the oral presentation, Where the project was conducted, Name(s) of supervisor(s) and examiner(s).(1 slide)</li>
<li lang="en">Problem statement, Why the problem is important to solve, and your Goals, problem context, delimitations, ... (1 or 2 slides)</li>
<li lang="en">Background and Related work (b slides)</li>
<li lang="en">Method used to solve the problem (m slides)</li>
<li lang="en">Results and Analysis (r slides)</li>
<li lang="en">Conclusion (1 or 2 slides)</li>
<li lang="en">Future work (1 or 2 slides)</li>
<li lang="en">Final slide - to solicit questions (1 slides)</li>
</ul>
<p lang="en">The typical number of slides will be less than ~30, hence b+m+r</p>
<p lang="en">Keep in mind that only the opponent(s), supervisor(s), and examiner(s) are likely to have read the who thesis beforehand - so you need to present the key points of your thesis project in your oral presentation at a level that the audience will be able to understand: what was the problem, why was it important to solve, what others have done, what you did, what you learned, and what should be done next.</p>
<p lang="en">Note that students are not allowed to use the KTH logo on their slides.</p>
<p lang="en">You should have a slide number on each of your slides (other than the title slide) to help listeners take notes - so that they can reference their questions to specific slides.</p>
<p lang="en">Avoid complex slide backgrounds and make sure that what you want your audience to be able to see will be visible (this means avoiding small fonts, yellow text/lines, ... ).</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna kan (valfritt) lägga fram ett utkast till sina presentationsbilder.</p>
<p lang="sv">En typisk muntlig presentation behandlar följande:
</p>
<ol>
<li lang="sv">Rubrikbild: Projekttitel [: undertext] namn student (er) som genomförde projektet, Datum för muntlig presentation, Om projektet genomfördes, namn (s) av handledare (s) och examinator (s) (1. diabilder)</li>
<li lang="sv">Problem uttalande, varför problemet är viktigt att lösa, och dina mål, problem sammanhang, avgränsningar, ... (1 eller 2 diabilder)</li>
<li lang="sv">Bakgrund och därmed sammanhängande arbete (b diabilder)</li>
<li lang="sv">Metod som används för att lösa problemet (m diabilder)</li>
<li lang="sv">Resultat och-analys (R diabilder)</li>
<li lang="sv">Slutsats (1 eller 2 diabilder)</li>
<li lang="sv">Framtida arbete (1 eller 2 diabilder)</li>
<li lang="sv">Slut slide - att värva frågor (1 diabilder)</li>
</ol>
<p lang="sv">Den typiska antal bilder kommer att vara mindre än ~ 30, därmed b + m + r 

</p>
<p lang="sv">Tänk på att bara motståndaren (s), handledare (s), och examinator (s) kommer sannolikt att ha läst som avhandlingen i förväg - så du behöver för att presentera de viktigaste punkterna i din examensarbete i muntlig presentation vid en nivå att publiken kommer att kunna förstå: vad var problemet, varför var det viktigt att lösa, vad andra har gjort, vad du gjorde, vad du lärt, och vad som bör göras härnäst.</p>

<p lang="sv">Observera att eleverna inte får använda KTH logo på sina bilder.</p>

<p lang="sv">Du bör ha en bildnummer på var och en av dina bilder (annat än rubrikbilden) för att hjälpa lyssnarna ta anteckningar - så att de kan referera till sina frågor till specifika bilder.</p>

<p lang="sv">Undvik komplicerade glid bakgrunder och se till att vad du vill att din publik ska kunna se kommer att vara synlig (detta innebär att undvika små teckensnitt, gul text / linjer, ...).</p>
</div>
</div>''',
        'Presentationsseminarium/Presentation seminar':
        '''
<p><span lang="en">Presentation seminar</span> (<span lang="sv">Presentationsseminarium</span>)</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<h3 lang="en">Procedure for the presentation seminar</h3>
<ol lang="en">
<li lang="en">The presenter, i.e., author of the thesis, presents the work for 20-35 minutes. Preferably, interesting and relevant pieces of information (for project and master thesis) is given during the seminar. (All students should have read the thesis before the seminar so it may not necessary to give all details at the presentation.) </li>
<li lang="en">The opponent gives feedback for 15 minutes. The opposition report must be submitted no later than the day before the seminar. Also, out of courtesy, take one printed copy of the opposition report to the seminar and give it to the presenter. Template for the opposition report can be fetched from <a id="" class="" title="Mallar/Templates" href="https://kth.instructure.com/courses/1586/pages/mallar-slash-templates" target="" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/pages/mallar-slash-templates" data-api-returntype="Page">Mallar/Templates</a>.</li>
<li lang="en">Active listeners shall ask at least one question each. The students that act as active listeners should have looked at the thesis before the seminar. Do not forget that you should be active listeners in, at least, two other seminars, besides your own presentation seminar and opposition seminar (i.e., four in total).</li>
<li lang="en">Next, the audience has a chance to ask questions about the thesis.</li>
<li lang="en">Finally, the examiner will ask any final questions that they have.</li>
<li lang="en">Make sure that you get your assessment report signed! It is the examiner of the presenter that signs the document.</li>
</ol>
<p lang="en"> </p>
</div>
<div id="fragment-sv">
<h3 lang="sv">Presentationsseminariet process</h3>
<ol lang="sv">
<li lang="sv">Presentatörerna presenterar arbetet på ca 20-35 minuter. Företrädesvis presenteras intressanta och relevanta delar (från både projektet och uppsatsrapport). Alla studenter ska ha läst uppsatsrapporten före seminariet så alla detaljer behöver inte vara relevanta.<span style="color: red;">How will these student's get access to the draft thesis?</span>
</li>
<li lang="sv">Opponenterna opponerar ca 10 min vardera - en opponent i taget. Undvik gärna att upprepa frågor som den andra opponenten redan har ställt. (Alla synpunkter skall stå i den oppositionsrapport som skall lämnas in - senast - dagen före presentationsseminariet. Tag gärna med en kopia och lämna till presentatörerna). Mall för oppositionsrapport finns att hämta i <a id="" class="" title="Mallar/Templates" href="https://kth.instructure.com/courses/1586/pages/mallar-slash-templates" target="" data-api-endpoint="https://kth.instructure.com/api/v1/courses/1586/pages/mallar-slash-templates" data-api-returntype="Page">Mallar/Templates</a>.</li>
<li lang="sv">Aktiva lyssnare skall, åtminstone, ställa en fråga var. De som är aktiva lyssnare bör ha tittat på uppsatsrapporten före seminariet. Glöm inte att varje student skall vara aktiv lyssnare på två andra seminarier än eget presentationsseminarium och oppositionsseminarium (totalt fyra seminarier).</li>
<li lang="sv">Nästa publiken har en chans att ställa frågor om avhandlingen.</li>
<li lang="sv">Slutligen kommer examinator ställa några sista frågor som de har.</li>
<li lang="sv">Se till att ni får bedömningsmallen ifylld! Examinator för presentatörerna signerar dokumentet. Om inte bedömningsmallen blir ifylld vid seminariet går ni miste om seminariet.</li>
</ol>
</div>
</div>''',
        'Examensarbete inlämnande/Final thesis submission':
        '''
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Students should submit the final version of their thesis.</p>
<p lang="en">When the thesis is approved it becomes a public document.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Eleverna ska lämna den slutliga versionen av sin avhandling.</p>
<p lang="sv">När avhandlingen är godkänd blir det en offentlig avhandling.</p>
</div>
</div>'''
        }

    list_of_assignments_with_peer_reviews={
        'Utkast till/Draft for opponent': True
        }

    target_group=False

    # check existing assignment group sets
    existing_assignment_groups=list_assignment_groups(course_id)

    # create an assignment group if necessary
    for ag in existing_assignment_groups:
        if group_name == ag['name']:
            target_group=ag['id']
            break
    if not target_group:
        position=1
        group_weight=0.0
        rules=''
        target_group=create_assignment_group(course_id, group_name, position, group_weight, rules)

    for a in list_of_assignments:
        # if the assignment is also in the list of those with a peer_review, then create it with a peer review
        # note that this means the entry has to be present in the original list_of_assignments (where the text is given) and be present in list_of_assignments_with_peer_reviews - but there does not have to be the text, only an entry 
        if a in list_of_assignments_with_peer_reviews:
            description=list_of_assignments[a]
            create_assignment_with_submission_with_peerreview(course_id, a, '1.0', 'pass_fail', description, target_group)
        else:
            description=list_of_assignments[a]
            create_assignment_with_submission(course_id, a, '1.0', 'pass_fail', description, target_group)

def list_assignment_groups(course_id):
    # GET /api/v1/courses/:course_id/assignment_groups
    assignment_groups_found_thus_far=[]

    url = "{0}/courses/{1}/assignment_groups".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting assignment groups: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            assignment_groups_found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of assignments
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links['current']['url'] != r.links['last']['url']:  
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting assignment groups for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    assignment_groups_found_thus_far.append(p_response)

    return assignment_groups_found_thus_far

def create_assignment_group(course_id, name, position, group_weight, rules):
    # Use the Canvas API to create an assignment
    # POST /api/v1/courses/:course_id/assignment_groups
    url = "{0}/courses/{1}/assignment_groups".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    #
    payload={'name': name,
             'position': position,
             'group_weight': group_weight,
             'rules': rules,
    }
    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post making an assignment group: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if (r.status_code == requests.codes.ok) or (r.status_code == requests.codes.created):
        page_response=r.json()
        print("inserted assignment group: {}".format(name))
        return page_response['id']
    return False



def create_active_listening_assignments(course_id, group_name):
    target_group=False

    # check existing assignment groups
    existing_assignment_groups=list_assignment_groups(course_id)

    # create an assignment group if necessary
    for ag in existing_assignment_groups:
        if group_name == ag['name']:
            target_group=ag['id']
            break
    if not target_group:
        position=2
        group_weight=0.0
        rules=''
        target_group=create_assignment_group(course_id, group_name, position, group_weight, rules)
    print("target_group={}".format(target_group))

    # create the two assignments for recording active listener participation
    assignment_name='aktiva deltagande/active listener'
    assignment_description='''
<p><span lang="en">Active listener</span> (<span lang="sv">Aktiva deltagande i seminarier</span>)</p>
<div class="enhanceable_content tabs">
<ul>
<li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul>
<div id="fragment-en">
<p lang="en">Active listeners shall ask at least one question each. Enter your question or questions below.</p>
</div>
<div id="fragment-sv">
<p lang="sv">Aktiva lyssnare skall, åtminstone, ställa en fråga var. Ange din fråga eller frågor nedan.</p>
</div>
</div>'''
    for i in range(2):
        name="{1}:{0}".format(assignment_name, i+1)
        create_assignment_with_textual_submission(course_id, name, '0.50', 'pass_fail', assignment_description, target_group)

def create_assessment_quiz(course_id, group_name):
    target_group=False

    # check existing assignment groups
    existing_assignment_groups=list_assignment_groups(course_id)

    # create an assignment group if necessary
    for ag in existing_assignment_groups:
        if group_name == ag['name']:
            target_group=ag['id']
            break
    if not target_group:
        position=3
        group_weight=0.0
        rules=''
        target_group=create_assignment_group(course_id, group_name, position, group_weight, rules)

    # Use the Canvas API to create a quiz
    # POST /api/v1/courses/:course_id/quizzes

    # Request Parameters:
    url = "{0}/courses/{1}/quizzes".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    description='''<div class="enhanceable_content tabs">

<ul><li lang="en"><a href="#fragment-en">English</a></li>
<li lang="sv"><a href="#fragment-sv">På svenska</a></li>
</ul><div id="fragment-en"><h1><span lang="en">Master students and Master of Engineering students</span></h1>
<h1><span>Guidelines for quality criteria for assessment of degree projects</span></h1>
<p lang="en">The degree project is assessed with the criteria: <strong>Process, Engineering-related and scientific content, </strong>and<strong> Presentation. </strong>For each criterion there is one or more objectives with the guidelines for quality assessment. The assessment of each objective is either of very high quality (VHQ), good quality (GQ) or insufficient quality (IQ). Observe that a degree project, where one subsidiary objective is considered to be of insufficient quality cannot receive a passing grade.</p>
<p>For more information about the goals, see higher education ordinance:&nbsp;<span><a href="http://www.hsv.se/lawsandregulations/thehighereducationordinance/annex2.4.8b3a8c21372be32ace80003246.html">http://www.hsv.se/lawsandregulations/thehighereducationordinance/annex2.4.8b3a8c21372be32ace80003246.html</a></span></p>
<p lang="en"><em>Degree of Master of Arts/Science (120 credits)&nbsp;&nbsp;[Masterexamen]</em></p>
<p lang="en"><em>Degree of Master of Science in Engineering [Civilingenj&ouml;rsexamen]</em></p>
<p lang="en">For more information about the KTHs criteria, see:&nbsp;<span><a href="https://intra.kth.se/polopoly_fs/1.147277!/Menu/general/column-content/attachment/Bedomningsgrunder%20och%20kriterier-eng.pdf">https://intra.kth.se/polopoly_fs/1.147277!/Menu/general/column-content/attachment/Bedomningsgrunder%20och%20kriterier-eng.pdf</a></span></p>
<p lang="en">Assessment of achievement of objectives is carried out by describing how the objectives have been achieved and where, in the degree project report, the different objectives are included.</p></p></div>
<div id="fragment-sv">
<h1><span lang="sv">Master- och Civilingenjörsstudenter, åk 5</span></h1>
<h1><span lang="sv">Riktlinjer för kvalitetskriterier för bedömning av examensarbete</span></h1>
<p lang="sv">Examensarbetet bedöms med hjälp av kriterierna: Process, Ingenjörsmässigt och vetenskapligt innehåll samt Presentation. För varje kriterium finns ett eller flera mål med riktlinjer för kvalitetsbedömning. Bedömningen av varje mål är antingen godkänd kvalitet (GK) eller bristande kvalitet (BK). Observera att ett examensarbete där ett delmål bedöms ha bristande kvalitet kan inte erhålla godkänt betyg. </p>
<p lang="sv">För mer information om högskoleförordningen 
<a href="https://www.riksdagen.se/sv/Dokument-Lagar/Lagar/Svenskforfattningssamling/Hogskoleforordning-1993100_sfs-1993-100/?bet=1993:100">https://www.riksdagen.se/sv/Dokument-Lagar/Lagar/Svenskforfattningssamling/Hogskoleforordning-1993100_sfs-1993-100/?bet=1993:100</a>
Civilingenjörsexamen<br>
Masterexamen</p>
<p lang="sv">För mer information om KTHs kriterier, se
<a href="https://intra.kth.se/regelverk/utbildning-forskning/grundutbildning/examensarbete/bilaga-a-bedomningsgrunder-och-kriterier-for-examensarbete-1.31698">https://intra.kth.se/regelverk/utbildning-forskning/grundutbildning/examensarbete/bilaga-a-bedomningsgrunder-och-kriterier-for-examensarbete-1.31698</a>
</p>
<p lang="sv">Värdering av måluppfyllnad görs i tabellen genom att beskriva hur målen har uppnåtts och ange vari examensarbetsrapporten de olika målen återfinns. Värderingen skall göras individuellt.</p></div></div>'''
    payload={'quiz[title]': 'Värdering av måluppfyllnad/Assessment of the achievement of objectives',
             'quiz[description]': description,
             'quiz[quiz_type]': 'assignment', # this means it will be graded
             'quiz[hide_results]': '',
             'quiz[show_correct_answers]': 'false',
             'quiz[allowed_attempts]': -1,
             'quiz[scoring_policy]': 'keep_latest',
             'quiz[published]': True,
             'quiz[assignment_group_id]': target_group
    }

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of post making a quiz: {}".format(r.text))
        print("r.status_code={}".format(r.status_code))
    if (r.status_code == requests.codes.created) or (r.status_code == requests.codes.ok):
        page_response=r.json()
        print("inserted quiz")
        return page_response['id']
    return False

def create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, English_text, Swedish_text):
    base_string='<div class="enhanceable_content tabs"><ul>'
    if cycle_number == '2':
        lang_alternatives='<li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en">'
    else:
        lang_alternatives='<li lang="sv"><a href="#fragment-sv">På svenska</a></li><li lang="en"><a href="#fragment-en">English</a></li></ul><div id="fragment-en">'

    div_string='<h3><span  lang="en">' + objective_name_English + ': Assessment</span></h3>'+English_text+'</div><div id="fragment-sv"><h3><span  lang="sv">'+objective_name_Swedish+': Måluppfyllnad</span></h3>'+Swedish_text+'</div>'

    if cycle_number == '2':
        assessment_name=objective_name_English+'/'+objective_name_Swedish
    else:
        assessment_name=objective_name_Swedish+'/'+objective_name_English

    assessment_answers=[{'text': 'GQ/GK', 'comments': '', 'comments_html': '', 'weight': 100.0, 'blank_id': 'Assessment'},
                                             {'text': 'VHQ/MHK', 'comments': '', 'comments_html': '', 'weight': 100.0, 'blank_id': 'Assessment'},
                                             {'text': 'IQ/BK', 'comments': '', 'comments_html': '', 'weight': 0.0, 'blank_id': 'Assessment'}]

    create_question_multiple_choice_with_points(course_id, assessment_quiz, index, assessment_name, 
                                                base_string+lang_alternatives+div_string,
                                                assessment_answers, 1)



def create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish):
    base_string='<div class="enhanceable_content tabs"><ul>'
    if cycle_number == '2':
        lang_alternatives='<li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en">'
        assessment_name=objective_name_English+': Achievement of objectives/'+objective_name_Swedish+': Måluppfyllnad'
    else:
        lang_alternatives='<li lang="sv"><a href="#fragment-sv">På svenska</a></li><li lang="en"><a href="#fragment-en">English</a></li></ul><div id="fragment-en">'
        assessment_name=objective_name_Swedish+': Måluppfyllnad/'+objective_name_English+': Achievement of objectives'

    div_string='<h3><span  lang="en">' + objective_name_English + ': Substantiate Assessment</span></h3><p lang="en">Describe your self-assessment of the objective. Substantiate your statements with arguments.</p></div><div id="fragment-sv"><h3><span  lang="sv">'+objective_name_Swedish+': Motivera bedömning</span></h3><p lang="sv">Här fyller studenten i sin självvärdering av målet. Argumentera.</p></div>'

    create_question_essay(course_id, assessment_quiz, index, assessment_name, base_string+lang_alternatives+div_string) 

def create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish):
    base_string='<div class="enhanceable_content tabs"><ul>'
    if cycle_number == '2':
        lang_alternatives='<li lang="en"><a href="#fragment-en">English</a></li><li lang="sv"><a href="#fragment-sv">På svenska</a></li></ul><div id="fragment-en">'
        assessment_name=objective_name_English+': References/'+objective_name_Swedish+': Hänvisning'
    else:
        lang_alternatives='<li lang="sv"><a href="#fragment-sv">På svenska</a></li><li lang="en"><a href="#fragment-en">English</a></li></ul><div id="fragment-en">'
        assessment_name=objective_name_Swedish+': Hänvisning/'+objective_name_English+': References'


    div_string='<h3><span  lang="en">' + objective_name_English + ': References</span></h3><p lang="en">Refer to the section and the page number in the degree project where the objective is addressed.</p></div><div id="fragment-sv"><h3><span  lang="sv">'+objective_name_Swedish+': Hänvisning</span></h3><p lang="sv">Hänvisning till sektion och sidor i examensarbetet.</p></div>'

    create_question_essay(course_id, assessment_quiz, index, assessment_name, base_string+lang_alternatives+div_string) 


def create_assessments(course_id, cycle_number, group_name):
    index=1
    assessment_quiz=create_assessment_quiz(course_id, group_name)

    # add the quiz to the appropriate module page
    module_id=check_for_module(course_id,  'Gatekeeper protected module 1')
    if Verbose_Flag:
        print("found module to place the quiz in is module_id: {}".format(module_id))
    q_module_id=create_module_quiz_item(course_id, module_id, assessment_quiz, 'Värdering av måluppfyllnad/Assessment of the achievement of objectives', 40)
    if Verbose_Flag:
        print("placed the quiz into module as module item id: {}".format(q_module_id))

    # Process P1
    objective_name_English='Process - Objective P1'
    objective_name_Swedish='Process - Mål P1'
    objective_text_English='''<p lang="en">Demonstrate, with a holistic approach, the ability to critically, independently and creatively identify, formulate, analyse, assess and deal with complex phenomena, issues and situations even with limited information.
</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>The work has a clear and distinct question that can be answered, adequately. There should be a clear link between the question formulation, results and conclusions. Work conclusions are well-founded and accurate.<br>Good ability to independently identify, formulate, analyze, assess and deal with complex phenomena.<br>
<em>Show good ability to put yourself in another's work and formulate relevant and constructive criticism.</em></td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>Additionally, the question (or problem statement) has been sophisticated formulated and the work demonstrates a holistic approach, by having the question formulation (or problem statement) and/or methods extracted from several subjects.<br>
<em>Very good ability to and, with a holistic view, critically, independently and creatively identify, formulate, analyze, assess and handle complex phenomena and question</em> <em>formulation (or problem statement) even with limited information</em></td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>The work has an unclear or missing question formulation (or problem statement) or goal formulation. Irrelevant (a) method(s) are used. The work does not report an answer to the question or the result is not related to the case. The conclusions are incorrect.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">
    Förmåga att med helhetssyn kritiskt, självständigt och kreativt identifiera, formulera, analysera, bedöma och hantera komplexa företeelser och frågeställningar även med begränsad information.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>Arbetet har en tydlig och avgränsad frågeställning som kan besvaras ett adekvat sätt. Det ska finnas en tydlig koppling mellan frågeställning, resultat och slutsatser. Arbetets slutsatser är väl underbyggda och korrekta.<br>
God förmåga att självständigt och kreativt identifiera, formulera, analysera, bedöma och hantera komplexa företeelser.<br>
<em>Visa god förmåga att sätta sig in i ett annat arbete och formulera relevant och konstruktiv kritik.</em></td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>Dessutom har frågeställningen varit kvalificerad och arbetet påvisar helhetssyn, genom att frågeställningen och/eller metoderna hämtats från flera ämnen.<br>
Mycket god förmåga att med helhetssyn kritiskt, självständigt och kreativt identifiera, formulera, analysera, bedöma och hantera komplexa företeelser och frågeställningar även med begränsad information.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Arbetet har en otydlig eller saknar frågeställning eller målformulering. Irrelevant(a) metod(er) används. Arbetet redovisar inte ett svar på frågan eller ett resultat är inte relaterat till målet. Slutsatserna är inkorrekta.</td>
</tr>
</tbody>
</table>'''
    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    # Process P2
    objective_name_English='Process - Objective P2'
    objective_name_Swedish='Process - Mål P2'
    objective_text_English='''<p lang="en">Demonstrate the ability to plan and with adequate methods undertake advanced tasks within predetermined parameters, as well as the ability to evaluate this work.
</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>An elaborated and realistic plan for the work has been formulated. The plan’s schedule (time frame with milestones), which has been communicated and agreed upon, has been followed during the implementation of the work.<br>
If adjustments have been necessary during the implementation of the work, these have been documented and communicated.<br>
<em>Independently plan and execute work within agreed time frames, show initiative and be open to supervision and criticism (feedback).</em></td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>In addition, the student has demonstrated very good planning and compliances of milestones.<br>
<em>Very good ability to plan and carry out advanced tasks within predetermined parameters. Selecting and applying appropriate methods to evaluate this work.</em></td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>Planning has failed and appropriate methods are missing. The plan and the contents have not followed the announced and established schedule (time frame with milestones). Documentation of the relevant factors for the deviations is not reported.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att planera och med adekvata metoder genomföra kvalificerade uppgifter inom givna ramar, samt att utvärdera detta arbete.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>En genomarbetad och realistisk plan för arbetet har formulerats. Planens hålltider, som har kommunicerats och fastställts, ska ha följts vid genomförande av arbetet.<br>
Om anpassningar har varit nödvändiga vid genomförandet av arbetet ska ha dokumenterats och kommunicerats.<br>
<em>Självständigt planera och genomföra arbetet inom överenskomna tidsramar, visa god initiativförmåga samt vara öppen för handledning och kritik.</em>
</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>Dessutom har studenten visat mycket god planering och efterlevnad av hållpunkter.<br>

<em>Mycket god förmåga att planera och genomföra kvalificerade uppgifter inom givna ramar. Välja och applicera adekvata metoder för att utvärdera detta arbete.</em></td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Planeringen har förfallit samt adekvata metoder saknas. Planen och innehåll har inte följt de kommunicerade och fastställda hålltiderna. Dokumentation av relevanta faktorer för avvikelser har ej redovisas.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    # Process P3
    objective_name_English='Process - Objective P3'
    objective_name_Swedish='Process - Mål P3'
    objective_text_English='''<p lang="en">Demonstrate the ability to integrate knowledge critically and systematically, as well as the ability to identify the need for additional knowledge.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>Obtain relevant knowledge and methods and applied them appropriately.<br>
<em>Independently identify own needs for new knowledge and acquire those skills.</em></td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>The evaluation is detailed (for example, several alternative methods are used) and the results are analyzed openly and critically.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>Areas of relevance to the work are not reported or are not used. Selected and acquired knowledge is not reported in a clear way and lacks justification.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att kritiskt och systematiskt integrera kunskap samt förmåga att identifiera behovet av ytterligare kunskap.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>Inhämta relevanta kunskaper och metoder och tillämpat dessa på lämpligt sätt.<br>
<em>Självständigt identifiera egna behov av ny kunskap, samt inhämta dessa kunskaper.</em>
</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>Utvärderingen är utförlig (t.ex. används flera alternativa metoder) och resultaten analyseras öppet och kritiskt.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Områden med relevans för arbetet tas ej upp eller används inte. Valda och inhämtade kunskaper redovisas inte på ett tydligt sätt och saknar motivering.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1


    # Engineering-related and scientific content, IV1-IV7
    objective_name_English='Engineering-related and scientific content - Objective IV1'
    objective_name_Swedish='Ingenjörsmässigt och vetenskapligt innehåll - Mål IV1'
    objective_text_English='''<p lang="en">Demonstrate considerably advanced knowledge within the main field of study/the specialisation for the education, including advanced insight into current research and development work.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>Demonstrate a significant and deeper insight into current research and development in the main field.<br>
The work utilizes knowledge from advanced studies in the main field. A comprehensive review of existing literature, as well as a reflection on the work linked to the frontiers of knowledge in the main field is present.<br>
This work contributes to a clearly recognized way to new knowledge in the main field. The work demonstrates the ability to make an independent contribution to the field.<br>
A written review of existing literature, as well as a reflection on the work linked to the frontiers of knowledge in the main field is presented.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>Additionally, the literature contains a clearer synthesis of past and current research and / or development work that is relevant to the work.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>Work linked to the main field is weak or missing. Knowledge from advanced studies in the main field is not utilized. Summary and of the literature, as well as reflection on the work linked to the associated area of expertise is lacking.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Väsentligt fördjupade kunskaper inom huvudområdet/inriktningen för utbildningen, inkluderande fördjupad insikt i aktuellt forsknings- och utvecklingsarbete.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>Uppvisa en väsentlig och fördjupad insikt i aktuellt forsknings- och utvecklingsarbete inom huvudområdet.<br>
Arbetet utnyttjar kunskaper från studier på avancerad nivå inom huvudområdet. En omfattande genomgång av befintlig litteratur samt en reflektion över arbetets koppling till kunskapsfronten inom huvudområdet finns.<br>
Arbetet bidrar på ett tydligt redovisat sätt till ny kunskap inom huvudområdet.<br>
Arbetet demonstrerar förmåga att ge ett självständigt bidrag till om rådet.<br>
En skriftlig genomgång av befintlig litteratur samt att en reflektion över arbetets koppling till kunskapsfronten inom huvudområdet finns.
</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>Dessutom, genomgången av litteraturen innehåller en tydligare syntes av tidigare forsknings- och/eller utvecklingsarbete som är relevant för arbetet.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Arbetets koppling till huvudområdet är svag eller saknas. Kunskaper från avancerad nivå inom huvudområdet utnyttjas inte.<br>
Litteratursammanställning samt reflektion över arbetets koppling till tillhörande kunskapsområde saknas.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    objective_name_English='Engineering-related and scientific content - Objective IV2'
    objective_name_Swedish='Ingenjörsmässigt och vetenskapligt innehåll - Mål IV2'
    objective_text_English='''<p lang="en">Demonstrate specialised methodological knowledge within the main field of study/the specialisation for the education.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>Demonstrate a deeper methodological knowledge in the main field / focus of the education programme. The relevant engineering or scientific theories and methods have been identified. A well-motivated choice of theories and methods has been made. Selected theories and methods have been applied in an innovative and accurate way.<br>
The degree project including written material uses a deep and broad knowledge of methodologies.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>In addition, selected theories and methods have been applied and / or combined in a more innovative way.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>Selected theories and methods for the work, are irrelevant. The student has not demonstrated that the selected theories, methods are mastered.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Fördjupad metodkunskap inom huvudområdet/inriktningen för utbildningen.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>Uppvisar fördjupad metodkunskap inom huvudområdet/inriktningen för utbildningen. Relevanta ingenjörsmässiga eller vetenskapliga teorier och metoder har identifierats. Ett välmotiverat val av teori och metod har gjorts. Valda teorier och metoder har tillämpats på ett innovativt och korrekt sätt.<br>
Examensarbetet inklusive skrivet material använder en djup och bred metodkunskap.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>Dessutom valda teorier och metoder har tillämpats och/eller kombinerats på ett mer innovativt sätt.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Arbetets valda teorier och metoder saknar relevans. Studenten har inte visat att valda teorier metoder behärskas.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    objective_name_English='Engineering-related and scientific content - Objective IV3'
    objective_name_Swedish='Ingenjörsmässigt och vetenskapligt innehåll - Mål IV3'
    objective_text_English='''<p lang="en">Demonstrate the ability to participate in research and development work and so contribute to the formation of knowledge.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>From problem statement and methodology, show very good ability to systematically apply engineering and scientific skills like problem formulation, modeling, analysis, development and evaluation.<br>
Involved in research and development work and contribute to the development of knowledge by clearly report the contribution to research or development work.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>In addition, the work contributes to the significance knowledge (it should, for example, after processing together with the supervisor, be able to be published in a peer-reviewed conference, or to apply it in practical use for engineering).</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>The work is of such character, where it is difficult to be linked to research or development work.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att delta i forsknings- och utvecklingsarbete och därigenom bidra till kunskapsutvecklingen.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>Utifrån problemställning och metodik, visa mycket god förmåga att på ett systematiskt sätt tillämpa ingenjörsmässiga och vetenskapliga färdigheter som problemformulering, modellering, analys, utveckling och utvärdering.<br>
Deltar i forsknings- och utvecklingsarbete och bidrar till kunskapsutvecklingen genom att tydligt redovisa bidraget till forsknings– eller utvecklingsarbete.
</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>Dessutom arbetet bidrar till ny kunskap av viss större betydelse (det ska exempelvis, efter bearbetning tillsammans med handledaren, kunna publiceras vid en granskad konferens, eller kunna omsättas i ingenjörsmässig praktisk användning).</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Arbetet har haft en sådan karaktär där det svårligen kan kopplas till forsknings– eller utvecklingsarbete.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    objective_name_English='Engineering-related and scientific content - Objective IV4'
    objective_name_Swedish='Ingenjörsmässigt och vetenskapligt innehåll - Mål IV4'
    objective_text_English='''<p lang="en">Demonstrate ability to create, analyse and critically evaluate various technological/architectural solutions, (only for master of engineering students).</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>Good ability to create, analyze and critically evaluate different technical / architectural solutions. The work will demonstrate new solutions that are critically and adequately analyzed and evaluated. Moreover, alternative solutions have been developed, analyzed and presented in a relevant and comprehensive manner.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>The work has not been reported clearly. Alternative solutions are lacking.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att skapa, analysera och kritiskt utvärdera olika tekniska/arkitektoniska lösningar ( endast Civing).</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>God förmåga att skapa, analysera och kritiskt utvärdera olika tekniska/arkitektoniska lösningar. Arbetet ska påvisa nya lösningar som analyseras och utvärderas på ett kritiskt och adekvat sätt. Även alternativa lösningar har tagits fram, analyseras samt presenteras på ett relevant och uttömmande sätt.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Arbetet har inte redovisat ovan på ett tydligt sätt. Alternativa lösningar saknas.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    objective_name_English='Engineering-related and scientific content - Objective IV5'
    objective_name_Swedish='Ingenjörsmässigt och vetenskapligt innehåll - Mål IV5'
    objective_text_English='''<p lang="en">Demonstrate the ability to, within the framework of the specific degree project, identify the issues that need to be answered in order to observe relevant dimensions of sustainable development.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>Identify the question formulations that must be addressed to be able to consider relevant dimensions of sustainable development.<br>
Report and motivate the work and discuss results from a perspective with a focus on sustainable development.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>Not take this aspect into account, despite the fact that the examiner considered to be of importance for the current thesis. This learning outcome can in some cases be irrelevant.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att inom ramen för det specifika examensarbetet kunna identifiera vilka frågeställningar som behöver besvaras för att relevanta dimensioner av hållbar utveckling skall beaktas.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>Identifiera frågeställningar som behöver besvaras för att relevanta dimensioner av hållbar utveckling skall beaktas.<br>
Redovisar och motiverar arbetet och diskuterar resultat utifrån ett perspektiv med fokus på hållbar utveckling.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Beaktar inte denna aspekt, trots att den av examinator bedöms vara av betydelse för det aktuella examensarbetet. Detta lärandemål kan för vissa examensarbete sakna relevans.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    objective_name_English='Engineering-related and scientific content - Objective IV6'
    objective_name_Swedish='Ingenjörsmässigt och vetenskapligt innehåll - Mål IV6'
    objective_text_English='''<p lang="en">Demonstrate the ability to, within the framework of the degree project, assess and show awareness of ethical aspects on research and development work with respect to methods, working methods and the results of the degree project.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>Where it is relevant to the task, show awareness of societal and ethical aspects, including economically, socially and ecologically sustainable development.<br>
Good ability to assess and demonstrate awareness of ethical aspects of research and development work regarding methods, procedures and results of the thesis.<br>
Reports ethical implications of the performed work.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>Takes no account of the ethical aspects, despite the fact that ethical aspects are considered to be relevant for the work.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att inom examensarbetets ramar bedöma och visa medvetenhet om etiska aspekter på forsknings- och utvecklingsarbete vad avser metoder, arbetssätt och resultat av examensarbetet.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>Där så är relevant för uppgiften, visa medvetenhet om samhälleliga och etiska aspekter, inklusive ekonomiskt, socialt och ekologiskt hållbar utveckling.
God förmåga att bedöma och visa medvetenhet om etiska aspekter på forsknings- och utvecklingsarbete vad avser metoder, arbetssätt och resultat av examensarbetet.<br>
Redovisar etiska konsekvenser av utfört arbete.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Beaktar inte etiska aspekter, trots att etiska aspekterna bedöms vara relevanta för arbetet.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    objective_name_English='Engineering-related and scientific content - Objective IV7'
    objective_name_Swedish='Ingenjörsmässigt och vetenskapligt innehåll - Mål IV7'
    objective_text_English='''<p lang="en">Demonstrate the ability to, within the framework of the degree project, identify the role of science and the engineer in the society.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td>In an independent way, identify science and engineer's role in society. Implemented the degree project course without extraordinary support or adjustments or otherwise required extra large resources for carrying out the work.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>Cannot by him- or herself prove science and the role of the engineer in society. Requires great need of support during project implementation.<br>
These supports have been too broad to ensure that students can work independently after graduation.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att inom examensarbetets ramar identifiera vetenskapens och ingenjörens roll i samhället.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td>På ett självständigt sätt identifiera vetenskapens och ingenjörens roll i samhället. Genomfört examensarbetet utan extraordinära stödinsatser eller anpassningar eller på annat sätt inte krävt extra stora resurser för arbetets genomförande.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Kan inte på egen hand påvisa vetenskapens och ingenjörens roll i samhället. Kräver stort behov av stödinsatser under projektets genomförande.<br>
Dessa stödinsatser har varit för omfattande för att kunna garantera att studenten kan arbeta självständigt efter examen.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    # Presentation
    objective_name_English='Presentation - Pres 1'
    objective_name_Swedish='Presentation - Pres 1'
    objective_text_English='''<p lang="en">Demonstrate the ability to, in English, clearly present and discuss his or her conclusions and the knowledge and arguments on which they are based in speech and writing to different audiences.</p>
<h4><span lang="en">Assessment criteria</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GQ</strong></td>
<td><em>Written report.</em> Show a very well written and well disposed report, with a clear statement of work and results, clear analysis and well substantiated arguments, as well as good language processing, formal and scientific accuracy.<br><br>

<em>Oral presentation.</em> Show ability to orally present with clear reasoning and analysis, and good ability to discuss work.<br><br>

The written material treats the selected area with a relevant and correct language.<br><br>

<em>Opposition.</em> The Opposition protocol (opposition report) is clearly and fully completed. Respondent's report has been valued critically, with strengths and weaknesses identified. Relevant and constructive suggestions for improvement have been given.<br>

The written opposition also has been given such relevant and realistic suggestions for improvement that the report clearly can be improved if they are followed. Estimates of the report is thorough and reviewing work methods, results and evaluation in a way that demonstrates the opponent's own in-depth knowledge in the main field.</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>VHQ</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>IQ</strong></td>
<td>The work lacks essentially adequate language processing, which makes the work difficult to understand, or poorly judged based on the report.</td>
</tr>
</tbody>
</table>'''
    objective_text_Swedish='''<p lang="sv">Förmåga att på engelska och/eller svenska muntligt och skriftligt klart redogöra för och diskutera sina slutsatser, samt den kunskap och de argument som ligger till grund för dessa.</p>
<h4><span lang="en">Bedömningskriterier</span></h4>
<table>
<tbody>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>GK</strong></td>
<td><em>Skriftlig rapport:</em> Uppvisa mycket välskriven och väldisponerad rapport, med tydlig redovisning av arbete och resultat, klar analys och väl underbyggd argumentation, samt god språkbehandling, formalia och vetenskaplig noggrannhet.<br><br>
<em>Muntlig presentation:</em> Visa god förmåga att muntligt redovisa med tydlig argumentation och analys, samt god förmåga att diskutera arbetet.<br><br>
Det skrivna materialet behandlar det valda området med ett relevant och korrekt språkbruk.<br><br>
<em>Opposition:</em> Oppositionsprotokollet är tydligt och fullständigt ifyllt. Respondentens rapport har värderats kritiskt, med styrkor och eventuella svagheter identifierade. Relevanta och konstruktiva förbättringsförslag har givits.<br><br>
Den skriftliga oppositionen har dessutom givits sådana relevanta och realistiska förbättringsförslag att rapporten tydligt kan förbättras om de följs. Värderingen av rapporten är fördjupad och granskar arbetets metod, resultat och utvärdering på ett sätt som påvisar opponentens egen fördjupade kunskap inom huvudområdet.
</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>MHK</strong></td>
<td>-</td>
</tr>
<tr>
<td style="width: 55px; vertical-align: top;"><strong>BK</strong></td>
<td>Arbetet saknar i huvudsak adekvat språkbehandling vilket gör att arbetet svårbegripligt eller bedömas undermåligt med rapporten som underlag.</td>
</tr>
</tbody>
</table>'''

    create_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish, objective_text_English, objective_text_Swedish)
    index += 1

    create_substantiate_assessment(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1

    create_assessment_reference(course_id, assessment_quiz, index, cycle_number, objective_name_English, objective_name_Swedish)
    index += 1


def list_features_for_course(course_id):
    list_of_all_features=[]
    # Use the Canvas API to get the list of external tools for this course
    # GET /api/v1/courses/:course_id/features
    url = "{0}/courses/{1}/features".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: " + url)

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting list of features: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        tool_response=r.json()
    else:
        print("No features for course_id: {}".format(course_id))
        return False


    for t_response in tool_response:  
        list_of_all_features.append(t_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links['current']['url'] != r.links['last']['url']:  
            r = requests.get(r.links['next']['url'], headers=header)  
            response = r.json()  
            for f_response in response:  
                list_of_all_features.append(f_response)

    return list_of_all_features


def set_features_for_course(course_id, feature, state):
    # PUT /api/v1/courses/:course_id/features/flags/:feature    
    url = "{0}/courses/{1}/features/flags/{2}".format(baseUrl, course_id, feature)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'state': state }
    r = requests.put(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of setting feature: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return []

def list_root_outcome_groups_for_couurse(course_id):
    # Use the Canvas API to get the root outcome group for the course
    #GET /api/v1/courses/:course_id/root_outcome_group

    url = "{0}/courses/{1}/root_outcome_group".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting root outcome group: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response

    return []

def list_outcomes_groups(course_id):
    found_thus_far=[]
    # Use the Canvas API to get the list of outcome groups for the course
    #GET /api/v1/courses/:course_id/outcome_groups

    url = "{0}/courses/{1}/outcome_groups".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting outcome groups: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of assignments
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links['current']['url'] != r.links['last']['url']:  
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting outcome groups for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    found_thus_far.append(p_response)

    return found_thus_far

def list_outcomes_subgroups(course_id, subgroup_id):
    found_thus_far=[]
    # Use the Canvas API to get the list of outcome subgroups for the course
    #GET /api/v1/courses/:course_id/outcome_groups/:id/subgroups

    url = "{0}/courses/{1}/outcome_groups/{2}/subgroups".format(baseUrl, course_id, subgroup_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting outcome subgroup: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of assignments
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links['current']['url'] != r.links['last']['url']:  
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting outcome subgroups for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    found_thus_far.append(p_response)

    return found_thus_far

def already_existing_OutcomeGroup(name, list_of_subgroups):
    for g in list_of_subgroups:
        if g['title'] == name:
            return g['id']
    return []

def create_outcomes_subgroup(course_id, group_id, name, description):
    # Use the Canvas API to get create an outcome subgroup for the course
    # POST /api/v1/courses/:course_id/outcome_groups/:id/subgroups
    # Creates a new empty subgroup under the outcome group with the given title and description.
    # Request Parameters:
    # Parameter		        Type	Description
    # title	Required	string	The title of the new outcome group.
    # description		string	The description of the new outcome group.
    # vendor_guid		string	A custom GUID for the learning standard

    url = "{0}/courses/{1}/outcome_groups/{2}/subgroups".format(baseUrl, course_id, group_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'title': name,
             'description': description,
             #'vendor_guid': xxx,
    }

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of creating outcomean  subgroup: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

    return page_response

def list_outcome(id):
    # Use the Canvas API to get the an outcome
    #GET /api/v1/outcomes/:id

    url = "{0}/outcomes/{1}".format(baseUrl, id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting outcome: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response

    return []

def create_one_outcome(course_id, group_id, name, description, display_name, ratings, calculation_method):
    # Use the Canvas API to create an outcome
    # POST /api/v1/courses/:course_id/outcome_groups/:id/outcomes
    # Parameter		Type	Description
    # outcome_id	integer	The ID of the existing outcome to link.
    # move_from		integer	The ID of the old outcome group. Only used if outcome_id is present.
    # title		string	The title of the new outcome. Required if outcome_id is absent.
    # display_name	string	A friendly name shown in reports for outcomes with cryptic titles, such as common core standards names.
    # description	string	The description of the new outcome.
    # vendor_guid	string	A custom GUID for the learning standard.
    # mastery_points	integer	The mastery threshold for the embedded rubric criterion.
    # ratings[][description]	string	The description of a rating level for the embedded rubric criterion.
    # ratings[][points]		integer	The points corresponding to a rating level for the embedded rubric criterion.
    # calculation_method	string	The new calculation method. Defaults to “decaying_average”
    #                                   Allowed values: decaying_average, n_mastery, latest, highest
    # calculation_int		integer	The new calculation int. Only applies if the calculation_method is “decaying_average” or “n_mastery”. Defaults to 65

    url = "{0}/courses/{1}/outcome_groups/{2}/outcomes".format(baseUrl, course_id, group_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'title': name,
             'description': description,
             'display_name': display_name,
             'mastery_points': 3,
             'ratings': ratings,
             #'ratings[][description]': ['Does Not Meet Expectations', 'Meets Expectations', 'Exceeds Expectations'],
             #'ratings[][points]': [0, 3, 5],
             #'ratings': [{"points":5, "description":"Exceeds Expectations"},{"points":3, "description":"Meets Expectations"},{"points":0, "description":"Does Not Meet Expectations"}],
             'calculation_method': calculation_method,
    }

    # payload['calculation_int']=calculation_int

    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of creating an outcome: {}".format(r.text))

    if Verbose_Flag:
        print("r.status_code = {}".format(r.status_code))
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response

    return []

def list_rubrics(course_id):
    # Use the Canvas API to get the rubrics for a course
    # GET /api/v1/courses/:course_id/rubrics

    url = "{0}/courses/{1}/rubrics".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting rubrics: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response

    return []

def create_a_rubric_for_an_assignment(course_id, assignment_id, outcome_id, name, description):
    # Use the Canvas API to create a rubric
    # POST /api/v1/courses/:course_id/rubrics
    url = "{0}/courses/{1}/rubrics".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    # Parameter					Type	Description
    # id					integer	The id of the rubric
    # rubric_association_id			integer	The id of the object with which this rubric is associated
    # rubric[title]				string	no description
    # rubric[free_form_criterion_comments]	boolean	no description
    # rubric_association[association_id]	integer	The id of the object with which this rubric is associated
    # rubric_association[association_type]	string	The type of object this rubric is associated with
    #                                                   Allowed values: Assignment, Course, Account
    # rubric_association[use_for_grading]	boolean	no description
    # rubric_association[hide_score_total]	boolean	no description
    # rubric_association[purpose]		string	no description
    # rubric[criteria]				Hash	An indexed Hash of RubricCriteria objects where the keys are integer ids and the values are the RubricCriteria objects

    payload={'rubric':
             {'title': name,
              'description': description, # internally this is a 'long_description'
              'free_form_criterion_comments': 'false',
              #'ignore_for_scoring': 'false', # this is optional
              #'criterion_use_range': 'false', # this is optional
              'criteria': {
                  '0': {
                      'points': 5,
                      'mastery_points': 3,     # this is optional
                      'description': name,
                      'long_description': description,    # this is optional
                      #'ignore_for_scoring': 'false', # this is optional
                      #'criterion_use_range': 'true', # this is optional
                      'learning_outcome_id': outcome_id,
                  }
                  }
             },
             #'rubric_association_id':
             #'learning_outcome_id': outcome_id,
             'rubric_association': {
                 'association_type': 'Assignment',
                 'association_id': assignment_id,
                 'purpose': 'grading'
             }
    }

    if Verbose_Flag:
        print("payload={}".format(payload))
    r = requests.post(url, headers = header, json=payload)
    if Verbose_Flag:
        print("result of creating a rubric: {}".format(r.text))

    if Verbose_Flag:
        print("r.status_code = {}".format(r.status_code))
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return []

def create_outcomes_and_rubrics(course_id):
    root_outcome_group=list_root_outcome_groups_for_couurse(course_id)
    existing_subgroups=list_outcomes_subgroups(course_id, root_outcome_group['id'])
    if Verbose_Flag:
        print("existing_subgroups is {}".format(existing_subgroups))
    process_OutcomeGroup=already_existing_OutcomeGroup('Process', existing_subgroups)
    if not process_OutcomeGroup:
        process_OutcomeGroup=create_outcomes_subgroup(course_id, root_outcome_group['id'], 'Process', '<p>Process related outcomes.</p><p>Processrelaterade lärandemål.</p>')

    content_OutcomeGroup=already_existing_OutcomeGroup('Engineering-related and scientific content', existing_subgroups)
    if not content_OutcomeGroup:
        content_OutcomeGroup=create_outcomes_subgroup(course_id, root_outcome_group['id'], 'Engineering-related and scientific content',
                                                      '<p><span lang="en">Engineering-related and scientific content related outcomes.</span> | <span lang="sv">Ingenjörsmässigt och vetenskapligt innehåll</span></p>')

    presentation_OutcomeGroup=already_existing_OutcomeGroup('Presentation', existing_subgroups)
    if not presentation_OutcomeGroup:
        presentation_OutcomeGroup=create_outcomes_subgroup(course_id, root_outcome_group['id'], 'Presentation', '<p><span lang="en">Presentation related outcomes</span> | <span lang="sv">Presentation relaterade resultat</span></p>')

    existing_subgroups=list_outcomes_subgroups(course_id, root_outcome_group['id'])
    if Verbose_Flag:
        print("final existing_subgroups is {}".format(existing_subgroups))

    ratings=[{'description': 'Exceeds Expectations', 'points': 5}, {'description': 'Meets Expectations', 'points': 3}, {'description': 'Does Not Meet Expectations', 'points': 0}]

    description=' <p>Demonstrate, with a holistic approach, the ability to critically, independently and creatively identify, formulate, analyse, assess and deal with complex phenomena, issues and situations even with limited information.</p><p>Förmåga att med helhetssyn kritiskt, självständigt och kreativt identifiera, formulera, analysera, bedöma och hantera komplexa företeelser och frågeställningar även med begränsad information.</p>'
    outcome_result=create_one_outcome(course_id, process_OutcomeGroup, 'P1', description, 'identify, formulate, analyse, assess and deal with', ratings, 'highest')
    if Verbose_Flag:
        print("P1 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate the ability to plan and with adequate methods undertake advanced tasks within predetermined parameters, as well as the ability to evaluate this work.</p><p>Förmåga att planera och med adekvata metoder genomföra kvalificerade uppgifter inom givna ramar, samt att utvärdera detta arbete.</p>'
    outcome_result=create_one_outcome(course_id, process_OutcomeGroup, 'P2', description, 'Plan+Methods', ratings, 'highest')
    if Verbose_Flag:
        print("P2 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate the ability to integrate knowledge critically and systematically, as well as the ability to identify the need for additional knowledge.</p><p>Förmåga att kritiskt och systematiskt integrera kunskap samt förmåga att identifiera behovet av ytterligare.</p>'
    outcome_result=create_one_outcome(course_id, process_OutcomeGroup, 'P3', description, 'Integrate knowledge', ratings, 'highest')
    if Verbose_Flag:
        print("P3 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate considerably advanced knowledge within the main field of study/the specialisation for the education, including advanced insight into current research and development work.</p><p>Väsentligt fördjupade kunskaper inom huvudområdet/inriktningen för utbildningen, inkluderande fördjupad insikt i aktuellt forsknings- och utvecklingsarbete.</p>'
    outcome_result=create_one_outcome(course_id, content_OutcomeGroup, 'IV1', description, 'advanced knowledge', ratings, 'highest')
    if Verbose_Flag:
        print("IV1 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate specialised methodological knowledge within the main field of study/the specialisation for the education.</p><p>Fördjupad metodkunskap inom huvudområdet/inriktningen för utbildningen,</p>'
    outcome_result=create_one_outcome(course_id, content_OutcomeGroup, 'IV2', description, 'methodological knowledge', ratings, 'highest')
    if Verbose_Flag:
        print("IV2 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate the ability to participate in research and development work and so contribute to the formation of knowledge.</p><p>Förmåga att delta i forsknings- och utvecklingsarbete och därigenom bidra till kunskapsutvecklingen.</p>'
    outcome_result=create_one_outcome(course_id, content_OutcomeGroup, 'IV3', description, 'participate \u0026 contribute', ratings, 'highest')
    if Verbose_Flag:
        print("IV3 outcome_result={}".format(outcome_result))


    description='<p>Demonstrate ability to create, analyse and critically evaluate various technological/architectural solutions.</p><p>(Observe – this only concerns Master of Science in Engineering students)</p><p>Förmåga att skapa, analysera och kritiskt utvärdera olika tekniska/arkitektoniska lösningar (endast Civing).</p>'
    outcome_result=create_one_outcome(course_id, content_OutcomeGroup, 'IV4', description, 'create, analyse and critically evaluate', ratings, 'highest')
    if Verbose_Flag:
        print("IV4 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate the ability to, within the framework of the specific degree project, identify the issues that need to be answered in order to observe relevant dimensions of sustainable development.</p><p>Förmåga att inom ramen för det specifika examensarbetet kunna identifiera vilka frågeställningar som behöver besvaras för att relevanta dimensioner av hållbar utveckling skall beaktas.</p>'
    outcome_result=create_one_outcome(course_id, content_OutcomeGroup, 'IV5', description, 'sustainable development', ratings, 'highest')
    if Verbose_Flag:
        print("IV5 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate the ability to, within the framework of the degree project, assess and show awareness of ethical aspects on research and development work with respect to methods, working methods and the results of the degree project.</p><p>Förmåga att inom examensarbetets ramar bedöma och visa medvetenhet om etiska aspekter på forsknings- och utvecklingsarbete vad avser metoder, arbetssätt och resultat av examensarbetet.</p>'
    outcome_result=create_one_outcome(course_id, content_OutcomeGroup, 'IV6', description, 'awareness of ethical aspects', ratings, 'highest')
    if Verbose_Flag:
        print("IV6 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate the ability to, within the framework of the degree project, identify the role of science and the engineer in the society.</p><p>Förmåga att inom examensarbetets ramar identifiera vetenskapens och ingenjörens roll i samhället.</p>'
    outcome_result=create_one_outcome(course_id, content_OutcomeGroup, 'IV7', description, 'role in the society', ratings, 'highest')
    if Verbose_Flag:
        print("IV7 outcome_result={}".format(outcome_result))

    description='<p>Demonstrate the ability to, in English, clearly present and discuss his or her conclusions and the knowledge and arguments on which they are based in speech and writing to different audiences.</p><p>Förmåga att på engelska och/eller svenska muntligt och skriftligt klart redogöra för och diskutera sina slutsatser, samt den kunskap och de argument som ligger till grund för dessa.</p>'
    outcome_result=create_one_outcome(course_id, presentation_OutcomeGroup, 'Pres1', description, 'Effective Written and Oral communication', ratings, 'highest')
    if Verbose_Flag:
        print("Pres1 outcome_result={}".format(outcome_result))
    
def main():
    global Verbose_Flag

    default_picture_size=128

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )
    parser.add_option("--config", dest="config_filename",
                      help="read configuration from FILE", metavar="FILE")

    parser.add_option('-C', '--containers',
                      dest="containers",
                      default=False,
                      action="store_true",
                      help="for the container enviroment in the virtual machine"
    )

    parser.add_option('-m', '--modules',
                      dest="modules",
                      default=False,
                      action="store_true",
                      help="create the two basic modules"
    )

    parser.add_option('-p', '--pages',
                      dest="pages",
                      default=False,
                      action="store_true",
                      help="create the basic pages"
    )

    parser.add_option('-s', '--survey',
                      dest="survey",
                      default=False,
                      action="store_true",
                      help="create the survey"
    )

    parser.add_option('-S', '--sections',
                      dest="sections",
                      default=False,
                      action="store_true",
                      help="create sections for examiners and programs"
    )

    parser.add_option('-c', '--columns',
                      dest="columns",
                      default=False,
                      action="store_true",
                      help="create the custom columns"
    )

    parser.add_option('-a', '--assignments',
                      dest="assignments",
                      default=False,
                      action="store_true",
                      help="create the basic assignments"
    )

    parser.add_option('-o', '--objectives',
                      dest="objectives",
                      default=False,
                      action="store_true",
                      help="create the objectives"
    )


    parser.add_option('-t', '--testing',
                      dest="testing",
                      default=False,
                      action="store_true",
                      help="execute test code"
    )


    parser.add_option('-A', '--all',
                      dest="all_features",
                      default=False,
                      action="store_true",
                      help="create the whole course"
    )


    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))
        print("Configuration file : {}".format(options.config_filename))

    initialize(options)

    if options.all_features:    # do it all
        options.modules=True
        options.dest=True
        options.survey=True
        options.sections=True
        options.columns=True
        options.pages=True
        options.assignments=True
        options.objectives=True

        
    if (len(remainder) < 5):
        print("Insuffient arguments - must provide cycle_number course_id school_acronym course_code program_code")
        sys.exit()
    else:
        cycle_number=remainder[0] # note that cycle_number is a string with the value '1' or '2'
        course_id=remainder[1]
        school_acronym=remainder[2]
        course_code=remainder[3]
        program_code=remainder[4]

        if (options.survey or options.sections) and (len(remainder) > 2):
            school_acronym=remainder[2]
            inputfile_name="course-data-{0}-cycle-{1}.json".format(school_acronym, cycle_number)
            try:
                with open(inputfile_name) as json_data_file:
                    all_data=json.load(json_data_file)
            except:
                print("Unable to open course data file named {}".format(inputfile_name))
                print("Please create a suitable file by running the program get-degree-project-course-data.py")
                sys.exit()
            
            cycle_number_from_file=all_data['cycle_number']
            school_acronym_from_file=all_data['school_acronym']
            if not ((cycle_number_from_file == cycle_number) and (school_acronym_from_file == school_acronym)):
                print("mis-match between data file and arguments to the program")
                sys.exit()

            programs_in_the_school_with_titles=all_data['programs_in_the_school_with_titles']
            dept_codes=all_data['dept_codes']
            all_course_examiners=all_data['all_course_examiners']
            AF_courses=all_data['AF_courses']
            PF_courses=all_data['PF_courses']
            relevant_courses_English=all_data['relevant_courses_English']
            relevant_courses_Swedish=all_data['relevant_courses_Swedish']


    # for a single course these are not needed
    # if options.modules:
    #     create_basic_modules(course_id)

    existing_modules=list_modules(course_id)
    if Verbose_Flag:
        if existing_modules:
            print("existing_modules={0}".format(existing_modules))

    if options.survey or options.sections:
        if Verbose_Flag:
            print("school_acronym={}".format(school_acronym))
        if Verbose_Flag:
            print("dept_codes={}".format(dept_codes))

        if Verbose_Flag:
            print("relevant_courses English={0} and Swedish={1}".format(relevant_courses_English, relevant_courses_Swedish))
            # relevant courses are of the format:{'code': 'II246X', 'title': 'Degree Project in Computer Science and Engineering, Second Cycle', 'href': 'https://www.kth.se/student/kurser/kurs/II246X?l=en', 'info': '', 'credits': '30.0', 'level': 'Second cycle', 'state': 'ESTABLISHED', 'dept_code': 'J', 'department': 'EECS/School of Electrical Engineering and Computer Science', 'cycle': '2', 'subject': 'Degree Project in Computer Science and Engineering'},

        if Verbose_Flag:
            print("PF_courses={0} and AF_courses={1}".format(PF_courses, AF_courses))
   
        all_examiners=set()
        for e in all_course_examiners[course_code]:
            all_examiners.add(e)

    # if options.survey:
    #     create_survey(course_id, cycle_number, school_acronym, PF_courses, AF_courses, relevant_courses_English, relevant_courses_Swedish, all_examiners, all_course_examiners)

    if options.sections:
        # create a section for student awaiting the assignment of an examiner
        create_sections_in_course(course_id, ["Awaiting Assignment of Examiner"])

        #create_sections_for_examiners_and_programs(course_id, all_examiners, programs_in_the_school_with_titles)
        create_sections_in_course(course_id, sorted(all_examiners))

        program_names=[]
        program_names.append("Program: {0}-{1}".format(program_code, programs_in_the_school_with_titles[program_code]['title_en'] ))
        create_sections_in_course(course_id, program_names)


    if options.columns:
        create_custom_columns(course_id, cycle_number)
        
    if options.pages:
        create_basic_pages(course_id, cycle_number, existing_modules)
        
    if options.assignments:
        create_basic_assignments(course_id, 'Assignments/Uppgifter')
        create_active_listening_assignments(course_id, 'Active listener group')

        # the following creates the self-assessment quiz
        create_assessments(course_id, cycle_number, 'Assignments/Uppgifter')

    if options.objectives:
        outcome_gradebook_enabled=False
        # check that the outcome_gradebook is enabled
        existing_features=list_features_for_course(course_id)
        for f in existing_features:
            if f['feature'] == 'outcome_gradebook':
                # check if the feature is on
                if f['feature_flag']['state'] == 'on':
                    print("feature {0} is already on".format('outcome_gradebook'))
                    outcome_gradebook_enabled=True
                    break

                # feature is off
                if f['feature_flag']['locked']:
                    print("feature {0} is locked".format(feature))
                    break
                # check if transition is allowed
                if f['feature_flag']['transitions']['on']['locked'] == False:
                    # time to set the state to on
                    output=set_features_for_course(course_id, 'outcome_gradebook', 'on')
                    outcome_gradebook_enabled=True
                    break

        if outcome_gradebook_enabled:
            print("Objectives to be implemented")
            create_outcomes_and_rubrics(course_id)

    if options.testing:
        print("testing for course_id={}".format(course_id))
        assignments=list_assignments(course_id)
        if Verbose_Flag:
            print("assignments {}".format(assignments))
        rubrics=list_rubrics(course_id)
        print("rubrics {}".format(rubrics))
        for a in assignments:
            if a['name'] == 'Presentationsseminarium/Presentation seminar':
                presentation_assignment_id=a['id']
                print("presentation_assignment_id is {}".format(presentation_assignment_id))
        outcome_id=1103
        result=create_a_rubric_for_an_assignment(course_id, presentation_assignment_id, outcome_id, 'Presentation outcome', 'Just a short description of the presentation outcome')
        print("result is {}".format(result))

if __name__ == "__main__": main()

