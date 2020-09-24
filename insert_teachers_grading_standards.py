#!/usr/bin/python3
#
# ./insert_teachers_grading_standards.py -a account_id cycle_number school_acronym course_code
# ./insert_teachers_grading_standards.py   course_id cycle_number school_acronym course_code
#
# Generate a "grading standard" scale with the names of teachers as the "grades".
# Note that if the grading scale is already present, it does nothing unless the "-f" (force) flag is set.
# In the latter case it adds the grading scale.
#
# G. Q. Maguire Jr.
#
# 2020.09.24
#
# Test with
#  ./insert_teachers_grading_standards.py -v 11 2 EECS II246X
#  ./insert_teachers_grading_standards.py -v --config config-test.json 11 2 EECS II246X
# 
#

import csv, requests, time
import optparse
import sys
import json


#############################
###### EDIT THIS STUFF ######
#############################

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
                     baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

                     header = {'Authorization' : 'Bearer ' + access_token}
                     payload = {}
       except:
              print("Unable to open configuration file named {}".format(config_file))
              print("Please create a suitable configuration file, the default name is config.json")
              sys.exit()


##############################################################################
## ONLY update the code below if you are experimenting with other API calls ##
##############################################################################

def create_grading_standard(course_or_account, id, name, scale):
       global Verbose_Flag
       # Use the Canvas API to create an grading standard
       # POST /api/v1/accounts/:account_id/grading_standards
       # or
       # POST /api/v1/courses/:course_id/grading_standards

       # Request Parameters:
       #Parameter		        Type	Description
       # title	Required	string	 The title for the Grading Standard.
       # grading_scheme_entry[][name]	Required	string	The name for an entry value within a GradingStandard that describes the range of the value e.g. A-
       # grading_scheme_entry[][value]	Required	integer	 -The value for the name of the entry within a GradingStandard. The entry represents the lower bound of the range for the entry. This range includes the value up to the next entry in the GradingStandard, or 100 if there is no upper bound. The lowest value will have a lower bound range of 0. e.g. 93

       if course_or_account:
              url = "{0}/courses/{1}/grading_standards".format(baseUrl, id)
       else:
              url = "{0}/accounts/{1}/grading_standards".format(baseUrl, id)

       if Verbose_Flag:
              print("url: {}".format(url))

       payload={'title': name,
                'grading_scheme_entry': scale
       }
    
       if Verbose_Flag:
              print("payload={0}".format(payload))

       r = requests.post(url, headers = header, json=payload)
       if r.status_code == requests.codes.ok:
              page_response=r.json()
              print("inserted grading standard")
              return True
       print("r.status_code={0}".format(r.status_code))
       return False

def get_grading_standards(course_or_account, id):
       global Verbose_Flag
       # Use the Canvas API to get a grading standard
       # GET /api/v1/accounts/:account_id/grading_standards
       # or
       # GET /api/v1/courses/:course_id/grading_standards

       # Request Parameters:
       #Parameter		        Type	Description
       if course_or_account:
              url = "{0}/courses/{1}/grading_standards".format(baseUrl, id)
       else:
              url = "{0}/accounts/{1}/grading_standards".format(baseUrl, id)

       if Verbose_Flag:
              print("url: " + url)

       r = requests.get(url, headers = header)
       if r.status_code == requests.codes.ok:
              page_response=r.json()
              return page_response
       return None

def main():
       global Verbose_Flag
       global Use_local_time_for_output_flag
       global Force_appointment_flag

       Use_local_time_for_output_flag=True

       parser = optparse.OptionParser()

       parser.add_option('-v', '--verbose',
                         dest="verbose",
                         default=False,
                         action="store_true",
                         help="Print lots of output to stdout"
       )

       parser.add_option('-a', '--account',
                         dest="account",
                         default=False,
                         action="store_true",
                         help="Apply grading scheme to indicated account"
       )

       parser.add_option('-f', '--force',
                         dest="force",
                         default=False,
                         action="store_true",
                         help="Replace existing grading scheme"
       )

       parser.add_option("--config", dest="config_filename",
                         help="read configuration from FILE", metavar="FILE")



       options, remainder = parser.parse_args()

       Verbose_Flag=options.verbose
       Force_Flag=options.force

       if Verbose_Flag:
              print('ARGV      :', sys.argv[1:])
              print('VERBOSE   :', options.verbose)
              print('REMAINING :', remainder)
              print("Configuration file : {}".format(options.config_filename))

       course_or_account=True
       if options.account:
              course_or_account=False
       else:
              course_or_account=True

       if Verbose_Flag:
              print("Course or account {0}: course_or_account = {1}".format(options.account,
                                                                            course_or_account))

       if (len(remainder) < 4):
              print("Insuffient arguments must provide a course_id|account_id cycle_number school_acronym course_code\n")
              return

       initialize(options)

       canvas_course_id=remainder[0]
       if Verbose_Flag:
              if course_or_account:
                     print("course_id={0}".format(canvas_course_id))
              else:
                     print("account_id={0}".format(canvas_course_id))

       cycle_number=remainder[1] # note that cycle_number is a string with the value '1' or '2'
       school_acronym=remainder[2]
       course_code=remainder[3]

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

       canvas_grading_standards=dict()
       available_grading_standards=get_grading_standards(True, canvas_course_id)
       if available_grading_standards:
              for s in available_grading_standards:
                     old_id=canvas_grading_standards.get(s['title'], None)
                     if old_id and s['id'] < old_id: # use only the highest numbered instance of each scale
                            continue
       else:
              canvas_grading_standards[s['title']]=s['id']
              if Verbose_Flag:
                     print("title={0} for id={1}".format(s['title'], s['id']))

       if Verbose_Flag:
              print("canvas_grading_standards={}".format(canvas_grading_standards))

       potential_grading_standard_id=canvas_grading_standards.get(course_code, None)
       if Force_Flag or (not potential_grading_standard_id):
              name=course_code
              scale=[]
              number_of_examiners=len(all_course_examiners[course_code])
              index=0
              for e in all_course_examiners[course_code]:
                     i=number_of_examiners-index
                     d=dict()
                     d['name']=e
                     d['value'] =(float(i)/float(number_of_examiners))*100.0
                     print("d={0}".format(d))
                     scale.append(d)
                     index=index+1
              scale.append({'name': 'none selected', 'value': 0.0})

              status=create_grading_standard(course_or_account, canvas_course_id, name, scale)
              print("status={0}".format(status))
              if Verbose_Flag and status:
                     print("Created new grading scale")

if __name__ == "__main__": main()
