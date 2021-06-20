#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_cover.py [-c course_id] --json file.json [--cycle 1|2] [--credits 7.5|15.0|30.0|50.0] [--exam 1|2|3|4|5|6|7|8 or or the name of the exam] [--area area_of_degree] [--area2 area_of_second_degree] [--trita trita_string] [--school ABE|CBH|EECS|ITM|SCI] [--file thesis_file.pdf] [--diva 1|2...]
#
# Purpose: The program creates a thesis cover using the information from the arguments and a JSON file.
# The JSON file can be produced by extract_pseudo_JSON-from_PDF.py
#
# Output: outputs the cover in a file: cover.pdf
#	and splits the cover.pdf into two pages: cover_pages-1 and cover_pages-2
#
# Example:
#  enter data from a JSON file
# ./JSON_to_cover.py -c 11  --json event.json
# ./JSON_to_cover.py -c 11 --config config-test.json  --json event.json
#
# ./JSON_to_cover.py -c 11  --json event.json --testing --exam 4
#
# For a file without For DIVA pages:
# ./JSON_to_cover.py  --json event.json --testing --exam 4 --file oscar.pdf
#
# For a file with two(2) For DIVA pages:
# ./JSON_to_cover.py  --json event.json --testing --exam 4 --file oscar.pdf --diva 2
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-06-04 G. Q. Maguire Jr.
# Base on earlier JSON_to_calendar.py
#
import re
import sys
import subprocess

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

programcodes={
    'ARKIT': {'cycle': 2,
	      'swe': 'Arkitektutbildning',
              'eng': 'Degree Programme in Architecture'},
    
    'CBIOT': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i bioteknik',
              'eng': 'Degree Programme in Biotechnology'},
    
    'CDATE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i datateknik',
              'eng': 'Degree Programme in Computer Science and Engineering'},
    
    'CDEPR': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i design och produktframtagning',
              'eng': 'Degree Programme in Design and Product Realisation'},
    
    'CELTE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i elektroteknik',
              'eng': 'Degree Programme in Electrical Engineering'},
    
    'CENMI': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i energi och miljö',
              'eng': 'Degree Programme in Energy and Environment'},
    
    'CFATE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i farkostteknik',
              'eng': 'Degree Programme in Vehicle Engineering'},
    
    'CINEK': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i industriell ekonomi',
              'eng': 'Degree Programme in Industrial Engineering and Management'},
    
    'CINTE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i informationsteknik',
              'eng': 'Degree Programme in Information and Communication Technology'},
    
    'CITEH': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i industriell teknik och hållbarhet',
              'eng': 'Degree Programme in Industrial Technology and Sustainability'},
    
    'CLGYM': {'cycle': 2,
	      'swe': 'Civilingenjör och lärare',
              'eng': 'Master of Science in Engineering and in Education'},
    'CMAST': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i maskinteknik',
              'eng': 'Degree Programme in Mechanical Engineering'},
    'CMATD': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i materialdesign',
              'eng': 'Degree Programme in Materials Design and Engineering'},
    'CMEDT': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i medicinsk teknik',
              'eng': 'Degree Programme in Medical Engineering'},
    'CMETE': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i medieteknik',
              'eng': 'Degree Programme in Media Technology'},
    'COPEN': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning öppen ingång',
              'eng': 'Degree Programme Open Entrance'},
    'CSAMH': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i samhällsbyggnad',
              'eng': 'Degree Programme in Civil Engineering and Urban Management'},
    'CTFYS': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i teknisk fysik',
              'eng': 'Degree Programme in Engineering Physics'},
    'CTKEM': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i teknisk kemi',
              'eng': 'Degree Programme in Engineering Chemistry'},
    'CTMAT': {'cycle': 2,
	      'swe': 'Civilingenjörsutbildning i teknisk matematik',
              'eng': 'Degree Programme in Engineering Mathematics'},
    'KPUFU': {'cycle': 2,
	      'swe': 'Kompletterande pedagogisk utbildning för ämneslärarexamen i matematik, naturvetenskap och teknik för forskarutbildade',
              'eng': 'Bridging Teacher Education Programme in Mathematics, Science and Technology for Graduates with a Third Cycle Degree'},
    'KPULU': {'cycle': 2,
	      'swe': 'Kompletterande pedagogisk utbildning',
              'eng': 'Bridging Teacher Education Programme'},
    'KUAUT': {'cycle': 2,
	      'swe': 'Kompletterande utbildning för arkitekter med avslutad utländsk utbildning',
              'eng': 'Bridging programme for architects with foreign qualifications'},
    'KUIUT': {'cycle': 2,
	      'swe': 'Kompletterande utbildning för ingenjörer med avslutad utländsk utbildning',
              'eng': 'Bridging programme for engineers with foreign qualifications'},
    'LÄRGR': {'cycle': 2,
	      'swe': 'Ämneslärarutbildning med inriktning mot teknik, årskurs 7-9',
              'eng': 'Subject Teacher Education in Technology, Secondary Education'},
    'TAEEM': {'cycle': 2,
	      'swe': 'Masterprogram, flyg- och rymdteknik',
              'eng': "Master's Programme, Aerospace Engineering, 120 credits"},
    'TAETM': {'cycle': 2,
	      'swe': 'Masterprogram, aeroelasticitet i turbomaskiner',
              'eng': "Master's Programme, Turbomachinery Aeromechanic University Training, 120 credits"},
    'TARKM': {'cycle': 2,
	      'swe': 'Masterprogram, arkitektur',
              'eng': "Master's Programme, Architecture, 120 credits"},
    'TBASA': {'cycle': 0,
	      'swe': 'Tekniskt basår, KTH Flemingsberg',
              'eng': 'Technical Preparatory Year'},
    'TBASD': {'cycle': 0,
	      'swe': 'Tekniskt basår, KTH Campus',
              'eng': 'Technical Preparatory Year'},
    'TBASE': {'cycle': 0,
	      'swe': 'Tekniskt basår, KTH Södertälje',
              'eng': 'Technical Preparatory Year'},
    'TBTMD': {'cycle': 0,
	      'swe': 'Tekniskt basår, termin 2, KTH Campus',
              'eng': 'Technical Preparatory Semester'},
    'TBTMH': {'cycle': 0,
	      'swe': 'Tekniskt basår, termin 2, KTH Flemingsberg',
              'eng': 'Technical Preparatory Semester'},
    'TBTMS': {'cycle': 0,
	      'swe': 'Tekniskt basår, termin 2, KTH Södertälje',
              'eng': 'Technical Preparatory Semester'},
    'TBYPH': {'cycle': 1,
	      'swe': 'Högskoleutbildning i byggproduktion',
              'eng': 'Degree Progr. in Construction Management'},
    'TCAEM': {'cycle': 2,
	      'swe': 'Masterprogram, husbyggnads- och anläggningsteknik',
              'eng': "Master's Programme, Civil and Architectural Engineering, 120 credits"},
    'TCOMK': {'cycle': 1,
	      'swe': 'Kandidatprogram, informations- och kommunikationsteknik',
              'eng': "Bachelor's Programme in Information and Communication Technology"},
    'TCOMM': {'cycle': 2,
	      'swe': 'Masterprogram, kommunikationssystem',
              'eng': "Master's Programme, Communication Systems, 120 credits"},
    'TCSCM': {'cycle': 2,
	      'swe': 'Masterprogram, datalogi',
              'eng': "Master's Programme, Computer Science, 120 credits"},
    'TDEBM': {'cycle': 2,
	      'swe': 'Magisterprogram, design och byggande i staden',
              'eng': "Master's Programme, Urban Development and Design, 60 credits"},
    'TDSEM': {'cycle': 2,
	      'swe': 'Masterprogram, decentraliserade smarta energisystem',
              'eng': "Master's Programme, Decentralized Smart Energy Systems, 120 credits"},
    'TDTNM': {'cycle': 2,
	      'swe': 'Masterprogram, datorsimuleringar inom teknik och naturvetenskap',
              'eng': "Master's Programme, Computer Simulations for Science and Engineering, 120 credits"},
    'TEBSM': {'cycle': 2,
	      'swe': 'Masterprogram, inbyggda system',
              'eng': "Master's Programme, Embedded Systems, 120 credits"},
    'TEEEM': {'cycle': 2,
	      'swe': 'Masterprogram, teknik och ledning för energi- och miljösystem',
              'eng': "Master's Programme, Management and Engineering of Environment and Energy, 120 credits"},
    'TEEGM': {'cycle': 2,
	      'swe': 'Masterprogram, miljöteknik',
              'eng': "Master's Programme, Environmental Engineering, 120 credits"},
    'TEFRM': {'cycle': 2,
	      'swe': 'Masterprogram, elektromagnetism, fusion och rymdteknik',
              'eng': "Master's Programme, Electromagnetics, Fusion and Space Engineering, 120 credits"},
    'TEILM': {'cycle': 2,
	      'swe': 'Magisterprogram, entreprenörskap och innovationsledning',
              'eng': "Master's Programme, Entrepreneurship and Innovation Management, 60 credits"},
    'TEINM': {'cycle': 2,
	      'swe': 'Masterprogram, innovations- och tillväxtekonomi',
              'eng': "Master's Programme, Economics of Innovation and Growth, 120 credits"},
    'TELPM': {'cycle': 2,
	      'swe': 'Masterprogram, elkraftteknik',
              'eng': "Master's Programme, Electric Power Engineering, 120 credits"},
    'TFAFK': {'cycle': 1,
	      'swe': 'Kandidatprogram, Fastighetsutveckling med fastighetsförmedling',
              'eng': "Bachelor's Programme in Property Development and Agency"},
    'TFAHM': {'cycle': 2,
	      'swe': 'Magisterprogram, fastigheter',
              'eng': "Master's Programme, Real Estate"},
    'TFOBM': {'cycle': 2,
	      'swe': 'Masterprogram, fastigheter och byggande',
              'eng': "Master's Programme, Real Estate and Construction Management, 120 credits"},
    'TFOFK': {'cycle': 1,
	      'swe': 'Kandidatprogram, fastighet och finans',
              'eng': "Bachelor's Programme in Real Estate and Finance"},
    'TFORM': {'cycle': 2,
	      'swe': 'Masterprogram, fordonsteknik',
              'eng': "Master's Programme, Vehicle Engineering, 120 credits"},
    'THSSM': {'cycle': 2,
	      'swe': 'Masterprogram, hållbar samhällsplanering och stadsutformning',
              'eng': "Master's Programme, Sustainable Urban Planning and Design, 120 credits"},
    'TIBYH': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i byggteknik och design',
              'eng': "Degree Programme in Constructional Engineering and Design"},
    'TIDAA': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i datateknik, Flemingsberg',
              'eng': "Degree Programme in Computer Engineering"},
    'TIDAB': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i datateknik, Kista',
              'eng': "Degree Programme in Computer Engineering"},
    'TIDTM': {'cycle': 2,
	      'swe': 'Masterprogram, idrottsteknologi',
              'eng': "Master's Programme, Sports Technology"},
    'TIEDB': {'cycle': 2,
	      'swe': 'Högskoleingenjörsutbildning i elektronik och datorteknik',
              'eng': "Degree Programme in Electronics and Computer Engineering"},
    'TIEEM': {'cycle': 2,
	      'swe': 'Masterprogram, innovativ uthållig energiteknik',
              'eng': "Master's Programme, Innovative Sustainable Energy Engineering, 120 credits"},
    'TIELA': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i elektroteknik, Flemingsberg',
              'eng': "Degree Programme in Electrical Engineering"},
    'TIEMM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell ekonomi',
              'eng': "Master's Programme, Industrial Engineering and Management, 120 credits"},
    'TIETM': {'cycle': 2,
	      'swe': 'Masterprogram, innovativ energiteknik',
              'eng': "Master's Programme, Energy Innovation, 120 credits"},
    'TIHLM': {'cycle': 2,
	      'swe': 'Masterprogram, innovativ teknik för en hälsosam livsmiljö',
              'eng': "Master's Programme, Innovative Technology for Healthy Living"},
    'TIIPS': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i industriell teknik och produktionsunderhåll',
              'eng': "Degree Programme in Industrial Technology and Production Maintenance"},
    'TIKED': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i kemiteknik',
              'eng': "Degree Programme in Chemical Engineering"},
    'TIMAS': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i maskinteknik, Södertälje',
              'eng': "Degree Programme in Mechanical Engineering"},
    'TIMBM': {'cycle': 2,
	      'swe': 'Masterprogram, Industriell och miljöinriktad bioteknologi',
              'eng': "Master's Programme, Industrial and Environmental Biotechnology, 120 credits"},
    'TIMEL': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i medicinsk teknik',
              'eng': "Degree Programme in Medical Technology"},
    'TIMTM': {'cycle': 2,
	      'swe': 'Masterprogram, interaktiv medieteknik',
              'eng': "Master's Programme, Interactive Media Technology, 120 credits"},
    'TINEM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell ekonomi',
              'eng': "Master's Programme, Industrial Management, 120 credits"},
    'TINNM': {'cycle': 2,
	      'swe': 'Masterprogram, information och nätverksteknologi',
              'eng': "Master's Programme, Information and Network Engineering, 120 credits"},
    'TIPDM': {'cycle': 2,
	      'swe': 'Masterprogram, integrerad produktdesign',
              'eng': "Master's Programme, Integrated Product Design, 120 credits"},
    'TIPUM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell produktutveckling',
              'eng': "Master's Programme, Engineering Design, 120 credits"},
    'TITEH': {'cycle': 1,
	      'swe': 'Högskoleingenjörsutbildning i teknik och ekonomi',
              'eng': "Degree Programme in Engineering and Economics"},
    'TITHM': {'cycle': 2,
	      'swe': 'Masterprogram, hållbar produktionsutveckling',
              'eng': "Master's Programme, Sustainable Production Development, 120 credits"},
    'TIVNM': {'cycle': 2,
	      'swe': 'Masterprogram, ICT Innovation',
              'eng': "Master's Programme, ICT Innovation, 120 credits"},
    'TJVTM': {'cycle': 2,
	      'swe': 'Masterprogram, järnvägsteknik',
              'eng': "Master's Programme, Railway Engineering, 120 credits"},
    'TKEMM': {'cycle': 2,
	      'swe': 'Masterprogram, kemiteknik för energi och miljö',
              'eng': "Master's Programme, Chemical Engineering for Energy and Environment, 120 credits"},
    'TLODM': {'cycle': 2,
	      'swe': 'Magisterprogram, ljusdesign',
              'eng': "Master's Programme,  Architectural Lighting Design, 60 credits"},
    'TMAIM': {'cycle': 2,
	      'swe': 'Masterprogram, maskininlärning',
              'eng': "Master's Programme, Machine Learning, 120 credits"},
    'TMAKM': {'cycle': 2,
	      'swe': 'Masterprogram, matematik',
              'eng': "Master's Programme, Mathematics, 120 credits"},
    'TMBIM': {'cycle': 2,
	      'swe': 'Masterprogram, medicinsk bioteknologi',
              'eng': "Master's Programme, Medical Biotechnology, 120 credits"},
    'TMEGM': {'cycle': 2,
	      'swe': 'Masterprogram, marinteknik',
              'eng': "Master's Programme, Maritime Engineering, 120 credits"},
    'TMESM': {'cycle': 2,
	      'swe': 'Masterprogram, miljövänliga energisystem',
              'eng': "Master's Programme, Environomical Pathways for Sustainable Energy Systems, 120 credits"},
    'TMHIM': {'cycle': 2,
	      'swe': 'Masterprogram, miljöteknik och hållbar infrastruktur',
              'eng': "Master's Programme, Environmental Engineering and Sustainable Infrastructure, 120 credits"},
    'TMLEM': {'cycle': 2,
	      'swe': 'Masterprogram, medicinsk teknik',
              'eng': "Master's Programme, Medical Engineering, 120 credits"},
    'TMMMM': {'cycle': 2,
	      'swe': 'Masterprogram, makromolekylära material',
              'eng': "Master's Programme, Macromolecular Materials, 120 credits"},
    'TMMTM': {'cycle': 2,
	      'swe': 'Masterprogram, media management',
              'eng': "Master's Programme, Media Management, 120 credits"},
    'TMRSM': {'cycle': 2,
	      'swe': 'Masterprogram, marina system',
              'eng': "Master's Programme, Naval Architecture, 120 credits"},
    'TMTLM': {'cycle': 2,
	      'swe': 'Masterprogram, molekylära tekniker inom livsvetenskaperna',
              'eng': "Master's Programme, Molecular Techniques in Life Science, 120 credits"},
    'TMVTM': {'cycle': 2,
	      'swe': 'Masterprogram, molekylär vetenskap och teknik',
              'eng': "Master's Programme, Molecular Science and Engineering, 120 credits"},
    'TNEEM': {'cycle': 2,
	      'swe': 'Masterprogram, kärnenergiteknik',
              'eng': "Master's Programme, Nuclear Energy Engineering, 120 credits"},
    'TNTEM': {'cycle': 2,
	      'swe': 'Masterprogram, nanoteknik',
              'eng': "Master's Programme, Nanotechnology, 120 credits"},
    'TPRMM': {'cycle': 2,
	      'swe': 'Masterprogram, industriell produktion',
              'eng': "Master's Programme, Production Engineering and Management, 120 credits"},
    'TSCRM': {'cycle': 2,
	      'swe': 'Masterprogram, systemteknik och robotik',
              'eng': "Master's Programme, Systems, Control and Robotics, 120 credits"},
    'TSEDM': {'cycle': 2,
	      'swe': 'Masterprogram, programvaruteknik för distribuerade system',
              'eng': "Master's Programme, Software Engineering of Distributed Systems, 120 credits"},
    'TSUEM': {'cycle': 2,
	      'swe': 'Masterprogram, hållbar energiteknik',
              'eng': "Master's Programme, Sustainable Energy Engineering, 120 credits"},
    'TSUTM': {'cycle': 2,
	      'swe': 'Masterprogram, teknik och hållbar utveckling',
              'eng': "Master's Programme, Sustainable Technology, 120 credits"},
    'TTAHM': {'cycle': 2,
	      'swe': 'Masterprogram, teknik, arbete och hälsa',
              'eng': "Master's Programme, Technology, Work and Health, 120 credits"},
    'TTEMM': {'cycle': 2,
	      'swe': 'Masterprogram, teknisk mekanik',
              'eng': "Master's Programme, Engineering Mechanics, 120 credits"},
    'TTFYM': {'cycle': 2,
	      'swe': 'Masterprogram, teknisk fysik',
              'eng': "Master's Programme, Engineering Physics, 120 credits"},
    'TTGTM': {'cycle': 2,
	      'swe': 'Masterprogram, transport och geoinformatik',
              'eng': "Master's Programme, Transport and Geoinformation Technology, 120 credits"},
    'TTMAM': {'cycle': 2,
	      'swe': 'Masterprogram, tillämpad matematik och beräkningsmatematik',
              'eng': "Master's Programme, Applied and Computational Mathematics, 120 credits"},
    'TTMIM': {'cycle': 2,
	      'swe': 'Masterprogram, transport, mobilitet och innovation',
              'eng': "Master's Programme, Transport, Mobility and Innovation"},
    'TTMVM': {'cycle': 2,
	      'swe': 'Masterprogram, teknisk materialvetenskap',
              'eng': "Master's Programme, Engineering Materials Science, 120 credits"},
    'TURSM': {'cycle': 2,
	      'swe': 'Magisterprogram, urbana studier',
              'eng': "Master's Programme, Urbanism Studies, 60 credits"}
}

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

