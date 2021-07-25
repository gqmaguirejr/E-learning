#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./MODS_to_titles_and_subtitles.py --mods file.mods
#
# Purpose: The program ouputs a spreadsheet of title and subtitle split by language given a MODS file
#
#
# Example:
#
#  enter events from a MODS file
# ./MODS_to_titles_and_subtitles.py --mods theses.mods
# 
# based on earlier JSON_to_calendar-old.py
#
# 2021-07-19 G. Q. Maguire Jr.
#
import re
import sys

import json
import argparse
import os			# to make OS calls, here to get time zone info

import requests, time

# Use Python Pandas to create XLSX files
import pandas as pd

import pprint

# for dealing with MODS file
from bs4 import BeautifulSoup

# for dealing with XML
from eulxml import xmlmap
from eulxml.xmlmap import load_xmlobject_from_file, mods
import lxml.etree as etree

from collections import defaultdict


import datetime
import isodate                  # for parsing ISO 8601 dates and times
import pytz                     # for time zones
from dateutil.tz import tzlocal

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

def local_to_utc(LocalTime):
    EpochSecond = time.mktime(LocalTime.timetuple())
    utcTime = datetime.datetime.utcfromtimestamp(EpochSecond)
    return utcTime

def datetime_to_local_string(canvas_time):
    global Use_local_time_for_output_flag
    t1=isodate.parse_datetime(canvas_time)
    if Use_local_time_for_output_flag:
        t2=t1.astimezone()
        return t2.strftime("%Y-%m-%d %H:%M")
    else:
        return t1.strftime("%Y-%m-%d %H:%M")

def cycle_of_program(s):
    # replace ’ #x2019 with ' #x27
    s=s.replace(u"\u2019", "'")
    for p in programcodes:
        pname_eng=programcodes[p]['eng']
        pname_swe=programcodes[p]['swe']
        e_offset=s.find(pname_eng)
        s_offset=s.find(pname_swe)
        if (e_offset >= 0) or (s_offset >= 0):
            return programcodes[p]['cycle']
    # secondary check
    if s.find("Magisterprogram") >= 0 or s.find("Masterprogram") >= 0 or s.find("Master's") >= 0 or s.find("Master of Science") >= 0 or s.find("Civilingenjör") >= 0:
        return 2
    if s.find("Kandidatprogram") >= 0 or s.find("Bachelor's") >= 0 or s.find("Högskoleingenjör") >= 0:
        return 1
    print("cycle_of_program: Error in program name - did not match anything")
    return None



