#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./extract_diva2_ids_from_mods.py filename
#
# Output: diva2_ids.xlsx
#           a spreadsheet of diva2 ids
#
#
# Input file should contain MODS entries, such as output by: diva-get_bibmods_theses_school.py EECS 2018
#
# G. Q. Maguire Jr.
#
#
# 2019.05.09
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


def get_diva2ids(xml):
    list_of_diva2_ids=list()
    #
    found=xml.findAll('recordIdentifier')
    if found:
        if Verbose_Flag:
            print("length={0}, found={1}".format(len(found), found ))
        for idx, singlerow in enumerate(found):
            h1=singlerow.string
            if Verbose_Flag:
                print("h1 {0}={1}".format(idx, h1))
            if h1:
                list_of_diva2_ids.append(h1)
    return list_of_diva2_ids



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
        print("Insuffient arguments - MODS_filename")
        sys.exit()
    else:
        mods_filename=remainder[0]

    input_file=open(mods_filename, 'rb')
    xml=BeautifulSoup(input_file, 'lxml-xml')
    if Verbose_Flag:
        print("Finished parsing the xml")

    ids=get_diva2ids(xml)

    ids_df= pd.DataFrame(ids, columns=['diva2 ids'])

    writer = pd.ExcelWriter('diva2_ids.xlsx', engine='xlsxwriter')

    ids_df.to_excel(writer, sheet_name='Sheet1')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == "__main__": main()

