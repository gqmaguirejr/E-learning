#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_calendar.py -c course_id [--nocortina] --event 0|2|3 [--json file.json] [--mods file.mods]
#
# Purpose: The program creates an event entry:
#             from a JSON file (input event type 0),
#             from a MODS file (input event type 3), or
#             from fixed data (input event type 2).
#
# This event will be inserted into the KTH Cortina Calendar (unless the --nocortina flag is set or the user does not have a Cortina access key).
# The program also generates an announcement in the indicated Canvas course room and creates a calendar entry in the Canvas calendar for this course room.
#
#  It can also modify (using PUT) an existing Cortina Calendar entry.
#
# Example:
#  enter a fixed event
# ./JSON_to_calendar.py -c 11 --event 2
# ./JSON_to_calendar.py -t -v -c 11 --config config-test.json
#
#  enter events from a MODS file
# ./JSON_to_calendar.py -t -v -c 11 --config config-test.json --event 3 --mods theses.mods
# ./JSON_to_calendar.py -c 11 --config config-test.json --event 3 --mods t1.mods  --nocortina
#
#  enter event from a JSON file
# ./JSON_to_calendar.py -c 11  --json event.json
# ./JSON_to_calendar.py -c 11 --config config-test.json  --json event.json
# ./JSON_to_calendar.py -c 11 --config config-test.json  --json event.json  --nocortina
#
#
# Once I get the above working, then my plan is to make several programs that can feed it data:
# 1. to take data from DiVA for testing with earlier presentations (so I can generate lots of tests)
# 2. to extract data from my augmented PDF files (which have some of the JSON at the end)
# 3. to extract data from a Overleaf ZIP file that uses my thesis template
# 4. to extract data from a DOCX file that uses my thesis tempalte
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-04-22 G. Q. Maguire Jr.
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

#############################
###### EDIT THIS STUFF ######
#############################

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests
global cortina_baseUrl
global cortina_seminarlist_base_Url
global cortina_header 

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(args):
    global baseUrl, header, payload
    global cortina_baseUrl, cortina_header, cortina_seminarlist_base_Url
    global nocortina

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


            if configuration.get('KTH_Calendar_API') and configuration['KTH_Calendar_API'].get('host') and configuration['KTH_Calendar_API'].get('key'):
                cortina_baseUrl=configuration['KTH_Calendar_API']['host']+"/v1/seminar"
                cortina_seminarlist_base_Url=configuration['KTH_Calendar_API']['host']+"/v1/seminarlist"
                api_key=configuration['KTH_Calendar_API']['key']
                cortina_header={'api_key': api_key, 'Content-Type': 'application/json'}
                nocortina=False
            else:
                cortina_baseUrl=None
                cortina_seminarlist_base_Url=None
                cortina_header=None
                nocortina=True

    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()

