#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./get-school-acronyms-and-program-names-data-3rd-cycle.py
#
# Output: produces a file containing the school acronyms and all of the program names, in the format for inclusion into the thesis template
#
#
# "-t" or "--testing" to enable small tests to be done
# 
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./setup-degree-project-course.py --config config-test.json 1 EECS
#
# Example for a 2nd cycle course for EECS:
#
# ./get-school-acronyms-and-program-names-data.py --config config-test.json
#
# G. Q. Maguire Jr.
#
#
# 2020-02-16
# based on earlier program: get-degree-project-course-data.py
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

# https://api.kth.se/api/kopps/v2/schools
#[{"code":"ABE","name":"ABE/Arkitektur och samhällsbyggnad","orgUnit":"A"},{"code":"STH","name":"STH/Teknik och hälsa","orgUnit":"H"},{"code":"ITM","name":"ITM/Industriell teknik och management","orgUnit":"M"},{"code":"BIO","name":"BIO/Bioteknologi","orgUnit":"B"},{"code":"CSC","name":"CSC/Datavetenskap och kommunikation","orgUnit":"D"},{"code":"EES","name":"EES/Elektro- och systemteknik","orgUnit":"E"},{"code":"CHE","name":"CHE/Kemivetenskap","orgUnit":"K"},{"code":"ICT","name":"ICT/Informations- och kommunikationsteknik","orgUnit":"I"},{"code":"XXX","name":"XXX/Samarbete med andra universitet","orgUnit":"U"},{"code":"ECE","name":"ECE/Teknikvetenskaplig kommunikation och lärande","orgUnit":"L"},{"code":"SCI","name":"SCI/Teknikvetenskap","orgUnit":"S"},{"code":"CBH","name":"CBH/Kemi, bioteknologi och hälsa","orgUnit":"C"},{"code":"EECS","name":"EECS/Elektroteknik och datavetenskap","orgUnit":"J"}]
#
# https://api.kth.se/api/kopps/v2/schools?l=en
# [{"code":"ABE","name":"ABE/Architecture and the Built Environment","orgUnit":"A"},{"code":"STH","name":"STH/Technology and Health","orgUnit":"H"},{"code":"ITM","name":"ITM/Industrial Engineering and Management","orgUnit":"M"},{"code":"BIO","name":"BIO/Biotechnology","orgUnit":"B"},{"code":"CSC","name":"CSC/Computer Science and Communication","orgUnit":"D"},{"code":"EES","name":"EES/Electrical Engineering","orgUnit":"E"},{"code":"CHE","name":"CHE/Chemical Science and Engineering","orgUnit":"K"},{"code":"ICT","name":"ICT/Information and Communication Technology","orgUnit":"I"},{"code":"XXX","name":"XXX/Cooperation with other universities","orgUnit":"U"},{"code":"ECE","name":"ECE/Education and Communication in Engineering Science","orgUnit":"L"},{"code":"SCI","name":"SCI/Engineering Sciences","orgUnit":"S"},{"code":"CBH","name":"CBH/Engineering Sciences in Chemistry, Biotechnology and Health","orgUnit":"C"},{"code":"EECS","name":"EECS/Electrical Engineering and Computer Science","orgUnit":"J"}]

def v2_get_schools():
    global Verbose_Flag
    schools_list_swe=[]
    schools_list_eng=[]
    schools=dict()
    old_schools=['BIO', 'CHE', 'ECE', 'CSC', 'EES', 'ICT', 'STH', 'XXX']
    #
    # Use the KOPPS API to get the data
    # note that this returns XML
    url = "{0}/api/kopps/v2/schools".format(KOPPSbaseUrl)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting v2 schools: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        schools_list_swe=r.json()           # simply return the XML
    #
    url = "{0}/api/kopps/v2/schools?l=en".format(KOPPSbaseUrl)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting v2 schools: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        schools_list_eng=r.json()           # simply return the XML
    #
    # Iterate throught the lists and augment the dict
    for s in schools_list_swe:
        name=s['name'].split('/')
        schools[s['code']]={'sv': name[1]}
    #
    for s in schools_list_eng:
        name=s['name'].split('/')
        schools[s['code']]['en']=name[1]
    #
    for s in old_schools:
        schools.pop(s)
    #
    return schools



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

def v2_get_programmes_third_cycle():
    global Verbose_Flag
    #
    # Use the KOPPS API to get the data
    # note that this returns JSON
    #
    # https://api.kth.se/api/kopps/v2/dr/programmes
    url = "{0}/api/kopps/v2/dr/programmes".format(KOPPSbaseUrl)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting v2 doctoral programme: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        return r.json()  # simply return the JSON
    #
    return None
