#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./cover_data.py school_acronym
#
# Output: produces a spreadsheet containing all of the data about degree project courses
# The filë́s name is of the form: exjobb_courses-{school_acronym}.xlsx
#
#
# Input
#
# "-t" or "--testing" to enable small tests to be done
# 
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./setup-degree-project-course.py --config config-test.json 1 EECS
#
# Example for a 2nd cycle course for EECS:
# G. Q. Maguire Jr.
#
# based on earlier program: get-degree-project-course-data.py
#
# 2019.02.26
#

import requests, time
import pprint
import optparse
import sys
import json

# Use Python Pandas to create XLSX files
import pandas as pd

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


# degree_project_course_codes_in({'II143X', 'II1305', 'IK2206', 'IC1007', 'SF1547', 'ID1217', 'II1307', 'ID2202', 'IE1202', 'ME2063', 'SK1118', 'ID2213', 'ID1206', 'ID1212', 'DD2350', 'SF1546', 'DD1351', 'SF1625', 'ID1354', 'II2202', 'EQ1110', 'SF1912', 'IK1203', 'SF1610', 'IV1350', 'ID1019', 'ID1020', 'EL1000', 'EQ1120', 'IV1013', 'ID2216', 'ME2015', 'IE1206', 'ID1018', 'IE1204', 'DD2352', 'AG1815', 'IH1611', 'II1306', 'SF1689', 'IK1552', 'SG1102', 'ID2201', 'IS1200', 'SH1011', 'IS2202', 'DD2372', 'IV1303', 'SF1686', 'SF1624', 'ID1214', 'IV1351', 'DD2401', 'ME1003'})
# returns {'II143X'}
def degree_project_course_codes_in(set_of_course_codes):
    dp_course_set=set()
    for c in set_of_course_codes:
        if c[-1:] == 'X':
            dp_course_set.add(c)
    return dp_course_set

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
        print("Insuffient arguments - must provide school_acronym")
        sys.exit()
    else:
        school_acronym=remainder[0]

    if Verbose_Flag:
        print("school_acronym={}".format(school_acronym))

        
    # the following was inspired by the section "Using XlsxWriter with Pandas" on http://xlsxwriter.readthedocs.io/working_with_pandas.html
    # set up the output write
    outputfile_name="exjobb_courses-{}.xlsx".format(school_acronym)
    writer = pd.ExcelWriter(outputfile_name, engine='xlsxwriter')

    # compute the list of degree project course codes
    all_dept_codes=get_dept_codes(Swedish_language_code)
    if Verbose_Flag:
        print("all_dept_codes={}".format(all_dept_codes))

    # Convert the dataframe to an XlsxWriter Excel object.
    all_dept_codes_df=pd.io.json.json_normalize(all_dept_codes)
    all_dept_codes_df.to_excel(writer, sheet_name='Dept Codes')

    dept_codes=dept_codes_in_a_school(school_acronym, all_dept_codes)
    if Verbose_Flag:
        print("dept_codes={}".format(dept_codes))

    courses_from_depts=[]
    for d in dept_codes:
        cs=get_dept_courses(d, English_language_code)
        if cs['courses']:
            if Verbose_Flag:
                print("cs={}".format(cs))
            for c in cs['courses']:
                if Verbose_Flag:
                    print("c={}".format(c))
                if (c['state'] == "ESTABLISHED") and (c['code'].endswith('x') or c['code'].endswith('X')):
                    courses_from_depts.append(c)

    courses_en_df=pd.io.json.json_normalize(courses_from_depts)
    courses_en_df.to_excel(writer, sheet_name='Courses')

    detailed_exjobb_courses=[]
    for c in courses_from_depts:
        cd=get_course_info(c['code'])
        credits=float(cd['credits'])
        if cd['level']['en'] == 'First cycle':
            if credits == 7.5:
                cd.update({'cover_degree': 'first-level-7'})
            elif credits == 10.0:
                cd.update({'cover_degree': 'first-level-10'})
            elif credits == 15.0:
                cd.update({'cover_degree': 'first-level-15'})
            else:
                print("Unhandled number of credits for a First cycle degree project course - course code={}".format(c['code']))
            
        if cd['level']['en'] == 'Second cycle':
            if credits == 15.0:
                cd.update({'cover_degree': 'second-level-15'})
            elif credits == 30.0:
                cd.update({'cover_degree': 'second-level-30'})
            elif credits == 60.0:
                cd.update({'cover_degree': 'second-level-60'})
            else:
                print("Unhandled number of credits for a Second cycle degree project course - course code={}".format(c['code']))


        if (c['code'] == 'II122X') or (c['code'] == 'II142X'):
            cd.update({'cover_exam': 2}) 				#  Högskoleingenjörsexamen
            cd.update({'cover_area': {'en': 'Computer Engineering',	#   Datateknik
                                      'sv': 'Datateknik'}})

        elif (c['code'] == 'IL122X') or (c['code'] == 'II122X'):
            cd.update({'cover_exam': 2}) 				# Högskoleingenjörsexamen
            cd.update({'cover_area': {'en': 'Electronics and Computer Engineering', 
                                      'sv': 'Elektronik och datorteknik'}}) 	#  Elektronik och datorteknik

        elif (c['code'] == 'IL122X') or (c['code'] == 'II122X'):
            cd.update({'cover_exam': 1}) 				# kandidate exam
            cd.update({'cover_area': {'en': 'Information and Communication Technology',
                                      'sv': 'Informations- och kommunikationsteknik'}}) 	#  Informations- och kommunikationsteknik

        elif (c['code'] == 'II249X'):
            cd.update({'cover_exam': 3}) 				# Magisterexamen
            cd.update({'cover_area': {'en': 'Computer Science and Engineering',
                                      'sv': 'Datalogi och datateknik'}}) 	#  Datalogi och datateknik

        elif (c['code'] == 'IL249X'):
            cd.update({'cover_exam': 3}) 				# Magisterexamen
            cd.update({'cover_area': {'en': 'Electrical Engineering', 	#  Elektroteknik
                                      'sv': 'Elektroteknik'}})

        elif (c['code'] == 'II225X') or (c['code'] == 'II245X'):
            cd.update({'cover_exam': 4}) 				# Civilingenjörsexamen
            cd.update({'cover_area': {'en': 'Information and Communication Technology',
                                      'sv': 'Informations- och kommunikationsteknik'}}) 	#  Informations- och kommunikationsteknik

        elif (c['code'] == 'IL228X') or (c['code'] == 'IL248X'):
            cd.update({'cover_exam': 4}) 				# Civilingenjörsexamen
            cd.update({'cover_area': {'en': 'Information and Communication Technology',
                                      'sv': 'Informations- och kommunikationsteknik'}}) 	#  Informations- och kommunikationsteknik

        elif (c['code'] == 'II226X') or (c['code'] == 'II246X'):
            cd.update({'cover_exam': 3}) 				# Masterexamen
            cd.update({'cover_area': {'en': 'Computer Science and Engineering',
                                      'sv': 'Datalogi och datateknik'}}) 	#  Datalogi och datateknik

        elif (c['code'] == 'II227X') or (c['code'] == 'II247X'):
            cd.update({'cover_exam': 3}) 				# Masterexamen - outside of program
            cd.update({'cover_area': {'en': 'Computer Science and Engineering',
                                      'sv': 'Datalogi och datateknik'}}) 	#  Datalogi och datateknik

        elif (c['code'] == 'IL226X') or (c['code'] == 'IL246X'):
            cd.update({'cover_exam': 3}) 				# Masterexamen
            cd.update({'cover_area': {'en': 'Electrical Engineering', 	#  Elektroteknik
                                      'sv': 'Elektroteknik'}})

        elif (c['code'] == 'IL227X') or (c['code'] == 'IL247X'):
            cd.update({'cover_exam': 3}) 				# Masterexamen - outside of program
            cd.update({'cover_area': {'en': 'Electrical Engineering', 	#  Elektroteknik
                                      'sv': 'Elektroteknik'}})

        elif (c['code'] == 'IF226X') or (c['code'] == 'IF246X'):
            cd.update({'cover_exam': 3}) 				# Masterexamen (not Civing.) or nanotechnology
            cd.update({'cover_area': {'en': 'Engineering Physics',	# Teknisk fysik
                                      'sv': 'Teknisk fysik'}})

        elif (c['code'] == 'IF227X') or (c['code'] == 'IF247X'):
            cd.update({'cover_exam': 3}) 				# Masterexamen - outside of program
            cd.update({'cover_area': {'en': 'Engineering Physics',	# Teknisk fysik
                                      'sv': 'Teknisk fysik'}})

        else:
            print("Unhandled exam and area - course code={}".format(c['code']))

        # Exam
        # <select id="exam" name="exam" disabled="disabled">
        # <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj examen</option>
        # <option class="firstLevel" value="1">Kandidatexamen</option>
        # <option class="firstLevel" value="1">Högskoleexamen</option>
        # <option class="firstLevel" value="2">Högskoleingenjörsexamen</option>
        # <option class="firstLevel" value="8">Ämneslärarexamen</option>
        # <option class="secondLevel" value="3">Magisterexamen</option>
        # <option class="secondLevel" value="3">Masterexamen</option>
        # <option class="secondLevel" value="4">Civilingenjörsexamen</option>
        # <option class="secondLevel" value="5">Arkitektexamen</option>
        # <option class="secondLevel" value="6">Ämneslärarexamen</option>
        # <option class="secondLevel" value="7">Civilingenjörs- och masterexamen</option>

        # Area
        # <select id="area" name="area" disabled="disabled">
        # <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj område</option>
        # <!-- Major areas -->
        # <option class="area-1 area-3 area-5" value="Arkitektur">Arkitektur</option>

        # The following are for an exam in Degree of Master (60 credits) or Degree of Master (120 credits)
        # <option class="area-3" value="Bioteknik">Bioteknik</option>
        # <option class="area-3" value="Datalogi och datateknik">Datalogi och datateknik</option>
        # <option class="area-3" value="Elektroteknik">Elektroteknik</option>
        # <option class="area-3" value="Industriell ekonomi">Industriell ekonomi</option>
        # <option class="area-3" value="Informations- och kommunikationsteknik">Informations- och kommunikationsteknik</option>
        # <option class="area-3" value="Kemiteknik">Kemiteknik</option>
        # <option class="area-3" value="Maskinteknik">Maskinteknik</option>
        # <option class="area-3" value="Matematik">Matematik</option>
        # <option class="area-3" value="Materialteknik">Materialteknik</option>
        # <option class="area-3" value="Medicinsk teknik">Medicinsk teknik</option>
        # <option class="area-3" value="Miljöteknik">Miljöteknik</option>
        # <option class="area-3" value="Samhällsbyggnad">Samhällsbyggnad</option>
        # <option class="area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
        # <option class="area-3" value="Teknik och hälsa">Teknik och hälsa</option>
        # <option class="area-3" value="Teknik och lärande">Teknik och lärande</option>
        # <option class="area-3" value="Teknik och management">Teknik och management</option>
        # <option class="area-3" value="Teknisk fysik">Teknisk fysik</option>

        # The following are for an exam in value="1">Bachelors degree or value="1">Higher Education Diploma
        # <option class="area-1 area-8" value="Teknik">Teknik</option>


        # The following are for an exam in value="2">Degree of Bachelor of Science in Engineering
        # <!-- Tech areas -->
        # <option class="area-2" value="Byggteknik och design">Byggteknik och design</option>
        # <option class="area-2" value="Datateknik">Datateknik</option>
        # <option class="area-2" value="Elektronik och datorteknik">Elektronik och datorteknik</option>
        # <option class="area-2" value="Elektroteknik">Elektroteknik</option>
        # <option class="area-2" value="Kemiteknik">Kemiteknik</option>
        # <option class="area-2" value="Maskinteknik">Maskinteknik</option>
        # <option class="area-2" value="Medicinsk teknik">Medicinsk teknik</option>
        # <option class="area-2 area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>

        # The following are for an exam in value="4">Degree of Master of Science in Engineering or value="7">Both Master of science in engineering and Master
        # <option class="area-4 area-7" value="Teknik och lärande">Teknik och lärande</option>
        # <option class="area-4 area-7" value="Bioteknik">Bioteknik</option>
        # <option class="area-4 area-7" value="Datateknik">Datateknik</option>
        # <option class="area-4 area-7" value="Design och produktframtagning">Design och produktframtagning</option>
        # <option class="area-4 area-7" value="Elektroteknik">Elektroteknik</option>
        # <option class="area-4 area-7" value="Energi och miljö">Energi och miljö</option>
        # <option class="area-4 area-7" value="Farkostteknik">Farkostteknik</option>
        # <option class="area-4 area-7" value="Industriell ekonomi">Industriell ekonomi</option>
        # <option class="area-4 area-7" value="Informationsteknik">Informationsteknik</option>
        # <option class="area-4 area-7" value="Maskinteknik">Maskinteknik</option>
        # <option class="area-4 area-7" value="Materialdesign">Materialdesign</option>
        # <option class="area-4 area-7" value="Medicinsk teknik">Medicinsk teknik</option>
        # <option class="area-4 area-7" value="Medieteknik">Medieteknik</option>
        # <option class="area-4 area-7" value="Samhällsbyggnad">Samhällsbyggnad</option>
        # <option class="area-4 area-7" value="Teknisk fysik">Teknisk fysik</option>
        # <option class="area-4 area-7" value="Teknisk kemi">Teknisk kemi</option>
        # <option class="area-4 area-7" value="Kemivetenskap">Kemivetenskap</option>
        # <option class="area-4 area-7" value="Mikroelektronik">Mikroelektronik</option>

        # The following are for an exam in value="6">Degree of Master of Science in Secondary Education
        # <!-- Subject areas -->
        # <option class="area-6 area-8" value="Teknik och lärande">Teknik och lärande</option>
        # <option class="area-6 area-8" value="Matematik och lärande">Matematik och lärande</option>
        # <option class="area-6 area-8" value="Kemi och lärande">Kemi och lärande</option>
        # <option class="area-6 area-8" value="Fysik och lärande">Fysik och lärande</option>
        # <option class="area-6 area-8" value="Ämnesdidaktik">Ämnesdidaktik</option>


        # Subject area (magister) for type 7 (master of science and master-->
        # <div class="double_field" id="master_field">
        # <label for="master">Huvudområde för masterexamen</label>
        # <div class="input">
        # <div class="selectContainer">
        # <select id="master" name="master">
        # <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj område</option>
        # <!-- Major areas -->
        # <option class="area-1 area-3 area-5" value="Arkitektur">Arkitektur</option>
        # <option class="area-3" value="Bioteknik">Bioteknik</option>
        # <option class="area-3" value="Datalogi och datateknik">Datalogi och datateknik</option>
        # <option class="area-3" value="Elektroteknik">Elektroteknik</option>
        # <option class="area-3" value="Industriell ekonomi">Industriell ekonomi</option>
        # <option class="area-3" value="Informations- och kommunikationsteknik">Informations- och kommunikationsteknik</option>
        # <option class="area-3" value="Kemiteknik">Kemiteknik</option>
        # <option class="area-3" value="Maskinteknik">Maskinteknik</option>
        # <option class="area-3" value="Matematik">Matematik</option>
        # <option class="area-3" value="Materialteknik">Materialteknik</option>
        # <option class="area-3" value="Medicinsk teknik">Medicinsk teknik</option>
        # <option class="area-3" value="Miljöteknik">Miljöteknik</option>
        # <option class="area-3" value="Samhällsbyggnad">Samhällsbyggnad</option>
        # <option class="area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
        # <option class="area-3" value="Teknik och hälsa">Teknik och hälsa</option>
        # <option class="area-3" value="Teknik och lärande">Teknik och lärande</option>
        # <option class="area-3" value="Teknik och management">Teknik och management</option>
        # <option class="area-3" value="Teknisk fysik">Teknisk fysik</option>

        print("cd={}".format(cd))
        detailed_exjobb_courses.append(cd)
    courses_details_df=pd.io.json.json_normalize(detailed_exjobb_courses)
    courses_details_df.to_excel(writer, sheet_name='Details')


    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    if options.testing:
        print("testing for course_id={}".format(course_id))

if __name__ == "__main__": main()

