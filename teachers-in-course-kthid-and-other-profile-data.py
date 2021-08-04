#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./teachers-in-course-kthid-and-other-profile-data.py -c course_id
#
# Output: XLSX spreadsheet with teachers in the course and add some KTH profile information
#
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./list_your_courses.py --config config-test.json
#
# Example:
# ./teachers-in-course-kthid-and-other-profile-data.py  11
#
# ./teachers-in-course-kthid-and-other-profile-data.py   --config config-test.json -c 25434
#
# 
# G. Q. Maguire Jr.
#
# based on earlier teachers-in-course.py
#
# 2021.08.04
#

import requests, time
import pprint
import argparse
import sys
import json

# Use Python Pandas to create XLSX files
import pandas as pd

# Import urlopen() for either Python 2 or 3.
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from PIL import Image

#############################
###### EDIT THIS STUFF ######
#############################

global canvas_baseUrl	# the base URL used for access to Canvas
global canvas_header	# the header for all HTML requests
global canvas_payload	# place to store additionally payload when needed for options to HTML requests

global host	# the base URL
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(args):
    global canvas_baseUrl, canvas_header, canvas_payload
    global host, header
    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    config_file=args["config"]

    try:
        with open(config_file) as json_data_file:
            try:
                configuration = json.load(json_data_file)
                access_token=configuration["canvas"]["access_token"]

                canvas_baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

                canvas_header = {'Authorization' : 'Bearer ' + access_token}
                canvas_payload = {}

                kth_info=configuration.get("KTH_API", None)
                if kth_info:
                    key=configuration["KTH_API"]["key"]
                    host=configuration["KTH_API"]["host"]
                    header = {'api_key': key, 'Content-Type': 'application/json', 'Accept': 'application/json' }
                    payload = {}
                else:
                    print("could not get KTH_API info")
            except:
                print("Unable to load JSON information")
    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()


# create the following dict to use as an associate directory about users
selected_user_data={}


def users_in_course(course_id):
    user_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(canvas_baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100'}
    r = requests.get(url, params=extra_parameters, headers = canvas_header)
    if Verbose_Flag:
        print("result of getting enrollments: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            user_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=canvas_header)  
            page_response = r.json()  
            for p_response in page_response:  
                user_found_thus_far.append(p_response)
    return user_found_thus_far


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

# KTH API call(s)

def get_user_by_kthid(kthid):
    global host, header
    # Use the KTH API to get the user information give an orcid
    #"#{$kth_api_host}/profile/v1/kthId/#{kthid}"

    url = "{0}/profile/v1/kthId/{1}".format(host, kthid)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting profile: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return []


def main(argv):
    global Verbose_Flag

    argp = argparse.ArgumentParser(description="thesis_titles.py: to collect thesis titles")

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

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]
    if Verbose_Flag:
        print("Configuration file : {}".format(args["config"]))

    initialize(args)

    course_id=args["canvas_course_id"]
    users=users_in_course(course_id)

    teachers=list()
    for u in users:
        if u['type'] == 'TeacherEnrollment':
            teachers.append(u)

    teacher_names_sortable=list()
    for u in teachers:
        kthid=u.get('sis_user_id', None)
        if kthid:
            kthprofile_data=get_user_by_kthid(kthid)
            defaultLanguage_info=kthprofile_data.get('defaultLanguage', None)
            if defaultLanguage_info:
                u['defaultLanguage']=defaultLanguage_info

            title_info=kthprofile_data.get('title', None)
            if title_info:
                swedish_title=title_info.get('sv', None)
                if swedish_title:
                    u['title_sv']=swedish_title
                english_title=title_info.get('en', None)
                if english_title:
                    u['title_en']=english_title
            researcher_info=kthprofile_data.get('researcher', None)
            if researcher_info:
                researchGate_info=researcher_info.get('researchGate', None)
                if researchGate_info:
                    u['researchGate']=researchGate_info
                googleScholarId_info=researcher_info.get('googleScholarId', None)
                if googleScholarId_info:
                    u['googleScholarId']=googleScholarId_info
                scopusId_info=researcher_info.get('scopusId', None)
                if scopusId_info:
                    u['scopusId']=scopusId_info
                researcherId_info=researcher_info.get('researcherId', None)
                if researcherId_info:
                    u['researcherId']=researcherId_info
                orcid_info=researcher_info.get('orcid', None)
                if orcid_info:
                    u['orcid']=orcid_info

            worksFor_info=kthprofile_data.get('worksFor', None)
            if worksFor_info:
                items=worksFor_info.get('items', None)
                if items:
                    for item in items:
                        ipath=item.get('path', None)
                        if ipath:
                            level_num=ipath.count('/')
                            if level_num == 1:
                                u['L1_path']=ipath
                                l1_name=item.get('name', None)
                                u['L1']=l1_name
                                l1_nameEn=item.get('nameEn', None)
                                u['L1_en']=l1_nameEn
                            elif level_num == 2:
                                u['L2_path']=ipath
                                l2_name=item.get('name', None)
                                u['L2']=l2_name
                                l2_nameEn=item.get('nameEn', None)
                                u['L2_en']=l2_nameEn
                            elif level_num == 3:
                                u['L3_path']=ipath
                                l3_name=item.get('name', None)
                                u['L3']=l3_name
                                l3_nameEn=item.get('nameEn', None)
                                u['L3_en']=l3_nameEn
                            elif level_num == 4:
                                u['L4_path']=ipath
                                l4_name=item.get('name', None)
                                u['L4']=l4_name
                                l4_nameEn=item.get('nameEn', None)
                                u['L4_en']=l4_nameEn
                            else:
                                print("Do not know how to handle an organizaiton level of {}".format(level_num))

    if Verbose_Flag:
        print("teacher_names_sortable={0}".format(teacher_names_sortable))

    # teacher_names_sortable_sorted=list()
    # if len(teacher_names_sortable) > 0:
    #     teacher_names_sortable_sorted=sorted(teacher_names_sortable)
    #     print("teacher_names_sortable_sorted={0}".format(teacher_names_sortable_sorted))

    if (teachers):
        teachers_df=pd.json_normalize(teachers)
                     
        fields_to_drop=['id', 'course_id', 'created_at', 'updated_at', 'associated_user_id', 'start_at', 'end_at', 'course_section_id', 'root_account_id', 'limit_privileges_to_course_section', 'role', 'role_id', 'last_activity_at', 'last_attended_at', 'total_activity_time', 'sis_account_id', 'sis_course_id', 'course_integration_id', 'sis_section_id', 'section_integration_id', 'user.created_at', 'type', 'enrollment_state']
        
        teachers_df.drop(fields_to_drop, axis=1, inplace=True)

        # drop duplicate rows
        teachers_df.drop_duplicates(ignore_index=True, inplace=True, keep='last')

        # the following was inspired by the section "Using XlsxWriter with Pandas" on http://xlsxwriter.readthedocs.io/working_with_pandas.html
        # set up the output write
        output_filename="teachers-{}.xlsx".format(course_id)
        writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
        teachers_df.to_excel(writer, sheet_name='Teachers')

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
