#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./add-constraints-for-degree-project-course-from-JSON-file.py cycle_number school_acronym
#
# Output: course-data-{0}-cycle-{1}c.json where {0} is school_acronym and {1} is cycle_number
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

        #Add the constraints that have been provided by humans
        PF_courses_by_program={
            'cycle1': {
                'CINTE': {'Teknik': {'default': ["II143X"]}},
                'CDATE': {'Teknik': {'default': ["II143X"]}},
                'CELTE': {'Teknik': {'default': ["II143X"]}},
                'CELTE+TNTEM': {'Teknik': {'default': ["II143X"]}},
                'TCOMK': {'Teknik': {'default': ["II143X"]}},

                'TIDAB': {'Teknik': {'default': ["II142X"]}},
                'TIEDB': {'Teknik': {'default': ["IL142X"]}},
                'TIELA': {'Teknik': {'default': [""]}},

            },
            'cycle2': {
                'CINTE': {'Datalogi och datateknik': {'default': ["II245X"] },
                          'Elektroteknik': {'default': ["IL248X"]},
                },
                'CDATE': {'Datalogi och datateknik': {'default': ["II245X"] },
                          'Elektroteknik': {'default': ["IL248X"]},
                },
                'CELTE': {'Datalogi och datateknik': {'default': ["II245X"] },
                          'Elektroteknik': {'default': ["IL248X"]},
                },
                'CELTE+TNTEM': {'Elektroteknik': {'default': ["IT245X"]},
                                'Teknisk Fysik': {'default': ["IF245X"] },
                },
                'TCOMM': {'Elektroteknik': {'default': ["IL248X"], "ITE": ["IL248X"], "SMK": ["IL248X"], "TRN": ["IL248X"]},
                },

                'TCSCM':  {'Datalogi och datateknik': {'default': [""], "CSCS": [""], "CSDA": [""], "CSID": [""], "CSSC": [""], "CSSP": [""], "CSST": [""], "CSTC": [""], "CSVG": [""] }
                },
                'TEBSM': {'Datalogi och datateknik': {'default': ["II246X"] },
                          
                          'Elektroteknik': {'default': ["IL246X"]},
                },
                'TEBSM': {'Datalogi och datateknik': {'default': ["II246X"], "INMV": ["II246X"]},
                          'Elektroteknik': {'default': ["IL246X"], "INDD": ["IL246X"], "INDK": ["IL246X"], "INEL": ["IL246X"], "INPF": ["IL246X"], "INSR": ["IL246X"]},
                },

                'TEFRM': {'Elektroteknik': {'default': [""], "MIC": [""], "PHS": [""], "PLA": [""], "SPA": [""]},
                          'Teknisk Fysik': {'default': [""], "MIC": [""], "PHS": [""], "PLA": [""], "SPA": [""]},

                },

                'TELPM': {'Elektroteknik': {'default': [""]},
                },


                'TIETM': {'Elektroteknik': {'default': [""], "NUEY": [""], "RENE": [""], "SENS": [""], "SMCS": [""]},
                          'Teknisk Fysik': {'default': [""], "NUEY": [""], "RENE": [""], "SENS": [""], "SMCS": [""]},

                },

                'TIMTM': {'Datalogi och datateknik': {'default': [""], "FID": [""], "LTM": [""], "VLM": [""]},
                          'Elektroteknik': {'default': [""], "FID": [""], "LTM": [""], "VLM": [""]},
                          'Teknisk Fysik': {'default': [""], "FID": [""], "LTM": [""], "VLM": [""]},
                },

                'TINNM': {'Datalogi och datateknik': {'default': [""], "COE": [""], "INF": [""], "MMB": [""], "NWS": [""]},
                          'Elektroteknik': {'default': ["EA260X"], "COE": [""], "INF": [""], "MMB": [""], "NWS": [""]}
                },

                'TIVNM': {'Datalogi och datateknik': {'default': ["II246X"], "AUSM": ["II246X"], "AUSY": ["II246X"], "CLNI": ["II246X"], "CLNS": ["II246X"], "DAMO": ["II246X"], "DASC": ["II246X"], "DASE": ["II246X"], "DMTE": ["II246X"], "DMTK": ["II246X"], "HCID": ["II246X"], "HCIN": ["II246X"], "INSM": ["II246X"], "VCCN": ["II246X"], "VCCO": ["II246X"] },
                          'Elektroteknik': {'default': ["IL246X"], "INSY": ["IL246X"], "ITAK": ["IL246X"], "ITAR": ["IL246X"]}
                },

                'TMAIM': {'Datalogi och datateknik': {'default': ["DA233X"]}
                },
                
                'TMMTM': {'Datalogi och datateknik': {'default': ["DA233X"]}
                },

                'TNTEM':  {'Elektroteknik': {'default': ["IL246X"], "NTEA": [""], "NTEA": [""]},
                          'Teknisk Fysik': {'default': ["IF246X"], "NTEA": [""], "NTEA": [""]}
                },

                'TSCRM': {'Datalogi och datateknik': {'default': ["DA236X"], "ELEM": [""], "NCSS": [""], "RASM": [""], "SCTY": [""]},
                          'Elektroteknik': {'default': ["EA236X"], "COE": [""], "ELEM": [""], "NCSS": [""], "RASM": [""], "SCTY": [""]}
                },

                'TSEDM': {'Datalogi och datateknik': {'default': ["II246X"], "DASC": [""], "PVT": [""]}
                },


                'Masterexjobb på KTH (ej civing)': {'Datalogi och datateknik': {'default': ["II246X"]},
                          'Elektroteknik': {'default': ["IL246X"]},
                          'Teknisk Fysik': {'default': ["IF246X"]},
                },
                

                'Masterexjobb utan program': {'Datalogi och datateknik': {'default': ["II247X"]},
                          'Elektroteknik': {'default': ["IL247X"]},
                          'Teknisk Fysik': {'default': ["IF247X"]},
                },

                'Magisterexjobb utan program': {'Datalogi och datateknik': {'default': ["II249X"]},
                          'Elektroteknik': {'default': ["IL249X"]},
                          'Teknisk Fysik': {'default': ["IF249X"]},
                },

                # ITM Industrial management program
                'TIMAM': {'Datalogi och datateknik': {'default': ["DA235X"]},
                }
            }
        }
        #  @majors=['Datalogi och datateknik', 'Elektroteknik', "Teknisk Fysik"]
        AF_courses_by_program={
            'cycle1': {
                'CINTE': {'Teknik': {'default': ["II123X"]}},
                'CDATE': {'Teknik': {'default': ["II123X"]}},
                'CELTE': {'Teknik': {'default': ["II123X"]}},
                'CELTE+TNTEM': {'Teknik': {'default': ["II123X"]}},
                'TCOMK': {'Teknik': {'default': ["II123X"]}},

                'TIDAB': {'Teknik': {'default': ["II122X"]}},
                'TIEDB': {'Teknik': {'default': ["IL122X"]}},
                'TIELA': {'Teknik': {'default': [""]}},

            },
            'cycle2': {
                'CINTE': {'Datalogi och datateknik': {'default': ["II225X"]},
                          'Elektroteknik': {'default': ["IL228X"]},
                },
                'CDATE': {'Datalogi och datateknik': {'default': ["II225X"]},
                          'Elektroteknik': {'default': ["IL228X"]},
                },
                'CELTE': {'Datalogi och datateknik': {'default': ["II225X"]},
                          'Elektroteknik': {'default': ["IL228X"]},
                },
                'CELTE+TNTEM': {'Elektroteknik': {'default': ["IT225X"]},
                                'Teknisk Fysik': {'default': ["IF225X"]},
                },
                'TCOMM': {'Elektroteknik': {'default': ["IL226X"], "ITE": ["IL226X"], "SMK": ["IL226X"], "TRN": ["IL226X"]},
                },
                'TCSCM':  {'Datalogi och datateknik': {'default': [""], "CSCS": [""], "CSDA": [""], "CSID": [""], "CSSC": [""], "CSSP": [""], "CSST": [""], "CSTC": [""], "CSVG": [""] }
                },
                'TEBSM': {'Datalogi och datateknik': {'default': ["II226X"], "INMV": ["II226X"]},
                          'Elektroteknik': {'default': ["IL226X"], "INDD": ["IL226X"], "INDK": ["IL226X"], "INEL": ["IL226X"], "INPF": ["IL226X"], "INSR": ["IL226X"]},
                },

                'TEFRM': {'Elektroteknik': {'default': [""], "MIC": [""], "PHS": [""], "PLA": [""], "SPA": [""]},
                          'Teknisk Fysik': {'default': [""], "MIC": [""], "PHS": [""], "PLA": [""], "SPA": [""]},

                },

                'TELPM': {'Elektroteknik': {'default': [""]},
                },

                'TIETM': {'Elektroteknik': {'default': [""], "NUEY": [""], "RENE": [""], "SENS": [""], "SMCS": [""]},
                          'Teknisk Fysik': {'default': [""], "NUEY": [""], "RENE": [""], "SENS": [""], "SMCS": [""]},

                },

                'TIMTM': {'Datalogi och datateknik': {'default': [""], "FID": [""], "LTM": [""], "VLM": [""]},
                          'Elektroteknik': {'default': [""], "FID": [""], "LTM": [""], "VLM": [""]},
                          'Teknisk Fysik': {'default': [""], "FID": [""], "LTM": [""], "VLM": [""]},
                },
                
                'TINNM': {'Datalogi och datateknik': {'default': [""], "COE": [""], "INF": [""], "MMB": [""], "NWS": [""]},
                          'Elektroteknik': {'default': [""], "COE": [""], "INF": [""], "MMB": [""], "NWS": [""]}
                },
                
                'TIVNM': {'Datalogi och datateknik': {'default': ["II246X"], "AUSM": ["II246X"], "AUSY": ["II246X"], "CLNI": ["II246X"], "CLNS": ["II246X"], "DAMO": ["II246X"], "DASC": ["II246X"], "DASE": ["II246X"], "DMTE": ["II246X"], "DMTK": ["II246X"], "HCID": ["II246X"], "HCIN": ["II246X"], "INSM": ["II246X"], "VCCN": ["II246X"], "VCCO": ["II246X"] },
                          'Elektroteknik': {'default': ["IL246X"], "INSY": ["IL246X"], "ITAK": ["IL246X"], "ITAR": ["IL246X"]}
                },

                'TNTEM':  {'Elektroteknik': {'default': ["IL226X"], "NTEA": [""], "NTEA": [""]},
                          'Teknisk Fysik': {'default': ["IF226X"], "NTEA": [""], "NTEA": [""]}
                },

                'TSEDM': {'Datalogi och datateknik': {'default': ["II226X"], "DASC": [""], "PVT": [""]}
                },



                'Masterexjobb på KTH (ej civing)': {'Datalogi och datateknik': {'default': ["II226X"]},
                          'Elektroteknik': {'default': ["IL226X"]},
                          'Teknisk Fysik': {'default': ["IF226X"]},
                },
                

                'Masterexjobb utan program': {'Datalogi och datateknik': {'default': ["II227X"]},
                          'Elektroteknik': {'default': ["IL227X"]},
                          'Teknisk Fysik': {'default': ["IF227X"]},
                }
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

