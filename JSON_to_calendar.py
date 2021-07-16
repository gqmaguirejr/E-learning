#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_calendar.py -c course_id [--nocortina] [--json file.json]
#
# Purpose: The program creates an event entry based on a JSON file
#
# This event will be inserted into the KTH Cortina Calendar (unless the --nocortina flag is set or the user does not have a Cortina access key).
# The program also generates an announcement in the indicated Canvas course room and creates a calendar entry in the Canvas calendar for this course room.
#
#  It can also modify (using PUT) an existing Cortina Calendar entry.
#
# Example:
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
# 2021-07-16 G. Q. Maguire Jr. - simplified to only take in JSON information
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

def list_of_canvas_course_announcements(course_id):
    global Verbose_Flag
    
    entries_found_thus_far=[]

    # Use the Canvas API to get the list of accounts this user can see
    # GET /api/v1/announcements
    url = "{0}/announcements".format(baseUrl)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100'}
    if course_id:
        extra_parameters['context_codes[]']="course_{}".format(course_id)

    r = requests.get(url, params=extra_parameters, headers = header)

    if Verbose_Flag:
        print("result of getting announcements: {}".format(r.text))

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



def put_canvas_announcement(course_id, title, message, topic_id):
    global Verbose_Flag
    
    # Use the Canvas API to update a discussion topic
    # PUT /api/v1/courses/:course_id/discussion_topics/:topic_id
    url = "{0}/courses/{1}/discussion_topics/{2}".format(baseUrl, course_id, topic_id)
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
    r = requests.put(url, params=extra_parameters, headers = header)

    if Verbose_Flag:
        print("result of posting an announcement: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    else:
        return r.status_code

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

# Cortina model for PUT
# {
#   "contentId": "string",
#   "seminartype": "dissertation",
#   "organisation": {
#     "school": "ABE",
#     "department": "string"
#   },
#   "dates_starttime": "string",
#   "dates_endtime": "string",
#   "contentName": {
#     "en_GB": "string",
#     "sv_SE": "string"
#   },
#   "lead": {
#     "en_GB": "string",
#     "sv_SE": "string"
#   },
#   "paragraphs_text": {
#     "en_GB": "string",
#     "sv_SE": "string"
#   },
#   "advisor": "string",
#   "examiner": "string",
#   "lecturer": "string",
#   "opponent": "string",
#   "presentationlang": {
#     "en_GB": "string",
#     "sv_SE": "string"
#   },
#   "respondent": "string",
#   "respondentDepartment": "string",
#   "location": "string",
#   "uri": "string",
#   "subjectarea": {
#     "en_GB": "string",
#     "sv_SE": "string"
#   }
# }



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

def list_of_canvas_calendar_events(course_id, start, end):
    global Verbose_Flag
    
    entries_found_thus_far=[]

    # Use the Canvas API to get the list of calendar events this user can see in this course
    # GET /api/v1/calendar_events
    url = "{0}/calendar_events".format(baseUrl)
    if Verbose_Flag:
        print("url: {}".format(url))

    start_date=start[0:10]
    end_date=end[0:10]
    print("start_date={}".format(start_date))
    extra_parameters={'per_page': '100',
                      'context_codes[]': "course_{}".format(course_id),
                      'start_date': start_date,
                      'end_date':   end_date
                      }


    r = requests.get(url, params=extra_parameters, headers = header)

    if Verbose_Flag:
        print("result of getting calendar events: {}".format(r.text))

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

    if r.status_code == requests.codes.ok or r.status_code == requests.codes.created:
        page_response=r.json()
        return page_response
    else:
        print("status code={}".format(r.status_code))
    return None
    
def update_calendar_event(course_id, start, end, title, description, location_name, location_address, event_id):
    # Use the Canvas API to get the calendar event
    #PUT /api/v1/calendar_events/:id
    url = "{0}/calendar_events/{1}".format(baseUrl, event_id)
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

    r = requests.put(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of creating a calendar event: {}".format(r.text))

    if r.status_code == requests.codes.ok or r.status_code == requests.codes.created:
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
               'presentationlang',
               'opponent',
               'examiner',
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
              'examiner',
              "respondent",
              "respondentDepartment",
              "location",
              'presentationlang',
              "uri",
              "subjectarea"]

def check_for_extra_keys(data):
    global Verbose_Flag
    if Verbose_Flag:
        print("Checking for extra keys")
    for key, value in data.items():
        if key not in required_keys:
            print("extra key={0}, value={1}".format(key, value))

def check_for_extra_keys_from_Swagger(data):
    global Verbose_Flag
    if Verbose_Flag:
        print("Checking for extra keys from Swagger")
    for key, value in data.items():
        if key not in swagger_keys:
            print("extra key={0}, value={1}".format(key, value))




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
    

def mathincluded(html):
    # look for LaTeX math in the html
    if html.find('\\(') >= 0 and html.find('\\)') >= 0:
        return True
    if html.find('\\[') >= 0 and html.find('\\]') >= 0:
        return True
    if html.find('$$') >= 0:
        return True
    return False

def transform_urls(html):
    # look for \\url{xxxxx} in the html
    start_of_url=html.find('\\url{')
    # print("start_of_url={}".format(start_of_url))
    while start_of_url >= 0:
        end_of_url=html.find('}', start_of_url+6)
        # print("end_of_url={}".format(end_of_url))
        url=html[start_of_url+5:end_of_url]
        # print("url={}".format(url))
        # <a href="xxxx">xxx</a>
        html_anchor="<a href='{0}'>{0}</a>".format(url)
        # print("html_anchor={}".format(html_anchor))
        html=url=html[0:start_of_url]+html_anchor+html[end_of_url+1:]
        # print("html={}".format(html))
        start_of_url=html.find('\\url{')
        # print("start_of_url={}".format(start_of_url))
    return html

def transform_math_for_cortina(html):
    # \( equation \)
    start_of_eqn=html.find('\\(')
    # print("start_of_eqn={}".format(start_of_eqn))
    while start_of_eqn >= 0:
        offset=start_of_eqn+3
        end_of_eqn=html.find('\\)', offset)
        # print("end_of_eqn={}".format(end_of_eqn))
        eqn=html[start_of_eqn+2:end_of_eqn]
        # print("eqn={}".format(eqn))
        # <span class=\"math-tex\">\\(x =  {-b \\pm \\sqrt{b^2-4ac} \\over 2a}\\)</span>
        eqn_string="<span class=\'math-tex\'>\\({0}\\)</span>".format(eqn)
        # print("eqn_string={}".format(eqn_string))
        html_part1=url=html[0:start_of_eqn]+eqn_string
        offset=len(html_part1)
        html=html_part1+html[end_of_eqn+2:]
        # print("html={}".format(html))
        start_of_eqn=html.find('\\(', offset)
        # print("start_of_eqn={}".format(start_of_eqn))
    # \[ equation \]
    start_of_eqn=html.find('\\[')
    print("start_of_eqn={}".format(start_of_eqn))
    while start_of_eqn >= 0:
        offset=start_of_eqn+3
        end_of_eqn=html.find('\\]', offset)
        # print("end_of_eqn={}".format(end_of_eqn))
        eqn=html[start_of_eqn+2:end_of_eqn]
        # print("eqn={}".format(eqn))
        # <span class=\"math-tex\">\\(x =  {-b \\pm \\sqrt{b^2-4ac} \\over 2a}\\)</span>
        eqn_string="<span class=\'math-tex\'>\\[{0}\\]</span>".format(eqn)
        # print("eqn_string={}".format(eqn_string))
        html_part1=url=html[0:start_of_eqn]+eqn_string
        offset=len(html_part1)
        html=html_part1+html[end_of_eqn+2:]
        # print("html={}".format(html))
        start_of_eqn=html.find('\\[', offset)
        # print("start_of_eqn={}".format(start_of_eqn))
    # $$ equation $$
    start_of_eqn=html.find('$$')
    # print("start_of_eqn={}".format(start_of_eqn))
    while start_of_eqn >= 0:
        offset=start_of_eqn+3
        end_of_eqn=html.find('$$', offset)
        # print("end_of_eqn={}".format(end_of_eqn))
        eqn=html[start_of_eqn+2:end_of_eqn]
        # print("eqn={}".format(eqn))
        # <span class=\"math-tex\">\\(x =  {-b \\pm \\sqrt{b^2-4ac} \\over 2a}\\)</span>
        eqn_string="<span class=\'math-tex\'>\\[{0}\\]</span>".format(eqn)
        # print("eqn_string={}".format(eqn_string))
        html_part1=url=html[0:start_of_eqn]+eqn_string
        offset=len(html_part1)
        html=html_part1+html[end_of_eqn+2:]
        # print("html={}".format(html))
        start_of_eqn=html.find('$$', offset)
        # print("start_of_eqn={}".format(start_of_eqn))
    #
    return html



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

    if Verbose_Flag:
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
        data['presentationlang'] ={
            "en_GB": "English",
            "sv_SE": "Engelska"
        }
    elif language_of_presentation == 'swe':
        language_of_presentation='Svenska'
        data['presentationlang'] ={
            "en_GB": "Swedish",
            "sv_SE": "Svenska"
        }
    else:
        language_of_presentation='Unknown language for presentation'


    event_date=p.get('Date')
    if Verbose_Flag:
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
                if Verbose_Flag:
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
                print("Author name is unknown: {}".format(examiner))
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

    # If the cycle information is explicit, then use it
    cycle=d.get('Cycle', None)
    if cycle and int(cycle) > 1:
        data['lead']={
            'en_GB': "Master's thesis presentation",
            'sv_SE': "Examensarbete presentation"
        }
    else:
        data['lead']={
            'en_GB': "Bachelor's thesis presentation",
            'sv_SE': "Kandidate Examensarbete presentation"
        }

    # otherwise, compute the cycle from the education program
    # "Degree1": {"Educational program": "Bachelor’s Programme in Information and Communication Technology"}
    degree1=d.get('Degree1', None)
    if degree1 and not cycle:
        ep=degree1.get('Educational program', None)
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
        if Verbose_Flag:
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
            # take care of URLs
            if abstracts_eng.find('\\url{') >= 0:
                abstracts_eng=transform_urls(abstracts_eng)

            # transform equations
            if mathincluded(abstracts_eng):
                abstracts_eng=transform_math_for_cortina(abstracts_eng)

            data['paragraphs_text']['en_GB']= abstracts_eng
        if abstracts_swe:
            if abstracts_swe.find('\\url{') >= 0:
                abstracts_swe=transform_urls(abstracts_swe)

            if mathincluded(abstracts_swe):
                abstracts_swe=transform_math_for_cortina(abstracts_swe)

            data['paragraphs_text']['sv_SE']= abstracts_swe
             
    if Verbose_Flag:
        print("data={}".format(data))
    check_for_extra_keys(data)
    check_for_extra_keys_from_Swagger(data)

    if not nocortina:
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

        if isinstance(existing_cortina_events, int):
            print("Failed to get seminar list from Cortina, error={}".format(existing_cortina_events))
        else:
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
                print("Error in putting/posting event to Cortina - response={0}".format(response))
            elif isinstance(response, dict):
                content_id=response['contentId']
                print("Cortina calendar content_id={}".format(content_id))
                # it successful, it return a content_id and the canonicalUrl of where it posted the event
                # "canonicalUrl": "https://www-r.referens.sys.kth.se/en/aktuellt/kalender/examensarbeten/how-to-visualize-historical-air-temperature-recordings-effectively-in-a-single-display-a-narrative-visualization-of-geospatial-time-dependent-data-1.1010690"
                canonicalUrl=response['canonicalUrl']
            else:
                print("problem in entering the calendar entry")

    event_date_time=utc_to_local(isodate.parse_datetime(data['dates_starttime']))
    if Verbose_Flag:
        print("event_date_time={}".format(event_date_time))

    event_date=event_date_time.date()
    event_time=event_date_time.time().strftime("%H:%M")
    title="{0}/{1} on {2} at {3}".format(data['lead']['en_GB'], data['lead']['sv_SE'], event_date, event_time)
    if Verbose_Flag:
        print("title={}".format(title))

    if data['lecturer'].find('&'): # replace the simple amptersand with the HTML
        data['lecturer']=data['lecturer'].replace('&', '&amp;')
        print("Correcting ampersand to HTML")

    pre_formatted0="<span lang=\"en_us\">Student</span>:\t{0}\n".format(data['lecturer'])
    pre_formatted1="<span lang=\"en_us\">Title</span>:\t{0}\n<span lang=\"sv_se\">Titel</span>:\t{1}\n".format(data['contentName']['en_GB'], data['contentName']['sv_SE'])
    pre_formatted2="<span lang=\"en_us\">Place</span>/<span lang=\"sv_se\">Plats</span>:\t{0}\n".format(data['location'])

    pre_formatted3="<span lang=\"en_us\">Examiner</span>/<span lang=\"sv_se\">Examinator</span>:\t{0}\n".format(data['examiner'])
    pre_formatted4="<span lang=\"en_us\">Academic Supervisor</span>/<span lang=\"sv_se\">Handledare</span>:\t{0}\n".format(data['advisor'])
    pre_formatted5="Opponent:\t{0}\n".format(data['opponent'])

    pre_formatted6="<span lang=\"en_us\">Language</span>/<span lang=\"sv_se\">Språk</span>:\t{0}\n".format(language_of_presentation)

    pre_formatted="<pre>{0}{1}{2}{3}{4}{5}{6}</pre>".format(pre_formatted0, pre_formatted1, pre_formatted2, pre_formatted3, pre_formatted4, pre_formatted5, pre_formatted6)
    if Verbose_Flag:
        print("pre_formatted={}".format(pre_formatted))

    # need to use the contentID to find the URL in the calendar
    if not nocortina:
        see_also="<p><span lang=en_us>See also</span>/<span lang=sv_se>Se även</span>: <a href='{0}'>{0}</a></p>".format(canonicalUrl)
    else:
        see_also=""

    # Appends the keywords if they exist
    # <p><strong>Keywords:</strong> <em>Unmanned aerial vehicle, Path planning, On-board computation, Autonomy</em></p>
    if keywords_eng and len(keywords_eng) > 0:
        data['paragraphs_text']['en_GB']=data['paragraphs_text']['en_GB']+"<p><strong>Keywords:</strong> <em>{0}</em></p>".format(keywords_eng)

    if keywords_swe and len(keywords_swe)  > 0:
        data['paragraphs_text']['sv_SE']=data['paragraphs_text']['sv_SE']+"<p><strong>Nyckelord:</strong> <em>{0}</em></p>".format(keywords_swe)


    body_html="<div style='display: flex;'><div><h2 lang='en'>Abstract</h2>{0}</div><div><h2 lang='sv'>Sammanfattning</h2>{1}</div></div>".format(data['paragraphs_text']['en_GB'], data['paragraphs_text']['sv_SE'])
 

    # if there are any URLs, replace them with an HTML anchor
    if body_html.find('\\url{') >= 0:
        body_html=transform_urls(body_html)

    # save the original HTML body
    original_body_html=body_html

    # adding the following MATHML snippet causes MathJAX to get loaded by Canvas
    # based on https://chalmers.instructure.com/courses/2/pages/math-slash-latex-in-canvas-pages?module_item_id=22197
    # see also https://community.canvaslms.com/t5/Canvas-Releases/Canvas-Release-Notes-2021-02-20/ta-p/434781#toc-hId-698876024
    if mathincluded(body_html):
        body_html=body_html+'<div><math></math></div>'
        print("Math included in HTML")

    if Verbose_Flag:
        print("body_html={}".format(body_html))

    if not nocortina:
        message="{0}{1}{2}".format(pre_formatted, see_also, body_html)
    else:
        message="{0}{1}".format(pre_formatted, body_html)

    current_announcements=list_of_canvas_course_announcements(course_id)
    print("current_announcements={}".format(current_announcements))
    topic_id=None
    for a in current_announcements:
        if a['title'] == title:
            topic_id=a['id']
            break

    if topic_id:
        canvas_announcement_response=put_canvas_announcement(course_id, title, message, topic_id)
        print("updated event with topic_id={}".format(topic_id))
    else:
        canvas_announcement_response=post_canvas_announcement(course_id, title, message)
        print("Inserted new event with id={}".format(canvas_announcement_response['id']))
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

    if Verbose_Flag:
        print("course_id={0}, start={1}, end={2}, title={3}, description={4}, location_name={5}, location_address={6}".format(course_id, start, end, title, description, location_name, location_address))
    
    existing_calendar_events=list_of_canvas_calendar_events(course_id, start, end)
    if Verbose_Flag:
        print("existing_calendar_events={}".format(existing_calendar_events))
    # 
    # In the code below one can either pass message to the create/update calendar or the description (which in this case would be the title in the language of the presentation)
    # The tests for the same lecturer versus the same description are used for these two cases.
    event_id=None
    for a in existing_calendar_events:
        if a['title'] == title:
            if Verbose_Flag:
                print("same title")
            if a['start_at'][0:19] == start[0:19]:
                if Verbose_Flag:
                    print("same start time")    
                if a['description'].find(data['lecturer']) >= 0:
                    if Verbose_Flag:
                        print("same lecturer")    
                    event_id=a['id']
                    print("existing event_id={}".format(event_id))
                    break

                if a['description'] == description:
                    if Verbose_Flag:
                        print("same description")
                    event_id=a['id']
                    print("existing event_id={}".format(event_id))
                    break
                else:
                    print("a['description']={0} message={1}".format(a['description'], message))
                    return

    if event_id:
        canvas_calender_event=update_calendar_event(course_id, start, end, title, message, location_name, location_address, event_id)
        print("Updated existing calendar event={}".format(canvas_calender_event['id']))
    else:
        canvas_calender_event=create_calendar_event(course_id, start, end, title, message, location_name, location_address)
        print("Created calendar event={}".format(canvas_calender_event['id']))

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

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    initialize(args)
    if Verbose_Flag:
        print("baseUrl={}".format(baseUrl))
        print("cortina_baseUrl={0}".format(cortina_baseUrl))

    course_id=args["canvas_course_id"]
    if Verbose_Flag:
        print("course_id={}".format(course_id))

    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))

    nocortina_arg=args["nocortina"]
    if Verbose_Flag:
        print("nocortina_arg={}".format(nocortina_arg))

    # nocortina - set if the user does not have a Cortina access key
    # if the nocortina arg is True, then disable the use of Cortina
    if nocortina_arg:
         nocortina=True

    if Verbose_Flag:
        print("nocortina={}".format(nocortina))

    json_filename=args["json"]
    process_event_from_JSON_file(json_filename)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
