#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./extract_customDocProperties.py filename.docx --json output.json
#
# Purpose: Extract document information and properties from a DOCX file to make a JSON output
#
# Example:
# ./extract_customDocProperties.py test.docx
#
# Pretty print the resulting JSON
# ./extract_customDocProperties.py Template-thesis-English-2021-with-for-DiVA.docx --pretty
#
# force English as the language of the body of the document
# ./extract_customDocProperties.py Template-thesis-English-2021-with-for-DiVA.docx --English
#
# force Swedish as the language of the body of the document
# ./extract_customDocProperties.py Template-thesis-English-2021-with-for-DiVA.docx --Swedish
#
#
# 2021-04-22 G. Q. Maguire Jr.
#
import re
import sys

import json
import argparse
import os			# to make OS calls, here to get time zone info

from zipfile import ZipFile

from bs4 import BeautifulSoup   # for parsing the XML

import pprint

def cleanup_otherinformat(list_of_wt):
    s1=''
    for wt in list_of_wt:
        s1=s1+wt.string
    s1=s1.replace('<w:t>', '')
    s1=s1.replace('</w:t>', '')
    s1=s1.replace('<w:t xml:space="preserve">', '')
    s1=s1.replace('”', '"')
    s1='{' + s1[:-1] + '}'
    return json.loads(s1)
        
def cleanup_abstract(list_of_s):
    trailers_to_remove=['<P>Keywords', '<P>Nykelord']
    s0=cleanup_abstract_or_keywords(list_of_s)
    #if the list ends in '<P>Keywords' or , then trim this from the list
    for t in trailers_to_remove:
        if s0.endswith(t):
            s0=s0[:-(len(t))]
    if s0.startswith('<P>'):
        s0='<P>'+s0[3:].replace('<P>', '</P><P>')
    else:
        s0='<P>'+s0.replace('<P>', '</P><P>')
    if s0.endswith('<P>'):
        return s0[:-len('<P>')]
    if s0.startswith('<P>'):
        return s0+'</P>'
    return s0

def cleanup_keywords(list_of_s):
    s0=cleanup_abstract_or_keywords(list_of_s)
    s0=s0.replace('<P>', '')    #  no need for paragraphs in list of keywords
    return s0

    
def cleanup_abstract_or_keywords(list_of_s):
    #print("length of list_of_s={}".format(len(list_of_s)))
    s0=list()
    for s in list_of_s:
        s1=''
        #print("type of s={0}, s={1}".format(type(s), s))
        if type(s) == list:
            s1=s1+cleanup_abstract_or_keywords(s)
        else:
            style=s.find('w:pstyle')# When there is a change in paragraph style, it must be a new paragraph
            if style:
                #print("style={}".format(style))
                s1=s1+'<P>'
            for wt in s.findAll('w:t'):
                #print("wt={}".format(wt))
                if wt.text:
                    #print("wt.text={}".format(wt.text))
                    s1=s1+wt.text
        if len(s1)> 0:
            s0.append(s1)
    s2=''.join(s0)
    #print("s2={}".format(s2))
    return s2
    