# processing of MODS data:
def extract_list_of_dicts_from_mods(tree):
    global testing
    json_records=list()
    current_subject_language=''
    list_of_topics_English=list()
    list_of_topics_Swedish=list()
    thesis_abstract_language=list()

    for i in range(0, len(tree.node)):
        if testing and i > 10:   # limit the number of theses to process when testing
            break
        print("processing node={}".format(i))
        if tree.node[i].tag.count("}modsCollection") == 1:
            # case of a modsCollection
            if Verbose_Flag:
                print("Tag: " + tree.node[i].tag)
                print("Attribute: ")
                print(tree.node[i].attrib)
                # case of a mods
        elif tree.node[i].tag.count("}mods") == 1:
            if Verbose_Flag:
                print("new mods Tag: " + tree.node[i].tag)
                #  print "Attribute: " + etree.tostring(tree.node[i].attrib, pretty_print=True) 
                print("Attribute: {}".format(tree.node[i].attrib))
                
            # extract information about the publication
            pub_info=dict()


            #
            current_mod=tree.node[i]
            pub_info['node']=[i]

            pub_info['thesis_title']=dict()
            pub_info['thesis_subtitle']=dict()
            authors=list()
            supervisors=list()
            examiners=list()
            opponents=list()
            list_of_topics=dict()
            list_of_HSV_subjects=dict()
            list_of_HSV_codes=set()
            current_subject_language=None

            # note types
            level=dict()
            universityCredits=dict()
            venue=None
            cooperation=None

            if Verbose_Flag:
                print("Length of mod: {0}".format(len(current_mod)))
            for mod_element in range(0, len(current_mod)):
                current_element=current_mod[mod_element]
                if Verbose_Flag:
                    print("current element {0}".format(current_element))
                if current_element.tag.count("}genre") == 1:
                    if Verbose_Flag:
                        print("attribute={}".format(current_element.attrib))
                        print("text={}".format(current_element.text))
                    attribute=current_element.attrib
                    type=attribute.get('type', None)
                    if type and (type == 'publicationTypeCode'):
                        if current_element.text == 'studentThesis':
                            pub_info['genre_publicationTypeCode']=current_element.text
                        elif current_element.text in ['comprehensiveDoctoralThesis',
                                                      'comprehensiveLicentiateThesis',
                                                      'monographDoctoralThesis',
                                                      'monographLicentiateThesis']:
                            pub_info['genre_publicationTypeCode']=current_element.text
                        else:
                            print("Unexpected genre publicationTypeCode = {}".format(current_element.text))

                elif current_element.tag.count("}name") == 1:
                    name_given=None
                    name_family=None
                    corporate_name=''
                    affiliation=''
                    role=None
                    kthid=None

                    name_type=current_element.attrib.get('type', 'Unknown')
                    if Verbose_Flag:
                        print("name_type={}".format(name_type))
                        print("current_element.attrib={}".format(current_element.attrib))
                    # note the line below is based on the manual expansion of the xlink name space
                    kthid=current_element.attrib.get('{http://www.w3.org/1999/xlink}href', None)
                    if Verbose_Flag:
                        print("kthid={}".format(kthid))

                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}namePart") == 1:
                            if name_type == 'personal':
                                #   name_family, name_given, name_type, affiliation
                                if Verbose_Flag:
                                    print("namePart: {}".format(elem.text))
                                if len(elem.attrib) > 0 and Verbose_Flag:
                                    print(elem.attrib)
                                namePart_type = elem.attrib.get('type', None)
                                if namePart_type and namePart_type == 'family':
                                    name_family=elem.text
                                    if Verbose_Flag:
                                        print("name_family: {}".format(name_family))
                                elif namePart_type and namePart_type == 'given':
                                    name_given=elem.text
                                    if Verbose_Flag:
                                        print("name_given: {}".format(name_given))
                                elif namePart_type and namePart_type == 'date':
                                    name_date=elem.text
                                    if Verbose_Flag:
                                        print("name_date: {}".format(name_date))
                                elif namePart_type and Verbose_Flag:
                                    print("Cannot parse namePart {0} {1}".format(elem.attrib['type'], elem.text))
                                else:
                                    print("here is no namePart_type")
                            elif name_type == 'corporate':
                                if len(corporate_name) > 0:
                                    corporate_name = corporate_name + "," + elem.text
                                else:
                                    corporate_name = elem.text
                            else:
                                print("dont' know what do do about a namePart")

                        elif elem.tag.count("}role") == 1:
                            if Verbose_Flag and elem.text is not None:
                                print("role: elem {0} {1}".format(elem.attrib, elem.text))
                                print("role length is {}".format(len(elem)))
                            for j in range(0, len(elem)):
                                rt=elem[j]
                                if rt.tag.count("}roleTerm") == 1:
                                    # role, affiliation, author_affiliation, supervisor_affiliation, examiner_affiliation
                                    #  name_family, name_given, author_name_family, author_name_given, supervisor_name_family, supervisor_name_given
                                    #  examiner_name_family, examiner_name_given, corporate_name, publisher_name
                                    #
                                    if len(rt.attrib) > 0 and Verbose_Flag:
                                        print("roleTerm: {}".format(rt.attrib))
                                    if rt.text is not None:
                                        if Verbose_Flag:
                                            print(rt.text)
                                        if rt.text.count('aut') == 1:
                                            author_name_family = name_family
                                            author_name_given = name_given
                                            role = 'aut'
                                            if Verbose_Flag:
                                                print("author_name_family: {}".format(name_family))
                                                print("author_name_given: {}".format(name_given))
                                        elif rt.text.count('ths') == 1:
                                            role = 'ths'
                                            if Verbose_Flag:
                                                print("supervisor_name_family: {}".format(name_family))
                                                print("supervisor_name_given: {}".format(name_given))
                                        elif rt.text.count('mon') == 1:
                                            role = 'mon'
                                            if Verbose_Flag:
                                                print("examiner_name_family: {}".format(name_family))
                                                print("examiner_name_given: {}".format(name_given))
                                        elif rt.text.count('opn') == 1:
                                            role = 'opn'
                                            if Verbose_Flag:
                                                print("examiner_name_family: {}".format(name_family))
                                                print("examiner_name_given: {}".format(name_given))
                                        elif rt.text.count('pbl') == 1:
                                            publisher_name = corporate_name
                                            role = 'pbl'
                                            if Verbose_Flag:
                                                print("publisher_name: {}".format(publisher_name))
                                        elif rt.text.count('oth') == 1:
                                            # clear the corporate_name if this is a "oth" role
                                            corporate_name=''
                                            if Verbose_Flag:
                                                print("name_family: {}".format(name_family))
                                                print("name_given: {}".format(name_given))
                                        else:
                                            if Verbose_Flag:
                                                print("rt[{0}]={1}".format(j, rt))
                        elif elem.tag.count("}affiliation") == 1:
                            # Extract
                            # affiliation, author_affiliation, supervisor_affiliation, examiner_affiliation
                            if Verbose_Flag:
                                print("affiliation :")
                            if len(elem.attrib) > 0:
                                if Verbose_Flag:
                                    print(elem.attrib)
                            if elem.text is not None:
                                if len(affiliation) > 0:
                                    affiliation = affiliation + ' ,' + elem.text
                                else:
                                    affiliation=elem.text
                                    if Verbose_Flag:
                                        print(elem.text)

                        elif elem.tag.count("}description") == 1:
                            if Verbose_Flag:
                                if len(elem.attrib) > 0:
                                    if Verbose_Flag and elem.text is not None:
                                        print("description: {0} {1}".format(elem.attrib, elem.text))

                        else:
                            if Verbose_Flag:
                                print("mod_emem[{0}]={1}".format(n, elem))

                    if  name_given and name_family:
                        full_name=name_given+' '+name_family
                    elif name_given:
                        full_name=name_given
                    elif name_family:
                        full_name=name_family
                    else:
                        full_name=None

                    if full_name:
                        if role == 'aut':
                            author={'name': full_name}
                            if kthid:
                                author['kthid']=kthid
                            if affiliation:
                                author['affiliation']=affiliation
                            authors.append(author)
                        elif role == 'ths':
                            supervisor={'name': full_name}
                            if kthid:
                                supervisor['kthid']=kthid
                            if affiliation:
                                supervisor['affiliation']=affiliation
                            supervisors.append(supervisor)
                        elif role == 'mon':
                            examiner={'name': full_name}
                            if kthid:
                                examiner['kthid']=kthid
                            if affiliation:
                                examiner['affiliation']=affiliation
                            examiners.append(examiner)
                        elif role == 'opn':
                            opponent={'name': full_name}
                            if kthid:
                                opponent['kthid']=kthid
                            if affiliation:
                                opponent['affiliation']=affiliation
                            opponents.append(opponent)
                        elif role == 'pbl':
                            # publisher_name
                            print("publisher_name={}".format(publisher_name))
                        elif role == 'oth':
                            # clear the corporate_name if this is a "oth" role
                            print("role is oth")
                        else:
                            if name_given and name_family:
                                print("Unknown role for {0} {1}".format(name_given, name_family))
                    if authors:
                        pub_info['authors']=authors
                    if supervisors:
                        pub_info['supervisors']=supervisors
                    if examiners:
                        pub_info['examiners']=examiners
                    if opponents:
                        pub_info['opponents']=opponents
                # end of processing a name

                # <titleInfo lang="eng"><title>A Balance between Precision and Privacy</title><subTitle>Recommendation Model for the Healthcare Sector</subTitle></titleInfo>
                # <titleInfo lang="eng"><title>A comparative analysis of CNN and LSTM for music genre classification</title></titleInfo><language><languageTerm type="code" authority="iso639-2b">eng</languageTerm></language><titleInfo type="alternative" lang="swe"><title>En jämförande analys av CNN och LSTM för klassificering av musikgenrer</title></titleInfo>
                # <titleInfo lang="eng"><title>A Comparative Analysis of RNN and SVM</title><subTitle>Electricity Price Forecasting in Energy Management Systems</subTitle></titleInfo><language><languageTerm type="code" authority="iso639-2b">eng</languageTerm></language><titleInfo type="alternative" lang="swe"><title>En jämförande analys av RNN och SVM</title><subTitle>Prognos för elpriser i energiledningssystem</subTitle></titleInfo>
                elif current_element.tag.count("}titleInfo") == 1:
                    if Verbose_Flag:
                        print("TitleInfo: ")
                    if len(current_element.attrib) > 0:
                        if Verbose_Flag:
                            print("current_element.attrib={}".format(current_element.attrib))
                        titleInfo_type=current_element.attrib.get('type', None)
                        titleInfo_lang=current_element.attrib.get('lang', None)
                        if current_element.text is not None:
                            if Verbose_Flag:
                                print("{}".format(current_element.text))
                        for j in range(0, len(current_element)):
                            elem=current_element[j]
                            if elem.tag.count("}title") == 1:
                                if len(elem.attrib) > 0:
                                    if Verbose_Flag:
                                        print("{}".format(elem.attrib))
                                if elem.text is not None:
                                    if titleInfo_type == 'alternative':
                                        if pub_info['thesis_title'].get('alternative', None):
                                            pub_info['thesis_title']['alternative'][titleInfo_lang]=elem.text
                                        else:
                                            pub_info['thesis_title']['alternative']=dict()
                                            pub_info['thesis_title']['alternative'][titleInfo_lang]=elem.text
                                    else:
                                        pub_info['thesis_title'][titleInfo_lang]=elem.text
                            elif elem.tag.count("}subTitle") == 1:
                                if len(elem.attrib) > 0:
                                    if Verbose_Flag:
                                        print("{}".format(elem.attrib))
                                if elem.text is not None:
                                    if titleInfo_type == 'alternative':
                                        if pub_info['thesis_subtitle'].get('alternative', None):
                                            pub_info['thesis_subtitle']['alternative'][titleInfo_lang]=elem.text
                                        else:
                                            pub_info['thesis_subtitle']['alternative']=dict()
                                            pub_info['thesis_subtitle']['alternative'][titleInfo_lang]=elem.text
                                    else:
                                        pub_info['thesis_subtitle'][titleInfo_lang]=elem.text
                            else:
                                if Verbose_Flag:
                                    print("mod_emem[{0}]={1}".format(i, elem))


                elif current_element.tag.count("}identifier") == 1:
                    if current_element.text is not None:
                        identifier_type=current_element.attrib.get('type', None)
                        if identifier_type == 'uri':
                            pub_info['thesis_uri']=current_element.text
                        elif identifier_type == 'isbn':
                            pub_info['thesis_isbn']=current_element.text
                        else:
                            print("Unhandled identifier: {0} of type {1}".format(current_element.text, identifier_type))

            if Verbose_Flag:
                print("pub_info is {}".format(pub_info))

        json_records.append(pub_info)
    return json_records