# Canvas API related functions
def list_of_accounts():
    global Verbose_Flag
    
    entries_found_thus_far=[]

    # Use the Canvas API to get the list of accounts this user can see
    # GET /api/v1/accounts
    url = "{0}/accounts".format(baseUrl)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100'}
    r = requests.get(url, params=extra_parameters, headers = header)

    if Verbose_Flag:
        print("result of getting accounts: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            entries_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            if Verbose_Flag:
                print("result of getting accounts for a paginated response: {}".format(r.text))
            page_response = r.json()  
            for p_response in page_response:  
                entries_found_thus_far.append(p_response)

    return entries_found_thus_far

# Announcements
# Announcements are a special type of discussion in Canvas
# The GUI to create and announcement is of the form ttps://canvas.kth.se/courses/:course_id/discussion_topics/new?is_announcement=true
#

def post_canvas_announcement(course_id, title, message):
    global Verbose_Flag
    
    # Use the Canvas API to Create a new discussion topic
    # POST /api/v1/courses/:course_id/discussion_topics
    url = "{0}/courses/{1}/discussion_topics".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    # title		string	no description
    # message		string	no description
    # is_announcement		boolean	If true, this topic is an announcement. It will appear in the announcement's section rather than the discussions section. This requires announcment-posting permissions.
    # specific_sections		string	A comma-separated list of sections ids to which the discussion topic should be made specific to. If it is not desired to make the discussion topic specific to sections, then this parameter may be omitted or set to “all”. Can only be present only on announcements and only those that are for a course (as opposed to a group).

    extra_parameters={'is_announcement': True,
                      'title':           title,
                      'message':	 message
                      }
    r = requests.post(url, params=extra_parameters, headers = header)

    if Verbose_Flag:
        print("result of posting an announcement: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    else:
        return r.status_code

# Cortina
type_of_seminars=['dissertation', 'licentiate', 'thesis']
schools=['ABE', 'EECS', 'ITM', 'CBH', 'SCI']
departments={"EECS":
             {'CS':  "Datavetenskap",
              'EE':  "Elektroteknik",
              'IS':  "Intelligenta system",
              'MKT': "Människocentrerad teknologi"}}

def post_to_Cortina(seminartype, school, data):
    global Verbose_Flag

    # Use the Cortina Calendar API - to create a new seminar event
    # POST ​/v1​/seminar​/{seminartype}​/{school}
    url = "{0}/{1}/{2}".format(cortina_baseUrl, seminartype, school)
    if Verbose_Flag:
        print("url: {}".format(url))
    r = requests.post(url, headers = cortina_header, json=data)

    if Verbose_Flag:
        print("result of post_to_Cortina: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return r.status_code

def put_to_Cortina(seminartype, school, content_id, data):
    global Verbose_Flag

    # Use the Cortina Calendar API - to create a new seminar event
    # POST ​/v1​/seminar​/{seminartype}​/{school}
    url = "{0}/{1}/{2}/{3}".format(cortina_baseUrl, seminartype, school, content_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    r = requests.put(url, headers = cortina_header, json=data)

    if Verbose_Flag:
        print("result of put_to_Cortina: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return r.status_code

def get_from_Cortina(seminartype, school, content_id):
    global Verbose_Flag

    # Use the Cortina Calendar API - to Get seminar event
    # GET ​/v1​/seminar​/{seminartype}​/{school}​/{contentId}
    url = "{0}/{1}/{2}/{3}".format(cortina_baseUrl, seminartype, school, content_id)
    if Verbose_Flag:
        print("url: {}".format(url))
    r = requests.get(url, headers = cortina_header)

    if Verbose_Flag:
        print("result of get_from_Cortina: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return r.status_code

# https://api-r.referens.sys.kth.se/api/cortina-calendar/v1/seminarlist/thesis/EECS/Datavetenskap/2021
# https://api-r.referens.sys.kth.se/api/cortina-calendar/v1/seminar​list​/thesis/EECS/Datavetenskap/2021
def get_seminarlist_from_Cortina(seminartype, school, department, year):
    global Verbose_Flag

    # Use the Cortina Calendar API - to Get seminar event
    # GET ​/v1​/seminar​/{seminartype}​/{school}​/{department}/{year}
    url = "{0}/{1}/{2}/{3}/{4}".format(cortina_seminarlist_base_Url, seminartype, school, department, year)
    if Verbose_Flag:
        print("url: {}".format(url))
    r = requests.get(url, headers = cortina_header)

    if Verbose_Flag:
        print("result of get_seminarlist_from_Cortina: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return r.status_code

# Canvas related functions

def create_calendar_event(course_id, start, end, title, description, location_name, location_address):
    # Use the Canvas API to get the calendar event
    # POST /api/v1/calendar_events
    url = "{0}/calendar_events".format(baseUrl)
    if Verbose_Flag:
        print("url: " + url)

    context_code="course_{}".format(course_id) # note that this established the course content
    print("context_code={}".format(context_code))

    payload={'calendar_event[context_code]': context_code,
             'calendar_event[title]': title,
             'calendar_event[description]': description,
             'calendar_event[start_at]': start,
             'calendar_event[end_at]':   end
    }

    # calendar_event[location_name]		string	Location name of the event.
    # calendar_event[location_address]		string	Location address

    if location_name:
        payload['location_name']=location_name
    if location_address:
        payload['location_address']=location_address

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of creating a calendar event: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    else:
        print("status code={}".format(r.status_code))
    return None
    
def get_calendar_event(calendar_event_id):
       # Use the Canvas API to get the calendar event
       #GET /api/v1/calendar_events/:id
       url = "{0}/calendar_events/{1}".format(baseUrl, calendar_event_id)
       if Verbose_Flag:
              print("url: " + url)

       r = requests.get(url, headers = header)
       if Verbose_Flag:
              print("result of getting a single calendar event: {}".format(r.text))

       if r.status_code == requests.codes.ok:
              page_response=r.json()
              return page_response

       return None

required_keys=['advisor',
                'contentId',
                'contentName',
                'dates_endtime',
                'dates_starttime',
                'lead',
                'lecturer',
                'location',
                'opponent',
                'organisation',
                'respondent',
                'respondentUrl',
                'respondentDepartment',
                'seminartype',
                'subjectarea',
                'paragraphs_text',
                'uri']
    
swagger_keys=["contentId",
              "seminartype",
              "organisation",
              "dates_starttime",
              "dates_endtime",
              "contentName",
              "lead",
              "paragraphs_text",
              "advisor",
              "lecturer",
              "opponent",
              "respondent",
              "respondentDepartment",
              "location",
              "uri",
              "subjectarea"]

def check_for_extra_keys(data):
    print("Checking for extra keys")
    for key, value in data.items():
        if key not in required_keys:
            print("extra key={0}, value={1}".format(key, value))

def check_for_extra_keys_from_Swagger(data):
    print("Checking for extra keys from Swagger")
    for key, value in data.items():
        if key not in swagger_keys:
            print("extra key={0}, value={1}".format(key, value))



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
                # end of processing a name
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
                            else:
                                if Verbose_Flag:
                                    print("mod_emem[{0}]={1}".format(i, elem))

                # skip this:
                elif current_element.tag.count("}language") == 1:
                    objectPart=current_element.attrib.get('objectPart', None)
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}languageTerm") == 1:
                            type=elem.attrib.get('type', None)
                            if type == 'code' and objectPart == 'defence':
                                pub_info['defence_language']=elem.text
                            if type == 'code' and objectPart is None:
                                pub_info['thesis_language']=elem.text

                
                elif current_element.tag.count("}originInfo") == 1:
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}dateIssued") == 1:
                            if elem.text is not None:
                                pub_info['dateIssued']=elem.text
                        elif elem.tag.count("}dateOther") == 1:
                            if elem.text is not None:
                                if Verbose_Flag:
                                    print("dateOther: {0} {1}".format(elem.attrib, elem.text))
                                if pub_info.get('dateOther', None) is None:
                                    pub_info['dateOther']=dict()
                                dateOther_type=elem.attrib.get('type', None)
                                pub_info['dateOther'][dateOther_type]=elem.text
                        else:
                            if Verbose_Flag:
                                print("mod_emem[{0}]={1}".format(i, elem))

                elif current_element.tag.count("}physicalDescription") == 1:
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if pub_info.get('physicalDescription', None) is None:
                            pub_info['physicalDescription']=dict()
                        if elem.tag.count("}form") == 1:
                            if elem.text is not None:
                                pub_info['physicalDescription']['form']=elem.text
                        elif elem.tag.count("}extent") == 1:
                            if elem.text is not None:
                                pub_info['physicalDescription']['extent']=elem.text
                        else:
                            if Verbose_Flag:
                                print("physicalDescription elem[{0}]={1}".format(i, elem))


                elif current_element.tag.count("}identifier") == 1:
                    if current_element.text is not None:
                        identifier_type=current_element.attrib.get('type', None)
                        if identifier_type == 'uri':
                            pub_info['thesis_uri']=current_element.text
                        elif identifier_type == 'isbn':
                            pub_info['thesis_isbn']=current_element.text
                        else:
                            print("Unhandled identifier: {0} of type {1}".format(current_element.text, identifier_type))

                elif current_element.tag.count("}abstract") == 1:
                    abstract_lang=current_element.attrib.get('lang', None)
                    if abstract_lang is None:
                        print("No language for abstract={}".format(current_element.text))
                    else:
                        if pub_info.get('abstract', None) is None:
                            pub_info['abstract']=dict()
                        if current_element.text is not None:
                            pub_info['abstract'][abstract_lang]=current_element.text
                            if Verbose_Flag:
                                print("Abstract: {0} {1}".format(abstract_lang, current_element.text))


                elif current_element.tag.count("}subject") == 1:
                    if len(current_element.attrib) > 0:
                        if Verbose_Flag:
                            print("subject attributes={}".format(current_element.attrib))
                        current_subject_language=current_element.attrib.get('lang', None)
                        authority=current_element.attrib.get('authority', None)
                        xlink=current_element.attrib.get('{http://www.w3.org/1999/xlink}href', None)
                        if xlink:
                            if Verbose_Flag:
                                print("xlink={}".format(xlink))
                            list_of_HSV_codes.add(xlink) # the codes are the same independent of the language
                        if Verbose_Flag:
                            print("current_subject_language={}".format(current_subject_language))
                        if Verbose_Flag:
                            if len(current_element.attrib) > 0:
                                if Verbose_Flag:
                                    print("subject: {0} {1} {2}".format(current_element.tag, current_element.text, current_element.attrib))
                            else:
                                print("subject: {0} {1}".format(current_element.tag, current_element.text))

                        for j in range(0, len(current_element)):
                            elem=current_element[j]
                            if elem.tag.count("}topic") == 1:
                                if elem.text is not None:
                                    if current_subject_language:
                                        if authority == 'hsv':
                                            add_word_to_dictionary(list_of_HSV_subjects, current_subject_language, elem.text)
                                        else:
                                            add_word_to_dictionary(list_of_topics, current_subject_language, elem.text)
                                    else:
                                        print("no language specified for subject, topic is: {}".format(elem.text))

                                    if Verbose_Flag:
                                        print("topic: {0} {1}".format(elem.tag, elem.text))

                            else:
                                if Verbose_Flag:
                                    print("mod_emem[{0}]={1}".format(i, elem))

                elif current_element.tag.count("}recordInfo") == 1:
                    if Verbose_Flag:
                        print("recordInfo: {}".format(current_element))
                        for j in range(0, len(current_element)):
                            elem=current_element[j]
                            if elem.tag.count("}recordOrigin") == 1:
                                if elem.text is not None:
                                    thesis_recordOrigin=elem.text
                                    pub_info['recordOrigin']=elem.text
                            elif elem.tag.count("}recordContentSource") == 1:
                                if elem.text is not None:
                                    pub_info['recordContentSource']=elem.text
                            elif elem.tag.count("}recordCreationDate") == 1:
                                if elem.text is not None:
                                    pub_info['recordCreationDate']=elem.text
                            elif elem.tag.count("}recordChangeDate") == 1:
                                if elem.text is not None:
                                    pub_info['recordChangeDate']=elem.text
                            elif elem.tag.count("}recordIdentifier") == 1:
                                if elem.text is not None:
                                    pub_info['recordIdentifier']=elem.text
                            else:
                                if Verbose_Flag:
                                    print("mod_emem[{0}]={1}".format(i, elem))
                

                elif current_element.tag.count("}note") == 1:
                    type=current_element.attrib.get('type', None)
                    lang=current_element.attrib.get('lang', None)
                    if type == 'level':
                        add_word_to_dictionary(level, lang, current_element.text)
                    elif type == 'universityCredits':
                        add_word_to_dictionary(universityCredits, lang, current_element.text)
                    elif type == 'venue':
                        pub_info['venue']=current_element.text
                    elif type == 'cooperation':
                        pub_info['cooperation']=current_element.text
                    elif type == 'degree':
                        pub_info['degree']=current_element.text
                    elif type == 'funder':
                        pub_info['funder']=current_element.text
                    elif type == 'thesis':
                        pub_info['thesis_note']=current_element.text
                    elif type == 'papers':
                        pub_info['papers_note']=current_element.text
                    elif type == 'project':
                        pub_info['project']=current_element.text
                    elif type == 'publicationChannel':
                        pub_info['publicationChannel']=current_element.text
                    elif type == None:
                        if Verbose_Flag:
                            print("note type of None")
                    else:
                        print("unknown note type={0} {1}".format(type, current_element.text))

                elif current_element.tag.count("}typeOfResource") == 1:
                    if Verbose_Flag:
                        print("typeOfResource: {0} {1}".format(current_element.tag, current_element.text))
                    pub_info['typeOfResource']=current_element.text

                elif current_element.tag.count("}relatedItem") == 1:
                    relatedItem=current_element.attrib.get('type', None)
                    for j in range(0, len(current_element)):
                        elem=current_element[j]
                        if elem.tag.count("}titleInfo") == 1:
                            for k in range(0, len(elem)):
                                relatedItem_titleInfo=elem[k]
                                if relatedItem_titleInfo.tag.count("}title") == 1:
                                    if relatedItem_titleInfo.text is not None:
                                        if pub_info.get('relatedItem', None) is None:
                                            pub_info['relatedItem']=dict()
                                        pub_info['relatedItem']['title']=relatedItem_titleInfo.text
                        elif elem.tag.count("}identifier") == 1:
                            relatedItem_id_type=elem.attrib.get('type', None)
                            if pub_info.get('relatedItem', None) is None:
                                pub_info['relatedItem']=dict()
                            if pub_info['relatedItem'].get('identifier', None) is None:
                                pub_info['relatedItem']['identifier']=dict()
                            pub_info['relatedItem']['identifier'][relatedItem_id_type]=elem.text
                            if Verbose_Flag:
                                print("relatedItem {0} {1}".format(relatedItem_id_type, elem.text))
                        else:
                            if Verbose_Flag:
                                print("Unknown relatedItem elem{0}]={1}".format(i, elem))

            if authors:
                pub_info['authors']=authors
            if supervisors:
                pub_info['supervisors']=supervisors
            if examiners:
                pub_info['examiners']=examiners
            if opponents:
                pub_info['opponents']=opponents

            if list_of_topics:
                pub_info['keywords']=list_of_topics

            if list_of_HSV_subjects:
                pub_info['HSV_subjects']=list_of_HSV_subjects

            if list_of_HSV_codes:
                pub_info['HSV_codes']=list_of_HSV_codes

            if level:
                pub_info['level']=level
            if universityCredits:
                pub_info['universityCredits']=universityCredits

            if Verbose_Flag:
                print("pub_info is {}".format(pub_info))
            #df2 = pd.DataFrame(record) 
            #print("df for record is {}".format(df2))

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

def expand_school_name(school):
    si=schools_info.get(school, None)
    if si:
        return schools_info[school]['eng']
    else:
        return "Unknown"
    

def process_events_from_MODS_file(mods_filename):
    global testing
    global course_id
    global nocortina

    try:
        with open(mods_filename, "rb") as mods_data_file:
            tree=load_xmlobject_from_file(mods_data_file, mods.MODS)
            xml=BeautifulSoup(mods_data_file, 'lxml-xml')

    except:
        print("Unable to open mods file named {}".format(mods_filename))
        print("Please create a suitable mods file, the default name is theses.mods")
        sys.exit()


    if mods_filename:
        #tree.node
        #<Element {http://www.loc.gov/mods/v3}modsCollection at 0x34249b0>
        #>>> tree.node[1]
        #<Element {http://www.loc.gov/mods/v3}mods at 0x3d46aa0>
        json_records=extract_list_of_dicts_from_mods(tree)
        if Verbose_Flag:
            print("json_records={}".format(json_records))

        for i in range(0, len(json_records)):
            record=json_records[i]

            data=dict()
            data['contentId']=''

            typeOfDocument=record.get('genre_publicationTypeCode', None)
            
            if typeOfDocument == 'studentThesis':
                data['seminartype']='thesis'
            elif typeOfDocument in ['comprehensiveDoctoralThesis',
                                                      'comprehensiveLicentiateThesis',
                                                      'monographDoctoralThesis',
                                                      'monographLicentiateThesis']:
                continue
            else:
                print("Unexpected type of document={}".format(typeOfDocument))
                continue

            # 2021-01-28T13:00:00
            dateother=record.get('dateOther', None)
            if dateother:
                oral_presentation_date_time=dateother.get('defence', None)
                if oral_presentation_date_time:
                    local_start=datetime.datetime.fromisoformat(oral_presentation_date_time)
                    utc_datestart=local_to_utc(local_start).isoformat()+'.000Z'
                    local_end=local_start+datetime.timedelta(hours = 1.0)
                    utc_dateend=local_to_utc(local_end).isoformat()+'.000Z'
                    data['dates_starttime']=utc_datestart
                    data['dates_endtime']=utc_dateend
                else:
                    continue    # If there is no date, then there is no point in trying to put an entry in the calendar
            else:
                continue        # If there is no date, then there is no point in trying to put an entry in the calendar

            series=record['relatedItem']['title']
            if series.find('ABE') > 0:
                school='ABE'
            elif series.find('CBH') > 0:
                school='CBH'
            elif series.find('EECS') > 0:
                school='EECS'
            elif series.find('ITM') > 0:
                school='ITM'
            elif series.find('SCI') > 0:
                school='SCI'
            else:
                school='Unknown'
                print("Unknown series={}".format(series))

            authors_names=[x['name'] for x in record['authors']]
            data['lecturer']=' & '.join(authors_names)
            data['respondent']="" 			# must be present but empty
            data['respondentDepartment']=""		# must be present but empty

            if record.get('opponents', None):
                opponents_names=[x['name'] for x in record['opponents']]
                data['opponent']=' & '.join(opponents)
            else:
                data['opponent']="TBA"   		# we do not know the opponents from the DiVA record

            # 'supervisors': [{'name': 'Anders Västberg', 'kthid': 'u1ft3a12', 'affiliation': 'KTH, ...}]
            supervisr_names=[x['name'] for x in record['supervisors']]
            data['advisor']=' & '.join(supervisr_names)

            examiners_names=[x['name'] for x in record['examiners']]
            # for the momement do not add examiner - until the API supports it
            # data['examiner']=' & '.join(examiners_names)

            # take organisation from examiner's affiliation
            examiners_affiliation=[x['affiliation'] for x in record['examiners']]
            if examiners_affiliation:
                examiners_affiliation_text=' & '.join(examiners_affiliation)
                print("examiners_affiliation_text={}".format(examiners_affiliation_text))
                if examiners_affiliation_text.find('Computer Science') > 0:
                    department='Datavetenskap'
                elif examiners_affiliation_text.find('Electrical Engineering') > 0:
                    department='Elektroteknik'
                elif examiners_affiliation_text.find('Human Centered Technology') > 0:
                    department='Människocentrerad teknologi'
                elif examiners_affiliation_text.find('Intelligent Systems') > 0:
                    department='Intelligenta system'
                elif examiners_affiliation_text == 'KTH, Kommunikationssystem, CoS':
                    department='Datavetenskap'
                elif examiners_affiliation_text == 'KTH, Tal-kommunikation':
                    department='Datavetenskap'
                else:
                    department='Unknown'
               
                data['organisation']= { "school": school,
                                        "department": department }
            else:
                data['organisation']={"school": school,
                                      "department": "Unknown" }

                    

            # 'thesis_title': {'eng': '2D object detection and semantic segmentation in the Carla simulator', 'alternative': {'swe': '2D-objekt detektering och semantisk segmentering i Carla-simulatorn'}}
            # "contentName": {
            # "en_GB": "UAV Navigation using Local Computational Resources: Keeping a target in sight",
            # "sv_SE": "UAV Navigering med Lokala Beräkningsresurser: Bevara ett mål i sensorisk räckvidd"
            # },
            
            thesis_title=record['thesis_title']
            thesis_main_title_lang=None
            thesis_secondary_title_lang=None
            thesis_secondary_title=None

            # note that here were are only supporting a main or secondary language of eng or swe
            # as the Cortina Calendar API is only supporting thwse two languages (as  en_GB and sv_SE
            # case of an English primary title and possible Swedish alternative title
            thesis_main_title=thesis_title.get('eng', None)
            if thesis_main_title:
                thesis_main_title_lang='eng'
                thesis_secondary_title_alternative=thesis_title.get('alternative', None)
                if thesis_secondary_title_alternative:
                    thesis_secondary_title=thesis_secondary_title_alternative.get('swe', None)
                    if thesis_secondary_title:
                        thesis_secondary_title_lang='swe'
            else:
                # case of an Swedish primary title and possible English alternative title
                thesis_main_title=thesis_title.get('swe', None)
                if thesis_main_title:
                    thesis_main_title_lang='swe'
                    thesis_secondary_title_alternative=thesis_title.get('alternative', None)
                    if thesis_secondary_title_alternative:
                        thesis_secondary_title=thesis_secondary_title_alternative.get('eng', None)
                        if thesis_secondary_title:
                            thesis_secondary_title_lang='eng'

            # If no secondary title, use the primary title
            if not thesis_secondary_title:
                thesis_secondary_title=thesis_main_title

            if not thesis_main_title_lang:
                print("language of main title is not eng or swe, I'm dazed and confused")
            else:
                if thesis_main_title_lang == 'eng':
                    data['contentName']={'en_GB': thesis_main_title,
                                         'sv_SE': thesis_secondary_title
                                         }
                else:
                    data['contentName']={'en_GB': thesis_secondary_title,
                                         'sv_SE': thesis_main_title
                                         }

            # from level and credits we can determine if it is a 1st or 2nd cycle thesis
            # 'level': {'swe': ['Självständigt arbete på avancerad nivå (masterexamen)']}, 'universityCredits': {'swe': ['20 poäng / 30 hp']}}, {'node': [1], 'thesis_title': {'eng': '3D Human Pose and Shape-aware Modelling', 'alternative': {'swe': 'Modellering av mänskliga poser och former i 3D'}}
            # "Level": {
            #     // Level field:
            #     // <option value="H1">Independent thesis Advanced level (degree of Master (One Year))</option>
            #     // <option value="H2">Independent thesis Advanced level (degree of Master (Two Years))</option>
            #     // <option value="H3">Independent thesis Advanced level (professional degree)</option>
            #     // <option value="M2">Independent thesis Basic level (degree of Bachelor)</option>
            #     // <option value="M3">Independent thesis Basic level (professional degree)</option>
            #     // <option value="M1">Independent thesis Basic level (university diploma)</option>
            #     // <option value="L1">Student paper first term</option>
            #     // <option value="L3">Student paper other</option>
            #     // <option value="L2">Student paper second term</option>
            #     'Independent thesis Advanced level (degree of Master (One Year))': 'H1',
            #     'Independent thesis Advanced level (degree of Master (Two Years))': 'H2',
            #     'Independent thesis Advanced level (professional degree)': 'H3',
            #     'Independent thesis Basic level (degree of Bachelor)': 'M2',
            #     'Independent thesis Basic level (professional degree)': 'M3',
            #     'Independent thesis Basic level (university diploma)': 'M1',
            #     'Student paper first term': 'L1',
            #     'Student paper other': 'L3',
            #     'Student paper second term': 'L2'
            # },
            # "University credits": {
            #     '7,5 HE credits':	'5',
            #     '10 HE credits':	'7',
            #     '12 HE credits':	'8',
            #     '15 HE credits':	'10',
            #     '18 HE credits':	'12',
            #     '22,5 HE credits':	'15',
            #     '16 HE credits':	'16',
            #     '20 HE credits':	'17',
            #     '30 HE credits': 	'20',
            #     '37,5 HE credits':	'25',
            #     '45 HE credits':	'30',
            #     '60 HE credits':	'40',
            #     '90 HE credits':	'60',
            #     '120 HE credits':	'80',
            #     '180 HE credits':	'120',
            #     '210 HE credits':	'140',
            #     '240 HE credits':	'160',
            #     '300 HE credits':	'200',
            #     '330 HE credits':	'220',
            # },
            # "lead": {
            #     "en_GB": "Master's thesis presentation",
            #     "sv_SE": "Examensarbete presentation"
            # }

            level=record.get('level', None)
            universityCredits=record.get('universityCredits', None)
            if level:
                print("level={}".format(level))
            if universityCredits:
                print("universityCredits={}".format(universityCredits))

            level_swedish=level.get('swe', None)
            if level_swedish:
                if len(level_swedish) > 0:
                    if level_swedish[0].find('grundnivå') > 0:
                        data['lead']={
                            'en_GB': "Bachelor's thesis presentation",
                            'sv_SE': "Kandidate Examensarbete presentation"
                        }
                    else:
                        data['lead']={
                            'en_GB': "Master's thesis presentation",
                            'sv_SE': "Examensarbete presentation"
                        }
                else:
                    if level_swedish.find('grundnivå') > 0:
                        if level_swedish.find('grundnivå') > 0:
                            data['lead']={
                                'en_GB': "Bachelor's thesis presentation",
                                'sv_SE': "Kandidate Examensarbete presentation"
                            }
                        else:
                            data['lead']={
                                'en_GB': "Master's thesis presentation",
                                'sv_SE': "Examensarbete presentation"
                            }
                        
            venue=record.get('venue', None)
            if venue:
                print("venue={}".format(venue))
                data['location']=venue
            else:
                data['location']="Unknown location"


            # pub_info['keywords']=list_of_topics
            # pub_info['HSV_subjects']=list_of_HSV_subjects
            # pub_info['HSV_codes']=list_of_HSV_codes

            keywords_eng_text=''
            keywords_swe_text=''

            list_of_topics=record.get('keywords', None)
            if Verbose_Flag:
                print("list_of_topics={}".format(list_of_topics))
            if list_of_topics:
                keywords_eng=list_of_topics.get('eng', None)
                if keywords_eng:
                    keywords_eng_text=', '.join(keywords_eng)

                keywords_swe=list_of_topics.get('swe', None)
                if keywords_swe:
                    keywords_swe_text=', '.join(keywords_swe)

            #"subjectarea": {
            #"en_GB": "networking",
            #"sv_SE": "nät"
            #}
            data['subjectarea']=dict()
            data['subjectarea']['en_GB']=keywords_eng_text
            data['subjectarea']['sv_SE']=keywords_swe_text


            # "paragraphs_text": {
            #  "en_GB": "<p></p><p><strong>Keywords:</strong> <em>Unmanned aerial vehicle, Path planning, On-board computation, Autonomy</em></p>",
            #  "sv_SE": "<p></p><p><b>Nyckelord:</b> <em>Obemannade drönare, Vägplanering, Lokala beräkningar, Autonomi&#8203;</em></p>"
            # }
            abstracts=record.get('abstract', None)
            if abstracts:
                abstracts_eng=abstracts.get("eng", '')
                abstracts_swe=abstracts.get("swe", '')

            data['paragraphs_text']={
                'en_GB': abstracts_eng,
                'sv_SE': abstracts_swe
                }
            

            data['uri']="https://www.kth.se"

            print("data={}".format(data))
            if Verbose_Flag:
                with open('event.json', 'w') as outfile:
                    json.dump(data, outfile, sort_keys = True, indent = 4, ensure_ascii = False)

            check_for_extra_keys(data)

            check_for_extra_keys_from_Swagger(data)

            if not nocortina:
                response=post_to_Cortina(data['seminartype'], school, data)
                if isinstance(response, int):
                    print("response={0}".format(response))
                elif isinstance(response, dict):
                    content_id=response['contentId']
                else:
                    print("problem in entering the calendar entry")

            event_date_time=utc_to_local(isodate.parse_datetime(data['dates_starttime']))
            print("event_date_time={}".format(event_date_time))

            event_date=event_date_time.date()
            event_time=event_date_time.time().strftime("%H:%M")
            title="{0}/{1} on {2} at {3}".format(data['lead']['en_GB'], data['lead']['sv_SE'], event_date, event_time)
            print("title={}".format(title))

            pre_formatted0="Student:\t{0}\n".format(data['lecturer'])
            pre_formatted1="Title:\t{0}\nTitl:\t{1}\n".format(data['contentName']['en_GB'], data['contentName']['sv_SE'])
            pre_formatted2="Place:\t{0}\n".format(data['location'])

            examiners=' & '.join(examiners_names)
            pre_formatted3="Examiner:\t{0}\n".format(examiners)
            pre_formatted4="Academic Supervisor:\t{0}\n".format(data['advisor'])
            pre_formatted5="Opponent:\t{0}\n".format(data['opponent'])

            language_of_presentation='Swedish'
            pre_formatted6="Language:\t{0}\n".format(language_of_presentation)

            pre_formatted="<pre>{0}{1}{2}{3}{4}{5}{6}</pre>".format(pre_formatted0, pre_formatted1, pre_formatted2, pre_formatted3, pre_formatted4, pre_formatted5, pre_formatted6)
            print("pre_formatted={}".format(pre_formatted))

            # need to use the contentID to find the URL in the claendar
            see_also="<p>See also: <a href='https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842'>https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842</a></p>".format()

            body_html="<div style='display: flex;'><div><h2 lang='en'>Abstract</h2>{0}</div><div><h2 lang='sv'>Sammanfattning</h2>{1}</div></div>".format(data['paragraphs_text']['en_GB'], data['paragraphs_text']['sv_SE'])

            print("body_html={}".format(body_html))

            message="{0}{1}".format(pre_formatted, body_html)
            canvas_announcement_response=post_canvas_announcement(course_id, title, message)
            print("canvas_announcement_response={}".format(canvas_announcement_response))

            start=data['dates_starttime']
            end=data['dates_endtime']

            if language_of_presentation == 'Swedish':
                title=data['lead']['sv_SE']
            else:
                title=data['lead']['en_GB']

            if language_of_presentation == 'Swedish':
                description=data['contentName']['sv_SE']
            else:
                description=data['contentName']['en_GB']
        
            location_name=None
            location_address=None
            print("course_id={0}, start={1}, end={2}, title={3}, description={4}, location_name={5}, location_address={6}".format(course_id, start, end, title, description, location_name, location_address))

            canvas_calender_event=create_calendar_event(course_id, start, end, title, message, location_name, location_address)
            print("canvas_calender_event={}".format(canvas_calender_event))

def process_fixed_event():
    global testing
    global course_id
    global nocortina

    seminartype='thesis'
    school='EECS'

    presentation_date="2021-01-19"
    local_startTime="16:00"
    local_endTime="17:00"
    utc_datestart=local_to_utc(datetime.datetime.fromisoformat(presentation_date+'T'+local_startTime)).isoformat()+'.000Z'
    utc_dateend=local_to_utc(datetime.datetime.fromisoformat(presentation_date+'T'+local_endTime)).isoformat()+'.000Z'
    data={
        "advisor": "Anders Västberg",
        "contentId": "",
        "contentName": {
            "en_GB": "UAV Navigation using Local Computational Resources: Keeping a target in sight",
            "sv_SE": "UAV Navigering med Lokala Beräkningsresurser: Bevara ett mål i sensorisk räckvidd"
        },
        #"dates_starttime": "2021-01-19T15:00:00.000Z",
        "dates_starttime": utc_datestart,
        #"dates_endtime": "2021-01-19T16:00:00.000Z",
        "dates_endtime": utc_dateend,
        "lead": {
            "en_GB": "Master's thesis presentation",
            "sv_SE": "Examensarbete presentation"
        },
        "lecturer": "M C Hammer",
        "location": "Zoom via https://kth-se.zoom.us/j/xxxxx",
        "opponent": "xxxxxx",
        "organisation": { "school": "EECS", "department": "Datavetenskap" },
        "respondent": "",
        "respondentDepartment": "",
        #"respondentUrl": "",
        "seminartype": "thesis",
        "subjectarea": {
            "en_GB": "networking",
            "sv_SE": "nät"
        },
        "paragraphs_text": {
            "en_GB": "<p>When tracking a moving target, an Unmanned Aerial Vehicle (UAV) must keep the target within its sensory range while simultaneously remaining aware of its surroundings. However, ... its current position.</p><p><strong>Keywords:</strong> <em>Unmanned aerial vehicle, Path planning, On-board computation, Autonomy</em></p>",
            "sv_SE": "<p>När en obemannade luftfarkost, även kallad drönare, ... om sin nuvarande position.</p><p><b>Nyckelord:</b> <em>Obemannade drönare, Vägplanering, Lokala beräkningar, Autonomi&#8203;</em></p>"
        },
        "uri": "https://www.kth.se"
    }

    if Verbose_Flag:
        print("advisor={}".format(data['advisor']))
        print("contentId={}".format(data['contentId']))
        print("contentName={}".format(data['contentName']))
        print("dates_endtime={}".format(data['dates_endtime']))
        print("dates_starttime={}".format(data['dates_starttime']))
        print("lead={}".format(data['lead']))
        print("lecturer={}".format(data['lecturer']))
        print("location={}".format(data['location']))
        print("opponent={}".format(data['opponent']))
        print("organisation={}".format(data['organisation']))
        print("respondent={}".format(data['respondent']))
        #print("respondentUrl={}".format(data['respondentUrl']))
        print("respondentDepartment={}".format(data['respondentDepartment']))
        print("seminartype={}".format(data['seminartype']))
        print("subjectarea={}".format(data['subjectarea']))
        print("paragraphs_text={}".format(data['paragraphs_text']))
        print("uri={}".format(data['uri']))
    
    print("Checking for extra keys")
    for key, value in data.items():
        if key not in required_keys:
            print("extra key={0}, value={1}".format(key, value))
 
    print("Checking for extra keys from Swagger")
    for key, value in data.items():
        if key not in swagger_keys:
            print("extra key={0}, value={1}".format(key, value))

    if not testing and not nocortina:
        response=post_to_Cortina(seminartype, school, data)
        if isinstance(response, int):
            print("response={0}".format(response))
        elif isinstance(response, dict):
            content_id=response['contentId']

            data['lead']['en_GB']="Master's thesis presentation"
            print("updated lead={}".format(data['lead']))

            # must add the value for the contentId to the data
            data['contentId']=content_id
            response2=put_to_Cortina(seminartype, school, content_id, data)
            print("response2={0}".format(response2))

            event=get_from_Cortina(seminartype, school, content_id)
            print("event={0}".format(event))
        else:
            print("unexpected response={0}".format(response))
        

    event_date_time=utc_to_local(isodate.parse_datetime(data['dates_starttime']))
    print("event_date_time={}".format(event_date_time))

    event_date=event_date_time.date()
    event_time=event_date_time.time().strftime("%H:%M")
    title="{0}/{1} on {2} at {3}".format(data['lead']['en_GB'], data['lead']['sv_SE'], event_date, event_time)
    print("title={}".format(title))


    # <pre>Student:   Karim Kuvaja Rabhi
    # Title:     Automatisering av aktiv lyssnare processen inom examensarbetesseminarium
    # Time:      Monday 3 June 2019 at 17:00
    # Place:     Seminar room Grimeton at COM (Kistag&aring;ngen 16), East, Floor 4, Kista
    # Examiner:  Professor Gerald Q. Maguire Jr.
    # Academic Supervisor: Anders V&auml;stberg
    # Opponent: Sebastian Forsmark and Martin Brisfors
    # Language: Swedish 
    # </pre>


    pre_formatted0="Student:\t{0}\n".format(data['lecturer'])
    pre_formatted1="Title:\t{0}\nTitl:\t{1}\n".format(data['contentName']['en_GB'], data['contentName']['sv_SE'])
    pre_formatted2="Place:\t{0}\n".format(data['location'])

    examiner="Professor Gerald Q. Maguire Jr."
    pre_formatted3="Examiner:\t{0}\n".format(examiner)
    pre_formatted4="Academic Supervisor:\t{0}\n".format(data['advisor'])
    pre_formatted5="Opponent:\t{0}\n".format(data['opponent'])

    #language_of_presentation='Swedish'
    pre_formatted6="Language:\t{0}\n".format(language_of_presentation)

    pre_formatted="<pre>{0}{1}{2}{3}{4}{5}{6}</pre>".format(pre_formatted0, pre_formatted1, pre_formatted2, pre_formatted3, pre_formatted4, pre_formatted5, pre_formatted6)
    print("pre_formatted={}".format(pre_formatted))

    # need to use the contentID to find the URL in the claendar
    see_also="<p>See also: <a href='https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842'>https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842</a></p>".format()

    body_html="<div style='display: flex;'><div><h2 lang='en'>Abstract</h2>{0}</div><div><h2 lang='sv'>Sammanfattning</h2>{1}</div></div>".format(data['paragraphs_text']['en_GB'], data['paragraphs_text']['sv_SE'])

    print("body_html={}".format(body_html))

    message="{0}{1}".format(pre_formatted, body_html)
    canvas_announcement_response=post_canvas_announcement(course_id, title, message)
    print("canvas_announcement_response={}".format(canvas_announcement_response))



    start=data['dates_starttime']
    end=data['dates_endtime']

    if language_of_presentation == 'Swedish':
        title=data['lead']['sv_SE']
    else:
        title=data['lead']['en_GB']

    if language_of_presentation == 'Swedish':
        description=data['contentName']['sv_SE']
    else:
        description=data['contentName']['en_GB']
    
    location_name=None
    location_address=None
    print("course_id={0}, start={1}, end={2}, title={3}, description={4}, location_name={5}, location_address={6}".format(course_id, start, end, title, description, location_name, location_address))

    canvas_calender_event=create_calendar_event(course_id, start, end, title, message, location_name, location_address)
    print("canvas_calender_event={}".format(canvas_calender_event))

def process_event_from_JSON_file(json_file):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global course_id
    global nocortina

    with open(json_file, 'r') as event_FH:
        try:
            event_string=event_FH.read()
            d=json.loads(event_string)
        except:
            print("Error in reading={}".format(event_string))
            sys.exit()

    print("read event: {}".format(d))

    # The data dictionary will hold the even information 
    data=dict()
    data['contentId']=''        # initially we do not know this, but need to have it in the dict
    data['uri']='https://www.kth.se'  # this is a required element for Cortina
    data['seminartype']='thesis' # Here: we only process 1st and 2nd cycle degree project presentations

    # "Presentation": {"Date": "2021-03-15 13:00", "Language": "eng", "Room": "via Zoom", "City": "Stockholm"

    p=d.get('Presentation', None)
    if not p:
        print("Event lacks presentation information")
        return

    location_room=p.get('Room', None)
    location_address=p.get('Address', None)
    location_city=p.get('City', None)

    if location_room is None:
        location_room='TBA'
    if location_city is None:
        location_city='Stockholm'
    if location_address and location_city:
        location_address=location_address+', '+location_city
    else:
        location_address=location_city

    data['location']=location_room+', '+location_address

    language_of_presentation=p.get('Language', None)
    if language_of_presentation == 'eng':
        language_of_presentation='English'
    elif language_of_presentation == 'swe':
        language_of_presentation='Svenska'
    else:
        language_of_presentation='Unknown language for presentation'


    event_date=p.get('Date')
    print("event_date={}".format(event_date))
    local_start = datetime.datetime.strptime(event_date, '%Y-%m-%d %H:%M')
    utc_datestart=local_to_utc(local_start).isoformat()+'.000Z'
    local_end=local_start+datetime.timedelta(hours = 1.0)
    utc_dateend=local_to_utc(local_end).isoformat()+'.000Z'
    data['dates_starttime']=utc_datestart
    data['dates_endtime']=utc_dateend

    school=None
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
                        school=s
                        break
                    school_name_eng=schools_info[s]['eng']
                    offset=examiner_L1.find(school_name_eng)
                    if offset >= 0:
                        school=s
                        break
            if school is None:
                school='EECS'   # if no school was no found, guess the biggest school!
            
            examiner_L2=examiner_organisation.get('L2', None)
            if examiner_L2:
                if school == 'EECS':
                    if examiner_L2 == 'Computer Science':
                        examiner_L2='Datavetenskap'
                    elif  examiner_L2 == 'Electrical Engineering':
                        examiner_L2='Elektroteknik'
                    elif  examiner_L2 == 'Intelligent Systems':
                        examiner_L2='Intelligenta system'
                    elif  examiner_L2 == 'Human Centered Technology':
                        examiner_L2='Människocentrerad teknologi'
                    else:
                        examiner_L2='Datavetenskap' # if department not found, guess largest department

                elif school == 'ITM':
                    if examiner_L2 == 'Energy Technology':
                        examiner_L2='Energiteknik'
                    elif examiner_L2 == 'Sustainable Production Development':
                        examiner_L2='Hållbar produktionsutveckling'
                    elif examiner_L2 == 'Industrial Economics and Management':
                        examiner_L2='Industriell ekonomi och organisation'
                    elif examiner_L2 == 'Production Engineering':
                        examiner_L2='Industriell produktion'
                    elif examiner_L2 == 'Learning':
                        examiner_L2='Lärande'
                    elif examiner_L2 == 'Machine Design':
                        examiner_L2='Maskinkonstruktion'
                    elif examiner_L2 == 'Materials Science and Engineering':
                        examiner_L2='Materialvetenskap'
                    else:
                        examiner_L2='Unknown department in ITM'

                elif school == 'CBH':
                    if examiner_L2 == 'Biomedical Engineering and Health Systems':
                        examiner_L2='Medicinsk teknik och hälsosystem'
                    elif examiner_L2 == 'Chemistry':
                        examiner_L2='Kemi'
                    elif examiner_L2 == 'Chemical Engineering':
                        examiner_L2='Kemiteknik'
                    elif examiner_L2 == 'Fibre and Polymer Technology':
                        examiner_L2='Fiber- och polymerteknologi'
                    elif examiner_L2 == 'Engineering Pedagogics':
                        examiner_L2='Ingenjörspedagogik'
                    elif examiner_L2 == 'Gene Technology':
                        examiner_L2='Genteknologi'
                    elif examiner_L2 == 'Industrial Biotechnology':
                        examiner_L2='Industriell bioteknologi'
                    elif examiner_L2 == 'Protein Science':
                        examiner_L2='Proteinvetenskap'
                    elif examiner_L2 == 'Theoretical Chemistry and Biology':
                        examiner_L2='Teoretisk kemi och biologi'
                    else:
                        examiner_L2='Unknown department in CBH'

                elif  school == 'SCI':
                    if examiner_L2 == 'Physics':
                        examiner_L2='Fysik'
                    elif examiner_L2 == 'Mathematics':
                        examiner_L2='Matematik'
                    elif examiner_L2 == 'Engineering Mechanics':
                        examiner_L2='Teknisk mekanik'
                    elif examiner_L2 == 'Applied physics':
                        examiner_L2='Tillämpad fysik'
                    else:
                        examiner_L2='Unknown department in SCI'

                elif school == 'ABE':
                    if examiner_L2 == 'Architecture':
                        examiner_L2='Arkitektur'
                    elif examiner_L2 == 'Civil and Architectural Engineering':
                        examiner_L2='Byggvetenskap'
                    elif examiner_L2 == 'Philosophy and History':
                        examiner_L2='Filosofi och historia'
                    elif examiner_L2 == 'Real Estate and Construction Management':
                        examiner_L2='Fastigheter och byggande'
                    elif examiner_L2 == 'Sustainable development, environmental science and engineering':
                        examiner_L2='Hållbar utveckling, miljövetenskap och teknik'
                    elif examiner_L2 == 'Urban Planning and Environment':
                        examiner_L2='Samhällsplanering och miljö'
                    else:
                        examiner_L2='Unknown department in ABE'
                else:
                    examiner_L2='Unknown'

                data['organisation']= { "school": school,
                                    "department":  examiner_L2}

    if school is None:
        print("Unable to determine the school")

    supervisr_names=list()
    for i in range(1, 10):
        which_supervisor="Supervisor{}".format(i)
        supervisor=d.get(which_supervisor, None)
        if supervisor:
            last_name=supervisor.get('Last name', None)
            first_name=supervisor.get('First name', None)
            if first_name and last_name:
                supervisr_name=first_name+' '+last_name
            elif not first_name and last_name:
                supervisr_name=last_name
            elif first_name and not last_name:
                supervisr_name=first_name
            else:
                print("Supervisor name is unknown: {}".format(examiner))
            supervisr_names.append(supervisr_name)

    data['advisor']=' & '.join(supervisr_names)

    author_names=list()
    for i in range(1, 10):
        which_supervisor="Author{}".format(i)
        supervisor=d.get(which_supervisor, None)
        if supervisor:
            last_name=supervisor.get('Last name', None)
            first_name=supervisor.get('First name', None)
            if first_name and last_name:
                author_name=first_name+' '+last_name
            elif not first_name and last_name:
                author_name=last_name
            elif first_name and not last_name:
                author_name=first_name
            else:
                print("Supervisor name is unknown: {}".format(examiner))
            author_names.append(author_name)

    data['lecturer']=' & '.join(author_names)
    data['respondent']="" 			# must be present but empty
    data['respondentDepartment']=""		# must be present but empty

    opponents=d.get('Opponents', None)
    if opponents:
        opponents_names=opponents.get('Name', None)
        if opponents_names:
            data['opponent']=opponents_names
        else:
            data['opponent']="TBA"

    # "Title": {"Main title": "This is the title in the language of the thesis", "Subtitle": "An subtitle in the language of the thesis", "Language": "eng"}, "Alternative title": {"Main title": "Detta är den svenska översättningen av titeln", "Subtitle": "Detta är den svenska översättningen av undertiteln", "Language": "swe"}
    title=d.get('Title', None)
    if title:
        thesis_main_title=title.get('Main title', None)
        thesis_main_title_lang=title.get('Language', None)
        thesis_main_subtitle=title.get('Subtitle', None)

        if thesis_main_title_lang is None:
            thesis_main_title_lang='eng'
    else:
        print("Event has no title information")

    if thesis_main_title and thesis_main_subtitle:
        thesis_main_title=thesis_main_title+': '+thesis_main_subtitle

    alternative_title=d.get('Alternative title', None)
    if alternative_title:
        thesis_secondary_title=alternative_title.get('Main title', None)
        thesis_secondary_title_lang=alternative_title.get('Language', None)
        thesis_secondary_subtitle=alternative_title.get('Subtitle', None)
    else:
        print("Event has no alternative title information")

    if thesis_secondary_title and thesis_secondary_subtitle:
        thesis_secondary_title=thesis_secondary_title+': '+thesis_secondary_subtitle

    if thesis_main_title_lang == 'eng':
        data['contentName']={'en_GB': thesis_main_title,
                             'sv_SE': thesis_secondary_title
                             }
    else:
        data['contentName']={'en_GB': thesis_secondary_title,
                             'sv_SE': thesis_main_title
                             }

    # "Degree": {"Educational program": "Bachelor’s Programme in Information and Communication Technology"}
    degree=d.get('Degree', None)
    if degree:
        ep=degree.get('Educational program', None)
        if ep:
            cycle=cycle_of_program(ep)
            if cycle and cycle > 1:
                data['lead']={
                    'en_GB': "Master's thesis presentation",
                    'sv_SE': "Examensarbete presentation"
                }
            else:
                data['lead']={
                    'en_GB': "Bachelor's thesis presentation",
                    'sv_SE': "Kandidate Examensarbete presentation"
                }

    keywords=d.get('keywords', None)
    if keywords:
        keywords_eng=keywords.get('eng', None)
        keywords_swe=keywords.get('swe', None)
        print("keywords {0} {1}".format(keywords_eng, keywords_swe))
        if keywords_eng or keywords_swe:
            data['subjectarea']=dict()
            if keywords_eng:
                data['subjectarea']['en_GB']=keywords_eng
            if keywords_swe:
                data['subjectarea']['sv_SE']=keywords_swe

    abstracts=d.get('abstracts', None)
    if abstracts:
        abstracts_eng=abstracts.get('eng', None)
        abstracts_swe=abstracts.get('swe', None)

        data['paragraphs_text']=dict()
        if abstracts_eng:
            data['paragraphs_text']['en_GB']= abstracts_eng
        if abstracts_swe:
            data['paragraphs_text']['sv_SE']= abstracts_swe
             
    print("data={}".format(data))
    check_for_extra_keys(data)
    check_for_extra_keys_from_Swagger(data)

    # for testing we need to remove the examiner information until the Cortina API is updated
    if not nocortina:
        save_examiner_info=data['examiner']
        data.pop('examiner')    # remove the examiner

        # similar means same time and date, same lecturer, pssibly sample title?
        proposed_event_start=data['dates_starttime']
        proposed_event_lecturer=data['lecturer']

        # look for an existing event that is "similar"
        # "organisation": {
        #   "school": "EECS",
        #   "department": "Datavetenskap"
        # }
        proposed_school=data['organisation']['school']
        proposed_department=data['organisation']['department']
        proposed_year=proposed_event_start[0:4]
        existing_cortina_events=get_seminarlist_from_Cortina(data['seminartype'], proposed_school, proposed_department, proposed_year)

        existing_event=None
        for cal_event in existing_cortina_events:
            if (cal_event['dates_starttime'] == proposed_event_start) and (cal_event['lecturer'] == proposed_event_lecturer):
                existing_event=cal_event['contentId']
                break

        # if there is an existing event, then use put rather than post
        #post_to_Cortina(seminartype, school, data):
        #put_to_Cortina(seminartype, school, content_id, data):
        if existing_event:
            print("Updating existing event={}".format(existing_event))
            data['contentId']=existing_event
            response=put_to_Cortina(data['seminartype'], school, existing_event, data)
        else:
            response=post_to_Cortina(data['seminartype'], school, data)

        if isinstance(response, int):
            print("response={0}".format(response))
        elif isinstance(response, dict):
            content_id=response['contentId']
            print("Cortina calendar content_id={}".format(content_id))
        else:
            print("problem in entering the calendar entry")

        # restore examiner information
        data['examiner']=save_examiner_info

    event_date_time=utc_to_local(isodate.parse_datetime(data['dates_starttime']))
    print("event_date_time={}".format(event_date_time))

    event_date=event_date_time.date()
    event_time=event_date_time.time().strftime("%H:%M")
    title="{0}/{1} on {2} at {3}".format(data['lead']['en_GB'], data['lead']['sv_SE'], event_date, event_time)
    print("title={}".format(title))

    pre_formatted0="Student:\t{0}\n".format(data['lecturer'])
    pre_formatted1="Title:\t{0}\nTitel:\t{1}\n".format(data['contentName']['en_GB'], data['contentName']['sv_SE'])
    pre_formatted2="Place:\t{0}\n".format(data['location'])

    pre_formatted3="Examiner:\t{0}\n".format(data['examiner'])
    pre_formatted4="Academic Supervisor:\t{0}\n".format(data['advisor'])
    pre_formatted5="Opponent:\t{0}\n".format(data['opponent'])

    pre_formatted6="Language:\t{0}\n".format(language_of_presentation)

    pre_formatted="<pre>{0}{1}{2}{3}{4}{5}{6}</pre>".format(pre_formatted0, pre_formatted1, pre_formatted2, pre_formatted3, pre_formatted4, pre_formatted5, pre_formatted6)
    print("pre_formatted={}".format(pre_formatted))

    # need to use the contentID to find the URL in the claendar
    see_also="<p>See also: <a href='https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842'>https://www.kth.se/en/eecs/kalender/exjobbspresentatione/automatisering-av-aktiv-lyssnare-processen-inom-examensarbetesseminarium-1.903842</a></p>".format()

    # Appends the keywords if they exist
    # <p><strong>Keywords:</strong> <em>Unmanned aerial vehicle, Path planning, On-board computation, Autonomy</em></p>
    if keywords_eng and len(keywords_eng) > 0:
        data['paragraphs_text']['en_GB']=data['paragraphs_text']['en_GB']+"<p><strong>Keywords:</strong> <em>{0}</em></p>".format(keywords_eng)

    if keywords_swe and len(keywords_swe)  > 0:
        data['paragraphs_text']['sv_SE']=data['paragraphs_text']['sv_SE']+"<p><strong>Nyckelord:</strong> <em>{0}</em></p>".format(keywords_swe)


    body_html="<div style='display: flex;'><div><h2 lang='en'>Abstract</h2>{0}</div><div><h2 lang='sv'>Sammanfattning</h2>{1}</div></div>".format(data['paragraphs_text']['en_GB'], data['paragraphs_text']['sv_SE'])

    print("body_html={}".format(body_html))

    message="{0}{1}".format(pre_formatted, body_html)
    canvas_announcement_response=post_canvas_announcement(course_id, title, message)
    print("canvas_announcement_response={}".format(canvas_announcement_response))

    start=data['dates_starttime']
    end=data['dates_endtime']

    if language_of_presentation == 'Swedish':
        title=data['lead']['sv_SE']
    else:
        title=data['lead']['en_GB']

    if language_of_presentation == 'Swedish':
        description=data['contentName']['sv_SE']
    else:
        description=data['contentName']['en_GB']
                
    # "Presentation": {"Date": "2021-03-15 13:00", "Language": "eng", "Room": "via Zoom", "City": "Stockholm"
    location_name=location_room

    print("course_id={0}, start={1}, end={2}, title={3}, description={4}, location_name={5}, location_address={6}".format(course_id, start, end, title, description, location_name, location_address))
    
    canvas_calender_event=create_calendar_event(course_id, start, end, title, message, location_name, location_address)
    print("canvas_calender_event={}".format(canvas_calender_event))



def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global course_id
    global nocortina


    Use_local_time_for_output_flag=True

    timestamp_regex = r'(2[0-3]|[01][0-9]|[0-9]):([0-5][0-9]|[0-9]):([0-5][0-9]|[0-9])'

    argp = argparse.ArgumentParser(description="II2202-grades_to_report.py: look for students who have passed the 4 assignments and need a grade assigned")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")

    argp.add_argument("-c", "--canvas_course_id", type=int, required=True,
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

    argp.add_argument('-m', '--mods',
                      type=str,
                      default="theses.mods",
                      help="read mods formatted information from file"
                      )

    argp.add_argument('-n', '--nocortina',
                      default=False,
                      action="store_true",
                      help="to not put events in cortina"
                      )

    argp.add_argument('-j', '--json',
                      type=str,
                      default="event.json",
                      help="JSON file for extracted calendar event"
                      )

    argp.add_argument('-e', '--event',
                      type=int,
                      default=0,
                      help="type of even input"
                      )


    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    initialize(args)
    if Verbose_Flag:
        print("baseUrl={}".format(baseUrl))
        print("cortina_baseUrl={0}".format(cortina_baseUrl))

    course_id=args["canvas_course_id"]
    print("course_id={}".format(course_id))

    testing=args["testing"]
    print("testing={}".format(testing))

    nocortina_arg=args["nocortina"]
    print("nocortina_arg={}".format(nocortina_arg))

    # nocortina - set if the user does not have a Cortina access key
    # if the nocortina arg is True, then disable the use of Cortina
    if nocortina_arg:
         nocortina=True

    print("nocortina={}".format(nocortina))

    event_input_type=args["event"]
    print("event_input_type={}".format(event_input_type))
    if event_input_type == 3:
        mods_filename=args["mods"]
        process_events_from_MODS_file(mods_filename)
    elif event_input_type == 2:
        process_fixed_event()
    elif event_input_type == 0:
        json_filename=args["json"]
        process_event_from_JSON_file(json_filename)
    else:
        print("Unknown source for the event: {}".format(event_input_type))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

