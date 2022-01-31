#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./degree_project_courses_subjects.py
#
# Purpose to collect information about the subjects of the various degree project courses using the information from KOPPS
#
# Outpus the result as an XLSX file with a name:  degree_project_courses_info.xlsx
# and a JSON file with the name: degree_project_courses_info.json
#
# G. Q. Maguire Jr.
#
# 2022-01-30
#
# Based in the earlier setup-degree-project-course.py
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

def main():
    global Verbose_Flag

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

    output_filename_xls='degree_project_courses_info.xlsx'
    output_filename='degree_project_courses_info.json'

    writer = pd.ExcelWriter(output_filename_xls, engine='xlsxwriter')

    kth_wide_exjobb_list=[]
    all_course_info=None
    for school_acronym in KTH_Schools: # can also just give a short list ['EECS']
        print("Working on school: {}".format(school_acronym))

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

        all_course_info=[]
        max_mainSubjects=0
        for course in courses_Swedish:
            course_code=course['code']
            course_info=get_course_info(course_code)
            # skip deactivated courses
            if course_info['state'] == 'DEACTIVATED':
                continue

            # delete some unnecessary info
            del course_info['info']
            del course_info['courseWebUrl']
            del course_info['possibilityToCompletion']
            del course_info['possibilityToAddition']
            del course_info['courseLiterature']
            del course_info['requiredEquipment']
            del course_info['rounds']
            del course_info['href']
            del course_info['courseDeposition']
            mainSubjects=course_info.get('mainSubjects', None)
            if not mainSubjects:
                print("{0} has no main subjects".format(course_code))
            else:
                number_of_mainsubjects=len(mainSubjects)
                if Verbose_Flag and number_of_mainsubjects > 1:
                    print("course_code={0} has {1}".format(course_code, number_of_mainsubjects))
                if number_of_mainsubjects > max_mainSubjects:
                    max_mainSubjects=len(mainSubjects)
                for idx, s in enumerate(mainSubjects):
                    for k in course_info['mainSubjects'][idx].keys():
                        name="mainSubjects_{0}_{1}".format(idx,k)
                        course_info[name]=course_info['mainSubjects'][idx].get(k)

            all_course_info.append(course_info)
        if (all_course_info):
            all_course_info_df=pd.json_normalize(all_course_info)
            # the following was inspired by the section "Using XlsxWriter with Pandas" on http://xlsxwriter.readthedocs.io/working_with_pandas.html
            # set up the output write

            all_course_info_df.to_excel(writer, sheet_name=school_acronym)
        print("max_mainSubjects={0} in {1}".format(max_mainSubjects, school_acronym))
        kth_wide_exjobb_list.extend(all_course_info)
    
    kth_wide_exjobb_list_df=pd.json_normalize(kth_wide_exjobb_list)
    kth_wide_exjobb_list_df.to_excel(writer, sheet_name='All')
    with open(output_filename, 'w', encoding='utf-8') as output_FH:
        j_as_string = json.dumps(kth_wide_exjobb_list, ensure_ascii=False)
        print(j_as_string, file=output_FH)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()


    return





if __name__ == "__main__": main()

