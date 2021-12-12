#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./DiVA_organization_info.py [--orgid org_id] [--orgname organization_name] [--json filename.json] [--csv]
#
# Purpose: The program creates a XLSX file of orgniazation data based upon the DiVA cora API for Organisationsmetadata
#
# Where filename.json is the output of a query such as:
#   wget -O UUB-20211210-get.json  'https://cora.diva-portal.org/diva/rest/record/searchResult/publicOrganisationSearch?searchData={"name":"search","children":[{"name":"include","children":[{"name":"includePart","children":[{"name":"divaOrganisationDomainSearchTerm","value":"kth"}]}]},{"name":"start","value":"1"},{"name":"rows","value":"800"}]}' 
#
# Note that in the above query you have to give it a number of rows large anough to get all of the data, as otherwise it returns only the first 100 rows of data
#
# Output: outputs a file with a name of the form DiVA_org_id_date.xlsx
# Columns of the spread sheet are organisation_id, organisation_name_sv, organisation_name_en, organisation_type_code, organisation_type_name, organisation_parent_id\,	closed_date, organisation_code
#
#
# The command has --verbose and --testing optional arguments for more information and more limiting the number of records processed.
#
# Example:
#  get data from a JSON file
# ./DiVA_organization_info.py --orgid 177 --json UUB-20211210-get.json
#
#  get data from a JSON file with out specifying the orgid, it will take this from the topOrganisation
# ./DiVA_organization_info.py --json UUB-20211210-get.json
#
#  get date via the organization name
# ./DiVA_organization_info.py --orgname kth
#
# ouput a CSV file rather than a XLSX file
# ./DiVA_organization_info.py --json UUB-20211210-get.json --csv
#
# Note:
# Currently the getting of the data using just the --orgid does not work, it only get the top level entry
#
# 2021-12-11 G. Q. Maguire Jr.
#
import re
import sys
import subprocess

import json
import argparse
import os			# to make OS calls, here to get time zone info

import time

import pprint

import requests

# Use Python Pandas to create XLSX files
import pandas as pd

from collections import defaultdict


from datetime import datetime

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# ----------------------------------------------------------------------
schools_info={'ABE': {'swe': 'Skolan för Arkitektur och samhällsbyggnad',
                      'eng': 'School of Architecture and the Built Environment'},
              'ITM': {'swe': 'Skolan för Industriell teknik och management',
                      'eng': 'School of Industrial Engineering and Management'},
              'SCI': {'swe': 'Skolan för Teknikvetenskap',
                      'eng': 'School of Engineering Sciences'},
              'CBH': {'swe': 'Skolan för Kemi, bioteknologi och hälsa',
                      'eng': 'School of Engineering Sciences in Chemistry, Biotechnology and Health'},
              'EECS': {'swe': 'Skolan för Elektroteknik och datavetenskap',
                      'eng': 'School of Electrical Engineering and Computer Science'}
              }


def read_external_JSON_file_of_data(json_filename):
    with open(json_filename, 'r') as json_FH:
        try:
            if Verbose_Flag:
                print("Trying to open file: {}".format(json_filename))
            json_string=json_FH.read()
            if Verbose_Flag:
                print("length of json_string={}".format(len(json_string)))
            try:
                diva_organization_json=json.loads(json_string)
                return diva_organization_json
            except:
                print("Error in loading JSON string from file={}".formatjson_filename())
                return None
        except:
            print("Error in reading JSON file={}".formatjson_filename())
            return None

# functions to get information from the DiVA organization records
def domain_of_child(x):
    global Verbose_Flag
    value=None
    if x.get('children', None):
        for c in x['children']:
            name=c.get('name')
            if name:
                if name=='domain':
                    value=c.get('value')
                    if Verbose_Flag:
                        print("id: {}".format(value))
    return value

