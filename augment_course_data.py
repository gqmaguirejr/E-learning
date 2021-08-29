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

# shorten the names of the degree project courses
#
to_remove=['specialising in', 'specializing in']
#
acronyms={
    'CSE': 'Computer Science and Engineering',
    'CS': 'Computer Science',
    'EE':  'Electrical Engineering'
}

def shorten_course_names(df, column, prefix, postfix):
    for index, row in df.iterrows():
        name=row[column]
        if len(prefix) > 0:
            start_offset=name.find(prefix)
            if start_offset >= 0:
                name=name[start_offset+len(prefix):]
                #print("reduced name={}".format(name))
        if len(postfix) > 0:
            end_offset=name.find(postfix)
            if end_offset >= 0:
                name=name[:end_offset]
        for k, v in acronyms.items():
            name=name.replace(v, k)
        for s in to_remove:
            name=name.replace(s, '')
        # replace two spaces with one
        name=name.replace('  ', '')
        # update the name
        df.at[index, column]=name
    return df


def degree_project_pie_chart(writer, df, cat_col, val_col, sheet_name, title, pos, color_vector):
    workbook = writer.book

    # make pie chart of 1st cycle degree projects
    worksheet = writer.sheets[sheet_name]

    # Create a chart object.
    chart = workbook.add_chart({'type': 'pie'})

    # Configure the series of the chart from the dataframe data.
    max_row = len(df)
    if max_row > 19:
        print("Uses a Pie in Pie chart to show this data (sheetname={})".format(sheet_name))
    cats="='{0}'!{1}2:{1}{2}".format(sheet_name, cat_col, max_row + 1)
    values="='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
    print("max_row={0}, cats={1}, values={2}".format(max_row, cats, values))
    if color_vector:
        if Verbose_Flag:
            print("Using specified colors")
        chart.add_series({
            'name':       title,
            'categories': cats,
            #'values':     [sheet_name, 1, 4, max_row, 4],
            'values': "='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
            'data_labels':{'value':True,
                           'category':True,
                           'position':'best_fit',
                           'border': {'color': 'black'},
                           'transparency': 50,
                           'font': {'name': 'Consolas', 'color': 'black', 'bg_color': 'white', 'size': 12},
                           },
            #'data_labels':{'value':True,'category':True,'position':'outside_end'}
            'points': color_vector
        })
    else:
        chart.add_series({
            'name':       title,
            'categories': cats,
            #'values':     [sheet_name, 1, 4, max_row, 4],
            'values': "='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
            'data_labels':{'value':True,
                           'category':True,
                           'position':'best_fit',
                           'border': {'color': 'black'},
                           'transparency': 50,
                           'font': {'name': 'Consolas', 'color': 'red', 'bg_color': 'white', 'size': 12},
                           }
            #'data_labels':{'value':True,'category':True,'position':'outside_end'}
        })

    chart.set_style(10)        # white outline and shadow
    # Insert the chart into the worksheet.
    worksheet.insert_chart(pos, chart)

def xls_col_num_to_letters(colnum):
    a = []
    while colnum:
        colnum, remainder = divmod(colnum - 1, 26)
        a.append(remainder)
    a.reverse()
    return ''.join([chr(n + ord('A')) for n in a])

def df_name_to_col(df, col_name):
    column_names=df.columns
    for index, col in enumerate(column_names):
        #print("col_name={0}, col_name type={1}, index={2}, col={3}, col ltype={4}".format(col_name, type(col_name), index, col, type(col)))
        if col_name == col:
            return xls_col_num_to_letters(index+2)
    # If the column name could be interpreted as an integer, then df.columns returns the integer
    # try matching integers
    for index, col in enumerate(column_names):
        #print("col_name={0}, col_name type={1}, index={2}, col={3}, col type={4}".format(col_name, type(col_name), index, col, type(col)))
        if type(col) is int:
            if col_name ==str (col):
                return xls_col_num_to_letters(index+2)

    print("Unable to convert column name to spreadsheet column")
    return 'A'