def programcode_from_degree(s):
    # replace ’ #x2019 with ' #x27
    s=s.replace(u"\u2019", "'")
    for p in programcodes:
        pname_eng=programcodes[p]['eng']
        pname_swe=programcodes[p]['swe']
        e_offset=s.find(pname_eng)
        s_offset=s.find(pname_swe)
        if (e_offset >= 0) or (s_offset >= 0):
            return p
    return None

#############################
###### EDIT THIS STUFF ######
#############################

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(args):
    global baseUrl, header, payload

    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    config_file=args["config"]

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            access_token=configuration["canvas"]["access_token"]

            if args["containers"]:
                baseUrl="http://"+configuration["canvas"]["host"]+"/api/v1"
                print("using HTTP for the container environment")
            else:
                baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}

    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()


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

def expand_school_name(school):
    si=schools_info.get(school, None)
    if si:
        return schools_info[school]['eng']
    else:
        return "Unknown"

# English version of form:
# <div class="form">
#     		<a href="https://intra.kth.se"><img src="/kth-cover/assets/images/logotype.jpg" class="logotype"></a>

# 			<h2 class="site">KTH Intranet</h2>

# 			<div class="breadcrums" id="breadcrums">
# 				<a href="https://intra.kth.se/en">KTH INTRANET</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration">ADMINISTRATION</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation">COMMUNICATION</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation/mallar">TEMPLATES</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation/mallar/avhandlingarochexamensarbeten">THESIS</a> <span class="separator">/</span>
# 				CREATE THESIS COVER
# 			</div>

#       <h1>Create a KTH Thesis Cover Page as PDF</h1>
# 			<div class="langSwitcher">
				
# 					<a href="/kth-cover" title="">På svenska <img src="/kth-cover/assets/images/sv_SE.png" class="logotype"></a>
				
# 			</div>
#       <p>This form will generate an English cover. If you would like a Swedish cover, please follow the link På svenska to the right.</p>
#       <p>When you have filled in the cycle, the credits, and the degree of the degree project, the possible alternatives for the field of technology or main field of study will appear in the pull down menu.</p>
#       <p>For bachelor and master of science in engineering degrees the field of technology should be given, which you will recognize from the name of your programme. For the degree of master you will find the main field of study in the official course syllabus for the degree project course in the Course and Programme Directory. If the course has several main fields of study, you will need to either ask the programme director or inspect the main field of studies of the specialised second cycle courses that you have taken, and choose the main field of study where you have taken at least 30 credits.</p>
       

# <form action="/kth-cover/kth-cover.pdf" method="POST" enctype="multipart/form-data" onsubmit="return validate()">
    

