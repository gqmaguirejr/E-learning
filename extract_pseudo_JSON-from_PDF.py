#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./extract_pseudo_JSON-from_PDF.py --pdf test.pdf [--acronyms acronyms.tex]
#
# Purpose: Extract data from the end of a PDF file that has been put out by my LaTeX template for use when inserting a thesis into DiVA.
#
# Example:
# ./extract_pseudo_JSON-from_PDF.py --pdf test5.pdf
# default output file is calendar_event.json
#
# ./extract_pseudo_JSON-from_PDF.py --pdf test5.pdf --json event.json --pdf test.pdf --acronyms acronyms.tex
##
#
# To get the correct pdfminer package od:
# pip install pdfminer.six
#
# 2021-04-22 G. Q. Maguire Jr.
#
import re
import sys

import json
import argparse
import os			# to make OS calls, here to get time zone info

from io import StringIO

from pdfminer.converter import TextConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from pdfminer.high_level import extract_pages
from io import BytesIO

def remove_comment_to_EOL(s):
    global Verbose_Flag
    offset=s.find('%')
    if offset < 0:              # if no comments, then return right away
        return s
    while (offset) >= 0:
        if (offset == 0) or (s[offset-1] != '\\'):
            # remove to EOL
            EOL_offset=s.find('\n', offset)
            if EOL_offset > 0:
                if (offset == 0):
                    s=s[EOL_offset+1:]
                else:
                    s=s[0:offset] + '\n' +s[EOL_offset+1:]
        offset=s.find('%', offset+1)
    return s



def replace_latex_symbol(s, symbol, insert_symbol):
    global Verbose_Flag
    cmd_offset=s.find(symbol)
    while (cmd_offset) > 0:
        s1=s[:cmd_offset]
        s2=s[cmd_offset+len(symbol):]
        s=s1+insert_symbol+s2
        cmd_offset=s.find(symbol, cmd_offset)
    return s


# usage: replace_latex_command(s1, '\\textit{', '<i>', '</i>')
def replace_latex_command(s, command, insert_at_start, insert_at_end):
    global Verbose_Flag
    cmd_offset=s.find(command)
    while (cmd_offset) > 0:
        s1=s[:cmd_offset]
        end_offset=s.find('}', cmd_offset+len(command))
        s2=s[cmd_offset+len(command):end_offset]
        s3=s[end_offset+1:]
        s=s1+insert_at_start+s2+insert_at_end+s3
        cmd_offset=s.find(command, cmd_offset)
    return s

