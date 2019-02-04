#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./get-degree-project-course-data.py cycle_number school_acronym
#
# Output: produces a file containing all of the data about courses, examiners, etc. This can then be used by other programs.
# The filë́s name is of the form: course-data-{school_acronym}-cycle-{cycle_number}.json
#
#
# Input
# cycle_number is either 1 or 2 (1st or 2nd cycle)
#
# "-t" or "--testing" to enable small tests to be done
# 
#
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./setup-degree-project-course.py --config config-test.json 1 EECS
#
# Example for a 2nd cycle course for EECS:
#
# ./get-degree-project-course-data.py --config config-test.json 2 EECS
#
# G. Q. Maguire Jr.
#
#
# 2019.02.04
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

def v1_get_programmes():
    global Verbose_Flag
    #
    # Use the KOPPS API to get the data
    # GET /api/kopps/v1/course/{course code}
    # note that this returns XML
    url = "{0}/api/kopps/v1/programme".format(KOPPSbaseUrl)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting v1 programme: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        return r.text           # simply return the XML
    #
    return None

def programs_and_owner_and_titles():
    programs=v1_get_programmes()
    xml=BeautifulSoup(programs, "lxml")
    program_and_owner_titles=dict()
    for prog in xml.findAll('programme'):
        if prog.attrs['cancelled'] == 'false':
            owner=prog.owner.string
            titles=prog.findAll('title')
            title_en=''
            title_sv=''
            for t in titles:
                if t.attrs['xml:lang'] == 'en':
                    title_en=t.string
                if t.attrs['xml:lang'] == 'sv':
                    title_sv=t.string
            program_and_owner_titles[prog.attrs['code']]={'owner': owner, 'title_en': title_en, 'title_sv': title_sv}
    #
    return program_and_owner_titles

def programs_and_owner():
    programs=v1_get_programmes()
    xml=BeautifulSoup(programs, "lxml")
    program_and_owner=dict()
    for prog in xml.findAll('programme'):
        if prog.attrs['cancelled'] == 'false':
            program_and_owner[prog.attrs['code']]=prog.owner.string
    #
    return program_and_owner

def programs_in_school(programs, school_acronym):
    programs_in_the_school=list()
    #
    for p in programs:
        if programs[p]['owner'] == school_acronym:
            programs_in_the_school.append(p)
    return programs_in_the_school

def programs_in_school_with_titles(programs, school_acronym):
    relevant_programs=dict()
    #
    for p in programs:
        if programs[p]['owner'] == school_acronym:
            relevant_programs[p]=programs[p]
    return relevant_programs

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

def get_course_info(course_code):
    global Verbose_Flag
    # Use the KOPPS API to get the data
    # GET /api/kopps/v2/course/{course code}
    url = "{0}/api/kopps/v2/course/{1}".format(KOPPSbaseUrl, course_code)
    if Verbose_Flag:
        print("url: {}".format(url))
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting course info: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    #
    return None