#         <!-- Degree -->
#         <fieldset>
#           <div class="clearfix" id="degree_field">
#             <label for="degree">Cycle and credits of the degree project</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="degree" name="degree">
#                   <option value="tech-label" disabled="" selected="">Choose degree project</option>
#                   <option value="first-level-7">Degree project, first cycle (7.5 credits)</option>
#                   <option value="first-level-10">Degree project, first cycle (10 credits)</option>
#                   <option value="first-level-15">Degree project, first cycle (15 credits)</option>
#                   <option value="second-level-15">Degree project, second cycle (15 credits)</option>
#                   <option value="second-level-30">Degree project, second cycle (30 credits)</option>
#                   <option value="second-level-60">Degree project, second cycle (60 credits)</option>
#                 </select>
#               </div>
#             </div>
#           </div>

#           <!-- Exam -->
#           <div class="clearfix" id="exam_field">
#             <label for="exam">Degree</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="exam" name="exam" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Choose degree</option>
#                   <option class="firstLevel" value="1">Bachelors degree</option>
#                   <option class="firstLevel" value="1">Higher Education Diploma</option>
#                   <option class="firstLevel" value="2">Degree of Bachelor of Science in Engineering</option>
#                   <option class="firstLevel" value="8">Degree of Master of Science in Secondary Education</option>
#                   <option class="secondLevel" value="3">Degree of Master (60 credits)</option>
#                   <option class="secondLevel" value="3">Degree of Master (120 credits)</option>
#                   <option class="secondLevel" value="4">Degree of Master of Science in Engineering</option>
#                   <option class="secondLevel" value="5">Degree of Master of Architecture</option>
#                   <option class="secondLevel" value="6">Degree of Master of Science in Secondary Education</option>
#                   <option class="secondLevel" value="7">Both Master of science in engineering and Master</option>
#                 </select>
#               </div>
#             </div>
#           </div>
#           <!-- Major, tech or subject area -->
#           <div class="clearfix" id="area_field">
#             <label id="area_field_label_normal" for="area">Main field or subject of your degree</label>
#             <label id="area_field_label_mix" for="area">Field of technology (Master of science in engineering)</label>
#               <div class="input">
#               <div class="selectContainer">
#                 <select id="area" name="area" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Choose field of study</option>
#                   <!-- Major areas -->
#                   <option class="area-1 area-3 area-5" value="Architecture">Architecture</option>
#                   <option class="area-3" value="Biotechnology">Biotechnology</option>
#                   <option class="area-3" value="Computer Science and Engineering">Computer Science and Engineering</option>
#                   <option class="area-3" value="Electrical Engineering">Electrical Engineering</option>
#                   <option class="area-3" value="Industrial Management">Industrial Management</option>
#                   <option class="area-3" value="Information and Communication Technology">Information and Communication Technology</option>
#                   <option class="area-3" value="Chemical Science and Engineering">Chemical Science and Engineering</option>
#                   <option class="area-3" value="Mechanical Engineering">Mechanical Engineering</option>
#                   <option class="area-3" value="Mathematics">Mathematics</option>
#                   <option class="area-3" value="Materials Science and Engineering">Materials Science and Engineering</option>
#                   <option class="area-3" value="Medical Engineering">Medical Engineering</option>
#                   <option class="area-3" value="Environmental engineering">Environmental engineering</option>
#                   <option class="area-3" value="The Built Environment">The Built Environment</option>
#                   <option class="area-3" value="Technology and Economics">Technology and Economics</option>
#                   <option class="area-3" value="Technology and Health">Technology and Health</option>
#                   <option class="area-3" value="Technology and Learning">Technology and Learning</option>
#                   <option class="area-3" value="Technology and Management">Technology and Management</option>
#                   <option class="area-3" value="Engineering Physics">Engineering Physics</option>
#                   <option class="area-1 area-8" value="Technology">Technology</option>
#                   <!-- Tech areas -->
#                   <option class="area-2" value="Constructional Engineering and Design">Constructional Engineering and Design</option>
#                   <option class="area-2" value="Computer Engineering">Computer Engineering</option>
#                   <option class="area-2" value="Electronics and Computer Engineering">Electronics and Computer Engineering</option>
#                   <option class="area-2" value="Electrical Engineering">Electrical Engineering</option>
#                   <option class="area-2" value="Chemical Engineering">Chemical Engineering</option>
#                   <option class="area-2" value="Mechanical Engineering">Mechanical Engineering</option>
#                   <option class="area-2" value="Medical Technology">Medical Technology</option>
#                   <option class="area-2 area-3" value="Engineering and Economics">Engineering and Economics</option>
#                   <option class="area-4 area-7" value="Technology and Learning">Technology and Learning</option>
#                   <option class="area-4 area-7" value="Biotechnology">Biotechnology</option>
#                   <option class="area-4 area-7" value="Computer Science and Engineering">Computer Science and Engineering</option>
#                   <option class="area-4 area-7" value="Design and Product Realisation">Design and Product Realisation</option>
#                   <option class="area-4 area-7" value="Electrical Engineering">Electrical Engineering</option>
#                   <option class="area-4 area-7" value="Energy and Environment">Energy and Environment</option>
#                   <option class="area-4 area-7" value="Vehicle Engineering">Vehicle Engineering</option>
#                   <option class="area-4 area-7" value="Industrial Engineering and Management">Industrial Engineering and Management</option>
#                   <option class="area-4 area-7" value="Information and Communication Technology">Information and Communication Technology</option>
#                   <option class="area-4 area-7" value="Mechanical Engineering">Mechanical Engineering</option>
#                   <option class="area-4 area-7" value="Materials Design and Engineering">Materials Design and Engineering</option>
#                   <option class="area-4 area-7" value="Medical Engineering">Medical Engineering</option>
#                   <option class="area-4 area-7" value="Media Technology">Media Technology</option>
#                   <option class="area-4 area-7" value="Civil Engineering and Urban Management">Civil Engineering and Urban Management</option>
#                   <option class="area-4 area-7" value="Engineering Physics">Engineering Physics</option>
#                   <option class="area-4 area-7" value="Engineering Chemistry">Engineering Chemistry</option>
#                   <option class="area-4 area-7" value="Chemical Science and Engineering">Chemical Science and Engineering</option>
#                   <option class="area-4 area-7" value="Microelectronics">Microelectronics</option>
#                   <!-- Subject areas -->
#                   <option class="area-6 area-8" value="Technology and Learning">Technology and Learning</option>
#                   <option class="area-6 area-8" value="Mathematics and Learning">Mathematics and Learning</option>
#                   <option class="area-6 area-8" value="Chemistry and Learning">Chemistry and Learning</option>
#                   <option class="area-6 area-8" value="Physics and Learning">Physics and Learning</option>
#                   <option class="area-6 area-8" value="Subject-Based Teaching">Subject-Based Teaching</option>
#                 </select>
#               </div>
#             </div>
#           </div>


#             <!-- Subject area (magister) for type 7 (master of science and master-->
#             <div class="double_field" id="master_field">
#                 <label for="master">Main field of study (Degree of master)</label>
#                 <div class="input">
#                     <div class="selectContainer">
#                         <select id="master" name="master">
#                             <option class="firstLevel secondLevel" value="" disabled="" selected="">Choose field of study</option>
#                             <!-- Major areas -->
#                             <option class="area-1 area-3 area-5" value="Architecture">Architecture</option>
#                             <option class="area-3" value="Biotechnology">Biotechnology</option>
#                             <option class="area-3" value="Computer Science and Engineering">Computer Science and Engineering</option>
#                             <option class="area-3" value="Electrical Engineering">Electrical Engineering</option>
#                             <option class="area-3" value="Industrial Management">Industrial Management</option>
#                             <option class="area-3" value="Information and Communication Technology">Information and Communication Technology</option>
#                             <option class="area-3" value="Chemical Science and Engineering">Chemical Science and Engineering</option>
#                             <option class="area-3" value="Mechanical Engineering">Mechanical Engineering</option>
#                             <option class="area-3" value="Mathematics">Mathematics</option>
#                             <option class="area-3" value="Materials Science and Engineering">Materials Science and Engineering</option>
#                             <option class="area-3" value="Medical Engineering">Medical Engineering</option>
#                             <option class="area-3" value="Environmental engineering">Environmental engineering</option>
#                             <option class="area-3" value="The Built Environment">The Built Environment</option>
#                             <option class="area-3" value="Technology and Economics">Technology and Economics</option>
#                             <option class="area-3" value="Technology and Health">Technology and Health</option>
#                             <option class="area-3" value="Technology and Learning">Technology and Learning</option>
#                             <option class="area-3" value="Technology and Management">Technology and Management</option>
#                             <option class="area-3" value="Engineering Physics">Engineering Physics</option>
#                         </select>
#                     </div>
#                 </div>
#             </div>

#             <div class="clearfix" id="title_field">
#                 <label for="title">Title</label>

#                 <div class="input">
#                     <input type="text" id="title" name="title" value="" class="title">
#                 </div>
#                 <span class="titleHint">You may specify the location of line breaks in this field with &lt;br/&gt;. Other allowed tags are those for &lt;i&gt;italic&lt;/i&gt;, &lt;sup&gt;superscript&lt;/sup&gt; or &lt;sub&gt;subscript&lt;/sub&gt; text.</span>
#             </div>

#             <div class="clearfix" id="secondaryTitle_field">
#                 <label for="title">Subtitle</label>

#                 <div class="input">
#                     <input type="text" id="secondaryTitle" name="secondaryTitle" value="" class="subtitle">
#                 </div>
#                 <span class="titleHint">You may specify the location of line breaks in this field with &lt;br/&gt;. Other allowed tags are those for &lt;i&gt;italic&lt;/i&gt;, &lt;sup&gt;superscript&lt;/sup&gt; or &lt;sub&gt;subscript&lt;/sub&gt; text.</span>
#             </div>

#             <div class="clearfix" id="author_field">
#                 <label for="author">Author</label>

#                 <div class="input">
#                     <input type="text" id="author" name="author" value="">
#                 </div>
#             </div>

#             <div class="clearfix" id="author_2_field">
#                 <label for="author_2">Author (if applicable)</label>

#                 <div class="input">
#                     <input type="text" id="author_2" name="author_2" value="">
#                 </div>
#             </div>

#             <div id="image_field" class="clearfix">
#                 <label for="image">Upload an image to use as front page image (jpg, png)</label>

#                 <div class="input">
#                     <input type="file" name="image" id="image" class="image">
#                 </div>
#             </div>
#         </fieldset>

#         <fieldset>
#           <div class="clearfix" id="school_field">
#             <label for="school">School at KTH where the degree project was examined</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="school" name="school">
#                   <option value="School of Architecture and the Built Environment">School of Architecture and the Built Environment</option>
#                   <option value="School of Industrial Engineering and Management">School of Industrial Engineering and Management</option>
#                   <option value="School of Engineering Sciences">School of Engineering Sciences</option>
#                   <option value="School of Engineering Sciences in Chemistry, Biotechnology and Health">School of Engineering Sciences in Chemistry, Biotechnology and Health</option>
#                   <option value="School of Electrical Engineering and Computer Science">School of Electrical Engineering and Computer Science</option>
#                 </select>
#               </div>
#             </div>
#           </div>

# 					<div class="clearfix" id="year_field">
# 						<label for="year">Year</label>
# 						<div class="input">
# 							<input type="text" id="year" name="year" value="" required="">
# 						</div>
# 					</div>
# 				</fieldset>
				
# 				<fieldset>
# 					<div class="clearfix" id="trita_field">
# 						<label for="trita">TRITA</label>
# 						<div class="input">
# 							<input type="text" id="trita" name="trita" value="">
# 						</div>
#           </div>
# 				</fieldset>
        