# \textregistered
# \textcopyright
# \texttrademark
def clean_up_abstract(s):
    #print("in clean_up_abstract abstract={}".format(s))
    if s[0] == '\n':
        s=s[1:]
    s=remove_comment_to_EOL(s)
    s='<p>'+s+'</p>'
    #s=s.replace('<span style="font-family: TeXGyreHeros-Bold; font-size:5px">', '<span style="font-weight:bold">')
    #s=s.replace('<span style="font-family: TeXGyreHeros-Italic; font-size:5px">', '<span style="font-style:italic">')
    #s=s.replace('<span style="font-family: TeXGyreHeros-Regular; font-size:5px">', '<span>')
    #s=s.replace('<span style="font-family: TeXGyreCursor-Regular; font-size:5px">', '<span>')
    s=s.replace('', '') 
    s=s.replace('\x0c', '')
    s=s.replace('\n\n', '</p><p>')
    s=s.replace('\\&', '&amp;')
    s=s.replace('\\linebreak[4]', '')
    s=replace_latex_command(s, '\\textit{', '<i>', '</i>')
    s=replace_latex_command(s, '\\emph{', '<strong>', '</strong>')
    s=replace_latex_command(s, '\\textbf{', '<bold>', '</bold>')
    s=replace_latex_command(s, '\\texttt{', '<tt>', '</tt>')
    s=replace_latex_command(s, '\\textsubscript{', '<sub>', '</sub>')
    s=replace_latex_command(s, '\\textsuperscript{', '<sup>', '</sup>')
    s=replace_latex_symbol(s, '\\ldots', ' ... ')
    s=replace_latex_symbol(s, '\\textregistered', '&reg;')
    s=replace_latex_symbol(s, '\\texttrademark', '&trade;')
    s=replace_latex_symbol(s, '\\textcopyright', '&copy;')
    s=s.replace('\\begin{itemize}</p><p>\\item', '</p><ul><li>')
    s=s.replace('\\item', '</li><li>')
    s=s.replace('</p><p>\\end{itemize}</p>', '</li></ul>')
    s=s.replace('\\end{itemize}', '</li></ul>')
    s=s.replace('\\begin{enumerate}</p><p>\\item', '</p><ol><li>')
    s=s.replace('</p><p>\\end{enumerate}</p>', '</li></il>')
    s=s.replace('\n', ' ')

    # Following three lines added for processing abstracts from DOCX documents
    s=s.replace('<p>  </p><p>   </p><p> </p>', '') # remove this pattern from abstracts - It is due to the spacing from the heading
    s=s.replace(' </p>', '</p>') # remove space before </p>' from abstracts
    s=s.replace('<p>•</p><p>', '<p>• ') # join the bullet with the paragraph


    # handle defines.tex macros
    s=s.replace('\\eg', 'e.g.')
    s=s.replace('\\Eg', 'E.g.')
    s=s.replace('\\ie', 'i.e.')
    s=s.replace('\\Ie', 'I.e.')
    s=s.replace('\\etc', 'etc.')
    s=s.replace('\\etal', 'et al.')
    s=s.replace('\\first', '(i) ')
    s=s.replace('\\Second', '(ii) ')
    s=s.replace('\\third', '(iii) ')
    s=s.replace('\\fourth', '(iv) ')
    s=s.replace('\\fifth', '(v) ')
    s=s.replace('\\sixth', '(vi) ')
    s=s.replace('\\seventh', '(vii) ')
    s=s.replace('\\eighth', '(viii) ')
    # handle some units
    s=s.replace('{\\meter\\squared}', '\u202Fm<sup>2</sup>')
    s=s.replace('{\\meter\\per\\second}', '\u202Fm\u202Fs<sup>-1</sup>')
    s=s.replace('{\\second}', '\u202Fs')
    s=s.replace('{\\meter}', '\u202Fm')
    s=s.replace('{\\percent}', '%')
    s=replace_latex_command(s, '\\num{', '', '')
    s=replace_latex_command(s, '\\SI{', '', '')
    #
    trailing_empty_paragraph='<p> </p>'
    if s.endswith(trailing_empty_paragraph):
        s=s[:-len(trailing_empty_paragraph)]
    trailing_empty_paragraph='<p></p>'
    if s.endswith(trailing_empty_paragraph):
        s=s[:-len(trailing_empty_paragraph)]
    return s


def check_for_acronyms(a):
    if (a.find('\\gls{') >= 0) or (a.find('\\glspl{') >= 0) or \
       (a.find('\\Gls{') >= 0) or (a.find('\\Glspl{') >= 0) or \
       (a.find('\\acrlong{') >= 0) or (a.find('\\acrshort{') >= 0) or \
       (a.find('\\acrfull{') >= 0) or \
       (a.find('\\glsxtrshort{') >= 0) or (a.find('\\glsxtrlong{') >= 0) \
       or (a.find('\\glsxtrfull{') >= 0) :
        return True
    return False

# Format of acronyms, some examples
# \newacronym{NAS}{NAS}{Network Attached Storage}
# split_acronym_definition(l1)
#    {'parts': ['\newacronym', '{NAS}', '', '{NAS}', '', '{Network Attached Storage}'], 'option': ''}
#
# \newacronym[plural=NFs, firstplural=Network Functions (NFs)]{NF}{NF}{Network Function}
# split_acronym_definition(l2)
#    {'parts': ['\newacronym', '{NF}', '', '{NF}', '', '{Network Function}'], 'option': 'plural=NFs, firstplural=Network Functions (NFs)'}
#
# \newacronym[plural=NICs, firstplural=network interface cards (NICs)]{NIC}{NIC}{network interface card}
# split_acronym_definition(l3)
#    {'parts': ['\newacronym', '{NIC}', '', '{NIC}', '', '{network interface card}'], 'option': 'plural=NICs, firstplural=network interface cards (NICs)'}
#
# \newacronym{I2C}{I\textsuperscript{2}C}{Inter-Integrated Circuit}
# split_acronym_definition(l4)
#    {'parts': ['\newacronym', '{I2C}', '', '{I\textsuperscript{2}C}', '', '{Inter-Integrated Circuit}'], 'option': ''}

def split_acronym_definition(l):
    quoted_character=False
    level=0
    options=''
    options_start=False
    parts=[]
    #
    part=''
    #
    for i in range(0, len(l)):
        if l[i] == '\\':
            quoted_character=True
            part=part+'\\'
            continue
        if l[i] == '[' and not quoted_character:
            options_start=True
            continue
        if l[i] == ']' and not quoted_character:
            options_start=False
            continue
        if  options_start:
            options=options+l[i]
            quoted_character=False
            continue
        #
        if l[i] == '{' and not quoted_character:
            if level == 0:
                parts.append(part)
                part=''
            part=part+l[i]
            level=level + 1
            continue
        if l[i] == '}' and not quoted_character:
            part=part+l[i]
            level=level - 1
            if level == 0:
                parts.append(part)
                part=''
            continue
        part=part+l[i]
        quoted_character=False  # having added a character there is no more quoting
