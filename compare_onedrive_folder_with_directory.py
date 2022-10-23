#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
#!/usr/bin/python3
#
# ./compare_onedrive_folder_with_directory.py local_directory onedrive_spreadsheetFile
# 
# compare the files in a local directory to the files in a OneDriver folder
#
# The spradsheet is obtained from the Onedrive folder by exporting it to Excel.
# To do this you go to OneDrive and change to the classic interface and then export to Excel - which gives me a query.iqy file (i.e., a Microsoft Internet Query file) 
#
# This query.iqy has to be openned in a desktop version of Excel (it did not seem possible to open it via https://www.office.com/).
# Once you do yet another login, it does give a spreadsheet of the files.
#
# Oddly it does not say how large the files are but rather gives a "Huvudantal" column.  Now I will just have to figure out out to compare this with the results of "ls" and then figure out which files are missing.
#
# The preadhsheet is assumed to have the columns: 'Namn', 'Ändrat', 'Huvudantal', 'Ändrades av', 'Objekttyp', 'Sökväg'
#
#
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Example:
# ./compare_onedrive_folder_with_directory.py   /z3/maguire/II2202-for-Wouter  /z3/maguire/II2202-for-wouler-spreadsheet.xlsx
#
# G. Q. Maguire Jr.
#
# 2022-10-23
#

import csv, requests, time
import pprint
import optparse
import sys
import os.path
import glob

from io import StringIO, BytesIO

# Use Python Pandas to work with XLSX files
import pandas as pd

# to use math.isnan(x) function
import math

# to convert strings to python lists
import ast


def main():
    global Verbose_Flag

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
                      )

    parser.add_option('-t', '--testing',
                      dest="testing",
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )


    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print('ARGV      :', sys.argv[1:])
        print('VERBOSE   :', options.verbose)
        print('REMAINING :', remainder)

    pp = pprint.PrettyPrinter(indent=4) # configure prettyprinter

    if (len(remainder) < 2):
        print("Inusffient arguments: must provide local_directory onedrive_spreadsheetFile")
        return

    local_directory=remainder[0]
    spreadsheetFile=remainder[1]

    if Verbose_Flag:
        print("local_directory={0}, spreadsheetFile={1}".format(local_directory, spreadsheetFile))

    if os.path.isdir(local_directory):
        if Verbose_Flag:
            print("local directory exists")
    else:
        print("local directory {} does not exist".format(local_directory))
        return

    if os.path.isfile(spreadsheetFile):
        if Verbose_Flag:
            print("Spreadsheet file exists")
    else:
        print("Spreadsheet file {} does not exist".format(spreadsheetFile))
        return

    # Aty this point we know that both the local_directory and spreadsheetFile exist
    try:
        directory_df = pd.read_excel(open(spreadsheetFile, 'rb'))
    except:
        print("Unable to read spreadsheet file")
        sys.exit()
        return

    # check for column in spreadsheet data
    spreadsheetColumns=directory_df.columns.values.tolist()
    print(f"{spreadsheetColumns=}")

    # check that the spreadsheet has the expected columns
    expected_spreadsheet_columns=['Namn', 'Sökväg']
    for c in expected_spreadsheet_columns:
        if c not in spreadsheetColumns:
            print("spreadsheet is missing column: {}, please correct".format(c))
            return

    # get the set of files in the local_directory and their sizes
    list_of_files = filter( os.path.isfile,
                            glob.glob(local_directory + '/**/*', recursive=True) )

    # get list of files with their size
    files_with_size = [ (file_path, os.stat(file_path).st_size) 
                    for file_path in list_of_files ]

    # Iterate over list of tuples i.e. file_paths with size
    # and print them one by one
    if Verbose_Flag:
        for file_path, file_size in files_with_size:
            print(file_size, ' -->', file_path)   

    oneDrive_prefix=""
    oneDrive_files=list()

    # invald characters in folders and file names from https://support.microsoft.com/en-us/office/restrictions-and-limitations-in-onedrive-and-sharepoint-64883a5d-228e-48f5-b3d2-eb39e07630fa
    oneDriver_invalid_characters=['"', '*', ':',  '<', '>', '?', '/', '\\', '|']
    # removed '/' the set of oneDriver_invalid_characters to get bad_characters
    bad_characters=['"', '*', ':',  '<', '>', '?', '\\', '|']

    for idx, row in directory_df.iterrows():
        name=row['Namn']
        ftype=row['Objekttyp']
        path=row['Sökväg']
        if Verbose_Flag:
            print("idx={0}, name={1}, path={2}".format(idx, name, path))
        if idx == 0:
            oneDrive_prefix=path+'/'+name
            oneDrive_prefix_len=len(oneDrive_prefix)
            print(f"{oneDrive_prefix=} with length of {oneDrive_prefix_len}")

        if ftype == 'Item' and path.find(oneDrive_prefix) == 0:
            if path == oneDrive_prefix:
                fname=name
            else:
                if isinstance(name, int):
                    name=f"{name}"
                else:
                    if isinstance(name, float):
                        print("skipping a file wihout a valid name")
                        continue
                fname=path[oneDrive_prefix_len+1:]+'/'+name
            if Verbose_Flag:
                print(f"{fname=}")
            oneDrive_files.append(fname)

    for file_path, file_size in files_with_size:
        if file_path[len(local_directory)+1:] not in oneDrive_files:
            bad_char_exists=False
            for bc in bad_characters:
                if bc in file_path[len(local_directory)+1:]:
                    print(f"Due to a invalid charcter ({bc}) in a OneDriver filename, missing file: {file_path}")
                    bad_char_exists=True
            if not bad_char_exists:
                print(f"Missing file: {file_path}")

    return

        
if __name__ == "__main__": main()