def recordInfo_of_child(x):
    global Verbose_Flag
    if Verbose_Flag:
        print("recordInfo_of_child({})".format(x))
    s_info=dict()
    name=x.get('name')
    if name and name=='recordInfo' and x.get('children', None):
        for c in x['children']:
            s_name=c.get('name')
            if s_name:
                sc=c.get('children', None)
                if not sc:
                    s_info[s_name]=c.get('value')
                else:
                    sc_info=dict()
                    for scn in sc:
                        scn_name=scn.get('name')
                        if scn_name:
                            sc_info[scn_name]=scn.get('value')
                    s_info[s_name]=sc_info
        if Verbose_Flag:
            pprint.pprint("recordInfo_of_child={}".format(s_info))
        return s_info
    return None

def org_name_of_child(x):
    global Verbose_Flag
    if Verbose_Flag:
        print("org_name_of_child({})".format(x))
    s_info=dict()
    name=x.get('name')
    if name and name=='organisationName' and x.get('children', None):
        for c in x['children']:
            s_name=c.get('name')
            if s_name:
                s_info[s_name]=c.get('value')
        if Verbose_Flag:
            pprint.pprint("org_name_of_child={}".format(s_info))
        return s_info
    return None

def alt_org_name_of_child(x):
    global Verbose_Flag
    if Verbose_Flag:
        print("alt_org_name_of_child({})".format(x))
    s_info=dict()
    name=x.get('name')
    if name and name=='organisationAlternativeName' and x.get('children', None):
        for c in x['children']:
            s_name=c.get('name')
            if s_name:
                s_info[s_name]=c.get('value')
        #
        if Verbose_Flag:
            pprint.pprint("alt_org_name_of_child={}".format(s_info))
        return s_info
    return None

def close_date_of_child(x):
    global Verbose_Flag
    value=None
    name=x.get('name')
    if name:
        if name=='closedDate':
            value=x.get('value')
    return value

def org_type_of_child(x):
    global Verbose_Flag

    value=None
    if Verbose_Flag:
        print("org_type_of_child({})".format(x))
    name=x.get('name')
    if name and name=='organisationType':
        value=x.get('value')
    if Verbose_Flag:
        pprint.pprint("org_type_of_child={}".format(value))
    return value

def organisationCode_of_child(x):
    global Verbose_Flag

    value=None
    if Verbose_Flag:
        print("org_type_of_child({})".format(x))
    name=x.get('name')
    if name and name=='organisationCode':
        value=x.get('value')
    if Verbose_Flag:
        pprint.pprint("organisationCode_of_child={}".format(value))
    return value


def parentOrganisation_of_child(x):
    # {'children': [{'actionLinks': {'read': {'accept': 'application/vnd.uub.record+json',
    #                                         'rel': 'read',
    #                                         'requestMethod': 'GET',
    #                                         'url': 'https://cora.diva-portal.org/diva/rest/record/topOrganisation/177'}},
    #               'children': [{'name': 'linkedRecordType',
    #                            'value': 'topOrganisation'},
    #                        {'name': 'linkedRecordId', 'value': '177'}],
    #              'name': 'organisationLink'}],
    #  'name': 'parentOrganisation',
    #  'repeatId': '0'}
    global Verbose_Flag

    if Verbose_Flag:
        print("parentOrganisation_of_child({})".format(x))
    s_info=dict()
    name=x.get('name')
    repeat_id=x.get('repeatId')
    if name and name=='parentOrganisation' and x.get('children', None):
        for c in x['children']:
            c_name=c.get('name')
            if c_name == 'organisationLink':
                for cs in c['children']:
                    s_name=cs.get('name')
                    if s_name:
                        s_info[s_name]=cs.get('value')
        if Verbose_Flag:
            pprint.pprint("parentOrganisation_of_child{0}, repeatId={1}".format(s_info, repeat_id))
        return s_info
    return None


def address_of_child(x):
    global Verbose_Flag
    if Verbose_Flag:
        print("address_of_child({})".format(x))
    s_info=dict()
    name=x.get('name')
    if name and name=='address' and x.get('children', None):
        for c in x['children']:
            s_name=c.get('name')
            if s_name:
                s_info[s_name]=c.get('value')
        if Verbose_Flag:
            pprint.pprint("address_of_child={}".format(s_info))
        return s_info
    return None