#
    return {'parts':  parts, 'option': options}

def get_acronyms(acronyms_filename):
    acronym_dict=dict()
    #
    newacronym_pattern='newacronym'
    starting_marker='{'
    trailing_marker='}'
    start_option_marker='['
    end_option_marker=']'
    #
    with open(acronyms_filename, 'r', encoding='utf-8') as input_FH:
        for line in input_FH:
            line=line.strip()   # remove leading and trailing white space
            comment_offset=line.find('%')
            if comment_offset >= 0: #  of a comment line, simply skip the line
                line=line[0:comment_offset]
            # \setabbreviationstyle[acronym]{long-short}
            comment_offset=line.find('\\setabbreviationstyle')
            if comment_offset >= 0: #  if lines contains a setabbreviationstyle, skip
                continue
            if len(line) == 0:
                continue
            s=split_acronym_definition(line)
            # print("line={0}, s={1}".format(line, s))
            parts=s.get('parts', None)
            option=s.get('option', None)
            if not parts:
                print("Error in parsing for acronym definition line: {}".format(line))
                continue
            label=None
            acronym=None
            phrase=None
            which_part=0
            for i, value in enumerate(parts):
                #if which_part == 0:
                if which_part == 0 and value.strip().endswith('newacronym'):
                    which_part=1
                    continue
                elif which_part == 1: #  get label
                    if len(value.strip()) == 0:
                        continue
                    label=value.strip()
                    if label.startswith(starting_marker) and label.endswith(trailing_marker):
                        label=label[1:-1]
                        which_part = 2
                    else:
                        print("Error in parsing for label in line: {}".format(line))
                        continue
                elif which_part == 2: # get acronym
                    if len(value.strip()) == 0:
                        continue
                    acronym=value.strip()
                    if acronym.startswith(starting_marker) and acronym.endswith(trailing_marker):
                        acronym=acronym[1:-1]
                        which_part = 3
                    else:
                        print("Error in parsing for acronym in line: {}".format(line))
                        continue
                elif which_part == 3: # get phrase
                    if len(value.strip()) == 0:
                        continue
                    phrase=value.strip()
                    if phrase.startswith(starting_marker) and phrase.endswith(trailing_marker):
                        phrase=phrase[1:-1]
                    else:
                        print("Error in parsing for phrase in line: {}".format(line))
                        continue
                else:
                    print("Error in parsing in line: {}".format(line))
                    continue
            acronym_dict[label]={'acronym': acronym, 'phrase': phrase, 'option': option}
            #
    return acronym_dict

def replace_first_gls(a, offset, acronym_dict):
    global spelled_out
    a_prefix=a[:offset]
    end_of_acronym=a.find('}', offset+5)
    if end_of_acronym < 0:
        print("could not find end of acronym label")
        return a
    label=a[offset+5:end_of_acronym]
    a_postfix=a[end_of_acronym+1:]
    ad=acronym_dict.get(label, None)
    if ad:
        phrase=ad.get('phrase', None)
        acronym=ad.get('acronym', None)
        already_spelled_out=spelled_out.get(label, None)
        if already_spelled_out:
            if acronym:
                a=a_prefix+acronym+a_postfix
            else:
                print("acronym missing for label={}".format(label))
        else:
            if phrase and acronym:
                full_phrase="{0} ({1})".format(phrase, acronym)
                a=a_prefix+full_phrase+a_postfix
                spelled_out[label]=True
            else:
                print("phrase or acronym are missing for label={}".format(label))
    else:
        print("Missing acronym for {}".format(label))
        return None
    #
    return a

