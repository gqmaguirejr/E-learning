#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./EECS_theses_in_DIVA/get_full_text_from_diva.py diva.xlsx
#
# Fetch the full-text for each thesis in the list - using the URL in FullTextLink
#
# Output:
#   outputs file with a name of the form {PID}-FULLTEXT01.pdf
#   if the last part of the URL is FULLTEXT01.pdf
#
#
# G. Q. Maguire Jr.
#
#
# 2022-08-09
#

import requests, time
import pprint
import optparse
import sys
import json

# Use Python Pandas to create XLSX files
import pandas as pd

from bs4 import BeautifulSoup

import faulthandler


################################
######    DiVA related   ######
################################

def get_full_text_from_diva_page(pid, url):
    global Verbose_Flag
    #
    if Verbose_Flag:
        print("url: " + url)
    #
    last_slash_in_url=url.rfind('/')
    if last_slash_in_url < 0:
        print("Cannot create filename from URL")
        return

    output_file_name="{0}-{1}".format(pid, url[last_slash_in_url+1:])
    print(f'writing thesis to {output_file_name}')

    headers = {
        'Accept-Language': 'en-US;q=0.7,en;q=0.3',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
    }
    r = requests.get(url, headers=headers)
    if Verbose_Flag:
        print("result of getting get_full_text_from_diva_page: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        with open(output_file_name, 'wb') as f:
            f.write(r.content)
        return True
    else:
        print(f'error {r.status_code} when trying to access {url}')
    #
    return None

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

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))

    if (len(remainder) < 1):
        print("Insuffient arguments - spreadsheet_name")
        sys.exit()
    else:
        spreadsheet_name=remainder[0]

    if len(remainder) >= 2:
        skip_to_row=int(remainder[1])
    else:
        skip_to_row=False

    diva_df=pd.read_excel(open(spreadsheet_name, 'rb'))

    column_names=list(diva_df)
    
    faulthandler.enable()

    for idx, row in diva_df.iterrows():
        if skip_to_row and idx < skip_to_row:
            continue
        url=row['FullTextLink']
        author=row['Name']
        pid=row['PID']
        if pd.isna(url):
            print("no full text for theesis by {}".format(author))
        else:
            print(f'{idx}: {author}  {url}')
            get_full_text_from_diva_page(pid, url)

if __name__ == "__main__": main()