# helper functions
def add_word_to_dictionary(d, language, word):
    global Verbose_Flag
    if Verbose_Flag:
        print("d={0}, language={1}, word={2}".format(d, language, word))
    lang_dict=d.get(language, None)
    if lang_dict is None:
        d[language]=[word]
    else:
        d[language].append(word)
    return d

def process_entries_from_MODS_file(mods_filename):
    global testing
    global course_id

    try:
        with open(mods_filename, "rb") as mods_data_file:
            tree=load_xmlobject_from_file(mods_data_file, mods.MODS)
            xml=BeautifulSoup(mods_data_file, 'lxml-xml')

    except:
        print("Unable to open mods file named {}".format(mods_filename))
        print("Please create a suitable mods file, the default name is theses.mods")
        sys.exit()

    extracted_info=list()

    if mods_filename:
        #tree.node
        #<Element {http://www.loc.gov/mods/v3}modsCollection at 0x34249b0>
        #>>> tree.node[1]
        #<Element {http://www.loc.gov/mods/v3}mods at 0x3d46aa0>
        json_records=extract_list_of_dicts_from_mods(tree)
        if Verbose_Flag:
            print("json_records={}".format(json_records))
        output_filename="testing.json"
        
        if Verbose_Flag:
            print("output_filename={}".format(mods_filename[:-4]))
        with open(output_filename, 'w', encoding='utf-8') as output_FH:
            j_as_string = json.dumps(json_records, ensure_ascii=False)
            print(j_as_string, file=output_FH)

        for i in range(0, len(json_records)):
            record=json_records[i]

            data=dict()
            data['contentId']=''

            # {"node": [9], "thesis_title": {"eng": "A Comparative Analysis of RNN and SVM", "alternative": {"swe": "En jämförande analys av RNN och SVM"}}, "thesis_subtitle": {"eng": "Electricity Price Forecasting in Energy Management Systems", "alternative": {"swe": "Prognos för elpriser i energiledningssystem"}}, "genre_publicationTypeCode": "studentThesis", "thesis_uri": "http://urn.kb.se/resolve?urn=urn:nbn:se:kth:diva-259745"}

            
            authors=record['authors']
            for i, a in enumerate(authors):
                key1="author{}_name".format(i)
                key2="author{}_kthid".format(i)
                data[key1]=a.get('name', None)
                data[key2]=a.get('kthid', None)

            thesis_title=record['thesis_title']
            thesis_subtitle=record['thesis_subtitle']
            thesis_main_title_lang=None
            thesis_secondary_title_lang=None
            thesis_secondary_title=None

            # note that here were are only supporting a main or secondary language of eng or swe
            thesis_main_title=thesis_title.get('eng', None)
            if thesis_main_title:
                thesis_main_title_lang='eng'
                data['maintitle_English']=thesis_main_title
                thesis_secondary_title_alternative=thesis_title.get('alternative', None)
                if thesis_secondary_title_alternative:
                    thesis_secondary_title=thesis_secondary_title_alternative.get('swe', None)
                    if thesis_secondary_title:
                        data['alternative_title_Swedish']=thesis_secondary_title
            else:
                # case of an Swedish primary title and possible English alternative title
                thesis_main_title=thesis_title.get('swe', None)
                if thesis_main_title:
                    data['maintitle_Swedish']=thesis_main_title
                    thesis_secondary_title_alternative=thesis_title.get('alternative', None)
                    if thesis_secondary_title_alternative:
                        thesis_secondary_title=thesis_secondary_title_alternative.get('eng', None)
                        if thesis_secondary_title:
                            data['alternative_title_Engish']=thesis_secondary_title

            # note that here were are only supporting a main or secondary language of eng or swe
            thesis_main_title=thesis_subtitle.get('eng', None)
            if thesis_main_title:
                thesis_main_title_lang='eng'
                data['subtitle_English']=thesis_main_title
                thesis_secondary_title_alternative=thesis_subtitle.get('alternative', None)
                if thesis_secondary_title_alternative:
                    thesis_secondary_title=thesis_secondary_title_alternative.get('swe', None)
                    if thesis_secondary_title:
                        data['alternative_subtitle_Swedish']=thesis_secondary_title
            else:
                # case of an Swedish primary title and possible English alternative title
                thesis_main_title=thesis_subtitle.get('swe', None)
                if thesis_main_title:
                    data['subtitle_Swedish']=thesis_main_title
                    thesis_secondary_title_alternative=thesis_subtitle.get('alternative', None)
                    if thesis_secondary_title_alternative:
                        thesis_secondary_title=thesis_secondary_title_alternative.get('eng', None)
                        if thesis_secondary_title:
                            data['alternative_subtitle_Engish']=thesis_secondary_title
            data['thesis_uri']=record['thesis_uri']


            extracted_info.append(data)
        return extracted_info

def main(argv):
    global Verbose_Flag
    global testing

    Use_local_time_for_output_flag=True

    argp = argparse.ArgumentParser(description="MODS_to_titles_and_subtitles.py --mods file.mods")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-m', '--mods',
                      type=str,
                      default="theses.mods",
                      help="read mods formatted information from file"
                      )

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))

    mods_filename=args["mods"]
    extracted_info=process_entries_from_MODS_file(mods_filename)

    print("Total number of items of thesis information={}".format(len(extracted_info)))
    extracted_info_pd=pd.json_normalize(extracted_info)
    # 

    #df = df.reindex(columns=
    #extracted_info_pd = extracted_info_pd.reindex(columns=['maintitle_English',	'subtitle_English', 'alternative_title_Swedish', 'alternative_subtitle_Swedish', 'maintitle_Swedish', 'subtitle_Swedish', 'alternative_title_Engish', 'alternative_subtitle_Engish', 'thesis_uri'])
    output_filename="titles-from-{}.xlsx".format(mods_filename[:-5])
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    extracted_info_pd.to_excel(writer, sheet_name='Titles')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