def replace_first_glspl(a, offset, acronym_dict):
    global spelled_out
    a_prefix=a[:offset]
    end_of_acronym=a.find('}', offset+7)
    if end_of_acronym < 0:
        print("could not find end of acronym label")
        return a
    label=a[offset+7:end_of_acronym]
    a_postfix=a[end_of_acronym+1:]
    ad=acronym_dict.get(label, None)
    if ad:
        phrase=ad.get('phrase', None)
        acronym=ad.get('acronym', None)
        already_spelled_out=spelled_out.get(label, None)
        if already_spelled_out:
            if acronym:
                a=a_prefix+acronym+a_postfix
            else:
                print("acronym missing for label={}".format(label))
        else:
            firstplural=ad.get('firstplural', None)
            longplural=ad.get('longplural', None)
            if firstplural:
                full_phrase="{0} ({1})".format(longplural, acronym)
                a=a_prefix+firstplural+a_postfix
                spelled_out[label]=True
            elif longplural:
                full_phrase="{0} ({1})".format(longplural, acronym)
                a=a_prefix+longplural+a_postfix
                spelled_out[label]=True
            elif phrase and acronym:
                full_phrase="{0} ({1})".format(phrase, acronym)
                a=a_prefix+full_phrase+'s'+a_postfix
                spelled_out[label]=True
            else:
                print("phrase or acronym are missing for label={}".format(label))
    else:
        print("Missing acronym for {}".format(label))
        return None
    #
    return a

def spellout_acronyms_in_abstract(acronym_dict, a):
    # look for use of acronyms (i.e., a reference to an acronym's label) and spell out as needed
    # keep list of labels of acronyms found and spellout out
    global spelled_out
    spelled_out=dict()
    # Note that because we initialize it for each call of this routine, the acronyms will be spellout appropriately in each abstract
    #
    # first handle all cases where the full version is to be included
    acrfull_template='\\acrfull{'
    acrfull_offset=a.find(acrfull_template)
    while acrfull_offset >= 0:
        a_prefix=a[:acrfull_offset]
        end_of_acronym=a.find('}', acrfull_offset+len(acrfull_template))
        if end_of_acronym < 0:
            print("could not find end of acronym label")
            break
        label=a[acrfull_offset+len(acrfull_template):end_of_acronym]
        a_postfix=a[end_of_acronym+1:]
        ad=acronym_dict.get(label, None)
        if ad:
            phrase=ad.get('phrase', None)
            acronym=ad.get('acronym', None)
            if phrase and acronym:
                full_phrase="{0} ({1})".format(phrase, acronym)
                a=a_prefix+full_phrase+a_postfix
                spelled_out[label]=True
            else:
                print("phrase or acronym are missing for label={}".format(label))
            #
            acrfull_offset=a.find(acrfull_template, end_of_acronym)
    #
    # second handle all cases where the long version is to be included
    acrlong_template='\\acrlong{'
    acrlong_offset=a.find(acrlong_template)
    while acrlong_offset >= 0:
        a_prefix=a[:acrlong_offset]
        end_of_acronym=a.find('}', acrlong_offset+len(acrlong_template))
        if end_of_acronym < 0:
            print("could not find end of acronym label")
            break
        label=a[acrlong_offset+len(acrlong_template):end_of_acronym]
        a_postfix=a[end_of_acronym+1:]
        ad=acronym_dict.get(label, None)
        if ad:
            phrase=ad.get('phrase', None)
            if phrase:
                a=a_prefix+phrase+a_postfix
            else:
                print("phrase or acronym are missing for label={}".format(label))
            #
            acrlong_offset=a.find(acrlong_template, end_of_acronym)
    #
    #
    # third handle all cases where the short version is to be included
    acrshort_template='\\acrshort{'
    acrshort_offset=a.find(acrshort_template)
    while acrshort_offset >= 0:
        a_prefix=a[:acrshort_offset]
        end_of_acronym=a.find('}', acrshort_offset+len(acrshort_template))
        if end_of_acronym < 0:
            print("could not find end of acronym label")
            break
        label=a[acrshort_offset+len(acrshort_template):end_of_acronym]
        a_postfix=a[end_of_acronym+1:]
        ad=acronym_dict.get(label, None)
        if ad:
            acronym=ad.get('acronym', None)
            if acronym:
                a=a_prefix+acronym+a_postfix
            else:
                print("phrase or acronym are missing for label={}".format(label))
            #
            acrshort_offset=a.find(acrshort_template, end_of_acronym)

    # for the glossaries-extra versions
    # first handle all cases where the full version is to be included
    acrfull_template='\\glsxtrfull{'
    acrfull_offset=a.find(acrfull_template)
    while acrfull_offset >= 0:
        a_prefix=a[:acrfull_offset]
        end_of_acronym=a.find('}', acrfull_offset+len(acrfull_template))
        if end_of_acronym < 0:
            print("could not find end of acronym label")
            break
        label=a[acrfull_offset+len(acrfull_template):end_of_acronym]
        a_postfix=a[end_of_acronym+1:]
        ad=acronym_dict.get(label, None)
        if ad:
            phrase=ad.get('phrase', None)
            acronym=ad.get('acronym', None)
            if phrase and acronym:
                full_phrase="{0} ({1})".format(phrase, acronym)
                a=a_prefix+full_phrase+a_postfix
                spelled_out[label]=True
            else:
                print("phrase or acronym are missing for label={}".format(label))
            #
            acrfull_offset=a.find(acrfull_template, end_of_acronym)
    #
    # second handle all cases where the long version is to be included
    acrlong_template='\\glsxtrlong{'
    acrlong_offset=a.find(acrlong_template)
    while acrlong_offset >= 0:
        a_prefix=a[:acrlong_offset]
        end_of_acronym=a.find('}', acrlong_offset+len(acrlong_template))
        if end_of_acronym < 0:
            print("could not find end of acronym label")
            break
        label=a[acrlong_offset+len(acrlong_template):end_of_acronym]
        a_postfix=a[end_of_acronym+1:]
        ad=acronym_dict.get(label, None)
        if ad:
            phrase=ad.get('phrase', None)
            if phrase:
                a=a_prefix+phrase+a_postfix
            else:
                print("phrase or acronym are missing for label={}".format(label))
            #
            acrlong_offset=a.find(acrlong_template, end_of_acronym)
    #
    #
    # third handle all cases where the short version is to be included
    acrshort_template='\\glsxtrshort{'
    acrshort_offset=a.find(acrshort_template)
    while acrshort_offset >= 0:
        a_prefix=a[:acrshort_offset]
        end_of_acronym=a.find('}', acrshort_offset+len(acrshort_template))
        if end_of_acronym < 0:
            print("could not find end of acronym label")
            break
        label=a[acrshort_offset+len(acrshort_template):end_of_acronym]
        a_postfix=a[end_of_acronym+1:]
        ad=acronym_dict.get(label, None)
        if ad:
            acronym=ad.get('acronym', None)
            if acronym:
                a=a_prefix+acronym+a_postfix
            else:
                print("phrase or acronym are missing for label={}".format(label))
            #
            acrshort_offset=a.find(acrshort_template, end_of_acronym)

    #
    # handle cases where the acronym is conditionally spelled out and introduced or only the acronym is inserted
    # gls_offset=a.find('\\gls{')
    # lspl_offset=a.find('\\glspl{')
    # ggls_offset=a.find('\\Gls{')
    # gglspl_offset=a.find('\\Glspl{')
    # 
    s1=re.search('\\\\gls\{', a, re.IGNORECASE)
    s2=re.search('\\\\glspl\{', a, re.IGNORECASE)
    # find the earliest one
    while s1 or s2:
        if s1 and s2:
            gls_offset=s1.span()[0]
            glspl_offset=s2.span()[0]
            if  gls_offset < glspl_offset:
                # gls case occurs first
                a1=replace_first_gls(a, gls_offset, acronym_dict)
                if a1:
                    a=a1
                else:           # if the replacement failed, bail out
                    return a
            else:
                a=replace_first_glspl(a, glspl_offset, acronym_dict)
        elif s1 and not s2:
            gls_offset=s1.span()[0]
            a1=replace_first_gls(a, gls_offset, acronym_dict)
            if a1:
                a=a1
            else:
                return a
        else: # case of no s1 and s2:
            glspl_offset=s2.span()[0]
            a1=replace_first_glspl(a, glspl_offset, acronym_dict)
            if a1:
                a=a1
            else:
                return a
        s1=re.search('\\\\gls\{', a, re.IGNORECASE)
        s2=re.search('\\\\glspl\{', a, re.IGNORECASE)
    return a

