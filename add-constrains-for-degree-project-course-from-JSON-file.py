#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./add-constrains-for-degree-project-course-from-JSON-file.py cycle_number course_id school_acronym
#
# Output: none (it modifies the JSON file prodocued by setup-degree-project-course-from-JSON-file.py
#
#
# Input
# reads the JSON file produced by setup-degree-project-course-from-JSON-file.py
# and then adds constrains
#
# Note that the cycle_number is either 1 or 2 (1st or 2nd cycle)
#
# 
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
#   ./add-constrains-for-degree-project-course-from-JSON-file.py 2 EECS
#
# G. Q. Maguire Jr.
#
#
# 2019.02.09, base on setup-degree-project-course-from-JSON-file.py
#

import requests, time
import pprint
import optparse
import sys
import json

def main():
    global Verbose_Flag

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))

    if (len(remainder) < 2):
        print("Insuffient arguments - must provide cycle_number school_acronym")
        sys.exit()
    else:
        cycle_number=remainder[0] # note that cycle_number is a string with the value '1' or '2'
        school_acronym=remainder[1]
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

        if Verbose_Flag:
            print("school_acronym={}".format(school_acronym))
            print("dept_codes={}".format(dept_codes))
            print("relevant_courses English={0} and Swedish={1}".format(relevant_courses_English, relevant_courses_Swedish))
            print("PF_courses={0} and AF_courses={1}".format(PF_courses, AF_courses))

        # Do some cleanup
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

        #Add the constrains that have been provided by humans
        PF_courses_by_program={
            'cycle1': {
                'TIDAB': ["II142X"],
                'TIEDB': ["IL142X"],
                'TCOMK': ["II143X"],
                'CINTE': ["II143X"],
                #'CDATE': ["II143X"],
                'CELTE': ["II143X"],
                'CELTE+TNTEM': ["II143X"]
            },
            'cycle2': {
                'CINTE': ["II245X", "IL248X"],
                #'CDATE': ["II245X", "IL248X"],
                'CELTE': ["II245X", "IL248X"],
                'CELTE+TNTEM': ["IT245X", "IF245X"],
                'TCOMM': ["IL246X"],
                'TSEDM': ["II246X"],
                'TNTEM': ["IL246X", "IF246X"],
                'TEBSM, spår Inbyggd mjukvara': ["II246X"],
                'TEBSM, övriga spår': ["IL246X"],
                'TIVNM, spår INSY': ["IL246X"],
                'TIVNM, spår ITAK': ["IL246X"],
                'TIVNM, övriga spår': ["II246X"],
                'Masterexjobb på KTH (ej civing)': ["II246X", "IL246X", "IF246X"],
                'Masterexjobb utan program': ["II247X", "IL247X", "IF247X"],
                'Magisterexjobb utan program': ["II249X", "IL249X", "IF249X"]
            }
        }

        AF_courses_by_program={
            'cycle1': {
                'TIDAB': ["II122X"],
                'TIEDB': ["IL122X"],
                'TCOMK': ["II123X"],
                'CINTE': ["II123X"],
                #'CDATE': ["II123X"],
                'CELTE': ["II123X"],
                'CELTE+TNTEM': ["II123X"],
            },
            'cycle2': {
                'CINTE': ["II225X", "IL228X"],
                #'CDATE': ["II225X", "IL228X],
                'CELTE': ["II225X", "IL228X"],
                'CELTE+TNTEM': ["IT225X	IF225X"],
                'TCOMM': ["IL226X"],
                'TSEDM': ["II226X"],
                'TIVNM, spår INSY': ["IL226X"],
                'TIVNM, spår ITAK': ["IL226X"],
                'TIVNM, övriga spår': ["II226X"],
                'TEBSM, spår Inbyggd mjukvara': ["II226X"],
                'TEBSM, övriga spår': ["IL226X"],
                'TCOMM': ["IL226X"],
                'TNTEM': ["IL226X", "IF226X"],
                'Masterexjobb på KTH (ej civing)': ["II226X", "IL226X", "IF226X"],
                'Masterexjobb utan program': ["II227X", "IL227X", "IF227X"],
            }
        }


        # write out the data
        all_data={
            'cycle_number': cycle_number,
            'school_acronym': school_acronym,
            'programs_in_the_school_with_titles': programs_in_the_school_with_titles,
            'dept_codes': dept_codes,
            'all_course_examiners': all_course_examiners,
            'AF_courses': AF_courses,
            'PF_courses': PF_courses,
            'relevant_courses_English': relevant_courses_English,
            'relevant_courses_Swedish': relevant_courses_Swedish,
            'AF_course_codes_by_program': AF_courses_by_program,
            'PF_course_codes_by_program': PF_courses_by_program,
        }

        outpfile_name="course-data-{0}-cycle-{1}c.json".format(school_acronym, cycle_number)
        with open(outpfile_name, 'w') as json_url_file:
            json.dump(all_data, json_url_file)




if __name__ == "__main__": main()