# 				<fieldset class="pagesModel">
# 					<div class="clearfix" id="required_field">
# 						<label for="pages">Pages *</label>
# 						<div class="input">
# 							<input type="text" id="pages" name="pages" value="">
# 						</div>
# 					</div>

# 					<div class="clearfix" id="optional_field">
# 						<label for="model">Model</label>
# 						<div class="input">
# 							<input type="text" id="model" name="model" value="">
# 						</div>
# 					</div>
# 				</fieldset>

# 				<div class="actions">
# 					<input type="submit" class="btn primary" value="Create cover">
# 				</div>
#       		</form></div>

# Swedish version of form:
# <div class="form">
#     		<a href="https://intra.kth.se"><img src="/kth-cover/assets/images/logotype.jpg" class="logotype"></a>

# 			<h2 class="site">KTH Intranät</h2>

# 			<div class="breadcrums" id="breadcrums">
# 				<a href="https://intra.kth.se/en">KTH INTRANÄT</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration">ADMINISTRATIVT STÖD</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation">KOMMUNIKATION - RÅD OCH VERKTYG</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation/mallar">MALLAR</a> <span class="separator">/</span>
#         <a href="https://intra.kth.se/en/administration/kommunikation/mallar/avhandlingarochexamensarbeten">MALLAR FÖR AVHANDLINGAR OCH EXAMENSARBETEN</a> <span class="separator">/</span>
# 				SKAPA OMSLAG TILL EXAMENSARBETE
# 			</div>

#       <h1>Skapa omslag till examensarbete</h1>
# 			<div class="langSwitcher">
				
# 					<a href="/kth-cover?l=en" title="">In English <img src="/kth-cover/assets/images/en_UK.png" class="logotype"></a>
				
# 			</div>
#       <p>Detta formulär genererar ett svenskspråkigt omslag. Om du vill ha ett engelskspråkigt omslag ska du följa länken In English till höger.</p>
#       <p>När du fyllt i examensarbetets nivå och poäng samt den examen som examenarbetet ingår i kommer möjliga alternativ för huvud-, teknik- eller ämnesområde för din examen att komma upp i rullgardinsmenyn.</p>
#       <p>För högskoleingenjörsexamen och civilingenjörsexamen ska teknikområdet anges, vilket du känner igen från namnet på ditt program. För masterexamen hittar du huvudområdet genom att slå upp kursplanen för examensarbetskursen i kurs- och programkatalogen. Om kursen har flera huvudområden så behöver du fråga någon ansvarig för programmet eller inspektera huvudområdena för de fördjupande kurser på avancerad nivå som du läst och välja det huvudområde där du läst minst 30 hp.</p>
       

# <form action="/kth-cover/kth-cover.pdf" method="POST" enctype="multipart/form-data" onsubmit="return validate()">
    

#         <!-- Degree -->
#         <fieldset>
#           <div class="clearfix" id="degree_field">
#             <label for="degree">Examensarbetets nivå och poäng</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="degree" name="degree">
#                   <option value="tech-label" disabled="" selected="">Välj examensarbete</option>
#                   <option value="first-level-7">Examensarbete, grundnivå (7,5 hp)</option>
#                   <option value="first-level-10">Examensarbete, grundnivå (10 hp)</option>
#                   <option value="first-level-15">Examensarbete, grundnivå (15 hp)</option>
#                   <option value="second-level-15">Examensarbete, avancerad nivå (15 hp)</option>
#                   <option value="second-level-30">Examensarbete, avancerad nivå (30 hp)</option>
#                   <option value="second-level-60">Examensarbete, avancerad nivå (60 hp)</option>
#                 </select>
#               </div>
#             </div>
#           </div>

#           <!-- Exam -->
#           <div class="clearfix" id="exam_field">
#             <label for="exam">Examen</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="exam" name="exam" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj examen</option>
#                   <option class="firstLevel" value="1">Kandidatexamen</option>
#                   <option class="firstLevel" value="1">Högskoleexamen</option>
#                   <option class="firstLevel" value="2">Högskoleingenjörsexamen</option>
#                   <option class="firstLevel" value="8">Ämneslärarexamen</option>
#                   <option class="secondLevel" value="3">Magisterexamen</option>
#                   <option class="secondLevel" value="3">Masterexamen</option>
#                   <option class="secondLevel" value="4">Civilingenjörsexamen</option>
#                   <option class="secondLevel" value="5">Arkitektexamen</option>
#                   <option class="secondLevel" value="6">Ämneslärarexamen</option>
#                   <option class="secondLevel" value="7">Civilingenjörs- och masterexamen</option>
#                 </select>
#               </div>
#             </div>
#           </div>

#           <!-- Major, tech or subject area -->
#           <div class="clearfix" id="area_field">
#             <label id="area_field_label_normal" for="area">Huvud-, teknik- eller ämnesområde för din examen</label>
#             <label id="area_field_label_mix" for="area">Teknikområde för civilingenjörsexamen</label>
#               <div class="input">
#               <div class="selectContainer">
#                 <select id="area" name="area" disabled="disabled">
#                   <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj område</option>
#                   <!-- Major areas -->
#                   <option class="area-1 area-3 area-5" value="Arkitektur">Arkitektur</option>
#                   <option class="area-3" value="Bioteknik">Bioteknik</option>
#                   <option class="area-3" value="Datalogi och datateknik">Datalogi och datateknik</option>
#                   <option class="area-3" value="Elektroteknik">Elektroteknik</option>
#                   <option class="area-3" value="Industriell ekonomi">Industriell ekonomi</option>
#                   <option class="area-3" value="Informations- och kommunikationsteknik">Informations- och kommunikationsteknik</option>
#                   <option class="area-3" value="Kemiteknik">Kemiteknik</option>
#                   <option class="area-3" value="Maskinteknik">Maskinteknik</option>
#                   <option class="area-3" value="Matematik">Matematik</option>
#                   <option class="area-3" value="Materialteknik">Materialteknik</option>
#                   <option class="area-3" value="Medicinsk teknik">Medicinsk teknik</option>
#                   <option class="area-3" value="Miljöteknik">Miljöteknik</option>
#                   <option class="area-3" value="Samhällsbyggnad">Samhällsbyggnad</option>
#                   <option class="area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
#                   <option class="area-3" value="Teknik och hälsa">Teknik och hälsa</option>
#                   <option class="area-3" value="Teknik och lärande">Teknik och lärande</option>
#                   <option class="area-3" value="Teknik och management">Teknik och management</option>
#                   <option class="area-3" value="Teknisk fysik">Teknisk fysik</option>
#                   <option class="area-1 area-8" value="Teknik">Teknik</option>
#                   <!-- Tech areas -->
#                   <option class="area-2" value="Byggteknik och design">Byggteknik och design</option>
#                   <option class="area-2" value="Datateknik">Datateknik</option>
#                   <option class="area-2" value="Elektronik och datorteknik">Elektronik och datorteknik</option>
#                   <option class="area-2" value="Elektroteknik">Elektroteknik</option>
#                   <option class="area-2" value="Kemiteknik">Kemiteknik</option>
#                   <option class="area-2" value="Maskinteknik">Maskinteknik</option>
#                   <option class="area-2" value="Medicinsk teknik">Medicinsk teknik</option>
#                   <option class="area-2 area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
#                   <option class="area-4 area-7" value="Teknik och lärande">Teknik och lärande</option>
#                   <option class="area-4 area-7" value="Bioteknik">Bioteknik</option>
#                   <option class="area-4 area-7" value="Datateknik">Datateknik</option>
#                   <option class="area-4 area-7" value="Design och produktframtagning">Design och produktframtagning</option>
#                   <option class="area-4 area-7" value="Elektroteknik">Elektroteknik</option>
#                   <option class="area-4 area-7" value="Energi och miljö">Energi och miljö</option>
#                   <option class="area-4 area-7" value="Farkostteknik">Farkostteknik</option>
#                   <option class="area-4 area-7" value="Industriell ekonomi">Industriell ekonomi</option>
#                   <option class="area-4 area-7" value="Informationsteknik">Informationsteknik</option>
#                   <option class="area-4 area-7" value="Maskinteknik">Maskinteknik</option>
#                   <option class="area-4 area-7" value="Materialdesign">Materialdesign</option>
#                   <option class="area-4 area-7" value="Medicinsk teknik">Medicinsk teknik</option>
#                   <option class="area-4 area-7" value="Medieteknik">Medieteknik</option>
#                   <option class="area-4 area-7" value="Samhällsbyggnad">Samhällsbyggnad</option>
#                   <option class="area-4 area-7" value="Teknisk fysik">Teknisk fysik</option>
#                   <option class="area-4 area-7" value="Teknisk kemi">Teknisk kemi</option>
#                   <option class="area-4 area-7" value="Kemivetenskap">Kemivetenskap</option>
#                   <option class="area-4 area-7" value="Mikroelektronik">Mikroelektronik</option>
#                   <!-- Subject areas -->
#                   <option class="area-6 area-8" value="Teknik och lärande">Teknik och lärande</option>
#                   <option class="area-6 area-8" value="Matematik och lärande">Matematik och lärande</option>
#                   <option class="area-6 area-8" value="Kemi och lärande">Kemi och lärande</option>
#                   <option class="area-6 area-8" value="Fysik och lärande">Fysik och lärande</option>
#                   <option class="area-6 area-8" value="Ämnesdidaktik">Ämnesdidaktik</option>
#                 </select>
#               </div>
#             </div>
#           </div>


#             <!-- Subject area (magister) for type 7 (master of science and master-->
#             <div class="double_field" id="master_field">
#                 <label for="master">Huvudområde för masterexamen</label>
#                 <div class="input">
#                     <div class="selectContainer">
#                         <select id="master" name="master">
#                             <option class="firstLevel secondLevel" value="" disabled="" selected="">Välj område</option>
#                             <!-- Major areas -->
#                             <option class="area-1 area-3 area-5" value="Arkitektur">Arkitektur</option>
#                             <option class="area-3" value="Bioteknik">Bioteknik</option>
#                             <option class="area-3" value="Datalogi och datateknik">Datalogi och datateknik</option>
#                             <option class="area-3" value="Elektroteknik">Elektroteknik</option>
#                             <option class="area-3" value="Industriell ekonomi">Industriell ekonomi</option>
#                             <option class="area-3" value="Informations- och kommunikationsteknik">Informations- och kommunikationsteknik</option>
#                             <option class="area-3" value="Kemiteknik">Kemiteknik</option>
#                             <option class="area-3" value="Maskinteknik">Maskinteknik</option>
#                             <option class="area-3" value="Matematik">Matematik</option>
#                             <option class="area-3" value="Materialteknik">Materialteknik</option>
#                             <option class="area-3" value="Medicinsk teknik">Medicinsk teknik</option>
#                             <option class="area-3" value="Miljöteknik">Miljöteknik</option>
#                             <option class="area-3" value="Samhällsbyggnad">Samhällsbyggnad</option>
#                             <option class="area-3" value="Teknik och ekonomi">Teknik och ekonomi</option>
#                             <option class="area-3" value="Teknik och hälsa">Teknik och hälsa</option>
#                             <option class="area-3" value="Teknik och lärande">Teknik och lärande</option>
#                             <option class="area-3" value="Teknik och management">Teknik och management</option>
#                             <option class="area-3" value="Teknisk fysik">Teknisk fysik</option>
#                         </select>
#                     </div>
#                 </div>
#             </div>

