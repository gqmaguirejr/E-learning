#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./check_degree_projects_from_DiVA.py diva_shreadsheet.xlsx
#
# Output: produces an annotated spreadsheet concerning the examiners
# The filë́s name is of the form: diva_shreadsheet-examiners-checked.xlsx
#
#
# Input
# "-t" or "--testing" to enable small tests to be done
# 
#
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./check_degree_projects_from_DiVA.py --config config-test.json diva_shreadsheet.xlsx
#
#
# ./check_degree_projects_from_DiVA.py kth-student-theses-2019-20201008.xlsx
#
# G. Q. Maguire Jr.
#
#
# 2020.10.13
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
            credits_field=prog.findAll('credits')
            #print("credits_field={}".format(credits_field[0]))
            credit=credits_field[0].string
            program_and_owner_titles[prog.attrs['code']]={'owner': owner, 'title_en': title_en, 'title_sv': title_sv, 'credits': credit}
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
            print("d: {}".format(d))
            courses_d_all=get_dept_courses(d['code'], language_code)
            print("courses_d_all={}".format(courses_d_all))
            if not courses_d_all:
                continue
            courses_d=courses_d_all['courses']
            #if Verbose_Flag:
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



def v1_get_academic_year_plan_for_program(program_code, year):
    global Verbose_Flag
    #
    # Use the KOPPS API to get the data
    # GET /api/kopps/v1/course/{course code}
    # note that this returns XML
    # https://www.kth.se/api/kopps/v1/programme/TCOMM/academic-year-plan/2018:2/1
    url = "{0}/api/kopps/v1/programme/{1}/academic-year-plan/{2}:2/1".format(KOPPSbaseUrl, program_code, year)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting v1 programme academic-year-plan: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        return r.text           # simply return the XML
    #
    return None



def programs_specializations(programs_and_titles, school_acronym):
    year=2018
    program_and_specializations=dict()
    #   
    for prog in programs_and_titles:
        print("prog={}".format(prog))
        yp=v1_get_academic_year_plan_for_program(prog, year)
        print("yp={}".format(yp))
        xml=BeautifulSoup(yp, "lxml")
        tracks=[]
        for track in xml.findAll('specialisation'):
            print("track={}".format(track))
            track_code=track.attrs['programmespecialisationcode'] #  programmeSpecialisationCode'
            print("track_code={}".format(track_code))
            tracks.append(track_code)
        program_and_specializations[prog]={'tracks': tracks}
    #
    return program_and_specializations


second_levels=set(
    'Självständigt arbete på avancerad nivå (magisterexamen)'
    'Självständigt arbete på avancerad nivå (masterexamen)'
    'Självständigt arbete på avancerad nivå (yrkesexamen)')

first_levels=set(
    'Självständigt arbete på grundnivå (högskoleexamen)'
    'Självständigt arbete på grundnivå (kandidatexamen)'
    'Självständigt arbete på grundnivå (konstnärlig högskoleexamen)'
    'Självständigt arbete på grundnivå (konstnärlig kandidatexamen)'
    'Självständigt arbete på grundnivå (yrkesexamen)')

# unknown level
# Studentarbete andra termin

# Examiner names in the spreadshert are in order or and look like:
# Maguire Jr., Gerald Q. [u1d13i2c], professor (KTH [177], Skolan för informations- och kommunikationsteknik (ICT) [5994], Kommunikationssystem, CoS [5998], ;;;Radio Systems Laboratory (RS Lab) [13053])
def normaL_name_oder(sort_ordered_examiner):
    global Verbose_Flag
    first_left_bracket=sort_ordered_examiner.find('[')
    first_left_paren=sort_ordered_examiner.find('(')

    if (first_left_bracket >= 0): #  there is a left bracket
        if (first_left_paren >= 0): #  there is a left paren
            if (first_left_bracket < first_left_paren):  # [ (
                smaller_index=first_left_bracket
            else:                                        # ( [
                smaller_index=first_left_paren
        else:                                            # [
            smaller_index=first_left_bracket
    elif (first_left_paren >= 0): #  there is a left paren (
        smaller_index=first_left_paren
    else:
        smaller_index=len(sort_ordered_examiner)

    e1=sort_ordered_examiner[0:smaller_index].strip()
    if Verbose_Flag:
        print("sort_ordered_examiner={0}, e1={1}, type={2}".format(sort_ordered_examiner, e1, type(e1)))
    e2=e1.split(',')
    return "{0} {1}".format(e2[1].strip(), e2[0].strip())


