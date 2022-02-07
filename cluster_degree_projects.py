#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./cluster_degree_projects.py file_name.xlsx
#
# reads in data from a file
#
# outputs an updated spreadsheet finale_name_augmented.xlsx
#
# G. Q. Maguire Jr.
#
# 2022-02-01
#
# based on earlier augments-course-stats-with-plots.py
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


    argp = argparse.ArgumentParser(description="cluster_degree_projects.py: to examine the overlap between schools of main subjects")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument("--file", type=str, default='foo.xlsx',
                      help="input file")



    args = vars(argp.parse_args(argv))
    Verbose_Flag=args['verbose']

    # read in the sheets
    input_file=args['file']

    degree_project_courses_df = pd.read_excel(open(input_file, 'rb'), sheet_name='All')
    if Verbose_Flag:

        print("{}".format(degree_project_courses_df.columns))

    #Index(['Unnamed: 0', 'code', 'credits', 'creditUnitLabel', 'creditUnitAbbr',
    # 'state', 'emilSubjects', 'mainSubjects', 'mainSubjects_0_subjectCode',
    # 'mainSubjects_0_specializationCode', 'title.sv', 'title.en', 'level.sv',
    # 'level.en', 'level.level', 'level.emil', 'school.code',
    # 'school.org_unit', 'school.name.sv', 'school.name.en',
    # 'department.code', 'department.name.sv', 'department.name.en',
    # 'scbSubject.subjectCode', 'scbSubject.name.sv', 'scbSubject.name.en',
    # 'mainSubjects_0_name.sv', 'mainSubjects_0_name.en',
    # 'mainSubjects_0_specializationName.sv',
    # 'mainSubjects_0_specializationName.en', 'mainSubjects_1_subjectCode',
    # 'mainSubjects_1_specializationCode', 'mainSubjects_1_name.sv',
    # 'mainSubjects_1_name.en', 'mainSubjects_1_specializationName.sv',
    # 'mainSubjects_1_specializationName.en', 'mainSubjects_2_subjectCode',
    # 'mainSubjects_2_specializationCode', 'mainSubjects_2_name.sv',
    # 'mainSubjects_2_name.en', 'mainSubjects_2_specializationName.sv',
    # 'mainSubjects_2_specializationName.en'],

    ABE_color={'color': 'red', 'transparency': 50}
    CBH_color={'color': 'green', 'transparency': 50}
    EECS_color={'color': 'purple', 'transparency': 50}
    ITM_color={'color': 'orange', 'transparency': 50}
    SCI_color={'color': 'blue', 'transparency': 50}

    ABE_set=set()
    CBH_set=set()
    EECS_set=set()
    ITM_set=set()
    SCI_set=set()

    subjects=set()
    schools=set()

    output_file="{0}-augmented.xlsx".format(input_file[:-5])
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')


    # determine all of the subjects
    for index, row in  degree_project_courses_df.iterrows():
        school=row['school.code']
        s0=row['mainSubjects_0_name.en']
        s1=row['mainSubjects_1_name.en']
        s2=row['mainSubjects_2_name.en']
        if isinstance(school, str):
            schools.add(school)
        if isinstance(s0, str):
            subjects.add(s0)
        if isinstance(s1, str):
            subjects.add(s1)
        if isinstance(s2, str):
            subjects.add(s2)

    if Verbose_Flag:
        print("subjects={}".format(subjects))
    print("schools={}".format(schools))

    subjects_by_school=dict()
    for s in schools:
        subjects_by_school[s]=set()

    for index, row in  degree_project_courses_df.iterrows():
        school=row['school.code']
        s0=row['mainSubjects_0_name.en']
        s1=row['mainSubjects_1_name.en']
        s2=row['mainSubjects_2_name.en']
        
        if isinstance(s0, str):
            if s0 != 'Technology':
                subjects_by_school[school].add(s0)
        if isinstance(s1, str):
            if s1 != 'Technology':
                subjects_by_school[school].add(s1)
        if isinstance(s2, str):
            if s2 != 'Technology':
                subjects_by_school[school].add(s2)

    print("subjects_by_school={}".format(subjects_by_school))

    overlap_combinations=[]
    schools_list=list(schools)
    print("schools_list={}".format(schools_list))
    schools_list.sort()
    print("schools_list sorted={}".format(schools_list))

    overlapping_subjects=set()

    output_line=""
    for s in schools_list:
        output_line="{0}\t{1}".format(output_line, s)
    print(output_line)
    for s in schools_list:
        output_line="{}".format(s)
        for os in schools_list:
            if s == os:
                output_line="{0}\t ".format(output_line)        
                continue
            overlap=subjects_by_school[s].intersection(subjects_by_school[os])
            for o in overlap:
                overlapping_subjects.add(o)
            if Verbose_Flag:
                print("{0}|{1}: overlap={2}".format(s, os, overlap))
            if overlap:
                output_line="{0}\tX".format(output_line)
                if Verbose_Flag:
                    print("s={0}, os={1}, overlap={2}".format(s, os, overlap))
                combo={s, os}
                if combo not in overlap_combinations:
                    overlap_combinations.append(combo)
            else:
                output_line="{0}\t ".format(output_line)        
        print(output_line)

    print("overlap_combinations={}".format(overlap_combinations))

    print("overlapping_subjects={}".format(overlapping_subjects))

    overlapping_subjects_list=list(overlapping_subjects)
    overlapping_subjects_list.sort()

    output_line="                                             "
    for s in schools_list:
        output_line="{0}\t{1}".format(output_line, s)
    print(output_line)

    for subject in overlapping_subjects_list:
        output_line="{}".format(subject)
        for i in range(len(subject), 45):
            output_line=output_line+' '
        for s in schools_list:
            if subject in subjects_by_school[s]:
                output_line="{0}\tX".format(output_line)
            else:
                output_line="{0}\t ".format(output_line)
        print(output_line)
    return

    # write out the exiting data for all of the pages
    all_pages_df.to_excel(writer, sheet_name='Augmented')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
