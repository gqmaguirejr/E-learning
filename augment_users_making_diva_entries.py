#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# augment_users_making_diva_entries.py spreadsheet.xlsx
#
# Purpose: to take the result from users_making_diva_entries.py and add the user's first and last names from LDAP
#
# Output: an updated spreadsheet with "-augmented" added to the base filename
#
#
# Example:
# ./augment_users_making_diva_entries.py --file diva_admin_stats.xlsx
#   by default it processes the diva_admin_stats.xlsx file
#
# 2022-12-07 G. Q. Maguire Jr.
# buids on augment-kth-dept-people-URL.py
#
import re
import sys
import subprocess

import json
import argparse
import os                       # to make OS calls, here to get time zone info

import time
import pprint



import openpyxl
# Use Python Pandas to create XLSX files
import pandas as pd

import datetime

import shlex


def get_user_by_kthid(kthid):
    # use LDAP to get the user's information
    # ldapsearch -LLL -ZZ -x -h ldap.kth.se -b ou=Unix,dc=kth,dc=se ugkthid=$*
    #result=subprocess.run(['ldapsearch', '-LLL', '-ZZ', '-x', '-h', 'ldap.kth.se', '-b', 'ou=Unix,dc=kth,dc=se', f'ugkthid={kthid}']], stdout=subprocess.PIPE).stdout.decode('utf-8'))
    #cmd_line=f'ldapsearch -LLL -ZZ -x -h ldap.kth.se -b ou=Unix,dc=kth,dc=se ugkthid={kthid}'
    #args_to_use=shlex.split(cmd_line)
    #print(args_to_use)

    result=subprocess.run(['ldapsearch', '-LLL', '-ZZ', '-x', '-h', 'ldap.kth.se', '-b', 'ou=Unix,dc=kth,dc=se', f'ugkthid={kthid}'], stdout=subprocess.PIPE).stdout.decode('utf-8')

    family_name=''
    first_name= ''
    for l in result.split('\n'):
        target='sn: '
        if l.find(target) == 0:
            family_name=l[len(target):]
        target='givenName: '
        if l.find(target) == 0:
            first_name=l[len(target):]

    return {'first_name': first_name, 'last_name': family_name}

def main(argv):
    global Verbose_Flag
    global testing

    argp = argparse.ArgumentParser(description="augment_users_making_diva_entries.py: augment with user data from LDAP")
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
                      default="diva_admin_stats.xlsx",
                      help="XSLX file to process"
                      )

    args = vars(argp.parse_args(argv))
    
    Verbose_Flag=args["verbose"]

    #initialize(args)
    
    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))

    if testing:
        print("user={}".format(get_user_by_kthid('u1d13i2c')))
        return

    input_filename=args["file"]
    output_filename=input_filename[:-5]+'-augmented.xlsx'
    print("input_filename={0}, output_filename={1}".format(input_filename, output_filename))
    if not testing:
        writer = pd.ExcelWriter(f'{output_filename}', engine='xlsxwriter')

    working_df = pd.read_excel(input_filename, engine='openpyxl', index_col=0)
    working_df['ldap_firstName'] = working_df["ldap_firstName"].map(str)
    working_df['ldap_lastName']  = working_df["ldap_lastName"].map(str)

    working_df.reset_index(drop=True, inplace=True)

    for idx, row in working_df.iterrows():
    #print("row={}".format(row))
        kthid=row['diva_admin']
        if Verbose_Flag:
            print("kthid={}".format(kthid))
        try:
            user=get_user_by_kthid(kthid)
        except Exception as e:
            print("error for {}".format(user_home_url))
            print (e.__class__)
            continue
        
        if Verbose_Flag:
            print("user={}".format(user))

        working_df.at[idx, 'ldap_firstName']=user['first_name']
        working_df.at[idx, 'ldap_lastName']=user['last_name']

    # Eliminate the index pseudo column
    working_df.reset_index(drop=True, inplace=True)

    #
    if not testing:
        working_df.to_excel(writer, sheet_name='augmented')

    # Close the Pandas Excel writer and output the Excel file.
    if not testing:
        writer.close()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
