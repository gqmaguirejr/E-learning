#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./get-downloads-for-diva-documents.py urns.xlsx
#
# Output: diva-downloads.xlsx
#           a spreadsheet of download data
#
#
# Input
# URNs are of the form: urn:nbn:se:kth:diva-230996
# DiVA, id: diva2:1221139
# this corresponds to a web page at http://kth.diva-portal.org/smash/record.jsf?pid=diva2%3A1221139&dswid=-8502
#
# G. Q. Maguire Jr.
#
#
# 2019.05.08
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
######    DiVA related   ######
################################
DiVAUrlbase = 'http://kth.diva-portal.org/smash/record.jsf?pid=diva2%3A'


def get_diva_page(diva_id):
    global Verbose_Flag
    #
    url = "{0}{1}&dswid=-8502".format(DiVAUrlbase, diva_id)
    if Verbose_Flag:
        print("url: " + url)
    #
    r = requests.get(url)
    if Verbose_Flag:
        print("result of getting get_diva_page: {}".format(r.text))
    #
    if r.status_code == requests.codes.ok:
        return r.text           # simply return the XML
    #
    return None

def get_download_count(xml):
    #<div class="attachment">
    p1=xml.find('div', attrs={'class': 'attachment'})
    if p1:
        #<span class="singleRow">94 downloads</span>
        found=p1.find('span', attrs={'class': 'singleRow'})
        if found:
            for singlerow in found:
                h1=singlerow.string
                if h1:
                    offset_to_download_string=h1.find('downloads')
                    count_string=h1[0:(offset_to_download_string)]
                    if Verbose_Flag:
                        print("count_string={0}".format(count_string))
                    return int(count_string.strip())
    # no full text
    return -1

def get_hits_count(xml):
    #<div class="attachment">
    found=xml.findAll('span', attrs={'class': 'singleRow'})
    # look for <span class="singleRow">Total: 735                     hits</span>
    if found:
        if Verbose_Flag:
            print("found={0}, length={1}".format(found, len(found)))
        for idx, singlerow in enumerate(found):
            h1=singlerow.string
            if Verbose_Flag:
                print("h1{0}={1}".format(idx, h1))
            if h1:
                if h1.find('Total:')>=0:
                    offset_to_hits_string=h1.find('hits')
                    hits_string=h1[0:(offset_to_hits_string)].strip()
                    if Verbose_Flag:
                        print("hits_string={0}".format(hits_string))
                    total_hits_string=hits_string.split(':')
                    return int(total_hits_string[1].strip())
    # no hits information
    return -1

def get_year_and_language(xml):
    found=xml.findAll('span', attrs={'class': 'displayFields'})
    # look for <span class="displayFields">1995 (Swedish)</span>
    if found:
        if Verbose_Flag:
            print("found={0}, length={1}".format(found, len(found)))
        for idx, singlerow in enumerate(found):
            h1=singlerow.string
            if Verbose_Flag:
                print("h1 {0}={1}".format(idx, h1))
            if h1:
                if h1.find('(English)')>=0 or h1.find('(Swedish)')>=0:
                    fields=h1.split('(')
                    year_string=fields[0].strip()
                    lang_string=fields[1].strip(')')
                    if Verbose_Flag:
                        print("year_string={0}".format(year_string))
                        print("lang_string={0}".format(lang_string))
                    return {'year': int(year_string),
                            'lang': lang_string}
    # no year and language information
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
        print("Insuffient arguments - file of DiVA IDs")
        sys.exit()
    else:
        file_of_DiVA_ids=remainder[0]

    ids_df=pd.read_excel(open(file_of_DiVA_ids, 'rb'), sheet_name='Sheet1')

    column_names=list(ids_df)

    ids_df['Downloads']=None
    ids_df['Hits']=None
    ids_df['Year']=None
    ids_df['Language']=None
    
    for idx, row in ids_df.iterrows():
        diva2_id=row['diva2 ids'].split(':')[1]
        if Verbose_Flag:
            print("ids_df[{0}]={1}".format(idx, diva2_id))
        page=get_diva_page(diva2_id)
        xml=BeautifulSoup(page, features="html.parser")
        count=get_download_count(xml)
        ids_df.loc[idx, 'Downloads']=count
        hits=get_hits_count(xml)
        ids_df.loc[idx, 'Hits']=hits
        y_l=get_year_and_language(xml)
        ids_df.loc[idx, 'Year']=y_l['year']
        ids_df.loc[idx, 'Language']=y_l['lang']

    writer = pd.ExcelWriter('diva-downloads.xlsx', engine='xlsxwriter')

    ids_df.to_excel(writer, sheet_name='Downloads')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == "__main__": main()