# example of return value
# [{"programme":
#         {"code":"KTHARK","title":"Architecture","titleOther":"Arkitektur","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ABE"}]},
#           "subjects":[{"code":"ARKITEKT","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Architecture"}],
#           "revision":52},
#   {"programme":{"code":"KTHKON","title":"Art, Technology and Design ","titleOther":"Konst, teknik och design","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ABE"}]},"subjects":[{"code":"KONST","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Art, Technology and Design "}],"revision":36},
#   {"programme":{"code":"KTHBIO","title":"Biotechnology","titleOther":"Bioteknologi","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"BIO"}]},"subjects":[{"code":"BIOT","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Biotechnology"}],"revision":20},
#   {"programme":{"code":"KTHKEV","title":"Chemical Science and Engineering","titleOther":"Kemivetenskap","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"CHE"}]},"subjects":[{"code":"KEMI","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Chemistry"},{"code":"KEMTEK","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Chemical Engineering"},{"code":"FPVET","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Fibre and Polymer Science"}],"revision":14},
#   {"programme":{"code":"KTHBYV","title":"Civil and Architectural Engineering","titleOther":"Byggvetenskap","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ABE"}]},"subjects":[{"code":"BYV","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Civil and Architectural Engineering"}],"revision":55},
#   {"programme":{"code":"KTHDAT","title":"Computer Science","titleOther":"Datalogi ","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"CSC"}]},"subjects":[{"code":"DATALOGI","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Computer Science"},{"code":"LJUDMUSI","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Speech and Music Communication"}],"revision":9},
#   {"programme":{"code":"KTHEST","title":"Electrical Engineering","titleOther":"Elektro- och systemteknik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"EES"}]},"subjects":[{"code":"ELSYTEKN","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Electrical Engineering"}],"revision":12},
#   {"programme":{"code":"KTHEGI","title":"Energy Technology and Systems","titleOther":"Energiteknik och -system","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ITM"}]},"subjects":[{"code":"ENERGIT","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Energy Technology"}],"revision":6},
#   {"programme":{"code":"KTHTMV","title":"Engineering Materials Science","titleOther":"Teknisk materialvetenskap","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ITM"}]},"subjects":[{"code":"TEMATRVE","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Engineering Materials Science"}],"revision":25},
#   {"programme":{"code":"KTHMEK","title":"Engineering Mechanics","titleOther":"Teknisk Mekanik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"SCI"}]},"subjects":[{"code":"TEMEKAN","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Engineering Mechanics"}],"revision":28},
#   {"programme":{"code":"KTHGEO","title":"Geodesy and Geoinformatics","titleOther":"Geodesi och Geoinformatik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ABE"}]},"subjects":[{"code":"GEODEINF","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Geodesy and Geoinformatics"}],"revision":35},
#   {"programme":{"code":"KTHIEO","title":"Industrial Economics and Management","titleOther":"Industriell ekonomi och organisation","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ITM"}]},"subjects":[{"code":"INDEKO","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Industrial Economics and Management"}],"revision":26},

#   {"programme":{"code":"KTHIKT","title":"Information and Communication Technology","titleOther":"Informations- och kommunikationsteknik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ICT"}]},"subjects":[{"code":"INFKOMTE","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Information and Communication Technology"}],"revision":15},
#   {"programme":{"code":"KTHMAT","title":"Mathematics","titleOther":"Matematik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"SCI"}]},"subjects":[{"code":"MATTE","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Mathematics"}],"revision":22},
#   {"programme":{"code":"KTHKOM","title":"Mediated Communication","titleOther":"Medierad kommunikation ","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"CSC"}]},"subjects":[{"code":"LJUDMUSI","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Speech and Music Communication"},{"code":"MEDIAT","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Media Technology"},{"code":"MÄNDATOR","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Human-Computer Interaction"}],"revision":10},
#   {"programme":{"code":"KTHFYS","title":"Physics","titleOther":"Fysik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"SCI"}]},"subjects":[{"code":"FYSIK","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Physics"},{"code":"BIOLFYS","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Biological physics"}],"revision":20},
#   {"programme":{"code":"KTHPBA","title":"Planning and Decision Analysis","titleOther":"Planering och beslutsanalys","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ABE"}]},"subjects":[{"code":"PLANBEAN","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Planning and Decision Analysis"}],"revision":56},
#   {"programme":{"code":"KTHIIP","title":"Production Engineering","titleOther":"Industriell produktion","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ITM"}]},"subjects":[{"code":"INDPROD","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Production Engineering"}],"revision":14},
#   {"programme":{"code":"KTHHFL","title":"Solid Mechanics","titleOther":"Hållfasthetslära","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"SCI"}]},"subjects":[{"code":"HÅLLF","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Solid Mechanics"}],"revision":18},
#   {"programme":{"code":"KTHSHB","title":"The Built Environment and Society: Management, Economics and Law","titleOther":"Samhällsbyggnad: Management, ekonomi och juridik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"ABE"}]},"subjects":[{"code":"BUSINADM","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Business studies"},{"code":"FASTBYGG","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Real Estate and Construction Management"},{"code":"NATIONEK","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Economics"}],"revision":62},
#   {"programme":{"code":"KTHTKB","title":"Theoretical Chemistry and Biology","titleOther":"Teoretisk kemi och biologi","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"BIO"}]},"subjects":[{"code":"TKOB","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Theoretical Chemistry and Biology"}],"revision":8},
#   {"programme":{"code":"KTHFTK","title":"Vehicle and Maritime Engineering","titleOther":"Farkostteknik","state":{"name":"ESTABLISHED","key":"programmestate.established"},"schools":[{"name":"SCI"}]},"subjects":[{"code":"FARKTE","state":{"name":"ESTABLISHED","key":"programmestate.established"},"title":"Vehicle and Martime Engineering"}],"revision":43}]


