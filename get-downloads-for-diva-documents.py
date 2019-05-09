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

def get_download_count(diva_page):
    xml=BeautifulSoup(diva_page, features="html.parser")
    #<div class="attachment">
    p1=xml.find('div', attrs={'class': 'attachment'})
    #<span class="singleRow">94 downloads</span>
    for singlerow in p1.find('span', attrs={'class': 'singleRow'}):
        h1=singlerow.string
        if h1:
            offset_to_download_string=h1.find('downloads')
            count_string=h1[0:(offset_to_download_string)]
            print("count_string={0}".format(count_string))
            return int(count_string)
    return 0

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
    
    for idx, row in ids_df.iterrows():
        diva2_id=row[column_names[0]].split(':')[1]
        if Verbose_Flag:
            print("ids_df[{0}]={1}".format(idx, diva2_id))
        page=get_diva_page(diva2_id)
        count=get_download_count(page)
        ids_df.loc[idx, 'Downloads']=count

    writer = pd.ExcelWriter('diva-downloads.xlsx', engine='xlsxwriter')

    ids_df.to_excel(writer, sheet_name='Downloads')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == "__main__": main()