def collect_dept_names(df):
    dept_names=set()
    for index, row in df.iterrows():
        dept_name=row.get('department_en', None)
        if dept_name:
            dept_names.add(dept_name)
    return sorted(list(dept_names))


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

    # read in the sheets
    input_file="courses-in-{0}-{1}.xlsx".format(args["school"], args["year"])
    course_codes_df = pd.read_excel(open(input_file, 'rb'), sheet_name='course codes used')
    course_round_info_df = pd.read_excel(open(input_file, 'rb'), sheet_name='Rounds')

    # delete column named "Unnamed: 0"
    del course_codes_df['Unnamed: 0']
    del course_round_info_df['Unnamed: 0']

    dept_names=collect_dept_names(course_codes_df)
    print("dept_names={}".format(dept_names))
    dept_colors={}
    for index, d in enumerate(dept_names):
        if index == 0:
            c= {'color': 'blue', 'transparency': 50}
        elif index == 1:
            c= {'color': 'red', 'transparency': 50}
        elif index == 2:
            c= {'color': 'green', 'transparency': 50}
        elif index == 3:
            c= {'color': 'magenta', 'transparency': 50}
        elif index == 4:
            c= {'color': 'cyan', 'transparency': 50}
        elif index == 5:
            c= {'color': 'lime', 'transparency': 50}
        elif index == 6:
            c= {'color': 'navy', 'transparency': 50}
        elif index == 7:
            c= {'color': 'pink', 'transparency': 50}
        elif index == 8:
            c= {'color': 'gray', 'transparency': 50}
        elif index == 9:
            c= {'color': 'purple', 'transparency': 50}
        elif index == 10:
            c= {'color': 'brown', 'transparency': 50}
        elif index == 11:
            c= {'color': 'red', 'transparency': 70}
        elif index == 12:
            c= {'color': 'green', 'transparency': 70}
        elif index == 13:
            c= {'color': 'magenta', 'transparency': 70}
        elif index == 14:
            c= {'color': 'cyan', 'transparency': 70}
        elif index == 15:
            c= {'color': 'lime', 'transparency': 70}
        elif index == 16:
            c= {'color': 'navy', 'transparency': 70}
        elif index == 17:
            c= {'color': 'pink', 'transparency': 70}
        elif index == 18:
            c= {'color': 'gray', 'transparency': 70}
        elif index == 19:
            c= {'color': 'purple', 'transparency': 70}
        elif index == 20:
            c= {'color': 'brown', 'transparency': 70}
        elif index == 21:
            c= {'color': 'red', 'transparency': 30}
        elif index == 22:
            c= {'color': 'green', 'transparency': 30}
        elif index == 23:
            c= {'color': 'magenta', 'transparency': 30}
        elif index == 24:
            c= {'color': 'cyan', 'transparency': 30}
        elif index == 25:
            c= {'color': 'lime', 'transparency': 30}
        elif index == 26:
            c= {'color': 'navy', 'transparency': 30}
        elif index == 27:
            c= {'color': 'pink', 'transparency': 30}
        elif index == 28:
            c= {'color': 'gray', 'transparency': 30}
        elif index == 29:
            c= {'color': 'purple', 'transparency': 30}
        elif index == 40:
            c= {'color': 'brown', 'transparency': 30}


        else:
            c= {'color': 'orange', 'transparency': 50}
        dept_colors[d]={'name': d, 'color': c}
    print("dept_colors={}".format(dept_colors))

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
    gru_rounds.drop(gru_rounds[(gru_rounds.cycle < 1) | (gru_rounds.cycle > 2)].index, inplace=True)
    gru_rounds.sort_values(by='number_of_students', ascending=False, inplace=True)

    gru_rounds_counts_df=gru_rounds.groupby(['cycle', 'number_of_students']).size()
    gru_rounds_counts_unstacked=gru_rounds_counts_df.unstack(level=0)
    #print("gru_rounds_counts_unstacked.columns={}".format(gru_rounds_counts_unstacked.columns))
    #print("gru_rounds_counts_unstacked.len={}".format(len(gru_rounds_counts_unstacked)))
    # for index, row in gru_rounds_counts_unstacked.iterrows():
    #     print("row={}".format(row))

    # An alternative way of viewing this data is to bin it into "bins".
    max_number_of_students_in_a_course=gru_rounds_counts_unstacked.index.max()
    print("max_number_of_students_in_a_course={}".format(max_number_of_students_in_a_course))
    bin_size=10
    bins=[i for i in range(1, max_number_of_students_in_a_course+(2*bin_size), bin_size)]
    gru_rounds_counts_df2=gru_rounds.groupby(['cycle', pd.cut(gru_rounds.number_of_students, bins)]).count().unstack(level=0)
    gru_rounds_counts_df2 = gru_rounds_counts_df2['code']

    fofu_rounds=course_round_info_df.copy(deep=True)
    fofu_rounds.drop(fofu_rounds[fofu_rounds.cycle != 3].index, inplace=True)
    fofu_rounds.sort_values(by='number_of_students', ascending=False, inplace=True)

    totals_by_course_code_df=course_round_info_df.groupby(['code'])['number_of_students'].sum().reset_index()
    totals_by_course_code_df.sort_values(by='number_of_students', ascending=False, inplace=True)
    total_students=totals_by_course_code_df['number_of_students'].sum()
    print("total_students={}".format(total_students))
    totals_by_course_code_df['%']=100.0 * totals_by_course_code_df['number_of_students'] / total_students
    totals_by_course_code_df['cumulative %']=totals_by_course_code_df['%'].cumsum()

    degree_projects_df=course_round_info_df.copy(deep=True)
    degree_projects_df.insert(2, 'degree_project', '')
    for index, row in degree_projects_df.iterrows():
        course_code=row['code'].upper()
        if course_code[-1:] == 'X':
            degree_projects_df.at[index, 'degree_project']='X'
            
    degree_projects_df.drop(degree_projects_df[degree_projects_df.degree_project != 'X'].index, inplace=True)
    degree_projects_df.groupby(['code'])['number_of_students'].sum().reset_index()
    degree_projects_df.sort_values(by='number_of_students', ascending=False, inplace=True)

    totals_by_degree_project_course_cycle_df=degree_projects_df.groupby(['cycle'])['number_of_students'].sum().reset_index()

    #totals_by_degree_project_name_en_df=degree_projects_df.groupby(['cycle', 'name.en'])['number_of_students'].sum().reset_index()
    totals_by_degree_project_name_en_df=degree_projects_df.groupby(['cycle', 'name.en', 'department_en'])['number_of_students'].sum().reset_index()
    totals_by_degree_project_name_en_df.sort_values(by=['cycle', 'number_of_students'], ascending=False, inplace=True)

    cy1_degree_projects_df=totals_by_degree_project_name_en_df.copy(deep=True)
    cy1_degree_projects_df.drop(cy1_degree_projects_df[cy1_degree_projects_df.cycle != 1].index, inplace=True)
    cy1_degree_projects_df.drop(cy1_degree_projects_df[cy1_degree_projects_df.number_of_students == 0].index, inplace=True)

    # shorten the names of the degree project courses
    prefix="Degree Project in "
    postfix=", First Cycle"
    cy1_degree_projects_df=shorten_course_names(cy1_degree_projects_df, 'name.en', prefix, postfix)

    cy2_degree_projects_df=totals_by_degree_project_name_en_df.copy(deep=True)
    cy2_degree_projects_df.drop(cy2_degree_projects_df[cy2_degree_projects_df.cycle != 2].index, inplace=True)
    cy2_degree_projects_df.drop(cy2_degree_projects_df[cy2_degree_projects_df.number_of_students == 0].index, inplace=True)

    # shorten the names of the degree project courses
    prefix="Degree Project in "
    postfix=", Second Cycle"
    cy2_degree_projects_df=shorten_course_names(cy2_degree_projects_df, 'name.en', prefix, postfix)

    cy0_rounds=course_round_info_df.copy(deep=True)
    cy0_rounds.drop(cy0_rounds[cy0_rounds.cycle != 0].index, inplace=True)
    cy0_rounds.sort_values(by='number_of_students', ascending=False, inplace=True)

    cy5_rounds=course_round_info_df.copy(deep=True)
    cy5_rounds.drop(cy5_rounds[cy5_rounds.cycle != 5].index, inplace=True)
    cy5_rounds.sort_values(by='number_of_students', ascending=False, inplace=True)


    output_file="courses-in-{0}-{1}-augmented.xlsx".format(args["school"], args["year"])
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    course_codes_df.to_excel(writer, sheet_name='course codes used')
    course_round_info_df.to_excel(writer, sheet_name='Rounds')

    # Output sheets for cycles 0, 1+2, 3, and 5
    if len(cy0_rounds) > 0:
        cy0_rounds.to_excel(writer, sheet_name='cy0')

    gru_rounds.to_excel(writer, sheet_name='GRU rounds')

    fofu_rounds.to_excel(writer, sheet_name='FOFU rounds')

    if len(cy5_rounds) > 0:
        cy5_rounds.to_excel(writer, sheet_name='cy5')

    totals_by_course_code_df.to_excel(writer, sheet_name='Totals by course code')

    gru_rounds_counts_df.to_excel(writer, sheet_name='GRU rounds counts')
    gru_rounds_counts_unstacked.to_excel(writer, sheet_name='GRU unstacked')
    gru_rounds_counts_df2.to_excel(writer, sheet_name='GRU rounds counts2')

    degree_projects_df.to_excel(writer, sheet_name='degree projects')
    totals_by_degree_project_course_cycle_df.to_excel(writer, sheet_name='degree projects totals')

    totals_by_degree_project_name_en_df.to_excel(writer, sheet_name='degree name')
    cy1_degree_projects_df.to_excel(writer, sheet_name='cy1 degree name')
    cy2_degree_projects_df.to_excel(writer, sheet_name='cy2 degree name')

    if len(cy0_rounds) > 0:
        cy0_rounds.to_excel(writer, sheet_name='cy0')

    if len(cy5_rounds) > 0:
        cy5_rounds.to_excel(writer, sheet_name='cy5')


    # generate some plots
    # Access the XlsxWriter workbook and worksheet objects from the dataframe.
    #     
    
    sheet_name='Totals by course code'
    workbook = writer.book

    # make CDF showing cumulative %
    worksheet = writer.sheets[sheet_name]

    chart1 = workbook.add_chart({'type': 'line'})

    max_row = len(totals_by_course_code_df)
    if Verbose_Flag:
        print("In sheet 'Totals by course code' CDF max_row={}".format(max_row))
    # Configure the series.
    val_col=df_name_to_col(totals_by_course_code_df, 'cumulative %')
    chart1.add_series({
        'name':       "='{0}'!${1}$1".format(sheet_name, val_col),
        'values': "='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
        'line':{'color':'blue'}
    })

    # Add a chart title and some axis labels.
    chart1.set_title ({'name': 'Cumulative percentage of students'})
    chart1.set_x_axis({'name': 'i-th course code', 'interval_unit': 50})
    chart1.set_y_axis({'name': 'Cumulative percentage', 'min': 0, 'max': 100})
    chart1.set_legend({'none': True})

    # Set an Excel chart style.
    chart1.set_style(11)

    # Insert the chart into the worksheet
    worksheet.insert_chart('H2', chart1)

    sheet_name='GRU unstacked'
    workbook = writer.book

    # make pie chart of 1st cycle degree projects
    worksheet = writer.sheets[sheet_name]

    chart1 = workbook.add_chart({'type': 'scatter'})

    if Verbose_Flag:
        print("gru_rounds_counts_df.shape shape={}".format(gru_rounds_counts_df.shape))
    max_row = len(gru_rounds_counts_unstacked)
    if Verbose_Flag:
        print("max_row={}".format(max_row))
    # Configure the first series.
    # gru_rounds_counts_unstacked index is 'number_of_students'
    cat_col='A'
    val_col=df_name_to_col(gru_rounds_counts_unstacked, '1')
    #print("gru_rounds_counts_unstacked cat_col={0}, val_col={1}".format(cat_col, val_col))
    chart1.add_series({
        'name': "='{0}'!${1}$1".format(sheet_name, val_col),
        'categories': "='{0}'!${1}2:${1}{2}".format(sheet_name, cat_col, max_row+1),
        'values': "='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
        'marker': {'type': 'circle',
                   'size': 5,
                   #'line': {'none': True},
                   'border':  {'color': 'red', 'transparency': 50},
                   'fill':    {'color': 'red', 'transparency': 50}
                   }
    })

    # Configure the second series.
    # gru_rounds_counts_unstacked index is 'number_of_students'
    cat_col='A'
    val_col=df_name_to_col(gru_rounds_counts_unstacked, '2')
    chart1.add_series({
        'name': "='{0}'!${1}$1".format(sheet_name, val_col),
        'categories': "='{0}'!{1}2:${1}{2}".format(sheet_name, cat_col, max_row+1),
        'values': "='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
        'marker': {'type': 'square',
                   'size': 5,
                   #'line': {'none': True},
                   'border':  {'color': 'green', 'transparency': 50},
                   'fill':    {'color': 'green', 'transparency': 50}
                   },

    })

    # Add a chart title and some axis labels.
    chart1.set_title ({'name': 'Histogram of numbers of classes with a given number of students'})
    chart1.set_x_axis({'name': 'Number of students in a class'})
    chart1.set_y_axis({'name': 'Frequency', 'log_base': 10})

    # Set an Excel chart style.
    chart1.set_style(11)

    # Insert the chart into the worksheet (with an offset).
    #worksheet.insert_chart('D2', chart1, {'x_offset': 25, 'y_offset': 10})
    worksheet.insert_chart('D2', chart1)

    ## Make horizontal bar chart
    sheet_name='GRU rounds counts2'
    workbook = writer.book

    # make pie chart of 1st cycle degree projects
    worksheet = writer.sheets[sheet_name]

    chart1 = workbook.add_chart({'type': 'bar'})

    max_row = len(gru_rounds_counts_df2)
    if Verbose_Flag:
        print("max_row={}".format(max_row))
    # Configure the first series.
    cat_col='A'
    val_col=df_name_to_col(gru_rounds_counts_df2, '1')
    chart1.add_series({
        'name': "='{0}'!${1}$1".format(sheet_name, val_col),
        'categories': "='{0}'!${1}2:${1}{2}".format(sheet_name, cat_col, max_row+1),
        'values': "='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
        #'border':    {'color': 'red', 'transparency': 50},
        'border': {'none': True},
        'fill':    {'color': 'red', 'transparency': 50}
    })

    # Configure the second series.
    cat_col='A'
    val_col=df_name_to_col(gru_rounds_counts_df2, '2')

    chart1.add_series({
        'name': "='{0}'!${1}$1".format(sheet_name, val_col),
        'categories': "='{0}'!${1}2:${1}{2}".format(sheet_name, cat_col, max_row+1),
        'values': "='{0}'!${1}2:${1}{2}".format(sheet_name, val_col, max_row+1),
        #'border':    {'color': 'green', 'transparency': 50},
        'border': {'none': True},
        'fill':    {'color': 'green', 'transparency': 50}
    })

    # Add a chart title and some axis labels.
    chart1.set_title ({'name': "Histogram of numbers of classes with a given number of students with bin_size={}".format(bin_size)})
    chart1.set_x_axis({'name': 'Frequency'})
    chart1.set_y_axis({'name': 'Number of students in a class'})


    # Set an Excel chart style.
    chart1.set_style(11)

    # Insert the chart into the worksheet (with an offset).
    #worksheet.insert_chart('D2', chart1, {'x_offset': 25, 'y_offset': 10})
    worksheet.insert_chart('D2', chart1)

    # make pie chart of 1st cycle degree projects
    sheet_name='cy1 degree name'
    title="1st cycle theses by degree name"
    pos='K2'
    cat_col=df_name_to_col(cy1_degree_projects_df, 'name.en')
    val_col=df_name_to_col(cy1_degree_projects_df, 'number_of_students')
    color_vector=[]
    for index, row in cy1_degree_projects_df.iterrows():
        dept=row['department_en']
        color_info=dept_colors.get(dept, None)
        if color_info:
            color=color_info.get('color', None)
            if color:
                color_vector.append({'fill': color})
        else:
            color_vector.append({'fill': {'color': 'yellow', 'transparency': 50}})

    if Verbose_Flag:
        print("color_vector={}".format(color_vector))
    
    degree_project_pie_chart(writer, cy1_degree_projects_df, cat_col, val_col, sheet_name, title, pos, color_vector)

    # make pie chart of 2nd cycle degree projects
    sheet_name='cy2 degree name'
    title="2nd cycle theses by degree name"
    pos='K2'
    cat_col=df_name_to_col(cy2_degree_projects_df, 'name.en')
    val_col=df_name_to_col(cy2_degree_projects_df, 'number_of_students')
    #color_vector=None
    color_vector=[]
    for index, row in cy2_degree_projects_df.iterrows():
        dept=row['department_en']
        color_info=dept_colors.get(dept, None)
        if color_info:
            color=color_info.get('color', None)
            if color:
                color_vector.append({'fill': color})
        else:
            color_vector.append({'fill': {'color': 'yellow', 'transparency': 50}})

    if Verbose_Flag:
        print("color_vector={}".format(color_vector))
    

    degree_project_pie_chart(writer, cy2_degree_projects_df, cat_col, val_col, sheet_name, title, pos, color_vector)

    
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
