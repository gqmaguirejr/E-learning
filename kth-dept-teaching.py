#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# kth-dept-teaching.py url
#
# Purpose: to walk dept and collct who is a teacher in what
#
# Output: a spreadsheet named: personnel.xlsx with the data boua the persons in the EECS school by department
#
#
# Example:
# kth-dept-teaching.py https://www.kth.se/directory/j/jh
#
# 2022-04-08 G. Q. Maguire Jr.
#
import re
import sys
import subprocess

import json
import argparse
import os			# to make OS calls, here to get time zone info

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

global host	# the base URL
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

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

    argp.add_argument('--url',
                      type=str,
                      default=None,
                      help="url to dept"
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
        'EECS VS': 'https://www.kth.se/directory/j/jb',
        'HCT': 'https://www.kth.se/directory/j/jm',
        'IS': 'https://www.kth.se/directory/j/jr'
        }

    profile_urls=dict()
    personnel=dict()

    # initialize a dict of empty lists
    profile_urls=dict()
    for dept in depts:
        profile_urls[dept]=[]
        personnel[dept]=[]

    for dept in depts:
        r = requests.get(depts[dept])
        #print(r.status_code)
        if r.status_code == requests.codes.ok:
            # print(r.text)
            lines=r.text.splitlines(keepends=False)
            print("number of lines is {}".format(len(lines)))
            for l in lines:
                if l.find('<td class="lastname">') > 0:
                    pattern_1='<a href="'
                    start_offset_1=l.find(pattern_1)
                    if start_offset_1 > 0:
                        remainder_1=l[start_offset_1+len(pattern_1):]
                        pattern_2='?'
                        start_offset_2=remainder_1.find(pattern_2)
                        profile_url=remainder_1[:start_offset_2]
                        profile_urls[dept].append(profile_url)
    
    for dept in depts:
        for index, url_p in enumerate(profile_urls[dept]):
            pattern='https://www.kth.se/profile/'
            offset_to_name=url_p.find(pattern)
            if offset_to_name >= 0:
                name=url_p[offset_to_name+len(pattern):]
                user_info=get_user_by_name(name)
                if type(user_info) is not dict:
                    print("name={0} type is {1}".format(name, type(user_info)))
                    continue
                #print("{0}:{1}".format(name, user_info))
                # entry=dict()
                # if user_info.get('kthId'):
                #     entry['kthId']=user_info['kthId']
                # entry['username']=user_info['username']
                # if user_info.get('title'):
                #     entry['title']=user_info['title']
                # if user_info.get('emailAddress'):
                #     entry['emailAddress']=user_info['emailAddress']
                
                # if user_info['researcher']:
                #     entry['researchGate']=user_info['researcher'].get('researchGate')
                #     entry['googleScholarId']=user_info['researcher'].get('googleScholarId')
                #     entry['scopusId']=user_info['researcher'].get('scopusId')
                #     entry['researcherId']=user_info['researcher'].get('researcherId')
                # if user_info['courses']:
                #     c_user_info=[]
                #     for c in user_info['courses']:
                #         if user_info['courses'].get('code'):
                #             c_user_info.append({user_info['courses']['code']: user_info['courses']['roles']})
                #     entry['courses']=c_user_info
                personnel[dept].append(user_info)

    # for dept in depts:
    #     print("personnel[dept]={}".format(personnel[dept]))

    writer = pd.ExcelWriter('personnel.xlsx', engine='xlsxwriter')
    for dept in depts:
        personnel_df=pd.json_normalize(personnel[dept])
        personnel_df.to_excel(writer, sheet_name=dept)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