def url_of_child(x):
    global Verbose_Flag
    if Verbose_Flag:
        print("url_of_child({})".format(x))
    s_info=dict()
    name=x.get('name')
    if name and name=='url' and x.get('children', None):
        for c in x['children']:
            s_name=c.get('name')
            if s_name:
                s_info[s_name]=c.get('value')
        if Verbose_Flag:
            pprint.pprint("url_of_child={}".format(s_info))
        return s_info
    return None



# organisation_id","organisation_name","organisation_name","organisation_code","closed_date","organisation_parent_id","organisation_type_code","organisation_type_name"
# the first orgnization name is in Swedish and the second in English
# In terms of the DiVA JSON these fields are:
# 'id', 'organisationName', 'organisationAlternativeName', 'organisationCode', 'closedDate', 'parentOrganisation', 'organisationType', ??
#
# A diva_organization dict entry will have the following fields:
# {"organisation_id": ,
#  "organisation_name": ,
#  "organisation_name": ,
#  "organisation_code": ,
#  "closed_date": ,
#  "organisation_parent_id": ,
#  "organisation_type_code": ,
#  "organisation_type_name":
# ]

def english_org_name(d, key):
    org_name=d[key].get('organisationName')
    if org_name['language'] == 'en':
        return org_name['name']
    #
    org_name=d[key].get('organisationAlternativeName')
    if org_name['language'] == 'en':
        return org_name['name']
    #
    return None

def swedish_org_name(d, key):
    org_name=d[key].get('organisationName')
    if org_name['language'] == 'sv':
        return org_name['name']
    #
    org_name=d[key].get('organisationAlternativeName')
    if org_name['language'] == 'sv':
        return org_name['name']
    #
    return None

# to organize as a spreadsheet
def convert_to_spreadsheet(d):
    for_s=list()
    for key in sorted(d.keys()):
        entry=dict()
        entry['organisation_id']=key
        entry['organisation_name_sv']=swedish_org_name(d, key)
        entry['organisation_name_en']=english_org_name(d, key)
        x=d[key].get('organisationCode', None)
        if x:
            entry['organisation_code']=x
        x=d[key].get('closedDate', None)
        if x:
            entry['closed_date']=x
        x=d[key].get('parentOrganisation', None)
        if x:
            pid=x.get('linkedRecordId')
            if pid:
                try:            # try converting to int, if not just use the string
                    entry['organisation_parent_id']=int(pid)
                except:
                    entry['organisation_parent_id']=pid
        x=d[key].get('organisationType', None)
        if x:
            entry['organisation_type_code']=x
            if x=='university':
                entry['organisation_type_name']='Universitet'
            elif x=='faculty':
                entry['organisation_type_name']='Fakultet'
            elif x=='department':
                entry['organisation_type_name']='Institution'
            elif x=='unit':
                entry['organisation_type_name']='Enhet'
            elif x=='division':
                entry['organisation_type_name']='Avdelning'
            elif x=='centre':
                entry['organisation_type_name']='Centrum'
            elif x=='researchGroup':
                entry['organisation_type_name']='Forskningsgrupp'
            else:
                print("Unknown organisationType={}".format(x))

        for_s.append(entry)

    return for_s

