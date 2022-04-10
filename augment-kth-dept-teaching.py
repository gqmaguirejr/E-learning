#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# augment-kth-dept-teaching.py --file filename.xlsx
#
# Purpose: to take the result from kth-dept-teaching.py and expand on the role of each person in the courses that are taught.
#
# Output: an updated spreadsheet with "-augmented" added to the base filename
#
#
# Example:
# ./augment-kth-dept-teaching.py
#   by default it processes the personal.xlsx file
#
# 2022-04-10 G. Q. Maguire Jr.
# buids on kth-dept-teaching.py
#
import re
import sys
import subprocess

import json
import argparse
import os                       # to make OS calls, here to get time zone info

import requests

import time

import pprint

from collections import defaultdict

# Use Python Pandas to create XLSX files
import pandas as pd

from ast import literal_eval

import datetime
import isodate                  # for parsing ISO 8601 dates and times
import pytz                     # for time zones
from dateutil.tz import tzlocal

global host     # the base URL
global header   # the header for all HTML requests
global payload  # place to store additionally payload when needed for options to HTML requests

# 
def initialize(options):
    global host, header, payload

    config_file='config.json'

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            key=configuration["KTH_API"]["key"]
            host=configuration["KTH_API"]["host"]
            header = {'api_key': key, 'Content-Type': 'application/json', 'Accept': 'application/json' }
            payload = {}
    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()