#             <div class="clearfix" id="title_field">
#                 <label for="title">Titel</label>

#                 <div class="input">
#                     <input type="text" id="title" name="title" value="" class="title">
#                 </div>
#                 <span class="titleHint">Du kan ange plats för radbrytningar i detta fält med &lt;br/&gt;. Övriga tillåtna taggar är de för &lt;i&gt;kursiv&lt;/i&gt;, &lt;sup&gt;upphöjd&lt;/sup&gt; eller &lt;sub&gt;nedsänkt&lt;/sub&gt; text.</span>
#             </div>

#             <div class="clearfix" id="secondaryTitle_field">
#                 <label for="title">Undertitel</label>

#                 <div class="input">
#                     <input type="text" id="secondaryTitle" name="secondaryTitle" value="" class="subtitle">
#                 </div>
#                 <span class="titleHint">Du kan ange plats för radbrytningar i detta fält med &lt;br/&gt;. Övriga tillåtna taggar är de för &lt;i&gt;kursiv&lt;/i&gt;, &lt;sup&gt;upphöjd&lt;/sup&gt; eller &lt;sub&gt;nedsänkt&lt;/sub&gt; text.</span>
#             </div>

#             <div class="clearfix" id="author_field">
#                 <label for="author">Författare</label>

#                 <div class="input">
#                     <input type="text" id="author" name="author" value="">
#                 </div>
#             </div>

#             <div class="clearfix" id="author_2_field">
#                 <label for="author_2">Författare (om ytterligare författare)</label>

#                 <div class="input">
#                     <input type="text" id="author_2" name="author_2" value="">
#                 </div>
#             </div>

#             <div id="image_field" class="clearfix">
#                 <label for="image">Här kan du ladda upp en bild till omslaget (png eller jpg)</label>

#                 <div class="input">
#                     <input type="file" name="image" id="image" class="image">
#                 </div>
#             </div>
#         </fieldset>

#         <fieldset>
#           <div class="clearfix" id="school_field">
#             <label for="school">Skola vid KTH där examensarbetet examinerades</label>
#             <div class="input">
#               <div class="selectContainer">
#                 <select id="school" name="school">
#                   <option value="Skolan för arkitektur och samhällsbyggnad">Skolan för arkitektur och samhällsbyggnad</option>
#                   <option value="Skolan för industriell teknik och management">Skolan för industriell teknik och management</option>
#                   <option value="Skolan för teknikvetenskap">Skolan för teknikvetenskap</option>
#                   <option value="Skolan för kemi, bioteknologi och hälsa">Skolan för kemi, bioteknologi och hälsa</option>
#                   <option value="Skolan för elektroteknik och datavetenskap">Skolan för elektroteknik och datavetenskap</option>
#                 </select>
#               </div>
#             </div>
#           </div>

# 					<div class="clearfix" id="year_field">
# 						<label for="year">År</label>
# 						<div class="input">
# 							<input type="text" id="year" name="year" value="" required="">
# 						</div>
# 					</div>
# 				</fieldset>
				
# 				<fieldset>
# 					<div class="clearfix" id="trita_field">
# 						<label for="trita">TRITA</label>
# 						<div class="input">
# 							<input type="text" id="trita" name="trita" value="">
# 						</div>
#           </div>
# 				</fieldset>
        
# 				<fieldset class="pagesModel">
# 					<div class="clearfix" id="required_field">
# 						<label for="pages">Pages *</label>
# 						<div class="input">
# 							<input type="text" id="pages" name="pages" value="">
# 						</div>
# 					</div>

# 					<div class="clearfix" id="optional_field">
# 						<label for="model">Model</label>
# 						<div class="input">
# 							<input type="text" id="model" name="model" value="">
# 						</div>
# 					</div>
# 				</fieldset>

# 				<div class="actions">
# 					<input type="submit" class="btn primary" value="Skapa omslag">
# 				</div>
#       		</form></div>

# to transform a dict into something that can be passed as a files paramter to requests.post()
def files_transform_dict(d):
    output_dict=dict()
    for e in d:
        output_dict[e]= (None, d[e])
    return output_dict


def check_for_cover_keys(data):
    required_keys=['degree', 'exam', 'area', 'title', 'author', 'year']
    print("Checking for cover keys")
    num_keys=0
    for key, value in data.items():
        if key in required_keys:
            num_keys=num_keys+1
    if num_keys < len(required_keys):
        print("misisng a required key for cover")
        return False
    return True

# conver_info={
# 'degree': cover_degree,
# 'exam':   cover_exam,
# 'area':   cover_area,
# 'title':  thesis_info_title, 
# 'secondaryTitle': thesis_info_subtitle,
# 'author': authors,
# 'trita':  trita_string,
# 'year': year_of_thesis
# }
def make_cover(language, cover_info):
    global Verbose_Flag

    cookies=dict()
    headers=dict()
    # If missing a required key do not try to make a cover
    if not check_for_cover_keys(cover_info):
        return None
    #
    url='https://intra.kth.se/kth-cover/kth-cover.pdf'
    if language == 'eng':
        cookies={'PLAY_LANG': 'en'}
        headers={'referer': 'https://intra.kth.se/kth-cover?l=en',
                 'origin':  'https://intra.kth.se'
                 }
    else:
        cookies={'PLAY_LANG': 'sv'}
        headers={'referer': 'https://intra.kth.se/kth-cover',
                 'origin':  'https://intra.kth.se'
                 }
    #
    headers['Accept-Encoding']="gzip, deflate, br"
    headers['Accept-Language']="en-US,en;q=0.9"
    headers['Accept']="application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    #
    print("url={0}".format(url))
    # because we are going to pass it as a files argument in the request
    # it has to look like
    #{'degree': (None, 'second-level-30'), 'model': (None, '1337-brynjan!'), 'exam': (None, '3'), 'year': (None, '2021'), 'author': (None, 'A. B. Normal'), 'title': (None, 'Adapting to the new remote work era'), 'secondaryTitle': (None, 'Improving social well-being among IT remote workers'), 'area': (None, 'Computer Science and Engineering'), 'school': (None, 'School of Electrical Engineering and Computer Science'), 'trita': (None, ''), 'pages': (None, '')}
    cover_infot=files_transform_dict(cover_info)
    if Verbose_Flag:
        print("cover_info={0}, cookies={1}, header={2}".format(cover_info, cookies, headers))
    response = requests.post(url, files=cover_infot, cookies=cookies, headers=headers)
    if Verbose_Flag:
        print(response)
        print(response.headers)
        # should looke something like: {'Content-Length': '219391', 'Content-Type': 'application/pdf', 'Content-Disposition': 'attachment; filename="kth-cover6439631930039278186.pdf"', 'Referrer-Policy': 'origin-when-cross-origin', 'Strict-Transport-Security': 'max-age=63072000'}
    #
    if response.status_code == requests.codes.ok:
        if response.headers['Content-Type'] == 'application/pdf':
            return response.content
        print("make_cover did not get PDF back")
    return None

# Note that create_cover generates the encoded the values that the cover generator web pages output,
# i.e., https://intra.kth.se/kth-cover?l=en and https://intra.kth.se/kth-cover
#
def create_cover(language, cycle, number_of_credits, exam, area, area2, author_name1, author_name2, title, subtitle, school_acronym, year_of_thesis, trita_string):
    # the exam anc abe an exam code [1, 2, 3, 4, 5, 6, 7, 8] or the name of the exam
    # Cycle and credits of the degree project
    # Degree
    # Choose degree: Main field or subject of your degree
    # Title - You may specify the location of line breaks in this field with <br/>. Other allowed tags are those for <i>italic</i>, <sup>superscript</sup> or <sub>subscript</sub> text.
    # Subtitle - You may specify the location of line breaks in this field with <br/>. Other allowed tags are those for <i>italic</i>, <sup>superscript</sup> or <sub>subscript</sub> text.
    # Author
    # second "Author" (if applicable)
    # School at KTH where the degree project was examined
    # Year
    # TRITA
    cover_info=dict()
    #
    acceptable_error=1.0
    if cycle == 1:
        if (number_of_credits - 15.0) < acceptable_error:
            cover_info['degree']='first-level-15'
        elif (number_of_credits - 10.0) < acceptable_error:
            cover_info['degree']='first-level-10'
        elif (number_of_credits - 7.5) < acceptable_error:
            cover_info['degree']='first-level-7'
        else:
            print("Error in first cycle degree information, {}".format(number_of_credits))
            return None
    elif cycle == 2:
        if (number_of_credits == 30.0) < acceptable_error:
            cover_info['degree']='second-level-30'
        elif (number_of_credits == 15.0) < acceptable_error:
            cover_info['degree']='second-level-15'
        elif (number_of_credits == 60.0) < acceptable_error:
            cover_info['degree']='second-level-60'
        else:
            print("Error in second cycle degree information, {}".format(number_of_credits))
            return None
    else:
            print("Error in {0} cycle degree information and credits={1}".format(cycle, number_of_credits))
            return None

    if exam and exam in [1, 2, 3, 4, 5, 6, 7, 8]:
        cover_info['exam']=exam
    else:
        print("Error in exam {0} information={1}".format(exam))
        return None

    if area:
        cover_info['area']=area
    else:
        print("Error in area {0}".format(area))
        return None
    
    if cover_info['exam'] == 7:   # #             <!-- Subject area (magister) for type 7 (master of science and master-->
        if area2:
            cover_info['area2']=area2
        else:
            print("Error in area2 {0}".format(area2))

    cover_info['author']=author_name1
    if author_name2:
        cover_info['author_2']=author_name2

    cover_info['title']=title
    if subtitle and len(subtitle) > 0:
        cover_info['secondaryTitle']=subtitle

    if school_acronym:
        si=schools_info.get(school_acronym, None)
        if si:
            cover_info['school']=schools_info[school_acronym][language]

    if year_of_thesis:
        cover_info['year']=year_of_thesis

    if trita_string:
        cover_info['trita']=trita_string

    cover_info['pages']=''
    cover_info['model']='1337-brynjan!'

    if testing:
        print("In create_cover, cover_info={0}".format(cover_info))
        return

    resulting_cover=make_cover(language, cover_info)
    if resulting_cover and len(resulting_cover) > 0:
        with open("cover.pdf", 'wb') as f: # note that the PDF file has to be written in binary mode
            f.write(resulting_cover)

        # split the cover into two pages: cover_pages-1 and cover_pages-2
        try:
            cmd1 = subprocess.run(['qpdf', '--split-pages', 'cover.pdf', 'cover_pages'], capture_output=True)
        except:
            sys.stdout.buffer.write(command.stdout)
            sys.stderr.buffer.write(command.stderr)
            sys.exit(cmd1.returncode)

# Ruby code
#   cmd1="qpdf --split-pages cover.pdf cover_pages"
#   status1=system(cmd1)
#   # get thesis and save it in a file
#   final_thesis=session['final_thesis']
#   puts("final_thesis is #{final_thesis}")
#   attachments=final_thesis['attachments']
#   puts("attachments is #{attachments}")
#   if attachments
#     attachments.each do |attachment|
#       puts("process the PDF file named #{attachment['filename']}")
#       filename=attachment['filename']
#       url_to_file=attachment['url']
#       file_handle = open(url_to_file)
#       content_of_file = file_handle.read
#       file = File.open(filename, "w")
#       file.puts("#{content_of_file}")
#       file.close
#       # apply the cover
#       cmd2="qpdf  --empty --pages cover_pages-1 #{filename} cover_pages-2 -- #{filename[0..-5]}-with-cover.pdf"
#       status2=system(cmd2)

