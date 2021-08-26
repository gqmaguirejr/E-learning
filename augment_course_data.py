#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./augment_course_data.py -s school_acronym
#
# reads in course data from courses-in-{}.xlsx
#
# outputs an updated spreadsheet courses-in-{}-augmented.xlsx
#
# G. Q. Maguire Jr.
#
# 2021-08-26
#
# based on earlier augment_list__of_students_in_course_with_group.py
#

from pprint import pprint
import requests, time
import json
import argparse
import sys
import re
import datetime

# Use Python Pandas to create XLSX files
import pandas as pd

def main(argv):
    global Verbose_Flag
    global testing


    argp = argparse.ArgumentParser(description="thesis_titles_by_school.py: to collect thesis titles")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-s', '--school', type=str, default='EECS',
                      help="acronyms for a school within KTH")

    argp.add_argument('-y', '--year', type=int, default='2020',
                      help="starting year")

    args = vars(argp.parse_args(argv))
    Verbose_Flag=args["verbose"]

    # read the sheet of Students in
    input_file="courses-in-{}.xlsx".format(args["school"])
    course_codes_df = pd.read_excel(open(input_file, 'rb'), sheet_name='course codes used')
    course_round_info_df = pd.read_excel(open(input_file, 'rb'), sheet_name='Rounds')

    # delete column named "Unnamed: 0"
    del course_codes_df['Unnamed: 0']
    del course_round_info_df['Unnamed: 0']

    course_round_info_df.insert(1, 'cycle', '')
    for index, row in course_round_info_df.iterrows():
        course_code=row['code']
        if len(course_code) == 6:
            course_cycle=int(course_code[2])
            course_round_info_df.at[index, 'cycle']=course_cycle
        elif  len(course_code) == 7:
            course_cycle=int(course_code[3])
            course_round_info_df.at[index, 'cycle']=course_cycle
        else:
            print("Unable to determine cycle for course code={}".format(course_code))

    gru_rounds=course_round_info_df.copy(deep=True)
    gru_rounds.drop(gru_rounds[gru_rounds.cycle == 3].index, inplace=True)
    gru_rounds.sort_values(by='number_of_students', ascending=False, inplace=True)

    fofu_rounds=course_round_info_df.copy(deep=True)
    fofu_rounds.drop(fofu_rounds[fofu_rounds.cycle != 3].index, inplace=True)
    fofu_rounds.sort_values(by='number_of_students', ascending=False, inplace=True)

    totals_by_course_code_df=course_round_info_df.groupby(['code'])['number_of_students'].sum().reset_index()
    totals_by_course_code_df.sort_values(by='number_of_students', ascending=False, inplace=True)
    total_students=totals_by_course_code_df['number_of_students'].sum()
    print("total_students={}".format(total_students))
    totals_by_course_code_df['%']=100.0 * totals_by_course_code_df['number_of_students'] / total_students
    totals_by_course_code_df['cumulative %']=totals_by_course_code_df['%'].cumsum()

    output_file="courses-in-{}-augmented.xlsx".format(args["school"])
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    course_codes_df.to_excel(writer, sheet_name='course codes used')
    course_round_info_df.to_excel(writer, sheet_name='Rounds')

    gru_rounds.to_excel(writer, sheet_name='GRU rounds')
    fofu_rounds.to_excel(writer, sheet_name='FOFU rounds')

    totals_by_course_code_df.to_excel(writer, sheet_name='Totals by course code')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