def main(argv):
    parser = argparse.ArgumentParser(description='extract custom properties from a docx file.')
    parser.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    parser.add_argument('filenames', type=str, nargs='+',
                    help='name of docx file')

    parser.add_argument('--Swedish', type=int, nargs='?', required=False,
                        help='Force Swedish as the language of the body of document')

    parser.add_argument('--English', type=int, nargs='?', required=False,
                        help='Force English as the language of the body of document')

    parser.add_argument('--pretty', required=False,
                      default=False,
                      action="store_true",
                      help="Pretty print")

    parser.add_argument('-j', '--json',
                      type=str,
                      default="output.json",
                      help="JSON file for extracted data"
                      )

    args = vars(parser.parse_args(argv))
    Verbose_Flag=args["verbose"]

    if Verbose_Flag:
        print("args={}".format(args))
        
    if args['Swedish'] and args['English']:
        print("Error in trying to force the langauge of the document, it cannot be both Swedish and English")
        return

    if args['Swedish']:
        print("Lanaguge of the body forced to be Swedish")
    if args['English']:
        print("Lanaguge of the body forced to be English")

    filenames=args['filenames']
    if not filenames or len(filenames) < 1:
        print("No filename specified")
        return

    inputfile=filenames[0]
    if Verbose_Flag:
        print("inputfile={}".format(inputfile))

    # {"Author1": {"Last name": "", "First name": "", "Local User Id": "", "E-mail": "", "organisation": {"L1": ""}}, "Author2": {"Last name": "", "First name": "", "Local User Id": "", "E-mail": "", "organisation": {"L1": ""}}, "Cycle": "", "Course code": "", "Credits": "", "Degree1": {"Degree": "", "Educational program": "", "programcode": "", "subjectArea": ""}, "Title": {"Main title": "", "Subtitle": "", "Language": ""}, "Alternative title": {"Main title": "", "Subtitle": "", "Language": ""}, "Supervisor1": {"Last name": "", "First name": "", "Local User Id": "", "E-mail": "", "organisation": {"L1": "", "L2": ""}}, "Supervisor2": {"Last name": "", "First name": "", "Local User Id": "", "E-mail": "", "organisation": {"L1": "", "L2": ""}}, "Supervisor3": {"Last name": "", "First name": "", "E-mail": "", "Other organisation": ""}, "Examiner1": {"Last name": "", "First name": "", "Local User Id": "", "E-mail": "", "organisation": {"L1": "", "L2": ""}}, "Cooperation": {"Partner_name": ""}, "National Subject Categories": "", "Other information": {"Year": "", "Number of pages": ""}, "Series": {"Title of series": "", "No. in series": ""}, "Opponents": {"Name": ""}, "Presentation": {"Date": "", "Language": "", "Room": "", "Address": "", "City": ""}, "Number of lang instances": "", "abstracts": {"eng": "", "swe": "”, Keywords[swe]: ”"}, "keywords": {"eng": "", "swe": ""}}

    # {"Other information": {"Year": "", "Number of pages": ""} - still missing Number of pages 
    # "Number of lang instances": "", "abstracts": {"eng": "", "swe": "”, Keywords[swe]: ”"}, "keywords": {"eng": "", "swe": ""}}

    info=dict()
    info['Language']="Unknown"
    info['Title']=dict()
    info['Title']={'Main title': '', 'Subtitle': '', 'Language': ''}
    info['Alternative title']={'Main title': '', 'Subtitle': '', 'Language': ''}
    number_of_pages=''

    # Create a ZipFile Object and load sample.zip in it
    with ZipFile(inputfile, 'r') as zipObj:
        # Get a list of all archived file names from the zip
        listOfFileNames = zipObj.namelist()
        if Verbose_Flag:
            print("listOfFileNames={}".format(listOfFileNames))

        # Either the language is specified as an argument to the command or we need to guess
        if args['Swedish'] or args['English']:
            if args['Swedish']:
                info['Language']='swe'
            else:
                info['Language']='eng'
        else:                   # time to guess, look in the settings.xml for the default language
            # using information from https://docs.microsoft.com/en-us/dotnet/standard/linq/style-part-wordprocessingml-document
            fileName='word/styles.xml'
            if fileName in listOfFileNames:
                with zipObj.open(fileName) as myfile:
                    file_contents=myfile.read()
                    xml=BeautifulSoup(file_contents, "lxml")
                    #print("xml={}".format(xml))
                    doc_defaults=xml.find('w:docdefaults')
                    if Verbose_Flag:
                        print("doc_defaults={}".format(doc_defaults))

                    lang_specification=doc_defaults.find('w:lang')
                    lang_setting=lang_specification.get('w:val')
                    if Verbose_Flag:
                        print("document's default language setting is w:val={}".format(lang_setting))

                    if lang_setting == 'sv-SE':
                        info['Language']='swe'
                        print("Guessing this document is written in Swedish")
                    else:
                        info['Language']='eng'
                        print("Guessing this document is written in English")

        # pages can be found in the "document.xml" file, for example:
        #<w:pPr><w:pStyle w:val="ForDIVAItem"/></w:pPr><w:r w:rsidRPr="005C4433"><w:t>”Other</w:t></w:r><w:r><w:t xml:space="preserve"> information”: {”Year”</w:t></w:r><w:proofErr w:type="gramStart"/><w:r><w:t>: ”</w:t></w:r><w:proofErr w:type="gramEnd"/><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> DATE  \@ "yyyy"  \* MERGEFORMAT </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r w:rsidR="000945B8"><w:rPr><w:noProof/></w:rPr><w:t>2021</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r><w:r><w:t>”,</w:t></w:r><w:r w:rsidR="00555E35"><w:t xml:space="preserve"> </w:t></w:r><w:r w:rsidRPr="005C4433"><w:t>”Number of pages”: ”</w:t></w:r><w:r w:rsidR="004D25DE"><w:fldChar w:fldCharType="begin"/></w:r><w:r w:rsidR="004D25DE"><w:instrText xml:space="preserve">pageref </w:instrText></w:r><w:r w:rsidR="004D25DE" w:rsidRPr="004D25DE"><w:instrText>lastPageofPreface</w:instrText></w:r><w:r w:rsidR="004D25DE"><w:fldChar w:fldCharType="separate"/></w:r><w:r w:rsidR="006A23DE"><w:rPr><w:noProof/></w:rPr><w:t>xiii</w:t></w:r><w:r w:rsidR="004D25DE"><w:fldChar w:fldCharType="end"/></w:r><w:r w:rsidRPr="005C4433"><w:t>,</w:t></w:r><w:r w:rsidR="004D25DE"><w:fldChar w:fldCharType="begin"/></w:r><w:r w:rsidR="004D25DE"><w:instrText xml:space="preserve"> pageref </w:instrText></w:r><w:r w:rsidR="004D25DE" w:rsidRPr="004D25DE"><w:instrText>lastPageofMainmatter</w:instrText></w:r><w:r w:rsidR="004D25DE"><w:fldChar w:fldCharType="separate"/></w:r><w:r w:rsidR="006A23DE"><w:rPr><w:noProof/></w:rPr><w:t>19</w:t></w:r><w:r w:rsidR="004D25DE"><w:fldChar w:fldCharType="end"/></w:r><w:r w:rsidRPr="005C4433"><w:t>”},</w:t></w:r></w:p><w:p w:rsidR="000945B8" w:rsidRDefault="000945B8" w:rsidP="00555E35"><w:pPr><w:pStyle w:val="ForDIVAItem"/>

        # We use the page reference to 'lastPageofPreface' and 'lastPageofMainmatter' in the above to find the number of pages
        interesting_bookmarks=['SwedishAbstract', 'SwedishKeywords', 'EnglishAbstract', 'EnglishKeywords']
        paragraphs_within_bookmark={'SwedishAbstract': [],
                                    'SwedishKeywords': [],
                                    'EnglishAbstract': [],
                                    'EnglishKeywords': [],
                                    }

        fileName='word/document.xml'
        if fileName in listOfFileNames:
            with zipObj.open(fileName) as myfile:
                file_contents=myfile.read()
                xml=BeautifulSoup(file_contents, "lxml")
                if Verbose_Flag:
                    print("xml={}".format(xml))
                paragraphs=xml.findAll('w:p')
                # find "Other information with number of pages
                for p in paragraphs:
                    p_styles=p.findAll('w:pstyle')
                    for ps in p_styles:
                        possible_diva_item=ps.get('w:val', None)
                        if possible_diva_item == 'ForDIVAItem':
                            # print("found ForDIVAItem={}".format(p))
                            instrText_elements=p.findAll('w:instrtext')
                            for ie in instrText_elements:
                                if ie.string == 'lastPageofPreface':
                                    all_wt_in_p=p.findAll('w:t')
                                    if Verbose_Flag:
                                        print("all_wt_in_p={}".format(all_wt_in_p))
                                    other_info=cleanup_otherinformat(all_wt_in_p)
                                    print("other_info={}".format(other_info))
                                    oi=other_info.get('Other information', None)
                                    if oi:
                                        number_of_pages=oi.get('Number of pages', None)
                                        print("number_of_pages={}".format(number_of_pages))

                # get paragrpahs w:p and end of bookmarks w:bookmarkend and then information about bookmarks
                paragraphs2=xml.findAll(re.compile(r'(^w:p$|w:bookmarkend)'))
                inside_bm=False
                current_bm=None
                current_bm_id=None
                for p in paragraphs:
                    bookmark_starts=p.findAll('w:bookmarkstart')
                    if bookmark_starts:
                        for bs in bookmark_starts:
                            name_of_bs=bs.get('w:name', None)
                            id_of_bs=bs.get('w:id', None)
                            if name_of_bs in interesting_bookmarks:
                                if Verbose_Flag:
                                    print("name_of_bs={0}, id={1}".format(name_of_bs, id_of_bs))
                                inside_bm=True
                                current_bm=name_of_bs
                                current_bm_id=id_of_bs

                    # note that you have to do this right away otherwise if there is an bookmark end you will miss the first paragraph
                    if inside_bm:
                        #print("inside_bm name={0}, para={1}, type{2}".format(current_bm, paragraphs_within_bookmark[current_bm], type(paragraphs_within_bookmark[current_bm])))
                        ce=paragraphs_within_bookmark[current_bm]
                        #print("ce={}".format(ce))
                        if ce:
                            ce.append(list(p))
                        else:
                            ce=list(p)
                        paragraphs_within_bookmark[current_bm]=ce

                    bookmark_ends=p.findAll('w:bookmarkend')
                    for be in bookmark_ends:
                        id_of_be=be.get('w:id', None)
                        if id_of_be == current_bm_id:
                            if Verbose_Flag:
                                print("id_of_be={}".format(id_of_be))
                            inside_bm=False
                            current_bm=None
                
        if Verbose_Flag:
            print("paragraphs_within_bookmark={}".format(paragraphs_within_bookmark))
        
        info['Number of lang instances']='2'
        info['abstracts']={'eng': cleanup_abstract(paragraphs_within_bookmark['EnglishAbstract']),
                           'swe': cleanup_abstract(paragraphs_within_bookmark['SwedishAbstract'])}
        info['keywords']={'eng': cleanup_keywords(paragraphs_within_bookmark['EnglishKeywords']),
                          'swe': cleanup_keywords(paragraphs_within_bookmark['SwedishKeywords'])}

        # Get Title and last modified timestamp from core document properties
        fileName='docProps/core.xml'
        if fileName in listOfFileNames:
            with zipObj.open(fileName) as myfile:
                file_contents=myfile.read()
                xml=BeautifulSoup(file_contents, "lxml")
                title=xml.find('dc:title')
                if Verbose_Flag:
                    print("title={}".format(title.string))
                if title and len(title.string) > 0:
                    info['Title']['Main title']=title.string
                    if info['Language'] == 'eng':
                        info['Title']['Language']='eng'
                    else:
                        info['Title']['Language']='swe'

                last_modified=xml.find('dcterms:modified')
                if Verbose_Flag:
                    print("title={}".format(last_modified.string))
                if last_modified and len(last_modified.string) > 4:
                    other_informationExists=info.get('Other information', None)
                    if not other_informationExists:
                        info['Other information']={"Year": last_modified.string[0:4], "Number of pages": number_of_pages}
                    else:
                        info['Other information']['Year']=last_modified.string[0:4]
        else:
            print("No file {} - cannot get Title or last modified timestamp".format(fileName))

        # process the custom properties
        fileName='docProps/custom.xml'
        if fileName in listOfFileNames:
            with zipObj.open(fileName) as myfile:
                file_contents=myfile.read()
                xml=BeautifulSoup(file_contents, "lxml")
                for customProp in xml.findAll('property'):
                    if Verbose_Flag:
                        print("customProp={}".format(customProp))
                    name=customProp.get('name')
                    pid=customProp.get('pid')
                    value=customProp.string
                    if Verbose_Flag:
                        print("name={0}, pid={1}, value={2}".format(name, pid, value))
                    if name == 'Subtitle':
                        info['Title']['Subtitle']=value
                    elif name == 'Alternative_main_title':
                        info['Alternative title']['Main title']=value
                        if info['Language'] == 'eng':
                            info['Alternative title']['Language']='swe'
                        else:
                            info['Alternative title']['Language']='eng'
                    elif name == 'Alternative_subtitle':
                        info['Alternative title']['Subtitle']=value
                    elif name.startswith('Author1'):
                        if not info.get('Author1', None):
                            info['Author1']= {'Last name': '', 'First name': '', 'Local User Id': '', 'E-mail': ''}
                        if name == 'Author1_Last_name':
                            info['Author1']['Last name']=value
                        elif name == 'Author1_First_name':
                            info['Author1']['First name']=value
                        elif name == 'Author1_Local User Id':
                            info['Author1']['Local User Id']=value
                        elif name == 'Author1_E-mail':
                            info['Author1']['E-mail']=value
                        elif name == 'Author1_organization_L1':
                            if value == '<NA>':
                                continue
                            org_exists=info['Author1'].get('organisation', None)
                            if not org_exists:
                                info['Author1']['organisation']=dict()
                                info['Author1']['organisation']['L1']=value
                        elif name == 'Author1_organization_L2':
                            if value == '<NA>':
                                continue
                            org_exists=info['Author1'].get('organisation', None)
                            if org_exists and info['Author1']['organisation'].get('L1', None):
                                info['Author1']['organisation']['L2']=value
                        elif name == 'Author1_Other_organisation':
                            if value != '<NA>':
                                info['Author1']['Other organisation']=value
                        else:
                            print("Unknow Author1 property: {}".format(name))
                            continue
                    elif name.startswith('Author2'):
                        if not info.get('Author2', None):
                            info['Author2']= {'Last name': '', 'First name': '', 'Local User Id': '', 'E-mail': ''}
                        if name == 'Author2_Last_name':
                            info['Author2']['Last name']=value
                        elif name == 'Author2_First_name':
                            info['Author2']['First name']=value
                        elif name == 'Author2_Local User Id':
                            info['Author2']['Local User Id']=value
                        elif name == 'Author2_E-mail':
                            info['Author2']['E-mail']=value
                        elif name == 'Author2_organization_L1':
                            if value == '<NA>':
                                continue
                            org_exists=info['Author2'].get('organisation', None)
                            if not org_exists:
                                info['Author2']['organisation']=dict()
                            if value != '<NA>':
                                info['Author2']['organisation']['L1']=value
                        elif name == 'Author2_organization_L2':
                            if value == '<NA>':
                                continue
                            org_exists=info['Author2'].get('organisation', None)
                            if org_exists and info['Author2']['organisation'].get('L1', None):
                                info['Author2']['organisation']['L2']=value
                        elif name == 'Author2_Other_organisation':
                            if value != '<NA>':
                                info['Author2']['Other organisation']=value
                        else:
                            print("Unknow Author2 property: {}".format(name))
                            continue
                    elif name.startswith('Examiner1'):
                        if not info.get('Examiner1', None):
                            info['Examiner1']= {'Last name': '', 'First name': '', 'Local User Id': '', 'E-mail': ''}
                        if name == 'Examiner1_Last_name':
                            info['Examiner1']['Last name']=value
                        elif name == 'Examiner1_First_name':
                            info['Examiner1']['First name']=value
                        elif name == 'Examiner1_Local User Id':
                            info['Examiner1']['Local User Id']=value
                        elif name == 'Examiner1_E-mail':
                            info['Examiner1']['E-mail']=value
                        elif name == 'Examiner1_organization_L1':
                            if value == '<NA>':
                                continue
                            org_exists=info['Examiner1'].get('organisation', None)
                            if not org_exists:
                                info['Examiner1']['organisation']=dict()
                                info['Examiner1']['organisation']['L1']=value
                        elif name == 'Examiner1_organization_L2':
                            if value == '<NA>':
                                continue
                            org_exists=info['Examiner1'].get('organisation', None)
                            if org_exists and info['Examiner1']['organisation'].get('L1', None):
                                info['Examiner1']['organisation']['L2']=value
                        elif name == 'Examiner1_Other_organisation':
                            if value != '<NA>':
                                info['Examiner1']['Other organisation']=value
                        else:
                            print("Unknow Examiner1 property: {}".format(name))
                            continue
                    elif name.startswith('Supervisor1'):
                        if not info.get('Supervisor1', None):
                            info['Supervisor1']= {'Last name': '', 'First name': '', 'Local User Id': '', 'E-mail': ''}
                        if name == 'Supervisor1_Last_name':
                            info['Supervisor1']['Last name']=value
                        elif name == 'Supervisor1_First_name':
                            info['Supervisor1']['First name']=value
                        elif name == 'Supervisor1_Local User Id':
                            info['Supervisor1']['Local User Id']=value
                        elif name == 'Supervisor1_E-mail':
                            info['Supervisor1']['E-mail']=value
                        elif name == 'Supervisor1_organization_L1':
                            if value == '<NA>':
                                continue
                            org_exists=info['Supervisor1'].get('organisation', None)
                            if not org_exists:
                                info['Supervisor1']['organisation']=dict()
                                info['Supervisor1']['organisation']['L1']=value
                        elif name == 'Supervisor1_organization_L2':
                            if value == '<NA>':
                                continue
                            org_exists=info['Supervisor1'].get('organisation', None)
                            if org_exists and info['Supervisor1']['organisation'].get('L1', None):
                                info['Supervisor1']['organisation']['L2']=value
                        elif name == 'Supervisor1_Other_organisation':
                            if value != '<NA>':
                                info['Supervisor1']['Other organisation']=value
                        else:
                            print("Unknow Supervisor1 property: {}".format(name))
                            continue
                    elif name.startswith('Supervisor2'):
                        if not info.get('Supervisor2', None):
                            info['Supervisor2']= {'Last name': '', 'First name': '', 'Local User Id': '', 'E-mail': ''}
                        if name == 'Supervisor2_Last_name':
                            info['Supervisor2']['Last name']=value
                        elif name == 'Supervisor2_First_name':
                            info['Supervisor2']['First name']=value
                        elif name == 'Supervisor2_Local User Id':
                            info['Supervisor2']['Local User Id']=value
                        elif name == 'Supervisor2_E-mail':
                            info['Supervisor2']['E-mail']=value
                        elif name == 'Supervisor2_organization_L1':
                            if value == '<NA>':
                                continue
                            org_exists=info['Supervisor2'].get('organisation', None)
                            if not org_exists:
                                info['Supervisor2']['organisation']=dict()
                                info['Supervisor2']['organisation']['L1']=value
                        elif name == 'Supervisor2_organization_L2':
                            if value == '<NA>':
                                continue
                            org_exists=info['Supervisor2'].get('organisation', None)
                            if org_exists and info['Supervisor2']['organisation'].get('L1', None):
                                info['Supervisor2']['organisation']['L2']=value
                        elif name == 'Supervisor2_Other_organisation':
                            if value != '<NA>':
                                info['Supervisor2']['Other organisation']=value
                        else:
                            print("Unknow Supervisor2 property: {}".format(name))
                            continue
                    elif name.startswith('Supervisor3'):
                        if not info.get('Supervisor3', None):
                            info['Supervisor3']= {'Last name': '', 'First name': '', 'Local User Id': '', 'E-mail': ''}
                        if name == 'Supervisor3_Last_name':
                            info['Supervisor3']['Last name']=value
                        elif name == 'Supervisor3_First_name':
                            info['Supervisor3']['First name']=value
                        elif name == 'Supervisor3_Local User Id':
                            info['Supervisor3']['Local User Id']=value
                        elif name == 'Supervisor3_E-mail':
                            info['Supervisor3']['E-mail']=value
                        elif name == 'Supervisor3_organization_L1':
                            if value == '<NA>':
                                continue
                            org_exists=info['Supervisor3'].get('organisation', None)
                            if not org_exists:
                                info['Supervisor3']['organisation']=dict()
                                info['Supervisor3']['organisation']['L1']=value
                        elif name == 'Supervisor3_organization_L2':
                            if value == '<NA>':
                                continue
                            org_exists=info['Supervisor3'].get('organisation', None)
                            if org_exists and info['Supervisor3']['organisation'].get('L1', None):
                                info['Supervisor3']['organisation']['L2']=value
                        elif name == 'Supervisor3_Other_organisation':
                            if value != '<NA>':
                                info['Supervisor3']['Other organisation']=value
                        else:
                            print("Unknow Supervisor3 property: {}".format(name))
                            continue
                    elif name == 'Cooperation_Partner_name':
                        info['Cooperation']= {"Partner_name": value}
                    elif name == 'Cycle':
                        info['Cycle']=value
                    elif name == 'Course_code':
                        info['Course code']=value
                    elif name == 'Credits':
                        info['Credits']=value
                    elif name in ['programcode', 'Educational program', 'Degree', 'subjectArea']:
                        degreeExists=info.get('Degree1', None)
                        if not degreeExists:
                            info['Degree1']={"Degree": "", "Educational program": "", "programcode": "", "subjectArea": ""}
                        if name == 'programcode':
                            info['Degree1']['programcode']=value
                        elif name == 'Educational program':
                            info['Degree1']['Educational program']=value
                        elif name == 'Degree':
                            info['Degree1']['Degree']=value
                        elif name == 'subjectArea':
                            info['Degree1']['subjectArea']=value
                        else:
                            print("Unknown degree related name: {}".format(name))
                    elif name in ['Second_programcode', 'Second_Educational_program', 'Second_degree', 'Second_subjectarea']:
                        degreeExists=info.get('Degree2', None)
                        if not degreeExists:
                            info['Degree2']={"Degree": "", "Educational program": "", "programcode": "", "subjectArea": ""}
                        if name == 'Second_programcode':
                            info['Degree2']['programcode']=value
                        elif name == 'Second_Educational_program':
                            info['Degree2']['Educational program']=value
                        elif name == 'Second_degree':
                            info['Degree2']['Degree']=value
                        elif name == 'Second_subjectarea':
                                info['Degree2']['subjectArea']=value
                        else:
                            print("Unknown degree related name: {}".format(name))
                    elif name == 'National Subject Categories':
                        info['National Subject Categories']=value
                    elif name == 'Opponents_Name':
                        info['Opponents']={"Name": value}
                    elif name.startswith('Presentation_'):
                        presentationExists=info.get('Presentation', None)
                        if not presentationExists:
                            info['Presentation']={'Date': '', 'Language': '', 'Room': '', 'Address': '', 'City': ''}
                        if name == 'Presentation_Date':
                            info['Presentation']['Date']=value
                        elif name == 'Presentation_Language':
                            info['Presentation']['Language']=value
                        elif name == 'Presentation_Room':
                            info['Presentation']['Room']=value
                        elif name == 'Presentation_Address':
                            info['Presentation']['Address']=value
                        elif name == 'Presentation_City':
                            info['Presentation']['City']=value
                        else:
                            print("Unknown presentation related name: {}".format(name))
                    elif name in ['Series_name', 'Number_in_series']:
                        seriesExists=info.get('Series', None)
                        if not seriesExists:
                            info['Series']={"Title of series": "", "No. in series": ""}
                        if name == 'Series_name':
                            info['Series']['Title of series']=value
                        if name == 'Number_in_series':
                            info['Series']['No. in series']=value


            
    if args['pretty']:
        print("info=")
        pp = pprint.PrettyPrinter(indent=4, width=1024) # configure prettyprinter
        pp.pprint(info)
    else:
        print("info={}".format(info))

    output_filename=args["json"]
    print("output_filename={}".format(output_filename))
    with open(output_filename, 'w', encoding='utf-8') as output_FH:
        j_as_string = json.dumps(info, ensure_ascii=False)
        print(j_as_string, file=output_FH)

if __name__ == '__main__':
   sys.exit(main(sys.argv[1:]))