# ligature. LaTeX commonly does it for ff, fi, fl, ffi, ffl, ...
ligrature_table= {'\ufb00': 'ff', # 'ﬀ'
                  '\ufb03': 'f‌f‌i', # 'ﬃ'
                  '\ufb04': 'ffl', # 'ﬄ'
                  '\ufb01': 'fi', # 'ﬁ'
                  '\ufb02': 'fl', # 'ﬂ'
                  '\ua732': 'AA', # 'Ꜳ'
                  '\ua733': 'aa', # 'ꜳ'
                  '\ua733': 'aa', # 'ꜳ'
                  '\u00c6': 'AE', # 'Æ'
                  '\u00e6': 'ae', # 'æ'
                  '\uab31': 'aə', # 'ꬱ'
                  '\ua734': 'AO', # 'Ꜵ'
                  '\ua735': 'ao', # 'ꜵ'
                  '\ua736': 'AU', # 'Ꜷ'
                  '\ua737': 'au', # 'ꜷ'
                  '\ua738': 'AV', # 'Ꜹ'
                  '\ua739': 'av', # 'ꜹ'
                  '\ua73a': 'AV', # 'Ꜻ'  - note the bar
                  '\ua73b': 'av', # 'ꜻ'  - note the bar
                  '\ua73c': 'AY', # 'Ꜽ'
                  '\ua76a': 'ET', # 'Ꝫ'
                  '\ua76b': 'et', # 'ꝫ'
                  '\uab41': 'əø', # 'ꭁ'
                  '\u01F6': 'Hv', # 'Ƕ'
                  '\u0195': 'hu', # 'ƕ'
                  '\u2114': 'lb', # '℔'
                  '\u1efa': 'IL', # 'Ỻ'
                  '\u0152': 'OE', # 'Œ'
                  '\u0153': 'oe', # 'œ'
                  '\ua74e': 'OO', # 'Ꝏ'
                  '\ua74f': 'oo', # 'ꝏ'
                  '\uab62': 'ɔe', # 'ꭢ'
                  '\u1e9e': 'fs', # 'ẞ'
                  '\u00df': 'fz', # 'ß'
                  '\ufb06': 'st', # 'ﬆ'
                  '\ufb05': 'ſt', # 'ﬅ'  -- long ST
                  '\ua728': 'Tz', # 'Ꜩ'
                  '\ua729': 'tz', # 'ꜩ'
                  '\u1d6b': 'ue', # 'ᵫ'
                  '\uab63': 'uo', # 'ꭣ'
                  #'\u0057': 'UU', # 'W'
                  #'\u0077': 'uu', # 'w'
                  '\ua760': 'VY', # 'Ꝡ'
                  '\ua761': 'vy', # 'ꝡ'
                  # 
                  '\u0238': 'db', # 'ȸ'
                  '\u02a3': 'dz', # 'ʣ'
                  '\u1b66': 'dʐ', # 'ꭦ'
                  '\u02a5': 'dʑ', # 'ʥ'
                  '\u02a4': 'dʒ', # 'ʤ'
                  '\u02a9': 'fŋ', # 'ʩ'
                  '\u02aa': 'ls', # 'ʪ'
                  '\u02ab': 'lz', # 'ʫ'
                  '\u026e': 'lʒ', # 'ɮ'
                  '\u0239': 'qp', # 'ȹ'
                  '\u02a8': 'tɕ', # 'ʨ'
                  '\u02a6': 'ts', # 'ʦ'
                  '\uab67': 'tʂ', # 'ꭧ'
                  '\u02a7': 'tʃ', # 'ʧ'
                  '\uab50': 'ui', # 'ꭐ'
                  '\uab51': 'ui', # 'ꭑ' -- turned ui
                  '\u026f': 'uu', # 'ɯ'
                  # digraphs with single code points
                  '\u01f1': 'DZ', # 'Ǳ'
                  '\u01f2': 'Dz', # 'ǲ'
                  '\u01f3': 'dz', # 'ǳ'
                  '\u01c4': 'DŽ', # 'Ǆ'
                  '\u01c5': 'Dž', # 'ǅ'
                  '\u01c6': 'dž', # 'ǆ'
                  '\u0132': 'IJ', # 'Ĳ'
                  '\u0133': 'ij', # 'ĳ'
                  '\u01c7': 'LJ', # 'Ǉ'
                  '\u01c8': 'Lj', # 'ǈ'
                  '\u01c9': 'lj', # 'ǉ'
                  '\u01ca': 'NJ', # 'Ǌ'
                  '\u01cb': 'Nj', # 'ǋ'
                  '\u01cc': 'nj', # 'ǌ'
                  '\u1d7a': 'th', # 'ᵺ'
                  }