# Areas
program_areas = {
    'ARKIT': {'cycle': 2,
              'eng': 'Architecture', 'swe': 'Arkitektur'},
    'CBIOT': {'cycle': 2,
              'eng': 'Biotechnology', 'swe': 'Bioteknik'},
    'CDATE': {'cycle': 2,
              'eng': 'Computer Science and Engineering', 'swe': 'Datalogi och datateknik'},
    'CDEPR': {'cycle': 2,
              'eng': 'Design and Product Realisation', 'swe': 'Design och produktframtagning'},
    'CELTE': {'cycle': 2,
              'eng': 'Electrical Engineering', 'swe': 'Elektroteknik'},
    'CENMI': {'cycle': 2,
              'eng': 'Energy and Environment', 'swe': 'Energi och miljö'},
    'CFATE': {'cycle': 2,
              'eng': 'Vehicle Engineering', 'swe': 'Farkostteknik'},
    'CINEK': {'cycle': 2,
              'eng': 'Industrial Management', 'swe': 'Industriell ekonomi'},
    'CINTE': {'cycle': 2,
              'eng': 'Information and Communication Technology', 'swe': 'Informations- och kommunikationsteknik'},
    'CITEH': {'cycle': 2,
              'eng': '', 'swe': ''}, # 'Civilingenjörsutbildning i industriell teknik och hållbarhet', 'Degree Programme in Industrial Technology and Sustainability'
    'CTKEM': {'cycle': 2,
              'eng': 'Engineering Chemistry', 'swe': 'Teknisk kemi'},
    'CLGYM': {'cycle': 2,
              'eng': 'Technology and Learning', 'swe': 'Teknik och lärande'},
    'CMAST': {'cycle': 2,
              'eng': 'Mechanical Engineering', 'swe': 'Maskinteknik'},
    'CMATD': {'cycle': 2,
              'eng':'Materials Science and Engineering', 'swe': 'Materialteknik'},
    'CMEDT': {'cycle': 2,
              'eng': 'Medical Engineering', 'swe': 'Medicinsk teknik'},
    'CMETE': {'cycle': 2,
              'eng': 'Media Technology', 'swe': 'Medieteknik'},
    'COPEN': {'cycle': 2, # 'Civilingenjörsutbildning öppen ingång', 'Degree Programme Open Entrance'
	      'swe': '',
              'eng': ''},
    'CSAMH': {'cycle': 2,
              'eng': 'Civil Engineering and Urban Management', 'swe': 'Samhällsbyggnad'},
    'CTFYS': {'cycle': 2,
              'eng': 'Engineering Physics', 'swe': 'Teknisk fysik'},
    'CTMAT': {'cycle': 2,
              'eng': 'Mathematics', 'swe': 'Matematik'},
    'KPUFU': {'cycle': 2, # 'Kompletterande pedagogisk utbildning för ämneslärarexamen i matematik, naturvetenskap och teknik för forskarutbildade', 'Bridging Teacher Education Programme in Mathematics, Science and Technology for Graduates with a Third Cycle Degree'
              'eng': 'Subject-Based Teaching', 'swe':'Ämnesdidaktik'},
    'KPULU': {'cycle': 2, # 'Kompletterande pedagogisk utbildning', 'Bridging Teacher Education Programme'
              'eng': '', 'swe': ''},
    'KUAUT': {'cycle': 2, # 'Kompletterande utbildning för arkitekter med avslutad utländsk utbildning', 'Bridging programme for architects with foreign qualifications'
              'eng': 'Architecture', 'swe': 'Arkitektur'},
    'KUIUT': {'cycle': 2, # 'Kompletterande utbildning för ingenjörer med avslutad utländsk utbildning', 'Bridging programme for engineers with foreign qualifications'
              'eng': 'Architecture', 'swe': 'Arkitektur'},
    'LÄRGR': {'cycle': 2, # 'Ämneslärarutbildning med inriktning mot teknik, årskurs 7-9', 'Subject Teacher Education in Technology, Secondary Education'
              'eng': 'Subject-Based Teaching', 'swe':'Ämnesdidaktik'},
    'TAEEM': {'cycle': 2, # 'Masterprogram, flyg- och rymdteknik', "Master's Programme, Aerospace Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TAETM': {'cycle': 2, # 'Masterprogram, aeroelasticitet i turbomaskiner', "Master's Programme, Turbomachinery Aeromechanic University Training, 120 credits"
              'eng': '', 'swe': ''},
    'TARKM': {'cycle': 2, # 'Masterprogram, arkitektur', "Master's Programme, Architecture, 120 credits"
              'eng': 'Architecture', 'swe': 'Arkitektur'},
              # there are not theses for cycle 0, so skip the subject areas of these programs
    'TBYPH': {'cycle': 1, # 'Högskoleutbildning i byggproduktion', 'Degree Progr. in Construction Management'
              'eng': '', 'swe': ''},
    'TCAEM': {'cycle': 2, # 'Masterprogram, husbyggnads- och anläggningsteknik', "Master's Programme, Civil and Architectural Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TCOMK': {'cycle': 1, # 'Kandidatprogram, informations- och kommunikationsteknik', "Bachelor's Programme in Information and Communication Technology"
              'eng':  'Information and Communication Technology', 'swe': 'Informationsteknik'},
    'TCOMM': {'cycle': 2, # 'Masterprogram, kommunikationssystem', "Master's Programme, Communication Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TCSCM': {'cycle': 2, # 'Masterprogram, datalogi', "Master's Programme, Computer Science, 120 credits"
              'eng': '', 'swe': ''},
    'TDEBM': {'cycle': 2, #'Magisterprogram, design och byggande i staden',  "Master's Programme, Urban Development and Design, 60 credits"
              'eng': '', 'swe': ''},
    'TDSEM': {'cycle': 2, # 'Masterprogram, decentraliserade smarta energisystem', "Master's Programme, Decentralized Smart Energy Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TDTNM': {'cycle': 2, # 'Masterprogram, datorsimuleringar inom teknik och naturvetenskap', "Master's Programme, Computer Simulations for Science and Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TEBSM': {'cycle': 2, # 'Masterprogram, inbyggda system', "Master's Programme, Embedded Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TEEEM': {'cycle': 2, # 'Masterprogram, teknik och ledning för energi- och miljösystem', "Master's Programme, Management and Engineering of Environment and Energy, 120 credits"
              'eng': '', 'swe': ''},
    'TEEGM': {'cycle': 2, # 'Masterprogram, miljöteknik', "Master's Programme, Environmental Engineering, 120 credits"
              'eng': 'Environmental engineering', 'swe': 'Miljöteknik'},
    'TEFRM': {'cycle': 2, # 'Masterprogram, elektromagnetism, fusion och rymdteknik', "Master's Programme, Electromagnetics, Fusion and Space Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TEILM': {'cycle': 2, # 'Magisterprogram, entreprenörskap och innovationsledning', "Master's Programme, Entrepreneurship and Innovation Management, 60 credits"
              'eng': '', 'swe': ''},
    'TEINM': {'cycle': 2, # 'Masterprogram, innovations- och tillväxtekonomi', "Master's Programme, Economics of Innovation and Growth, 120 credits"
              'eng': '', 'swe': ''},
    'TELPM': {'cycle': 2, # 'Masterprogram, elkraftteknik', "Master's Programme, Electric Power Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TFAFK': {'cycle': 1, # 'Kandidatprogram, Fastighetsutveckling med fastighetsförmedling', "Bachelor's Programme in Property Development and Agency"
              'eng': '', 'swe': ''},
    'TFAHM': {'cycle': 2, # 'Magisterprogram, fastigheter', "Master's Programme, Real Estate"
              'eng': '', 'swe': ''},
    'TFOBM': {'cycle': 2, # 'Masterprogram, fastigheter och byggande', "Master's Programme, Real Estate and Construction Management, 120 credits"
              'eng': '', 'swe': ''},
    'TFOFK': {'cycle': 1, # 'Kandidatprogram, fastighet och finans', "Bachelor's Programme in Real Estate and Finance"
              'eng': '', 'swe': ''},
    'TFORM': {'cycle': 2, # 'Masterprogram, fordonsteknik', "Master's Programme, Vehicle Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'THSSM': {'cycle': 2, # 'Masterprogram, hållbar samhällsplanering och stadsutformning', "Master's Programme, Sustainable Urban Planning and Design, 120 credits"
              'eng': '', 'swe': ''},
    'TIBYH': {'cycle': 1, #  'Högskoleingenjörsutbildning i byggteknik och design', "Degree Programme in Constructional Engineering and Design"
              'eng': 'Constructional Engineering and Design', 'swe': 'Byggteknik och design'},
    'TIDAA': {'cycle': 1, # 'Högskoleingenjörsutbildning i datateknik, Flemingsberg', "Degree Programme in Computer Engineering"
              'eng': 'Computer Science and Engineering', 'swe': 'Datateknik'},
    'TIDAB': {'cycle': 1, # 'Högskoleingenjörsutbildning i datateknik, Kista', "Degree Programme in Computer Engineering"
              'eng': 'Computer Science and Engineering', 'swe': 'Datateknik'},
    'TIDTM': {'cycle': 2, # 'Masterprogram, idrottsteknologi', "Master's Programme, Sports Technology"
              'eng': '', 'swe': ''},
    'TIEDB': {'cycle': 2, # 'Högskoleingenjörsutbildning i elektronik och datorteknik', "Degree Programme in Electronics and Computer Engineering"
              'eng': 'Electronics and Computer Engineering', 'swe': 'Elektronik och datorteknik'},
    'TIEEM': {'cycle': 2, # 'Masterprogram, innovativ uthållig energiteknik', "Master's Programme, Innovative Sustainable Energy Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TIELA': {'cycle': 1, # 'Högskoleingenjörsutbildning i elektroteknik, Flemingsberg', "Degree Programme in Electrical Engineering"
              'eng': '', 'swe': ''},
    'TIEMM': {'cycle': 2, # 'Masterprogram, industriell ekonomi', "Master's Programme, Industrial Engineering and Management, 120 credits"
              'eng': '', 'swe': ''},
    'TIETM': {'cycle': 2, # 'Masterprogram, innovativ energiteknik',  "Master's Programme, Energy Innovation, 120 credits"
              'eng': '', 'swe': ''},
    'TIHLM': {'cycle': 2, # 'Masterprogram, innovativ teknik för en hälsosam livsmiljö', "Master's Programme, Innovative Technology for Healthy Living"
              'eng': '', 'swe': ''},
    'TIIPS': {'cycle': 1, # 'Högskoleingenjörsutbildning i industriell teknik och produktionsunderhåll', "Degree Programme in Industrial Technology and Production Maintenance"
              'eng': '', 'swe': ''},
    'TIKED': {'cycle': 1, # 'Högskoleingenjörsutbildning i kemiteknik', "Degree Programme in Chemical Engineering"
              'eng': '', 'swe': ''},
    'TIMAS': {'cycle': 1, # 'Högskoleingenjörsutbildning i maskinteknik, Södertälje', "Degree Programme in Mechanical Engineering"
              'eng': 'Mechanical Engineering', 'swe': 'Maskinteknik'},
    'TIMBM': {'cycle': 2, # 'Masterprogram, Industriell och miljöinriktad bioteknologi', "Master's Programme, Industrial and Environmental Biotechnology, 120 credits"
              'eng': '', 'swe': ''},
    'TIMEL': {'cycle': 1, # 'Högskoleingenjörsutbildning i medicinsk teknik', "Degree Programme in Medical Technology"
              'eng': '', 'swe': ''},
    'TIMTM': {'cycle': 2, # 'Masterprogram, interaktiv medieteknik', "Master's Programme, Interactive Media Technology, 120 credits"
              'eng': '', 'swe': ''},
    'TINEM': {'cycle': 2, # 'Masterprogram, industriell ekonomi', "Master's Programme, Industrial Management, 120 credits"
              'eng': '', 'swe': ''},
    'TINNM': {'cycle': 2, # 'Masterprogram, information och nätverksteknologi', "Master's Programme, Information and Network Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TIPDM': {'cycle': 2, # 'Masterprogram, integrerad produktdesign', "Master's Programme, Integrated Product Design, 120 credits"
              'eng': '', 'swe': ''},
    'TIPUM': {'cycle': 2, # 'Masterprogram, industriell produktutveckling', "Master's Programme, Engineering Design, 120 credits"
              'eng': '', 'swe': ''},
    'TITEH': {'cycle': 1, # 'Högskoleingenjörsutbildning i teknik och ekonomi', "Degree Programme in Engineering and Economics"
              'eng': '', 'swe': ''},
    'TITHM': {'cycle': 2, # 'Masterprogram, hållbar produktionsutveckling', "Master's Programme, Sustainable Production Development, 120 credits"
              'eng': '', 'swe': ''},
    'TIVNM': {'cycle': 2, # 'Masterprogram, ICT Innovation', "Master's Programme, ICT Innovation, 120 credits"
              'eng':  'Information and Communication Technology', 'swe': 'Informationsteknik'},
    'TJVTM': {'cycle': 2, # 'Masterprogram, järnvägsteknik', "Master's Programme, Railway Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TKEMM': {'cycle': 2, # 'Masterprogram, kemiteknik för energi och miljö', "Master's Programme, Chemical Engineering for Energy and Environment, 120 credits"
              'eng': '', 'swe': ''},
    'TLODM': {'cycle': 2, # 'Magisterprogram, ljusdesign', "Master's Programme,  Architectural Lighting Design, 60 credits"
              'eng': '', 'swe': ''},
    'TMAIM': {'cycle': 2, # 'Masterprogram, maskininlärning', "Master's Programme, Machine Learning, 120 credits"
              'eng': '', 'swe': ''},
    'TMAKM': {'cycle': 2, # 'Masterprogram, matematik', "Master's Programme, Mathematics, 120 credits"
              'eng': '', 'swe': ''},
    'TMBIM': {'cycle': 2, # 'Masterprogram, medicinsk bioteknologi', "Master's Programme, Medical Biotechnology, 120 credits"
              'eng': '', 'swe': ''},
    'TMEGM': {'cycle': 2, # 'Masterprogram, marinteknik', "Master's Programme, Maritime Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TMESM': {'cycle': 2, # 'Masterprogram, miljövänliga energisystem', "Master's Programme, Environomical Pathways for Sustainable Energy Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TMHIM': {'cycle': 2, # 'Masterprogram, miljöteknik och hållbar infrastruktur', "Master's Programme, Environmental Engineering and Sustainable Infrastructure, 120 credits"
              'eng': '', 'swe': ''},
    'TMLEM': {'cycle': 2, # 'Masterprogram, medicinsk teknik', "Master's Programme, Medical Engineering, 120 credits"
              'eng': 'Medical Technology', 'swe': 'Medicinsk teknik'},
    'TMMMM': {'cycle': 2, # 'Masterprogram, makromolekylära material', "Master's Programme, Macromolecular Materials, 120 credits"
              'eng': '', 'swe': ''},
    'TMMTM': {'cycle': 2, # 'Masterprogram, media management', "Master's Programme, Media Management, 120 credits"
              'eng': '', 'swe': ''},
    'TMRSM': {'cycle': 2, # 'Masterprogram, marina system', "Master's Programme, Naval Architecture, 120 credits"
              'eng': '', 'swe': ''},
    'TMTLM': {'cycle': 2, # 'Masterprogram, molekylära tekniker inom livsvetenskaperna', "Master's Programme, Molecular Techniques in Life Science, 120 credits"
              'eng': '', 'swe': ''},
    'TMVTM': {'cycle': 2, # 'Masterprogram, molekylär vetenskap och teknik', "Master's Programme, Molecular Science and Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TNEEM': {'cycle': 2, # 'Masterprogram, kärnenergiteknik', "Master's Programme, Nuclear Energy Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TNTEM': {'cycle': 2, # 'Masterprogram, nanoteknik', "Master's Programme, Nanotechnology, 120 credits"
              'eng': '', 'swe': ''},
    'TPRMM': {'cycle': 2, # 'Masterprogram, industriell produktion', "Master's Programme, Production Engineering and Management, 120 credits"
              'eng': '', 'swe': ''},
    'TSCRM': {'cycle': 2, # 'Masterprogram, systemteknik och robotik', "Master's Programme, Systems, Control and Robotics, 120 credits"
              'eng': '', 'swe': ''},
    'TSEDM': {'cycle': 2, # 'Masterprogram, programvaruteknik för distribuerade system', "Master's Programme, Software Engineering of Distributed Systems, 120 credits"
              'eng': '', 'swe': ''},
    'TSUEM': {'cycle': 2, # 'Masterprogram, hållbar energiteknik', "Master's Programme, Sustainable Energy Engineering, 120 credits"
              'eng': '', 'swe': ''},
    'TSUTM': {'cycle': 2, # 'Masterprogram, teknik och hållbar utveckling', "Master's Programme, Sustainable Technology, 120 credits"
              'eng': '', 'swe': ''},
    'TTAHM': {'cycle': 2, # 'Masterprogram, teknik, arbete och hälsa', "Master's Programme, Technology, Work and Health, 120 credits"
              'eng': 'Technology and Health', 'swe': 'Teknik och hälsa'},
    'TTEMM': {'cycle': 2, # 'Masterprogram, teknisk mekanik', "Master's Programme, Engineering Mechanics, 120 credits"
              'eng': '', 'swe': ''},
    'TTFYM': {'cycle': 2, # 'Masterprogram, teknisk fysik', "Master's Programme, Engineering Physics, 120 credits"
              'eng': 'Engineering Physics', 'swe': 'Teknisk fysik',},
    'TTGTM': {'cycle': 2, # 'Masterprogram, transport och geoinformatik', "Master's Programme, Transport and Geoinformation Technology, 120 credits"
              'eng': '', 'swe': ''},
    'TTMAM': {'cycle': 2, # 'Masterprogram, tillämpad matematik och beräkningsmatematik', "Master's Programme, Applied and Computational Mathematics, 120 credits"
              'eng': '', 'swe': ''},
    'TTMIM': {'cycle': 2, # 'Masterprogram, transport, mobilitet och innovation', "Master's Programme, Transport, Mobility and Innovation"
              'eng': '', 'swe': ''},
    'TTMVM': {'cycle': 2, # 'Masterprogram, teknisk materialvetenskap', "Master's Programme, Engineering Materials Science, 120 credits"
              'eng': '', 'swe': ''},
    'TURSM': {'cycle': 2, # 'Magisterprogram, urbana studier', "Master's Programme, Urbanism Studies, 60 credits
              'eng': '', 'swe': ''},
    #

    # 'eng': 'Electrical Engineering', 'swe': 'Elektroteknik',
    # 'eng': 'Engineering and Economics'. 'swe': '',
    # 'eng': 'Industrial Engineering and Management', 'swe': 'Industriell ekonomi',
    # 'eng': 'Materials Design and Engineering', 'swe': 'Materialdesign',
    # 'eng': 'Microelectronics', 'swe': 'Mikroelektronik',
    # 'eng': 'The Built Environment', 'swe': 'Samhällsbyggnad',

    # 'eng': 'Chemistry and Learning', 'swe': 'Kemi och lärande',
    # 'eng': 'Mathematics and Learning', 'swe': 'Matematik och lärande',
    # 'eng': 'Physics and Learning', 'swe': 'Fysik och lärande',
    # 'eng': 'Technology and Economics', 'swe': 'Teknik och ekonomi',
    # 'eng': 'Technology and Learning', 'swe': 'Teknik och lärande',
    # 'eng': 'Technology and Management', 'swe': 'Teknik och management',
    # 'eng': 'Technology', 'swe': 'Teknik',

}