def get_user_by_name(name):
    # Use the KTH API to get the user information give an orcid
    #"#{$kth_api_host}/profile/v1/name/#{name}"

    url = "{0}/profile/v1/user/{1}".format(host, name)
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
    global testing

    argp = argparse.ArgumentParser(description="kth-dept-teaching.py: to walk dept and collct who is a teacher in what")
    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('--file',
                      type=str,
                      default="personnel.xlsx",
                      help="XSLX file to process"
                      )

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")


    args = vars(argp.parse_args(argv))
    
    Verbose_Flag=args["verbose"]

    initialize(args)
    
    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))

    #dept_url=args['url']
    #print("URL is {}".format(dept_url))

    base_eecs_url='https://www.kth.se/directory/j'

    depts={
        'CS': 'https://www.kth.se/directory/j/jh',
        'EE': 'https://www.kth.se/directory/j/jj',
        # 'EECS VS': 'https://www.kth.se/directory/j/jb',   # not relevant for augmentation, possible dropt this sheet
        'HCT': 'https://www.kth.se/directory/j/jm',
        'IS': 'https://www.kth.se/directory/j/jr'
    }
    
    if not testing:
        writer = pd.ExcelWriter('personnel-augmented.xlsx', engine='xlsxwriter')

    summary=dict()
    personell_summary=dict()
       
    for dept in depts:
        course_code_info=dict()
        personnel_roles=dict()
        # number of degree project courses
        degree_project_courses_cycle1=[]
        degree_project_courses_cycle2=[]
        # number of non-courses courses
        courses_cycle1=[]
        courses_cycle2=[]
        courses_cycle3=[]

        print("dept={}".format(dept))
        working_df = pd.read_excel(open(args['file'], 'rb'), sheet_name=dept)
        # process the dept's data
        personell_summary[dept]=dict()

        for index, row in working_df.iterrows():
            course_items=row['courses.items']
            course_items=literal_eval(course_items)
            for course in course_items:
                course_code=course['code']
                course_roles=course['roles']
                course_titles=course['title']
                if course_code not in course_code_info:
                    course_code_info[course_code]=course_titles

        # things to do by dept
        if Verbose_Flag:
            print("Number of course codes is {}".format(len(course_code_info)))
        summary[dept]=dict()
        summary[dept]['Number of course codes']=len(course_code_info)

        for course_code in course_code_info:
            if len(course_code) == 6:
                if course_code[2] == '1':
                    if course_code.endswith('X'):
                        degree_project_courses_cycle1.append(course_code)
                    else:
                        courses_cycle1.append(course_code)
                elif course_code[2] == '2':
                    if course_code.endswith('X'):
                        degree_project_courses_cycle2.append(course_code)
                    else:
                        courses_cycle2.append(course_code)
            elif  len(course_code) == 7:
                if course_code[3] == '3':
                    courses_cycle3.append(course_code)
            else:
                print("Unexpect course code={}".format(course_code))

        print("Number of courses, cycle1={0}, cycle2={1}, cycle3={2}".format(len(courses_cycle1), len(courses_cycle2), len(courses_cycle3)))
        summary[dept]['Cycle 1']=len(courses_cycle1)
        summary[dept]['Cycle 2']=len(courses_cycle2)
        summary[dept]['Cycle 3']=len(courses_cycle3)

        print("Number of degree project courses, cycle1={0}, cycle2={1}".format(len(degree_project_courses_cycle1), len(degree_project_courses_cycle2)))
        summary[dept]['Degree project coursrs - Cycle 1']=len(degree_project_courses_cycle1)
        summary[dept]['Degree project coursrs - Cycle 2']=len(degree_project_courses_cycle2)

        if Verbose_Flag:
            print("First cycle courses:")
            for c in courses_cycle1:
                print("{0}: {1}".format(c, course_code_info[c]))
            print("Second cycle courses:")
            for c in courses_cycle2:
                print("{0}: {1}".format(c, course_code_info[c]))
                print("Third cycle courses:")
            for c in courses_cycle3:
                print("{0}: {1}".format(c, course_code_info[c]))

            print("First cycle degree project courses:")
            for c in degree_project_courses_cycle1:
                print("{0}: {1}".format(c, course_code_info[c]))
            print("Second cycle degree project courses:")
            for c in degree_project_courses_cycle2:
                print("{0}: {1}".format(c, course_code_info[c]))

        # Add one column to the spreadsheet per course code
        courses_cycle1.sort()
        for c in courses_cycle1:
            working_df[c]=""
        courses_cycle2.sort()
        for c in courses_cycle2:
            working_df[c]=""
        courses_cycle3.sort()
        for c in courses_cycle3:
            working_df[c]=""

        degree_project_courses_cycle1.sort()
        for c in degree_project_courses_cycle1:
            working_df[c]=""
        degree_project_courses_cycle2.sort()
        for c in degree_project_courses_cycle2:
            working_df[c]=""


        # augment spreadsheet
        for index, row in working_df.iterrows():
            course_items=row['courses.items']
            course_items=literal_eval(course_items)

            for course in course_items:
                course_code=course['code']
                course_roles=course['roles']
                working_df.at[index, course_code]=course_roles
                worksFor=literal_eval(row['worksFor.items'])
                #[{'key': 'app.katalog3.J.JH', 'path': 'j/jh', 'name': 'CS DATAVETENSKAP', 'nameEn': 'DEPARTMENT OF COMPUTER SCIENCE', 'location': ''}, {'key': 'app.katalog3.J.JH.JHK', 'path': 'j/jh/jhk', 'name': 'PROGRAMVARUTEKN & DATORSYSTEM', 'nameEn': 'DIVISION OF SOFTWARE AND COMPUTER SYSTEMS', 'location': 'KISTAGÅNGEN 16, 16440 KISTA'}]
                longest_path=0
                for w in worksFor:
                    path=w['path']
                    if path:
                        split_path=path.split('/')
                        if len(split_path) > longest_path:
                            longest_path=len(split_path)
                            name=w['name']
                            working_df.at[index, 'worksFor.items']=name

        # sort rows
        working_df.sort_values(by=['worksFor.items', 'title.sv', 'lastName', 'firstName'], inplace=True)


        new_row=dict()
        for course in course_code_info:
            course_name=course_code_info[course].get('sv')
            new_row[course]=course_name
        working_df=working_df.append(new_row, ignore_index=True)
            
        new_row=dict()
        for course in course_code_info:
            course_name=course_code_info[course].get('en')
            new_row[course]=course_name
            working_df=working_df.append(new_row, ignore_index=True)

        # remove unwanted columns
        unwanted_columns=['Unnamed: 0', '_id', 'acceptedTerms', 'isAdminHidden', 'createdAt',
                          'telephoneNumber', 'isStaff', 'isStudent', 'city', 'postalCode',
                          'lastSynced', 'pages', 'updatedAt', 'visibilityCompiled', 'visibility',
                          'avatar.visibility', 'room.placesId', 'room.title', 'links.visibility',
                          'links.items', 'description.visibility', 'description.sv', 'description.en', 'links',
                          'socialId', 'images.big', 'images.visibility', 'description', 'room', '__v', 'courses.visibility']
        working_df.drop(unwanted_columns, inplace=True, axis=1)

        if not testing:
            working_df.to_excel(writer, sheet_name=dept)


    summary_df=pd.DataFrame()
    for dept in depts:
        summary_df=summary_df.append(summary[dept], ignore_index=True)

    summary_df.to_excel(writer, sheet_name='Summary')

    # Close the Pandas Excel writer and output the Excel file.
    if not testing:
        writer.save()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