def highest_level(thesisLevels):
    # there canbe multiple levels separated by semicolons
    # Självständigt arbete på avancerad nivå (masterexamen);Självständigt arbete på avancerad nivå (masterexamen)
    # Självständigt arbete på avancerad nivå (yrkesexamen);Självständigt arbete på avancerad nivå (masterexamen)

    thesis_levels_strings=thesisLevels.split(';')
    for level in thesis_levels_strings:
        if level in second_levels:
            return 2
    return 1


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

    if (len(remainder) < 1):
        print("Insuffient arguments - must provide a spreadsheet from DiVA")
        sys.exit()

    spreadsheet_file=remainder[0]
    students_df = pd.read_excel(open(spreadsheet_file, 'rb'))
    print("read spreadsheet {}".format(spreadsheet_file))

    try:
        with open("KTH_examiners-cycle-1.json") as json_data_file:
            examiners_cycle_1_info = json.load(json_data_file)
    except:
        print("Unable to open configuration file named {}".format("KTH_examiners-cycle-1.json"))
        sys.exit()

    try:
        with open("KTH_examiners-cycle-2.json") as json_data_file:
            examiners_cycle_2_info = json.load(json_data_file)
    except:
        print("Unable to open configuration file named {}".format("KTH_examiners-cycle-2.json"))
        sys.exit()


    try:
        with open("examiners.json") as json_data_file:
            examiners_data = json.load(json_data_file)
    except:
        print("Unable to open file named {}".format("examiners.json"))
        sys.exit()

    corrected_names=examiners_data['corrected_names']
    special_situation=examiners_data['special_situation']

    examiners_cycle_1_with_courses=examiners_cycle_1_info['all_course_examiners']
    examiners_cycle_2_with_courses=examiners_cycle_2_info['all_course_examiners']


    all_examiners_cycle_1=set()
    for course in examiners_cycle_1_with_courses:
        for e in examiners_cycle_1_with_courses[course]:
            all_examiners_cycle_1.add(e)
   
    all_examiners_cycle_2=set()
    for course in examiners_cycle_2_with_courses:
        for e in examiners_cycle_2_with_courses[course]:
            all_examiners_cycle_2.add(e)
        
    all_examiners=all_examiners_cycle_1.union(all_examiners_cycle_2)
    print("Examiners (in KOPPS) 1st cycle: {0}, 2nd cycle: {1}, total: {2}".format(len(all_examiners_cycle_1), len(all_examiners_cycle_2), len(all_examiners)))

    for index, row in  students_df.iterrows():
        if Verbose_Flag:
            print("index: {0}, row['Examiners']: {1}, row['ThesisLevel']: {2}".format(index, row['Examiners'], row['ThesisLevel']))

        # stop when you reach an empty PID cell
        if not (isinstance(row['PID'], int)):
            break

        sort_ordered_examiner=row['Examiners']
        # handle chnages in name or spelling differences
            
        if (not (isinstance(sort_ordered_examiner, str))) or (isinstance(sort_ordered_examiner, str) and (len(sort_ordered_examiner) < 1)):
            students_df.at[index, 'Checked'] = 'No examiner'
            continue
        
        status='Unchecked'

        examiner=normaL_name_oder(sort_ordered_examiner)
        if corrected_names.get(examiner, False):
            examiner=corrected_names[examiner]

        if examiner in all_examiners:

            thesis_level=row['ThesisLevel']
            current_level=highest_level(thesis_level)

            if current_level == 2:
                if examiner in all_examiners_cycle_2:
                    status='Valid'
                else:
                    print("PID={0}, examiner={1}, current_level={2}, Not a valid level 2 examiner".format(row['PID'], examiner, current_level))
            else:
                if current_level == 1:
                    if (examiner in all_examiners_cycle_1):
                        status='Valid'
                    else:
                        if (examiner in all_examiners_cycle_2):
                            print("PID={0}, examiner={1}, current_level={2}, Not a valid level 1 examiner, but a valid level 2 examiner".format(row['PID'], examiner, current_level))
                            status='Valid'
                else:
                    print("PID={0}, examiner={1}, current_level={2}, Not a valid thesis level".format(row['PID'], examiner, current_level))
        else:
            es=special_situation.get(examiner, False)
            if es:
                status='Valid '+es
            else:
                status='Invalid examiner'
            print("PID={0}, examiner={1}, current_level={2}, status={3}".format(row['PID'], examiner, current_level, status))

        if Verbose_Flag:
            print("PID={0}, examiner={1}, current_level={2}, status={3}".format(row['PID'], examiner, current_level, status))
        students_df.at[index, 'Checked'] = status

    outputfile=spreadsheet_file[:-5]+'-examiners-checked.xlsx'
    writer = pd.ExcelWriter(outputfile, engine='xlsxwriter')

    students_df.to_excel(writer, sheet_name="Checked")

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    # examiners_data={
    #     'corrected_names': corrected_names,
    #     'special_situation': special_situation
    # }
    
    # with open('examiners.json', 'w') as outfile:
    #     json.dump(examiners_data, outfile, sort_keys = True, indent = 4,
    #               ensure_ascii = False)

if __name__ == "__main__": main()