def get_course_rounds_info(course_code, r_info):
#Course round
#Returns information about a course round with specified course code, term, and Ladok round id.
#/api/kopps/v1/course/{course code}/round/{year}:{term (1/2)}/{round id}/{language (en|sv)}
# E.g. /api/kopps/v1/course/HS1735/round/2010:1/2
#https://www.kth.se/api/kopps/v1/course/II2202/round/2018:2/1
    global Verbose_Flag
    #
    if Verbose_Flag:
        print("get_course_rounds_info({0},{1})".format(course_code, r_info))
    round_id=r_info['n']
    startTerm=r_info['startTerm']
    year=startTerm[0:4]
    term=startTerm[4]
    if Verbose_Flag:
        print("get_course_rounds_info: round_id={0}, year={1}, term={2})".format(round_id, year, term))
    # Use the KOPPS API to get the data
    # GET /api/kopps/v1/course/{course code}/round/{year}:{term (1/2)}/{round id}/{language (en|sv)}
    # note that this returns XML
    url = "{0}/api/kopps/v1/course/{1}/round/{2}:{3}/{4}".format(KOPPSbaseUrl, course_code, year, term, round_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting course round info: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        return r.text           # simply return the XML
    #
    return None

def v1_get_course_info(course_code):
    global Verbose_Flag
    #
    # Use the KOPPS API to get the data
    # GET /api/kopps/v1/course/{course code}
    # note that this returns XML
    url = "{0}/api/kopps/v1/course/{1}".format(KOPPSbaseUrl, course_code)
    if Verbose_Flag:
        print("url: {}".format(url))
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting v1 course info: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        return r.text           # simply return the XML
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

# returns a list of courses in the format: {'code': 'IL246X', 'title': 'Examensarbete inom elektroteknik, avancerad nivå', 'href': 'https://www.kth.se/student/kurser/kurs/IL246X', 'info': '', 'credits': '30,0', 'level': 'Avancerad nivå', 'state': 'ESTABLISHED', 'dept_code': 'J', 'department': 'EECS/Skolan för elektroteknik och datavetenskap', 'cycle': '2', 'subject': 'elektroteknik'}
def degree_project_courses(requested_dept_codes, language_code):
    global Verbose_Flag
    courses=[]                  # initialize the list of courses
    if len(requested_dept_codes) > 0:
        for d in requested_dept_codes:
            courses_d_all=get_dept_courses(d, language_code)
            courses_d=courses_d_all['courses']
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
                    courses.append(c)
                else:
                    continue
    else:
        return []
    return courses

def course_examiners(courses):
    global Verbose_Flag
    # get the examiners
    courses_info=dict()
    for c in courses:
        c_info=v1_get_course_info(c)
        xml=BeautifulSoup(c_info, "lxml")
        examiners=list()
        for examiner in xml.findAll('examiner'):
            examiners.append(examiner.string)
        courses_info[c]=examiners
    return courses_info

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

# returns a dict with the format:  {'II226X': 'AF', 'II246X': 'PF'}
# note that each of the course codes will only have one instance in the list
def course_gradingscale(courses):
    global Verbose_Flag
    # get the grading scale used for the course
    courses_info = dict()
    for c in courses:
        c_info=v1_get_course_info(c)
        xml=BeautifulSoup(c_info, "lxml")
        for gradingscale in xml.findAll('gradescalecode'):
            courses_info[c]="{}".format(gradingscale.string)
            if Verbose_Flag:
                print("gradingscale: {0}".format(gradingscale))
    return courses_info

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
    course_code_description='<div class="enhanceable_content tabs"><ul><li lang="en"><a href="#fragment-1">English</a></li><li lang="sv"><a href="#fragment-2">På svenska</a></li></ul><div id="fragment-1"><p lang="en"><table border="1" cellspacing="1" cellpadding="1"><tbody>'
    table_heading='<tr><th>Course Code</th><th>Credits</th><th>Name</th></tr>'
    course_code_description=course_code_description+table_heading

    for i in sorted(pf_courses):
        #table_row='<tr><td>'+str(i)+'</td><td>'+credits_for_course(i, courses_english)+'</td><td lang="en">'+title_for_course(i, courses_english)+'</td></tr>'
        table_row='<tr><td>{0}</td><td>{1}</td><td lang="en">{2}</td></tr>'.format(i, credits_for_course(i, courses_english), title_for_course(i, courses_english))
        course_code_description=course_code_description+table_row
    # end of table
    course_code_description=course_code_description+'</tbody></table></div><div id="fragment-2"><table border="1" cellspacing="1" cellpadding="1"><tbody>'
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


# programme_syllabi('CINTE')
# ['https://www.kth.se/student/kurser/program/CINTE/20192/arskurs1', 'https://www.kth.se/student/kurser/program/CINTE/20182/arskurs1', 'https://www.kth.se/student/kurser/program/CINTE/20172/arskurs2', 'https://www.kth.se/student/kurser/program/CINTE/20162/arskurs3', 'https://www.kth.se/student/kurser/program/CINTE/20152/arskurs4', 'https://www.kth.se/student/kurser/program/CINTE/20142/arskurs5', 'https://www.kth.se/student/kurser/program/CINTE/20132/arskurs5', 'https://www.kth.se/student/kurser/program/CINTE/20122/arskurs5', 'https://www.kth.se/student/kurser/program/CINTE/20112/arskurs5', 'https://www.kth.se/student/kurser/program/CINTE/20102/arskurs5', 'https://www.kth.se/student/kurser/program/CINTE/20092/arskurs5', 'https://www.kth.se/student/kurser/program/CINTE/20082/arskurs5', 'https://www.kth.se/student/kurser/program/CINTE/20072/arskurs5']
def programme_syllabi(program_code):
    list_of_links=list()
    url="{0}/student/kurser/program/{1}".format(KOPPSbaseUrl, program_code)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting programme_syllabi: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        xml=BeautifulSoup(r.text, "html")
        p1=xml.find('div', attrs={'class': 'paragraphs '})
        for link in p1.findAll('a'):
            h1=link.get('href')
            if h1:
                list_of_links.append(KOPPSbaseUrl+h1)
        return list_of_links
    #
    return None

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

def degree_project_course_codes_in_program(program_code):
    dp_course_set=set()
    syllabi=programme_syllabi(program_code)
    for s in syllabi:           # there are multiple syllabus - one for each year's new admitted students
        codes_per_year=course_codes_from_url(s)
        print("codes_per_year: {}".format(codes_per_year))
        dc=degree_project_course_codes_in(codes_per_year)
        print("dc: {}".format(dc))
        dp_course_set=dp_course_set | dc
    return dp_course_set

#https://www.kth.se/student/kurser/kurs/IL226X?l=sv
def target_group_for_course(course_code):
    list_of_links=list()
    url="{0}/student/kurser/kurs/{1}".format(KOPPSbaseUrl, course_code)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting course information: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        xml=BeautifulSoup(r.text, "html.parser")
        crc=xml.find('div', attrs={'id': 'courseRoundsContainer'})
        if crc:
            if crc:
                if Verbose_Flag:
                    print("crc={}".format(crc))
                crb=crc.find('div', attrs={'id': 'courseRoundBlocks'})
                if crb:
                    if Verbose_Flag:
                        print("crb={}".format(crb))
                    ifs=crb.find('ul', attrs={'class': 'infoset'})
                    if ifs:
                        if Verbose_Flag:
                            print("ifs={}".format(ifs))
                        for liw in ifs.findAll('li', attrs={'class': 'wide'}):
                            if Verbose_Flag:
                                print("liw={}".format(liw))
                            which_subheading = liw.find('h4')
                            if which_subheading.string == 'Målgrupp':
                                for para in liw.findAll('p'):
                                    if Verbose_Flag:
                                        print("para={}".format(para))
                                        print("para.string={}".format(para.string))
                                    if para.string and not (para.string.find('Endast') == 0):
                                        return [item.strip() for item in para.string.split(",")]
    #
    return None

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

    parser.add_option('-t', '--testing',
                      dest="testing",
                      default=False,
                      action="store_true",
                      help="execute test code"
    )



    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))
        print("Configuration file : {}".format(options.config_filename))

    if (len(remainder) < 2):
        print("Insuffient arguments - must provide cycle_number school_acronym")
        sys.exit()
    else:
        cycle_number=remainder[0] # note that cycle_number is a string with the value '1' or '2'
        school_acronym=remainder[1]

    if Verbose_Flag:
        print("school_acronym={}".format(school_acronym))
    # compute the list of degree project course codes
    all_dept_codes=get_dept_codes(Swedish_language_code)
    if Verbose_Flag:
        print("all_dept_codes={}".format(all_dept_codes))

    dept_codes=dept_codes_in_a_school(school_acronym, all_dept_codes)
    if Verbose_Flag:
        print("dept_codes={}".format(dept_codes))

    courses_English=degree_project_courses(dept_codes, English_language_code)
    courses_Swedish=degree_project_courses(dept_codes, Swedish_language_code)
    if Verbose_Flag:
        print("courses English={0} and Swedish={1}".format(courses_English, courses_Swedish))
        
    #relevant_courses_English=list(filter(lambda x: x['cycle'] == cycle_number, courses_English))
    #relevant_courses_Swedish=list(filter(lambda x: x['cycle'] == cycle_number, courses_Swedish))

    relevant_courses_English=dict()
    for c in courses_English:
        if c['cycle'] == cycle_number:
            relevant_courses_English[c['code']]=c


    relevant_courses_Swedish=dict()
    for c in courses_Swedish:
        if c['cycle'] == cycle_number:
            relevant_courses_Swedish[c['code']]=c

    if Verbose_Flag:
        print("relevant_courses English={0} and Swedish={1}".format(relevant_courses_English, relevant_courses_Swedish))
        # relevant courses are of the format:{'code': 'II246X', 'title': 'Degree Project in Computer Science and Engineering, Second Cycle', 'href': 'https://www.kth.se/student/kurser/kurs/II246X?l=en', 'info': '', 'credits': '30.0', 'level': 'Second cycle', 'state': 'ESTABLISHED', 'dept_code': 'J', 'department': 'EECS/School of Electrical Engineering and Computer Science', 'cycle': '2', 'subject': 'Degree Project in Computer Science and Engineering'},

    grading_scales=course_gradingscale(relevant_courses_Swedish)
    PF_courses=[]
    for i in grading_scales:
        if grading_scales[i] == 'PF':
            PF_courses.append(i)

    AF_courses=[]
    for i in grading_scales:
        if grading_scales[i] == 'AF':
            AF_courses.append(i)

    if Verbose_Flag:
        print("PF_courses={0} and AF_courses={1}".format(PF_courses, AF_courses))

    all_course_examiners=course_examiners(relevant_courses_Swedish)
    # list of names of those who are no longer examiners at KTH
    examiners_to_remove = [ 'Anne Håkansson',  'Jiajia Chen',  'Paolo Monti',  'Lirong Zheng']
    
    all_examiners=set()
    for course in all_course_examiners:
        for e in all_course_examiners[course]:
            all_examiners.add(e)

    # clean up list of examiners - removing those who should no longer be listed, but are listed in KOPPS
    for e in examiners_to_remove:
        if Verbose_Flag:
            print("examiner to remove={}".format(e))
        if e in all_examiners:
            all_examiners.remove(e)

    all_programs=programs_and_owner_and_titles()
    programs_in_the_school=programs_in_school(all_programs, school_acronym)
    programs_in_the_school_with_titles=programs_in_school_with_titles(all_programs, school_acronym)

    all_data={
        'cycle_number': cycle_number,
        'school_acronym': school_acronym,
        'programs_in_the_school_with_titles': programs_in_the_school_with_titles,
        'dept_codes': dept_codes,
        'all_course_examiners': all_course_examiners,
        'AF_courses': AF_courses,
        'PF_courses': PF_courses,
        'relevant_courses_English': relevant_courses_English,
        'relevant_courses_Swedish': relevant_courses_Swedish
    }

    outpfile_name="course-data-{0}-cycle-{1}.json".format(school_acronym, cycle_number)
    with open(outpfile_name, 'w') as json_url_file:
        json.dump(all_data, json_url_file)

    if options.testing:
        print("testing for course_id={}".format(course_id))

if __name__ == "__main__": main()