def replace_ligature(s):
    # check for ligratures and replace them with separate characters
    if not s:
        return s
    
    for l in ligrature_table:
        if s.find(l) >= 0:
            print("found ligrature {0} replacing with {1}".format(l, ligrature_table[l]))  
            s=s.replace(l, ligrature_table[l])
    #
    return s


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing

    argp = argparse.ArgumentParser(description="extract_pseudo_JSON-from_PDF.py: Extract the pseudo JSON from the end of the thesis PDF file")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-p', '--pdf',
                      type=str,
                      default="test.pdf",
                      help="read PDF file"
                      )

    argp.add_argument('-j', '--json',
                      type=str,
                      default="calendar_event.json",
                      help="JSON file for extracted calendar event"
                      )

    argp.add_argument('-a', '--acronyms',
                      type=str,
                      default="acronyms.tex",
                      help="acronyms filename"
                      )

    argp.add_argument('-l', '--ligatures',
                      default=False,
                      action="store_true",
                      help="leave ligatures rahter than replace them"
                      )



    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    filename=args["pdf"]
    if Verbose_Flag:
        print("filename={}".format(filename))

    #output_string = StringIO()
    output_string = BytesIO()
    with open(filename, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        #device = HTMLConverter(rsrcmgr, output_string, laparams=LAParams(), layoutmode='normal', codec='utf-8')

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

        text=output_string.getvalue().decode('UTF-8')
        if Verbose_Flag:
            print("text: {}".format(text))

    # define the maker string
    quad__euro_marker='€€€€'

    # look for the new start of the For DiVA information
    diva_start=text.find("{0} For DIVA {0}".format(quad__euro_marker))
    if diva_start < 0:
        # if not found, then try the older For DIVA string
        diva_start=text.find("For DIVA")

    if Verbose_Flag:
        print("For DIVA found at diva_start={}".format(diva_start))
    if diva_start >= 0:
        diva_data=text[:]
        diva_data=diva_data[diva_start:]
        diva_start=diva_data.find("{")
        if diva_start >= 0:
            diva_data=diva_data[diva_start:]
            end_block=diva_data.find('”Number of lang instances”:') # note these are right double quote marks
            if end_block < 0:            
                end_block=diva_data.find('"Number of lang instances":') # note these are straight double quote marks
            if end_block > 0:
                end_block=diva_data.find(',', end_block)
                if end_block > 0:
                    dict_string=diva_data[:]
                    dict_string=dict_string[:end_block]+'}'

                    dict_string=dict_string.replace('', '') #  remove any new page characters
                    dict_string=dict_string.replace('”', '"')
                    dict_string=dict_string.replace('\n\n', '\n')
                    dict_string=dict_string.replace(' \n', '')
                    dict_string=dict_string.replace(',}', '}')

                    dict_string=dict_string.replace('”', '"')
                    #dict_string=dict_string.replace('&quot;', '"')
                    #dict_string=dict_string.replace('<br>', '\n')
                    #dict_string=dict_string.replace('<br>"', '\n"')
                    #dict_string=dict_string.replace('<br>}', '\n}')
                    dict_string=dict_string.replace(',\n\n}', '\n}')
                    dict_string=dict_string.replace(',\n}', '\n}')

                    # fix an error in the early template
                    if dict_string.find(',Äddress": ') > 0:
                        print("fix an error in the early template")
                        dict_string=dict_string.replace(',Äddress": ', ',"Address": "')
                        dict_string=dict_string.replace('\"Lindstedtsvägen', 'Lindstedtsvägen')
                        dict_string=dict_string.replace('¨Lindstedtsvägen', 'Lindstedtsvägen')
                        dict_string=dict_string.replace('¨Isafjordsgatan', 'Isafjordsgatan')



                    if not args['ligatures']:
                        dict_string=replace_ligature(dict_string)
                        print("looking for and replacing ligatures")

                    if Verbose_Flag:
                        print("dict_string={}".format(dict_string))
                    print("dict_string={}".format(dict_string))
                    d=json.loads(dict_string)
                    if Verbose_Flag:
                        print("d={}".format(d))

                    abs_keywords=diva_data[(end_block+1):]
                    abs_keywords=abs_keywords.replace('', '')
                    if Verbose_Flag:
                        print("abs_keywords={}".format(abs_keywords))
                    number_of_quad_euros=abs_keywords.count(quad__euro_marker)
                    if Verbose_Flag:
                        print("number_of_quad_euros={}".format(number_of_quad_euros))
                    abstracts=dict()
                    keywords=dict()
                    if (number_of_quad_euros % 2) == 1:
                        print("Odd number of markers")

                    save_abs_keywords=abs_keywords[:]

                    number_of_pairs_of_markers=int(number_of_quad_euros/2)
                    for i in range(0, number_of_pairs_of_markers):
                        abstract_key_prefix='”Abstract['
                        key_offset=abs_keywords.find(abstract_key_prefix)
                        if key_offset > 0:
                            # found a key for an abstract
                            # get language code
                            lang_code_start=key_offset+len(abstract_key_prefix)
                            lang_code=abs_keywords[lang_code_start:lang_code_start+3]
                            quad__euro_marker_start=abs_keywords.find(quad__euro_marker, lang_code_start)
                            if quad__euro_marker_start >= 0:
                                quad__euro_marker_end=abs_keywords.find(quad__euro_marker, quad__euro_marker_start + 5)
                                abstracts[lang_code]=abs_keywords[quad__euro_marker_start+5:quad__euro_marker_end]
                                #br_offset=abstracts[lang_code].find('<br>')
                                #if br_offset >= 0:
                                #    abstracts[lang_code]=abstracts[lang_code][br_offset+4:]

                                abs_keywords=abs_keywords[quad__euro_marker_end+1:]
                        

                    abs_keywords=save_abs_keywords[:]

                    for i in range(0, number_of_pairs_of_markers):
                        abstract_key_prefix='”Keywords['
                        key_offset=abs_keywords.find(abstract_key_prefix)
                        if key_offset > 0:
                            # found a key for an abstract
                            # get language code
                            lang_code_start=key_offset+len(abstract_key_prefix)
                            lang_code=abs_keywords[lang_code_start:lang_code_start+3]
                            quad__euro_marker_start=abs_keywords.find(quad__euro_marker, lang_code_start)
                            if quad__euro_marker_start > 0:
                                quad__euro_marker_end=abs_keywords.find(quad__euro_marker, quad__euro_marker_start + 5)
                                keywords[lang_code]=abs_keywords[quad__euro_marker_start+5:quad__euro_marker_end]
                                keywords[lang_code]=keywords[lang_code].replace('\n', '') # remove newlines from keywords
                                keywords[lang_code]=keywords[lang_code].strip() # remove starting end ending white space
                                br_offset=keywords[lang_code].find('<br>')
                                if br_offset >= 0:
                                    keywords[lang_code]=keywords[lang_code][br_offset+4:]
                                abs_keywords=abs_keywords[quad__euro_marker_end+1:]
                        

                    for a in abstracts:
                        print("a={0}, abstract={1}".format(a, abstracts[a]))
                        abstracts[a]=clean_up_abstract(abstracts[a])

                    any_acronyms_in_abstracts=False
                    for a in abstracts:
                        acronyms_present=check_for_acronyms(abstracts[a])
                        if acronyms_present:
                            any_acronyms_in_abstracts=True

                    if any_acronyms_in_abstracts:
                        acronyms_filename=args["acronyms"]
                        print("Acronyms found, getting acronyms from {}".format(acronyms_filename))
                        acronym_dict=get_acronyms(acronyms_filename)
                        if len(acronym_dict) == 0:
                            print("no acronyms found in {}".format(acronyms_filename))
                        else:
                            # entries of the form: acronym_dict[label]={'acronym': acronym, 'phrase': phrase}
                            for a in abstracts:
                                abstracts[a]=spellout_acronyms_in_abstract(acronym_dict, abstracts[a])


                    print("abstracts={}".format(abstracts))
                    print("keywords={}".format(keywords))

                    d['abstracts']=abstracts
                    d['keywords']=keywords
                    output_filename=args["json"]
                    if Verbose_Flag:
                        print("output_filename={}".format(output_filename))
                    with open(output_filename, 'w', encoding='utf-8') as output_FH:
                        j_as_string = json.dumps(d, ensure_ascii=False)
                        print(j_as_string, file=output_FH)

            else:
                print('No "Number of lang instances" found')
                dict_string=diva_data[:]
                print("initial dict_string={}".format(dict_string))

                dict_string=dict_string.replace('', '') #  remove any new page characters

                dict_string=dict_string.replace('”', '"')
                dict_string=dict_string.replace('\n\n', '\n')
                dict_string=dict_string.replace(' \n', '')
                dict_string=dict_string.replace(',}', '}')

                #dict_string=dict_string.replace('&quot;', '"')
                #dict_string=dict_string.replace('<br>', '\n')
                #dict_string=dict_string.replace('<br>"', '\n"')
                #dict_string=dict_string.replace('<br>}', '\n}')
                dict_string=dict_string.replace(',\n\n}', '\n}')
                dict_string=dict_string.replace(',\n}', '\n}')
                # fix an error in the early template
                if dict_string.find(',Äddress": ') > 0:
                    print("fix an error in the early template")
                    dict_string=dict_string.replace(',Äddress": ', ',"Address": "')
                    dict_string=dict_string.replace('\"Lindstedtsvägen', 'Lindstedtsvägen')
                    dict_string=dict_string.replace('¨Lindstedtsvägen', 'Lindstedtsvägen')
                    dict_string=dict_string.replace('¨Isafjordsgatan', 'Isafjordsgatan')

                if not args['ligatures']:
                    dict_string=replace_ligature(dict_string)
                    print("looking for and replacing ligatures")

                print("dict_string={}".format(dict_string))
                d=json.loads(dict_string)
                print("d={}".format(d))

                output_filename=args["json"]
                if Verbose_Flag:
                    print("output_filename={}".format(output_filename))
                with open(output_filename, 'w', encoding='utf-8') as output_FH:
                    j_as_string = json.dumps(d, ensure_ascii=False)
                    print(j_as_string, file=output_FH)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