def main(argv):
    global Verbose_Flag
    global testing
    global Keep_picture_flag


    argp = argparse.ArgumentParser(description="JSON_to_DOCX_cover.py: to make a thesis cover using the DOCX template")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('--orgid',
                      type=int,
                      help="DiVA organization ID"
                      )

    argp.add_argument('--orgname',
                      type=str,
                      help="name of organization"
                      )

    argp.add_argument('-j', '--json',
                      type=str,
                      default=None,
                      help="JSON file of data from DiVA"
                      )

    argp.add_argument('--file',
                      type=str,
                      help="output file name"
                      )

    argp.add_argument('-c', '--csv',
                      default=False,
                      action="store_true",
                      help="store as CSV file rather than XLSX file"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))

    orgid=args['orgid']
    if Verbose_Flag:
        print("orgid={}".format(orgid))

    orgname=args['orgname']

    diva_organization_json=dict()
    diva_organization=dict()

    json_filename=args['json']
    if json_filename:
        diva_organization_json=read_external_JSON_file_of_data(json_filename)
    elif orgname:
        diva_url='https://cora.diva-portal.org/diva/rest/record/searchResult/publicOrganisationSearch?searchData={"name":"search","children":[{"name":"include","children":[{"name":"includePart","children":[{"name":"divaOrganisationDomainSearchTerm","value":"'+"{}".format(orgname) +'"}]}]},{"name":"start","value":"1"},{"name":"rows","value":"800"}]}'
        if Verbose_Flag:
            print("diva_url: {}".format(diva_url))

        r = requests.get(diva_url)
        if Verbose_Flag:
            print("result of getting DiVA url: {}".format(r.text))

        if r.status_code == requests.codes.ok:
            diva_organization_json=r.json()
        else:
            print("Error in getitng DiVA data using diva_url: {}".format(diva_url))

    elif orgid:
        # This part of the code is not yet working
        diva_url="https://cora.diva-portal.org/diva/rest/record/topOrganisation/{}".format(args['orgid'])
        if Verbose_Flag:
            print("diva_url: {}".format(diva_url))

        r = requests.get(diva_url)
        if Verbose_Flag:
            print("result of getting DiVA url: {}".format(r.text))

        if r.status_code == requests.codes.ok:
            diva_organization_json=r.json()
        else:
            print("Error in getitng DiVA data using diva_url: {}".format(diva_url))
    else:
        print("Neither an orgid, orgname, or JSON file name were provided")
        return

    if Verbose_Flag:
        print("Length of diva_organization_json={}".format(len(diva_organization_json)))
    if Verbose_Flag and testing:
        print("Got diva_organization_json={}".format(diva_organization_json))
   
    # Top level of JSON from external file is:
    # {'dataList': {'containDataOfType': 'mix',
    #               'data': [...],
    #               'fromNo': '1',
    #               'toNo': '700',
    #               'totalNo': '700'}}


    datalist=diva_organization_json.get('dataList', None)
    if not datalist:
        print("datalist nor present in data")
        return

    if Verbose_Flag:
        total_number_of_records=datalist.get('totalNo', None)
        print("total_number_of_records={}".format(total_number_of_records))

    diva_org_records=datalist.get('data', None)
    if not diva_org_records:
        print("data nor present in datalist")
        return

    # the data element looks like:
    # [{'record': {...}},
    #  {'record': {...}},
    #  {'record': {...}},
    #  {'record': {...}},
    #  ...
    # ]

    print("Number of diva_org_records found={}".format(len(diva_org_records)))
    if testing:
        limit=40

    # A diva_organization dict entry will have the following fields:
    # {"organisation_id": ,
    #  "organisationName": ,
    #  "organisationAlternativeName": ,
    #  "organisation_code": ,
    #  "closed_date": ,
    #  "organisation_parent_id": ,
    #  "organisation_type_code": ,
    #  "organisation_type_name":


    for rec in diva_org_records:
        if testing:
            limit=limit-1
            if limit == 0:
                break

        # each recond has the form:
        # {'actionLinks': {...}, 'data': {...}}
        # the 'data' has the form of:
        # {'children': [...], 'name': 'organisation'}

        diva_organization_dict_entry=dict()
        record_type=rec['record']['data']['name']
        if Verbose_Flag:
            print("record_type={}".format(record_type))

        for c in rec['record']['data']['children']:
            if Verbose_Flag:
                print("number_of_children={}".format(len(c)))
                print("pprint of child of record_type={}".format(record_type))
                pprint.pprint(c, depth=3)

            # [{'children': [...], 'name': 'recordInfo'},
            # {'children': [...], 'name': 'organisationName'},
            # {'children': [...], 'name': 'organisationAlternativeName'},
            # {'name': 'closedDate', 'value': '2010-12-31'},
            # {'name': 'organisationType', 'value': 'unit'},
            #{'children': [...], 'name': 'parentOrganisation', 'repeatId': '0'}]

            for sc in c:
                name=c.get('name')
                if name == 'recordInfo':
                    diva_organization_dict_entry['recordInfo']=recordInfo_of_child(c)
                    # use int() to convert to an integer
                    # if this fails, then just use the string
                    try:
                        id=int(diva_organization_dict_entry['recordInfo'].get('id', None))
                    except:
                        id=diva_organization_dict_entry['recordInfo'].get('id', None)
                    if Verbose_Flag:
                        print("id={}".format(id))
                    # if the orgid was not specified, then take it from the record for the topOrganisation
                    if not orgid:
                        orgtype=diva_organization_dict_entry['recordInfo'].get('type', None)
                        if orgtype and  orgtype.get('linkedRecordId', None) == 'topOrganisation':
                            orgid=id
                            print("setting orgid to {}".format(orgid))
                elif name == 'organisationName':
                    diva_organization_dict_entry['organisationName']=org_name_of_child(c)
                elif name == 'organisationAlternativeName':
                    diva_organization_dict_entry['organisationAlternativeName']=alt_org_name_of_child(c)
                elif name == 'closedDate':
                    diva_organization_dict_entry['closedDate']=close_date_of_child(c)
                elif name == 'organisationCode':
                      diva_organization_dict_entry['organisationCode']=organisationCode_of_child(c)
                elif name == 'organisationType':
                    diva_organization_dict_entry['organisationType']=org_type_of_child(c)
                elif name == 'parentOrganisation':
                    diva_organization_dict_entry['parentOrganisation']=parentOrganisation_of_child(c)
                elif name == 'address':
                    diva_organization_dict_entry['address']=address_of_child(c)
                elif name == 'URL':
                    diva_organization_dict_entry['URL']=url_of_child(c)
                elif name in ['doctoralDegreeGrantor', 'organisationNumber', 'earlierOrganisation']:
                    continue    #  just ignore these
                else:
                    print("Unknown name={}", name)

        diva_organization[id]=(diva_organization_dict_entry)
        if Verbose_Flag:
            print("id: {0} is {1}".format(id, diva_organization_dict_entry))
            print("domain_of_child={}".format(domain_of_child(c)))

    if Verbose_Flag:
        print("diva_organization")
        pprint.pprint(diva_organization, width=250)
        
    for_spreadsheet=convert_to_spreadsheet(diva_organization)
    
    diva_data_df=pd.json_normalize(for_spreadsheet)
    column_names=diva_data_df.columns
    if 'organisation_id' not in column_names:
        print("organisation_id missing from {}".format(column_names))
    # sort lines on organisation_id
    diva_data_df.sort_values(by='organisation_id', ascending=True, inplace=True)

    todays_date = datetime.now().strftime('%Y-%m-%d')

    if args['csv']:
        # save as CSV file
        if orgname:
            output_file="DiVA_{0}_{1}.csv".format(orgname, todays_date)
        else:
            output_file="DiVA_{0}_{1}.csv".format(orgid, todays_date)

        diva_data_df.to_csv(output_file, index=False,encoding='utf-8-sig') # write the BOM so Excel know the file contains utf-8 chars
    else:
        if orgname:
            output_file="DiVA_{0}_{1}.xlsx".format(orgname, todays_date)
        else:
            output_file="DiVA_{0}_{1}.xlsx".format(orgid, todays_date)

        # the following was inspired by the section "Using XlsxWriter with Pandas" on http://xlsxwriter.readthedocs.io/working_with_pandas.html
        # set up the output write
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        diva_data_df.to_excel(writer, sheet_name='DiVA organizations', index=False)
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