# for cocmbined Civing. and Master's
# <!-- Subject area (magister) for type 7 (master of science and master-->
program_areas2 = {
    'Architecture': {'eng': 'Architecture', 'swe': 'Arkitektur'},
    'Biotechnology':  {'eng': 'Biotechnology', 'swe': 'Bioteknik'},
    'Computer Science and Engineering': {'eng': 'Computer Science and Engineering', 'swe': 'Datalogi och datateknik'},
    'Electrical Engineering': {'eng':  'Electrical Engineering', 'swe': 'Elektroteknik'},
    'Industrial Management': { 'eng': 'Industrial Management', 'swe': 'Industriell ekonomi'},
    'Information and Communication Technology': { 'eng': 'Information and Communication Technology', 'swe': 'Informations- och kommunikationsteknik'},
    'Chemical Science and Engineering': {'eng': 'Chemical Science and Engineering', 'swe': 'Kemiteknik'},
    'Mechanical Engineering': {'eng': 'Mechanical Engineering', 'swe': 'Maskinteknik'},
    'Mathematics': {'eng' 'Mathematics', 'Matematik'},
    'Materials Science and Engineering': {'eng': 'Materials Science and Engineering', 'swe': 'Materialteknik'},
    'Medical Engineering': {'eng': 'Medical Engineering', 'swe': 'Medicinsk teknik'},
    'Environmental engineering': {'eng': 'Environmental engineering', 'swe': 'Miljöteknik'},
    'The Built Environment': {'eng': 'The Built Environment', 'swe': 'Samhällsbyggnad'},
    'Technology and Economics': {'eng': 'Technology and Economics', 'swe': 'Teknik och ekonomi'},
    'Technology and Health': {'eng': 'Technology and Health', 'swe': 'Teknik och hälsa'},
    'Technology and Learning': {'eng': 'Technology and Learning', 'swe': 'Teknik och lärande'},
    'Technology and Management': {'eng': 'Technology and Management', 'swe': 'Teknik och management'},
    'Engineering Physics': {'eng': 'Engineering Physics', 'swe': 'Teknisk fysik'},
}