def programs_and_titles_3rd_cycle():
    programs=v2_get_programmes_third_cycle()
    print("programs={0}".format(programs)) 
    program_and_titles=dict()
    for prog in programs:
        if Verbose_Flag:
            print("prog is {}".format(prog))
        
        code=prog['programme']['code']
        title_sv=prog['programme']['title']
        title_en=prog['programme']['titleOther']

        if Verbose_Flag:
            print("prog{0}, code={1}".format(prog, code))
        program_and_titles[code]={'title_en': title_en, 'title_sv': title_sv}
    #
    return program_and_titles

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

    schools=v2_get_schools()
    if Verbose_Flag:
        print("schools={}".format(schools))

    #\newcommand{\schoolAcronym}[1]{%
       #  \ifinswedish
       #  \IfEqCase{#1}{%
       #    {ABE}{\school{Skolan för Arkitektur och samhällsbyggnad}}%
       #    {CBH}{\school{Skolan för Kemi, bioteknologi och hälsa}}%
       #    {EECS}{\school{Skolan för elektroteknik och datavetenskap}}%
       #    {ITM}{\school{Skolan för Industriell teknik och management}}%
       #    {SCI}{\school{Skolan för Teknikvetenskap}}%
       #  }[\typeout{school's code not found}]
       #  \else
       #  \IfEqCase{#1}{%
       #    {ABE}{\school{School of Architecture and the Built Environment}}%
       #    {CBH}{\school{School of Engineering Sciences in Chemistry, Biotechnology and Health}}%
       #    {EECS}{\school{School of Electrical Engineering and Computer Science}}%
       #    {ITM}{\school{School of Industrial Engineering and Management}}%
       #    {SCI}{\school{School of Engineering Sciences}}%
       #  }[\typeout{school's code not found}]
       #  \fi
       #}

    options1=''
    options2=''
    for s in schools:
        st1='    {' + "{}".format(s) + '}{\school{Skolan för ' + "{}".format(schools[s]['sv']) + '}}%'
        st2='    {' + "{}".format(s) + '}{\school{School of ' + "{}".format(schools[s]['en']) + '}}%'
        options1=options1+st1+'\n'
        options2=options2+st2+'\n'
    #
    cmd='\\newcommand{\\schoolAcronym}[1]{%\n  \\ifinswedish\n  \\IfEqCase{#1}{%\n'+options1
    cmd=cmd+"  }[\\typeout{school's code not found}]\n  \\else\n  \\IfEqCase{#1}{%\n"
    cmd=cmd+options2+"  }[\\typeout{school's code not found}]\n  \\fi\n}\n"
    print("cmd={}".format(cmd))    

    #all_programs=programs_and_owner_and_titles()
    all_programs=programs_and_titles_3rd_cycle()
    if Verbose_Flag:
        print("all_programs={}".format(all_programs))

    options1=''
    options2=''
    for s in all_programs:
        st1='    {' + "{}".format(s) + '}{\programme{' + "{}".format(all_programs[s]['title_sv']) + '}}%'
        st2='    {' + "{}".format(s) + '}{\programme{' + "{}".format(all_programs[s]['title_en']) + '}}%'
        options1=options1+st1+'\n'
        options2=options2+st2+'\n'
    #
    cmdp='\\newcommand{\\programcode}[1]{%\n  \\ifinswedish\n  \\IfEqCase{#1}{%\n'+options1
    cmdp=cmdp+"  }[\\typeout{program's code not found}]\n  \\else\n  \\IfEqCase{#1}{%\n"
    cmdp=cmdp+options2+"  }[\\typeout{program's code not found}]\n  \\fi\n}\n"
    print("cmdp={}".format(cmdp))    


    outpfile_name="schools_and_programs_3rd_cycle.ins"
    with open(outpfile_name, 'w') as f:
        f.write(cmd)
        f.write(cmdp)
    return

if __name__ == "__main__": main()