# extras contains information from the command line options
def process_cover_from_JSON_file(json_file, extras):
    global Verbose_Flag
    global testing
    global course_id

    with open(json_file, 'r') as event_FH:
        try:
            event_string=event_FH.read()
            d=json.loads(event_string)
        except:
            print("Error in reading={}".format(event_string))
            return

    print("read JSON: {}".format(d))

    # The data dictionary will hold the information 
    data=dict()


    x=extras.get('school_acronym', None)
    if x:
        school_acronym = x
    else:
        school_acronym = None
        # "Examiner1": {"Last name": "Maguire Jr.", "First name": "Gerald Q.", "Local User Id": "u1d13i2c", "E-mail": "maguire@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science ", "L2": "Computer Science"}}
        examiner=d.get('Examiner1')
        if examiner:
            examiner_organisation=examiner.get('organisation', None)
            last_name=examiner.get('Last name', None)
            first_name=examiner.get('First name', None)
            if first_name and last_name:
                data['examiner']=first_name+' '+last_name
            elif not first_name and last_name:
                data['examiner']=last_name
            elif first_name and not last_name:
                data['examiner']=first_name
            else:
                print("Examiner name is unknown: {}".format(examiner))

            if examiner_organisation:
                examiner_L1=examiner_organisation.get('L1', None)
                if examiner_L1:
                    print("examiner_L1={}".format(examiner_L1))
                    for s in schools_info:
                        school_name_swe=schools_info[s]['swe']
                        offset=examiner_L1.find(school_name_swe)
                        if offset >= 0:
                            school_acronym=s
                            break
                        school_name_eng=schools_info[s]['eng']
                        offset=examiner_L1.find(school_name_eng)
                        if offset >= 0:
                            school_acronym=s
                            break
                    if school_acronym is None:
                        print("Unable to determine the school's acronyms from examiner's L1")
                    else:
                        print("school_acronym={0}".format(school_acronym))

    if school_acronym is None:
        print("Unable to determine the school's acronyms")
        return
        
    author_names=list()
    for i in range(1, 10):
        which_author="Author{}".format(i)
        author=d.get(which_author, None)
        if author:
            last_name=author.get('Last name', None)
            first_name=author.get('First name', None)
            if first_name and last_name:
                author_name=first_name+' '+last_name
            elif not first_name and last_name:
                author_name=last_name
            elif first_name and not last_name:
                author_name=first_name
            else:
                print("Author name is unknown: {}".format(author))
            author_names.append(author_name)

    if len(author_names) == 1:
        author_name1=author_names[0]
        author_name2=None
    elif len(author_names) == 2:
        author_name1=author_names[0]
        author_name2=author_names[1]
    else:
        print("Error cannot figure out author(s) name(s)")
        return

    print("author_name1={0}, author_name2={1}".format(author_name1, author_name2))

    # "Title": {"Main title": "This is the title in the language of the thesis", "Subtitle": "An subtitle in the language of the thesis", "Language": "eng"}, "Alternative title": {"Main title": "Detta är den svenska översättningen av titeln", "Subtitle": "Detta är den svenska översättningen av undertiteln", "Language": "swe"}
    title=d.get('Title', None)
    if title:
        thesis_main_title=title.get('Main title', None)
        language=title.get('Language', None)
        if language is None:
            language='eng'
            print("no language specied, guessin English")

        thesis_main_subtitle=title.get('Subtitle', None)

    else:
        print("Cannot figure out title information")
        return

    # "Degree": {"Educational program": "Bachelor’s Programme in Information and Communication Technology"}
    # extended Degree information 
    # "Degree": {"Educational program": "Bachelor’s Programme in Information and Communication Technology", "Level": "1", "Course code": "IA150X", "Credits": "15.0", "Exam": "Bachelors degree", "subjectArea": "Information and Communication Technology"}
    degree=d.get('Degree', None)
    if degree:
        ep=degree.get('Educational program', None)
        if ep:
            x=extras.get('cycle', None) # command line argument takes precedence
            if x:
                cycle = int(x)
            else:
                cycle=degree.get('Level', None)
                if cycle:
                    cycle = int(cycle)
                else:
                    cycle=cycle_of_program(ep)
                    if cycle:
                        cycle=int(cycle)
                    else:
                        print("Unable to determine cycle number")
                        return

            x=extras.get('number_of_credits', None) # command line argument takes precedence
            if x:
                number_of_credits = float(x)
            else:
                number_of_credits=degree.get('Credits', None)
                if number_of_credits:
                    number_of_credits=float(number_of_credits)
                else:
                    if cycle == 1:
                        number_of_credits=15.0
                    elif cycle == 2:
                        number_of_credits=30.0
                    else:
                        number_of_credits=None
                        print("Cannot guess number_of_credits")
                        return

            prgcode=programcode_from_degree(ep)
            print("degree={0}, cycle={1}, ep={2}, prgcode={3}".format(degree, cycle, ep, prgcode))

            x=extras.get('area', None) # command line argument takes precedence
            if x:
                area = x
            else:
                area = degree.get('subjectArea', None)
                if not area:
                    if prgcode:
                        area_dict=program_areas.get(prgcode, None)
                        if area_dict:
                            area=area_dict.get(language, None)
                            if not area:
                                print("Could not figure out area")

            # note that here "exam" is the exam codes used by the cover generator
            x=extras.get('exam', None)		# command line argument takes precedence
            if x and x in [1, 2, 3, 4, 5, 6, 7, 8]:
                exam = x
            else:
                exam_name=degree.get('Exam', None)
                if cycle == 1:
                    if exam_name == 'Bachelors degree' or exam_name == 'Higher Education Diploma' or exam_name == 'Kandidatexamen' or exam_name == 'Högskoleexamen':
                        exam=1
                    elif exam_name == 'Degree of Bachelor of Science in Engineering' or exam_name == 'Högskoleingenjörsexamen':
                        exam=2
                    elif exam_name == 'Degree of Master of Science in Secondary Education' or exam_name == 'Ämneslärarexamen':
                        exam=8
                    else:
                        print("Error in first cycle exam information - could not guess")
                elif cycle == 2:
                    if exam_name == 'Degree of Master (60 credits)' or exam_name == 'Degree of Master (120 credits)' or exam_name == 'Magisterexamen' or exam_name == 'Masterexamen':
                        exam=3
                    elif exam_name == 'Degree of Master of Science in Engineering' or exam_name == 'Civilingenjörsexamen':
                        exam=4
                    elif exam_name == 'Degree of Master of Architecture' or exam_name == 'Arkitektexamen':
                        exam=5
                    elif exam_name == 'Degree of Master of Science in Secondary Education' or exam_name == 'Ämneslärarexamen':
                        exam=6
                    elif exam_name == 'Both Master of science in engineering and Master' or exam_name == 'Civilingenjörs- och masterexamen':
                        exam=7
                    else:
                        print("Error in second cycle exam information - could not guess")
                else:
                    print("Error in exam {0} information={1}".format(exam))
                    
            # case of two degrees, get the second subject area
            if exam == '7':
                x=extras.get('area2', None)	# command line argument takes precedence
                area2=x
            else:
                area2=degree.get('secondSubjectArea', None)
                
    # {"Author1": {"Last name": "Rosquist", "First name": "Oscar", 
    #              "organisation": {"L1": "School of Electrical Engineering and Computer Science "}},
    # "Degree": {"Educational program": "Degree Programme in Computer Science and Engineering"},
    # "Title": {"Main title": "Adapting to the new remote work era",
    #           "Subtitle": "Improving social well-being among IT remote workers",
    #           "Language": "eng"},
    # "Examiner1": {"Last name": "Maguire Jr.", "First name": "Gerald Q.", 
    #               "organisation": {"L1": "School of Electrical Engineering and Computer Science ", "L2": "Computer Science"}},
    # "Other information": {"Year": "2021", "Number of pages": "xvii,115"},    

    other_info=d.get('Other information', None)
    if other_info:
        year=other_info.get('Year', None)
        
    x=extras.get('trita', None)
    if x:
        trita = x
    else:
        trita = None

    if Verbose_Flag:
        print("language={0}, cycle={1}, number_of_credits={2}, exam={3}, area={4}, area2={5}, author_name1={6}, author_name2={7}, thesis_main_title={8}, thesis_main_subtitle={9}, school_acronym={10}, year={11}, trita={12}".format(language, cycle, number_of_credits, exam, area, area2, author_name1, author_name2, thesis_main_title, thesis_main_subtitle, school_acronym, year, trita))

    create_cover(language, cycle, number_of_credits, exam, area, area2, author_name1, author_name2, thesis_main_title, thesis_main_subtitle, school_acronym, year, trita)



def main(argv):
    global Verbose_Flag
    global testing
    global course_id


    argp = argparse.ArgumentParser(description="JSON_to_cover.py: to make a thesis cover")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")

    argp.add_argument("-c", "--canvas_course_id", type=int,
                      # required=True,
                      help="canvas course_id")

    argp.add_argument('-C', '--containers',
                      default=False,
                      action="store_true",
                      help="for the container enviroment in the virtual machine, uses http and not https")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('-j', '--json',
                      type=str,
                      default="event.json",
                      help="JSON file for extracted data"
                      )

    argp.add_argument('--cycle',
                      type=int,
                      help="cycle of thesis"
                      )

    argp.add_argument('--credits',
                      type=float,
                      help="number_of_credits of thesis"
                      )

    argp.add_argument('--exam',
                      type=int,
                      help="type of exam"
                      )

    argp.add_argument('--area',
                      type=str,
                      help="area of thesis"
                      )

    argp.add_argument('--area2',
                      type=str,
                      help="area of thesis for combined Cinving. and Master's"
                      )

    argp.add_argument('--trita',
                      type=str,
                      help="trita string for thesis"
                      )

    argp.add_argument('--school',
                      type=str,
                      help="school acronym"
                      )

    argp.add_argument('--file',
                      type=str,
                      help="thesis PDF without For DIVA pages"
                      )

    argp.add_argument('--diva',
                      type=int,
                      help="Number of For DiVA pages to remove"
                      )


    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    # If there is a course number argument, then initializae in prepartion for Canvas API calls
    x=args["canvas_course_id"]
    if x:
        initialize(args)
        if Verbose_Flag:
            print("baseUrl={}".format(baseUrl))

    course_id=args["canvas_course_id"]
    print("course_id={}".format(course_id))

    testing=args["testing"]
    print("testing={}".format(testing))

    extras=dict()

    x=args['cycle']
    if x:
        extras['cycle']=x

    x=args['credits']
    if x:
        extras['credits']=x

    x=args['exam']
    if x:
        extras['exam']=x

    x=args['area']
    if x:
        extras['area']=x

    x=args['area2']
    if x:
        extras['area2']=x

    x=args['trita']
    if x:
        extras['trita']=x

    x=args['school']
    if x:
        extras['school_acronym']=x

    json_filename=args["json"]
    if json_filename:
        process_cover_from_JSON_file(json_filename, extras)
    else:
        print("Unknown source for the event: {}".format(event_input_type))


    x=args['file']
    if x:
        # check that file ends with .pdf
        if x.endswith('.pdf'):
            print("file to be processed is {}".format(x))
            # remove For Diva pages - requires a command line argument with the number of pages to remove
            d=args['diva']
            if d:
                page_range="1-r{}".format(d+1)
            else:
                page_range="1-z"
            # apply cover
            try:
                cmd1 = subprocess.run(['qpdf', x, '--pages', 'cover_pages-1', './'+x, page_range, 'cover_pages-2', '--', x[0:-4]+'-with-cover.pdf'], capture_output=True)
            except:
                sys.stdout.buffer.write(command.stdout)
                sys.stderr.buffer.write(command.stderr)
                sys.exit(cmd1.returncode)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

