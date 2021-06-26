#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./JSON_to_MODS.py [-c course_id] --json file.json [--cycle 1|2] [--credits 7.5|15.0|30.0|50.0] [--exam 1|2|3|4|5|6|7|8 or or the name of the exam] [--area area_of_degree] [--area2 area_of_second_degree] [--trita trita_string] [--school ABE|CBH|EECS|ITM|SCI]
#
# Purpose: The program creates a MODS file using the information from the arguments and a JSON file.
# The JSON file can be produced by extract_pseudo_JSON-from_PDF.py
#
# Output: outputs the MODS file: MODS.pdf
#
# Example:
#  enter data from a JSON file
# ./JSON_to_MODS.py -c 11  --json event.json
# ./JSON_to_MODS.py -c 11 --config config-test.json  --json oscar.json
#
# ./JSON_to_MODS.py -c 11  --json event.json --testing --exam 4
#
#
# The dates from Canvas are in ISO 8601 format.
# 
# 2021-06-25 G. Q. Maguire Jr.
# Base on earlier xmlGenerator.py and JSON_to_cover.py
#

import re
import sys

import json
import argparse
import os			# to make OS calls, here to get time zone info
#import time
import pprint

# for dealing with XML
from eulxml import xmlmap
from eulxml.xmlmap import load_xmlobject_from_file, mods
import lxml.etree as etree

from eulxml.xmlmap import  mods as modsFile
from xml.dom import minidom

#from collections import defaultdict

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
#----------------------------------------------------------------------

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


def transform_math_for_diva(html):
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


national_subject_categories_dict={
    '102': {'eng': ['Natural Sciences', 'Computer and Information Sciences'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap (Datateknik)']
            },
    '10201': {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Computer Sciences'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Datavetenskap (datalogi)']
            },

    '10202': {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Information Systems'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Systemvetenskap, informationssystem och informatik']
            },

    '10203': {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Bioinformatics (Computational Biology)'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Bioinformatik (beräkningsbiologi)']
            },

    '10204': {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Human Computer Interaction'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Människa-datorinteraktion (interaktionsdesign)']
            },

    '10205': {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Software Engineering'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Programvaruteknik']
            },

    '10206':  {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Computer Engineering'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Datorteknik']
            },
    '10207':  {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Computer Vision and Robotics (Autonomous Systems)'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Datorseende och robotik (autonoma system)']
            },
    '10208':  {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Language Technology (Computational Linguistics)'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Språkteknologi (språkvetenskaplig databehandling)']
            },
    '10209':  {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Media and Communication Technology'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Medieteknik']
            },

    '10299':  {'eng': ['Natural Sciences', 'Computer and Information Sciences', 'Other Computer and Information Science'],
              'swe':  ['Naturvetenskap', 'Data- och informationsvetenskap', 'Annan data- och informationsvetenskap']
            },

    '202': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik']
              },
    '20201': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', ''],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Robotteknik och automation Robotics']
              },
    '20202': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', 'Control Engineering'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Reglerteknik']
              },
    '20203': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', 'Communication Systems'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Kommunikationssystem']
              },
    '20204': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', 'Telecommunications'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Telekommunikation']
              },
    '20205': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', 'Signal Processing'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Signalbehandling']
              },
    '20206': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', 'Computer Systems'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Datorsystem']
              },
    '20207': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', 'Embedded Systems'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Inbäddad systemteknik']
              },
    '20299': {'eng': ['Engineering and Technology', 'Electrical Engineering, Electronic Engineering, Information Engineering', 'Other Electrical Engineering, Electronic Engineering, Information Engineering'],
              'swe': ['Teknik och teknologier', 'Elektroteknik och elektronik', 'Annan elektroteknik och elektronik']
              }
}


education_program_diva={
    '10522': {'eng': 'Bachelor of Science in Engineering',
              'swe': ''
              },
    '9800': {'eng': 'Bachelor of Science in Engineering -  Constructional Engineering and Design',
              'swe': ''
              },
    '9801': {'eng': 'Bachelor of Science in Engineering -  Constructional Engineering and Economics',
              'swe': ''
              },
    '9880': {'eng': 'Bachelor of Science in Engineering - Chemical Engineering',
              'swe': ''
              },
    '9989': {'eng': 'Bachelor of Science in Engineering - Computer Engineering and Economics',
              'swe': ''
              },

    '9921': {'eng': 'Bachelor of Science in Engineering - Computer Engineering',
              'swe': ''
              },

    '9990': {'eng': 'Bachelor of Science in Engineering - Computer Engineering',
              'swe': ''
              },
    '10751': {'eng': 'Bachelor of Science in Engineering - Constructional Engineering and Health',
              'swe': ''
              },
    '9949': {'eng': 'Bachelor of Science in Engineering - Electrical Engineering and Economics',
              'swe': ''
              },
    '9907': {'eng': 'Bachelor of Science in Engineering - Electrical Engineering',
              'swe': ''
              },
    '9948': {'eng': 'Bachelor of Science in Engineering - Electrical Engineering',
              'swe': ''
              },
    '9922': {'eng': 'Bachelor of Science in Engineering - Electronics and Computer Engineering',
              'swe': ''
              },
    '9992': {'eng': 'Bachelor of Science in Engineering - Engineering and Economics',
              'swe': ''
              },
    '9951': {'eng': 'Bachelor of Science in Engineering - Mechanical Engineering and Economics',
              'swe': ''
              },
    '9950': {'eng': 'Bachelor of Science in Engineering - Mechanical Engineering',
              'swe': ''
              },
    '9991': {'eng': 'Bachelor of Science in Engineering - Medical Technology',
              'swe': ''
              },
    '10523': {'eng': 'Bachelor of Science',
              'swe': ''
              },
    '10950': {'eng': 'Bachelor of Science - Architecture',
              'swe': ''
              },
    '9924': {'eng': 'Bachelor of Science - Business Engineering',
              'swe': ''
              },
    '17650': {'eng': 'Bachelor of Science - Energy and Environment',
              'swe': ''
              },
    '9925': {'eng': 'Bachelor of Science - Information and Communication Technology',
              'swe': ''
              },
    '9994': {'eng': 'Bachelor of Science - Medical Informatics',
              'swe': ''
              },
    '9805': {'eng': 'Bachelor of Science - Property Development and Agency',
              'swe': ''
              },
    '9804': {'eng': 'Bachelor of Science - Real Estate and Finance',
              'swe': ''
              },
    '9892': {'eng': 'Bachelor of Science - Simulation Technology and Virtual Design',
              'swe': ''
              },
    '10524': {'eng': 'Degree of Master',
              'swe': ''
              },
    '9858': {'eng': 'Degree of Master - Design and Building',
              'swe': ''
              },
    '9956': {'eng': 'Master of Science - Applied Logistics',
              'swe': ''
              },
    '9999': {'eng': 'Master of Science - Architectural Lighting Design',
              'swe': ''
              },
    '9997': {'eng': 'Master of Science - Computer Networks',
              'swe': ''
              },
    '9953': {'eng': 'Master of Science - Entrepreneurship and Innovation Management',
              'swe': ''
              },
    '9998': {'eng': 'Master of Science - Ergonomics and Human-Technology-Organisation',
              'swe': ''
              },
    '9954': {'eng': 'Master of Science - Product Realisation',
              'swe': ''
              },
    '9955': {'eng': 'Master of Science - Project Management and Operational Development',
              'swe': ''
              },
    '9996': {'eng': 'Master of Science - Work and Health',
              'swe': ''
              },
    '14553': {'eng': 'Teknologie magisterexamen - Teknik, hälsa och arbetsmiljöutveckling',
              'swe': ''
              },
    '10525': {'eng': 'Degree of Master',
              'swe': ''
              },
    '9850': {'eng': 'Degree of Master -  Architectural Enginering',
              'swe': ''
              },
    '28050': {'eng': 'Degree of Master -  Urbanism Studies',
              'swe': ''
              },
    '9882': {'eng': 'Degree of Master - Chemical Engineering for Energy and Environment',
              'swe': ''
              },
    '24400': {'eng': 'Degree of Master - Civil and Architectural Engineering',
              'swe': ''
              },
    '9864': {'eng': 'Degree of Master - Economics of Innovation and Growth',
              'swe': ''
              },
    '9863': {'eng': 'Degree of Master - Environmental Engineering and Sustainable Infrastructure',
              'swe': ''
              },
    '9862': {'eng': 'Degree of Master - Geodesy and Geoinformatics',
              'swe': ''
              },
    '9865': {'eng': 'Degree of Master - Infrastructure Engineering',
              'swe': ''
              },
    '9868': {'eng': 'Degree of Master - Land Management',
              'swe': ''
              },
    '9883': {'eng': 'Degree of Master - Macromolecular Materials',
              'swe': ''
              },
    '9885': {'eng': 'Degree of Master - Materials and Sensors System for Environmental Technologies',
              'swe': ''
              },
    '9884': {'eng': 'Degree of Master - Molecular Science and Engineering',
              'swe': ''
              },
    '9861': {'eng': 'Degree of Master - Real Estate Development and Financial Services',
              'swe': ''
              },
    '13400': {'eng': 'Degree of Master - Spatial Planning',
              'swe': ''
              },
    '9552': {'eng': 'Degree of Master - Sustainable Urban Planning and Design',
              'swe': ''
              },
    '9866': {'eng': 'Degree of Master - Transport Systems',
              'swe': ''
              },
    '13401': {'eng': 'Degree of Master - Urban Planning and Design',
              'swe': ''
              },
    '9867': {'eng': 'Degree of Master - Water System Technology',
              'swe': ''
              },
    '9977': {'eng': 'Master of Science - Aerospace Engineering',
              'swe': ''
              },
    '23002': {'eng': 'Master of Science - Applied and Computational Mathematics',
              'swe': ''
              },
    '10001': {'eng': 'Master of Science - Architectural Lighting Design and Health',
              'swe': ''
              },
    '9860': {'eng': 'Master of Science - Architecture',
              'swe': ''
              },
    '9894': {'eng': 'Master of Science - Computational and Systems Biology',
              'swe': ''
              },
    '9875': {'eng': 'Master of Science - Computational Chemistry and Computational Physics',
              'swe': ''
              },
    '9895': {'eng': 'Master of Science - Computer Science',
              'swe': ''
              },
    '9901': {'eng': 'Master of Science - Computer Simulation for Science and Engineering',
              'swe': ''
              },
    '9930': {'eng': 'Master of Science - Design and Implementation of ICT Products and Systems',
              'swe': ''
              },
    '9938': {'eng': 'Master of Science - Distributed Computing',
              'swe': ''
              },
    '9910': {'eng': 'Master of Science - Electric Power Engineering',
              'swe': ''
              },
    '9909': {'eng': 'Master of Science - Electrophysics',
              'swe': ''
              },
    '9928': {'eng': 'Master of Science - Embedded Systems',
              'swe': ''
              },
    '9983': {'eng': 'Master of Science - Engineeering Physics',
              'swe': ''
              },
    '9935': {'eng': 'Master of Science - Engineering and Management of Information Systems',
              'swe': ''
              },
    '9962': {'eng': 'Master of Science - Engineering Design',
              'swe': ''
              },
    '9965': {'eng': 'Master of Science - Engineering Materials Science',
              'swe': ''
              },
    '9982': {'eng': 'Master of Science - Engineering Mechanics',
              'swe': ''
              },
    '9969': {'eng': 'Master of Science - Environomical Pathways for Sustainable Energy Systems',
              'swe': ''
              },
    '9899': {'eng': 'Master of Science - Human-Computer Interaction',
              'swe': ''
              },
    '9873': {'eng': 'Master of Science - Industrial and Environmental Biotechnology',
              'swe': ''
              },
    '9959': {'eng': 'Master of Science - Industrial Engineering and Management',
              'swe': ''
              },
    '9929': {'eng': 'Master of Science - Information and Communication Systems Security',
              'swe': ''
              },
    '9966': {'eng': 'Master of Science - Innovative Sustainable Energy Engineering',
              'swe': ''
              },
    '9963': {'eng': 'Master of Science - Integrated Product Design',
              'swe': ''
              },
    '9934': {'eng': 'Master of Science - Interactive Systems Engineering',
              'swe': ''
              },
    '13450': {'eng': 'Master of Science - Internetworking',
              'swe': ''
              },
    '9896': {'eng': 'Master of Science - Machine Learning',
              'swe': ''
              },
    '9968': {'eng': 'Master of Science - Management and Engineering of Environment and Energy',
              'swe': ''
              },
    '9984': {'eng': 'Master of Science - Maritime Engineering',
              'swe': ''
              },
    '11254': {'eng': 'Master of Science - Materials Science and Engineering',
              'swe': ''
              },
    '9981': {'eng': 'Master of Science - Mathematics',
              'swe': ''
              },
    '9897': {'eng': 'Master of Science - Media Management',
              'swe': ''
              },
    '9898': {'eng': 'Master of Science - Media Technology',
              'swe': ''
              },
    '9874': {'eng': 'Master of Science - Medical Biotechnology',
              'swe': ''
              },
    '10003': {'eng': 'Master of Science - Medical Engineering',
              'swe': ''
              },
    '9931': {'eng': 'Master of Science - Nanotechnology',
              'swe': ''
              },
    '9980': {'eng': 'Master of Science - Naval Architecture',
              'swe': ''
              },
    '9911': {'eng': 'Master of Science - Network Services and Systems',
              'swe': ''
              },
    '9979': {'eng': 'Master of Science - Nuclear Energy Engineering',
              'swe': ''
              },
    '9914': {'eng': 'Master of Science - Nuclear Fusion Science and Engineering Physics',
              'swe': ''
              },
    '9927': {'eng': 'Master of Science - Photonics',
              'swe': ''
              },
    '9961': {'eng': 'Master of Science - Production Engineering and Management',
              'swe': ''
              },
    '9859': {'eng': 'Master of Science - Real Estate Management',
              'swe': ''
              },
    '9915': {'eng': 'Master of Science - School of Electrical Engineering (EES) - Master of Science - Research on Information and Communication Technologies',
              'swe': ''
              },
    '9900': {'eng': 'Master of Science - Scientific Computing',
              'swe': ''
              },
    '9932': {'eng': 'Master of Science - Software Engineering of Distributed Systems',
              'swe': ''
              },
    '9958': {'eng': 'Master of Science - Sustainable Energy Engineering',
              'swe': ''
              },
    '9964': {'eng': 'Master of Science - Sustainable Technology',
              'swe': ''
              },
    '9933': {'eng': 'Master of Science - System-on-Chip Design',
              'swe': ''
              },
    '9902': {'eng': 'Master of Science - Systems Biology',
              'swe': ''
              },
    '9912': {'eng': 'Master of Science - Systems, Control and Robotics',
              'swe': ''
              },
    '21652': {'eng': 'Master of Science - Transport and Geoinformation Technology',
              'swe': ''
              },
    '9970': {'eng': 'Master of Science - Turbomachinery Aeromechanic University Training',
              'swe': ''
              },
    '9978': {'eng': 'Master of Science - Vehicle Engineering',
              'swe': ''
              },
    '9913': {'eng': 'Master of Science - Wireless Systems',
              'swe': ''
              },
    '9939': {'eng': 'Master of Science -Communication Systems',
              'swe': ''
              },
    '10002': {'eng': 'Master of Science -Medical Imaging',
              'swe': ''
              },
    '9937': {'eng': 'Master of Science -Security and Mobile Computing',
              'swe': ''
              },
    '10521': {'eng': 'Higher Education Diploma',
              'swe': ''
              },
    '9802': {'eng': 'Higher Education Diploma - Construction Management',
              'swe': ''
              },
    '9803': {'eng': 'Higher Education Diploma - Constructional Technology and Real Estate Agency',
              'swe': ''
              },
    '10520': {'eng': 'Master of Architecture',
              'swe': ''
              },
    '9558': {'eng': 'Master of Architecture - Architecture',
              'swe': ''
              },
    '10500': {'eng': 'Master of Science in Engineering',
              'swe': ''
              },
    '9905': {'eng': 'Master of Science in Engineering -  Electrical Engineering',
              'swe': ''
              },
    '9871': {'eng': 'Master of Science in Engineering - Biotechnology',
              'swe': ''
              },
    '9878': {'eng': 'Master of Science in Engineering - Chemical Science and Engineering',
              'swe': ''
              },
    '9889': {'eng': 'Master of Science in Engineering - Computer Science and Technology',
              'swe': ''
              },
    '9942': {'eng': 'Master of Science in Engineering - Design and Product Realisation',
              'swe': ''
              },
    '9943': {'eng': 'Master of Science in Engineering - Energy and Environment',
              'swe': ''
              },
    '9973': {'eng': 'Master of Science in Engineering - Engineering and of Education',
              'swe': ''
              },
    '9944': {'eng': 'Master of Science in Engineering - Industrial Engineering and Management',
              'swe': ''
              },
    '9918': {'eng': 'Master of Science in Engineering - Information and Communication Technology',
              'swe': ''
              },
    '9946': {'eng': 'Master of Science in Engineering - Materials Design and Engineering',
              'swe': ''
              },
    '9945': {'eng': 'Master of Science in Engineering - Mechanical Engineering',
              'swe': ''
              },
    '9890': {'eng': 'Master of Science in Engineering - Media Technology',
              'swe': ''
              },
    '9987': {'eng': 'Master of Science in Engineering - Medical Engineering',
              'swe': ''
              },
    '9919': {'eng': 'Master of Science in Engineering - Microelectronics',
              'swe': ''
              },
    '10526': {'eng': 'Master of Science in Engineering - Urban Management',
              'swe': ''
              },
    '9974': {'eng': 'Master of Science in Engineering - Vehicle Engineering',
              'swe': ''
              },
    '9975': {'eng': 'Master of Science in Engineering -Engineering Physics',
              'swe': ''
              },
    '29550': {'eng': 'Other programmes',
              'swe': ''
              },
    '29551': {'eng': 'Subject Teacher Education in Technology, Secondary Education',
              'swe': ''
              },
    '9557': {'eng': 'Z - School of Architecture and the Built Environment (ABE)',
              'swe': ''
              },
    '9852': {'eng': 'School of Architecture and the Built Environment (ABE)  - Master of Science in Engineering',
              'swe': ''
              }
}

# Subject/course codes
# <option value="10260">Accelerator Technique</option>
# <option value="10306">Aeronautical Engineering</option>
# <option value="10261">Analytical Chemistry</option>
# <option value="10262">Antenna Systems Technology</option>
# <option value="10423">Applied Information Technology</option>
# <option value="10424">Applied Logistics</option>
# <option value="10426">Applied Material Physics</option>
# <option value="10427">Applied Materials Technology</option>
# <option value="10425">Applied Mathematical Analysis</option>
# <option value="28053">Applied Mathematics and Industrial Economics</option>
# <option value="10422">Applied Physics</option>
# <option value="10428">Applied Process Metallurgy</option>
# <option value="10369">Applied Thermodynamics</option>
# <option value="10429">Applied Thermodynamics</option>
# <option value="10258">Architectural Lighting Design and Health</option>
# <option value="10349">Architectural Lighting Design</option>
# <option value="10264">Architecture</option>
# <option value="10397">Automatic Control</option>
# <option value="10269">Biocomposites</option>
# <option value="10410">Biomechanics</option>
# <option value="10270">Biomedical Engineering</option>
# <option value="10253">Biotechnology</option>
# <option value="10271">Biotechnology</option>
# <option value="10273">Building and Real Estate Economics</option>
# <option value="10484">Building Design</option>
# <option value="10275">Building Materials</option>
# <option value="10471">Building Services Engineering and Energy</option>
# <option value="10277">Building Technology</option>
# <option value="10449">Building Technology</option>
# <option value="10266">Built Environment Analysis</option>
# <option value="10485">Built Environment</option>
# <option value="10371">Casting of Metals</option>
# <option value="10336">Ceramic Materials</option>
# <option value="10337">Ceramics</option>
# <option value="10335">Chemical Engineering</option>
# <option value="10472">Chemical Science and Engineering</option>
# <option value="10344">Circuit Electronics</option>
# <option value="10481">Civil Engineering Management</option>
# <option value="10338">Communication Networks</option>
# <option value="10340">Communication Theory</option>
# <option value="10339">Communications Systems</option>
# <option value="10420">Computational Thermodynamics</option>
# <option value="10279">Computer and Systems Sciences</option>
# <option value="10281">Computer Communication</option>
# <option value="10452">Computer Engineering with Business Economics</option>
# <option value="10453">Computer Engineering with Industrial Economy</option>
# <option value="10460">Computer Networks and Communication</option>
# <option value="10282">Computer Networks</option>
# <option value="10459">Computer Networks</option>
# <option value="10280">Computer Science</option>
# <option value="10283">Computer Systems</option>
# <option value="10454">Computer Technology and Graphic Programming</option>
# <option value="10456">Computer Technology and Real Time Programming</option>
# <option value="10455">Computer Technology and Software Engineering</option>
# <option value="10457">Computer Technology, Networks and Security</option>
# <option value="10458">Computer Technology, Program- and System Development</option>
# <option value="10268">Concrete Structures</option>
# <option value="10341">Condensed Matter Physics</option>
# <option value="10274">Construction Management and Economics</option>
# <option value="10278">Construction Management</option>
# <option value="10448">Constructional Design</option>
# <option value="10450">Constructional Engineering and Design with Business Economics</option>
# <option value="10451">Constructional Engineering and Design</option>
# <option value="10342">Corrosion Science</option>
# <option value="10284">Design and Building</option>
# <option value="10445">Design and Product Development</option>
# <option value="10446">Design and Vehicle Engineering</option>
# <option value="10285">Discrete Mathematics</option>
# <option value="10257">Economics of Innovation and Growth</option>
# <option value="10289">Electric Power Systems</option>
# <option value="10463">Electrical Engineering with Industrial Economy</option>
# <option value="10295">Electrical Engineering</option>
# <option value="10290">Electrical Machines and Drives</option>
# <option value="10291">Electrical Machines and Power Electronic</option>
# <option value="10287">Electrical Measurements</option>
# <option value="10288">Electrical Plant Engineering</option>
# <option value="10292">Electroacoustics</option>
# <option value="10418">Electromagnetic Theory</option>
# <option value="10294">Electronic System Design</option>
# <option value="10293">Electronic- and Computer Systems</option>
# <option value="10461">Electronics and Communications</option>
# <option value="10462">Electronics Design</option>
# <option value="10466">Embedded System Design</option>
# <option value="10296">Energy and Climate Studies</option>
# <option value="10297">Energy and Furnace Technology</option>
# <option value="10298">Energy Processes</option>
# <option value="10251">Energy Technology</option>
# <option value="10487">Engineering and Management</option>
# <option value="10415">Engineering Material Physics</option>
# <option value="10488">Engineering Physics</option>
# <option value="10255">Entrepreneurship and Innovation Management</option>
# <option value="10376">Environmental Assessment</option>
# <option value="10377">Environmental Strategies</option>
# <option value="10300">Ergonomics</option>
# <option value="10447">Facilities for Infrastructure</option>
# <option value="10304">Fiber Technology</option>
# <option value="10464">Finance</option>
# <option value="28052">Financial Mathematics</option>
# <option value="10402">Fluid Mechanics</option>
# <option value="10316">Foundry Technology</option>
# <option value="10309">Fusion Plasma Physics</option>
# <option value="10314">Geodesy</option>
# <option value="10315">Geoinformatics</option>
# <option value="10317">Ground Water Chemistry</option>
# <option value="10440">Heat Transfer</option>
# <option value="10435">Heating and Ventilating Technology</option>
# <option value="10321">High Voltage Engineering</option>
# <option value="10439">Highway Engineering</option>
# <option value="10412">History of Technology</option>
# <option value="10380">Human - Computer Interaction</option>
# <option value="10437">Hydraulic Engineering</option>
# <option value="10322">Industrial Biotechnology</option>
# <option value="10469">Industrial Business Administration and Manufacturing</option>
# <option value="10327">Industrial Control Systems</option>
# <option value="10323">Industrial Design</option>
# <option value="10324">Industrial Ecology</option>
# <option value="10325">Industrial Economics and Management</option>
# <option value="10468">Industrial Economy and Entrepreneurship</option>
# <option value="10467">Industrial IT</option>
# <option value="10329">Information and Communication Technology</option>
# <option value="10328">Information and Software Systems</option>
# <option value="10330">Information Technology</option>
# <option value="10470">Innovation and Design</option>
# <option value="10382">Inorganic Chemistry</option>
# <option value="10331">Integrated Product Development</option>
# <option value="10313">Internal Combustion Engineering</option>
# <option value="10354">Land and Water Resources</option>
# <option value="10254">Land Management</option>
# <option value="10352">Lightweight Structures</option>
# <option value="10475">Logistics, Business Administration and Manufacturing</option>
# <option value="10350">Logistics</option>
# <option value="10356">Machine Design</option>
# <option value="10351">Machine Elements</option>
# <option value="10355">Machine Elements</option>
# <option value="10363">Material Physics</option>
# <option value="10360">Materials and Process Design</option>
# <option value="10444">Materials Design and Engineering</option>
# <option value="10361">Materials Processing</option>
# <option value="10478">Materials Science and Engineering</option>
# <option value="10359">Mathematical Statistics</option>
# <option value="10358">Mathematics</option>
# <option value="10473">Mechanical Design</option>
# <option value="10477">Mechanical Engineering with Industrial Economy</option>
# <option value="10476">Mechanical Engineering</option>
# <option value="10368">Mechanical Metallurgy</option>
# <option value="10367">Mechanics</option>
# <option value="10479">Mechatronics and Robotics</option>
# <option value="10370">Mechatronics</option>
# <option value="10366">Media Technology</option>
# <option value="10365">Medical Engineering</option>
# <option value="10364">Medical Imaging</option>
# <option value="10265">Metal Working</option>
# <option value="10375">Micro Modelling in Process Science</option>
# <option value="10373">Microcomputer Systems</option>
# <option value="10374">Microelectronics and Applied Physics</option>
# <option value="10480">Mobile Communications Systems</option>
# <option value="10378">Molecular Biotechnology</option>
# <option value="10379">Music Acoustics</option>
# <option value="10353">Naval Systems</option>
# <option value="10346">Nuclear Chemistry</option>
# <option value="10395">Nuclear Reactor Engineering</option>
# <option value="10381">Numerical Analysis</option>
# <option value="10383">Optics</option>
# <option value="10384">Optimization and Systems Theory</option>
# <option value="10385">Organic Chemistry</option>
# <option value="10386">Paper Technology</option>
# <option value="10305">Philosophy</option>
# <option value="10308">Photonics with Microwave Engineering</option>
# <option value="10312">Physical Chemistry</option>
# <option value="10311">Physical Electrotechnology</option>
# <option value="10372">Physical Metallurgy</option>
# <option value="10310">Physics</option>
# <option value="10431">Planning of Traffic and Transportation</option>
# <option value="10387">Plasma Physics</option>
# <option value="10389">Polymer Technology</option>
# <option value="10388">Polymeric Materials</option>
# <option value="10286">Power Electronics</option>
# <option value="10362">Process Science of Materials</option>
# <option value="10390">Product Realisation and Management</option>
# <option value="10326">Production Engineering</option>
# <option value="10319">Project in Fluid Power</option>
# <option value="10392">Project Management and Operational Development</option>
# <option value="10357">Pulp Technology</option>
# <option value="10394">Radio Communication Systems</option>
# <option value="10393">Radio Electronics</option>
# <option value="10333">Railway Operation</option>
# <option value="10334">Railway Technology</option>
# <option value="10347">Reactor Safety</option>
# <option value="10252">Real Estate Development and Land Law</option>
# <option value="10302">Real Estate Economics</option>
# <option value="10465">Real Estate Management</option>
# <option value="10303">Real Estate Planning</option>
# <option value="10345">Refrigerating Engineering</option>
# <option value="10396">Regional Planning</option>
# <option value="10421">Reliability Centred Asset Management for Electrical Power Systems</option>
# <option value="10398">Risk and Safety</option>
# <option value="10407">Safety Research</option>
# <option value="10267">Scientific Computing</option>
# <option value="10318">Semiconductor Materials</option>
# <option value="10400">Signal Processing</option>
# <option value="10483">Software Design</option>
# <option value="10391">Software Engineering</option>
# <option value="10482">Software Engineering</option>
# <option value="10332">Soil and Rock Mechanics</option>
# <option value="10320">Solid Mechanics</option>
# <option value="10301">Solid State Electronics</option>
# <option value="10348">Sound and Image Processing</option>
# <option value="10443">Space and Plasma Physics</option>
# <option value="10399">Space Physics</option>
# <option value="10408">Speech Communication</option>
# <option value="10409">Speech Communication</option>
# <option value="10403">Steel Structures</option>
# <option value="10272">Structural Design and Bridges</option>
# <option value="10474">Structural Engineering</option>
# <option value="10276">Structural Mechanics and Engineering</option>
# <option value="10442">Surface Chemistry</option>
# <option value="10441">Surface Coating Technology</option>
# <option value="10414">Surveying</option>
# <option value="10436">Sustainable Buildings</option>
# <option value="10750">Sustainable development</option>
# <option value="10486">System Engineering</option>
# <option value="10404">System-on-Chip</option>
# <option value="10405">Systems Analysis and Economics</option>
# <option value="10406">Systems Engineering</option>
# <option value="10413">Technical Acoustics</option>
# <option value="10411">Technology and Learning</option>
# <option value="10489">Tele and Data Communication</option>
# <option value="10417">Telecommunication Systems</option>
# <option value="10416">Teleinformatics</option>
# <option value="10419">Theoretical Physics</option>
# <option value="10343">Thermal Engineering</option>
# <option value="10430">Traffic and Transport Planning</option>
# <option value="10432">Transport- and Location Analysis</option>
# <option value="20650">Urban and Regional Planning</option>
# <option value="10401">Urban Planning and Design</option>
# <option value="10307">Vehicle Engineering</option>
# <option value="10438">Water Resources Engineering</option>
# <option value="10259">Water, Sewage and Waste</option>
# <option value="10433">Wood Chemistry</option>
# <option value="10434">Wood Technology and Processing</option>
# <option value="10263">Work Science</option></select></div></div>


def process_dict_to_XML(content, extras):
    global testing
    #
    import xml.etree.ElementTree as ET
    root = ET.Element("modsCollection")
    root.set("xmlns", "http://www.loc.gov/mods/v3")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:schemaLocation", "http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-2.xsd")
    mods = ET.Element("mods")
    root.append(mods)
    mods.set("xmlns", "http://www.loc.gov/mods/v3")
    mods.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    mods.set("xmlns:xlink", "http://www.w3.org/1999/xlink")
    mods.set("version", "3.2")
    mods.set("xsi:schemaLocation", "http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-2.xsd")
    #genre
    genre2= ET.Element("genre")
    mods.append(genre2)
    genre2.set("authority" , "diva")
    genre2.set("type", "publicationTypeCode")
    genre2.text="studentThesis"
    #
    genre= ET.Element("genre")
    mods.append(genre)
    genre.set("authority" , "diva")
    genre.set("type", "publicationType")
    genre.set("lang", "swe")
    genre.text="Studentuppsats (Examensarbete)"
    #
    genre3= ET.Element("genre")
    mods.append(genre3)
    genre3.set("authority" , "diva")
    genre3.set("type", "publicationType")
    genre3.set("lang", "eng")
    genre3.text="Student thesis"
    #
    genre4= ET.Element("genre")
    mods.append(genre4)
    genre4.set("authority" , "diva")
    genre4.set("type", "publicationType")
    genre4.set("lang", "nor")
    genre4.text="Oppgave"
    #
    author_names=list()
    for i in range(1, 10):
        which_author="Author{}".format(i)
        author=content.get(which_author, None)
        if author:
            writer = ET.Element("name")
            mods.append(writer)
            #
            writer.set("type", "personal")
            local_user_Id=author.get('Local User Id')
            if local_user_Id:
                writer.set("authority", "kth")
                writer.set("xlink:href", local_user_Id)
            last_name=author.get('Last name', None)
            if last_name:
                name = ET.SubElement(writer, "namePart")
                name.set("type", "family")
                name.text=last_name
            #
            first_name=author.get('First name', None)        
            if first_name:
                fn = ET.SubElement(writer, "namePart")
                fn.set("type", "given")
                fn.text=first_name
            #
            #<description>orcid.org=0000-0002-6066-746X</description>
            orcid=author.get('ORCiD', None)
            if orcid:
                orcid_entry=ET.SubElement(writer, "description")
                orcid_entry.text="orcid.org={}".format(orcid)
                #
            email=author.get('E-mail', None)
            if email:
                mail = ET.SubElement(writer, "description")
                mail.text = "email={}".format(email)

            role =ET.SubElement(writer, "role")
            roleTerm = ET.SubElement(role, "roleTerm")
            roleTerm.set("type" , "code")
            roleTerm.set("authority" , "marcrelator")
            roleTerm.text ="aut"
        else:                   # if there was no such author, then stop looping
            break
    #
    #Examinor
    # "Examiner1": {"Last name": "Maguire Jr.", "First name": "Gerald Q.", "Local User Id": "u1d13i2c", "E-mail": "maguire@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science ", "L2": "Computer Science"}}
    examiner_info=content.get('Examiner1')
    if examiner_info:
        examinator = ET.Element("name")
        mods.append(examinator)
        examinator.set("type", "personal")
        local_user_Id=examiner_info.get('Local User Id')
        if local_user_Id:
            examinator.set("authority", "kth")
            examinator.set("xlink:href", local_user_Id)
        last_name=examiner_info.get('Last name', None)
        if last_name:
            name = ET.SubElement(examinator , "namePart")
            name.set("type", "family")
            name.text=last_name
        #
        first_name=examiner_info.get('First name', None)        
        if first_name:
            fn = ET.SubElement(examinator , "namePart")
            fn.set("type", "given")
            fn.text=first_name
            #
        email=examiner_info.get('E-mail', None)
        if email:
            mail = ET.SubElement(examinator , "description")
            mail.text = "email={}".format(email)

        #<description>orcid.org=0000-0002-6066-746X</description>
        orcid=examiner_info.get('ORCiD', None)
        if orcid:
            orcid_entry=ET.SubElement(examinator , "description")
            orcid_entry.text="orcid.org={}".format(orcid)
        #
        e_org=examiner_info.get('organisation')
        if e_org:
            e_org_l1=e_org.get('L1')
            e_org_l2=e_org.get('L2')
            if e_org_l1 and e_org_l2:
                organization="{0}, {1}".format(e_org_l1.strip(), e_org_l2.strip())
            elif  e_org_l1 and not e_org_l2:
                organization="{0}".format(e_org_l1.strip())
            else:
                organization=None
            #\
            if organization:
                org = ET.SubElement(examinator , "affiliation")
                org.text = organization
                examiner_organization=organization
        #
        # job = ET.SubElement(examinator , "namePart")
        # job.set("type", "termsOfAddress")
        # job.text = content.get("jobTitle_examinar")
        #
        role=ET.SubElement(examinator, "role")
        roleTerm=ET.SubElement(role, "roleTerm")
        roleTerm.set("type" , "code")
        roleTerm.set("authority" , "marcrelator")
        roleTerm.text ="mon"

    #"Supervisor1": {"Last name": "Västberg", "First name": "Anders", "Local User Id": "u1ft3a12", "E-mail": "vastberg@kth.se", "organisation": {"L1": "School of Electrical Engineering and Computer Science ", "L2": "Computer Science"}}
    supervisr_names=list()
    for i in range(1, 10):
        which_supervisor="Supervisor{}".format(i)
        supervisor=content.get(which_supervisor, None)
        if supervisor:
            #supervisor
            handledare = ET.Element("name")
            mods.append(handledare)

            last_name=supervisor.get('Last name', None)
            if last_name:
                handledare.set("type", "personal")
                local_user_Id=supervisor.get('Local User Id')
                if local_user_Id:
                    handledare.set("authority", "kth")
                    handledare.set("xlink:href", local_user_Id)

                name = ET.SubElement(handledare , "namePart")
                name.set("type", "family")
                name.text= last_name

            first_name=supervisor.get('First name', None)
            if first_name:
                fn = ET.SubElement(handledare , "namePart")
                fn.set("type", "given")
                fn.text = first_name

            s_org=supervisor.get('organisation')
            if s_org:
                s_org_l1=s_org.get('L1')
                s_org_l2=s_org.get('L2')
                if s_org_l1 and s_org_l2:
                    organization="{0}, {1}".format(s_org_l1, s_org_l2)
            elif  s_org_l1 and not s_org_l2:
                organization="{0}".format(s_org_l1)
            else:
                organization=None

            if organization:
                org = ET.SubElement(handledare , "affiliation")
                org.text = organization

            email=supervisor.get('E-mail', None)
            if email:
                mail = ET.SubElement(handledare, "description")
                mail.text = "email={}".format(email)

            # jobh = ET.SubElement(handledare , "namePart")
            # jobh.set("type", "termsOfAddress")
            # jobh.text = content.get("jobTitle-en_supervisor")

            role =ET.SubElement(handledare , "role")
            roleTerm = ET.SubElement(role , "roleTerm")
            roleTerm.set("type" , "code")
            roleTerm.set("authority" , "marcrelator")
            roleTerm.text ="ths"
        else:                   # if there was no such supervisor, then stop looping
            break

    
    #organization
    orglist = []
    organisation = ET.Element("name")
    mods.append(organisation)
    for word in examiner_organization.split(","):
        org = ET.SubElement(organisation, "namePart")
        org.text = word
    role =ET.SubElement(organisation , "role")
    roleTerm = ET.SubElement(role , "roleTerm")
    roleTerm.set("type" , "code")
    roleTerm.set("authority" , "marcrelator")
    roleTerm.text ="pbl"

    # "Title": {"Main title": "This is the title in the language of the thesis", "Subtitle": "An subtitle in the language of the thesis", "Language": "eng"}, "Alternative title": {"Main title": "Detta är den svenska översättningen av titeln", "Subtitle": "Detta är den svenska översättningen av undertiteln", "Language": "swe"}
    title=content.get('Title', None)
    if title:
        thesis_main_title=title.get('Main title', None)
        language=title.get('Language', None)
        if language is None:
            language='eng'
            print("no language specied, guessing English")

        thesis_main_subtitle=title.get('Subtitle', None)

        #title and subtitle 
        heading = ET.Element("titleInfo ")
        mods.append(heading)
        heading.set("lang", language)
        name = ET.SubElement(heading , "title")
        name.text =  thesis_main_title
        if thesis_main_subtitle:
            subname = ET.SubElement(heading , "subTitle")
            subname.text = thesis_main_subtitle
   
    # <titleInfo type="alternative"
    alternative_title=content.get('Alternative title', None)
    if alternative_title:
        alternative_main_title=alternative_title.get('Main title', None)
        alternative_thesis_main_subtitle=alternative_title.get('Subtitle', None)

        alternative_language=alternative_title.get('Language', None)
        if alternative_language is None:
            alternative_language='swe'
            print("no language specied, guessing Swedish")

        heading2 = ET.Element("titleInfo ")
        mods.append(heading2)
        heading2.set("lang", alternative_language)
        heading2.set("type", "alternative")
        name = ET.SubElement(heading2, "title")
        name.text =  alternative_main_title
        if alternative_thesis_main_subtitle:
            subname = ET.SubElement(heading2, "subTitle")
            subname.text = alternative_thesis_main_subtitle

    #keywords
    keywords=content.get('keywords', None)
    if keywords:
        number_of_abstracts=len(keywords)
        if number_of_abstracts > 0:
            for lang in keywords:
                keyterms = ET.Element("subject ")
                mods.append(keyterms)
                keyterms.set("lang", lang)
                keywords_text=keywords[lang]
                keywords_text=keywords_text.replace('\n', ' ') # replace newlines with spaces
                for word in keywords_text.split(","):
                    topic= ET.SubElement(keyterms, "topic")
                    word=word.strip() # remove starting and ending white space
                    topic.text =  word.replace(",", "")

    abstracts=content.get('abstracts', None)
    if abstracts:
        number_of_abstracts=len(abstracts)
        if number_of_abstracts > 0:
            for lang in abstracts:
                abs = ET.Element("abstract ")
                mods.append(abs)
                abs.set("lang", lang)

                abstract_text=abstracts[lang]
                # take care of URLs
                if abstract_text.find('\\url{') >= 0:
                    abstract_text=transform_urls(abstract_text)

                # transform equations
                if mathincluded(abstract_text):
                    abstract_text=transform_math_for_diva(abstract_text)
                abs.text =  abstract_text

    other_info=content.get('Other information', None)
    if other_info:
        physical_description = ET.Element("physicalDescription")
        form = ET.SubElement(physical_description, "form")
        form.set("authority", "marcform")
        form.text="electronic"
        number_of_pages=other_info.get('Number of pages', None)
        if number_of_pages:
            extent = ET.SubElement(physical_description, "extent")
            extent.text=number_of_pages
        mods.append(physical_description)

        #<place><placeTerm>Stockholm</placeTerm></place><publisher>KTH Royal Institute of Technology</publisher>
        originInfo = ET.Element("originInfo")
        mods.append(originInfo)
        place = ET.SubElement(originInfo, "place")
        placeTerm = ET.SubElement(place, "placeTerm")
        placeTerm.text="Stockholm"
        publisher = ET.SubElement(originInfo, "publisher")
        publisher.text="KTH Royal Institute of Technology"

        year=other_info.get('Year', None)
        if year:
            date_issued = ET.SubElement(originInfo, "dateIssued")
            date_issued.text=year

        presentation_info=content.get('Presentation', None)
        if presentation_info:
            # <dateOther type="defence">2021-03-31T15:00:00</dateOther>
            datetime_of_presentation=presentation_info.get('Date', None)
            if datetime_of_presentation:
                defence = ET.SubElement(originInfo, "dateOther")
                defence.set('type', "defence")
                offset=datetime_of_presentation.find(' ')
                if offset > 0:
                    datetime_of_presentation=datetime_of_presentation[0:offset]+'T'+datetime_of_presentation[offset+1:]+':00'
                    defence.text=datetime_of_presentation



    type_of_resource = ET.Element("typeOfResource")
    type_of_resource.text="text"
    mods.append(type_of_resource)

    x=extras.get('trita', None)
    if x:
        trita = x
    else:
        trita = None

    relatedItem = ET.Element("relatedItem ")
    relatedItem.set('type', "series")
    ti = ET.SubElement(relatedItem, "titleInfo")
    series_title=ET.SubElement(ti, "title")
    # split trita string into series and number
    year_string="{}:".format(year)
    offset_to_number=trita.find(year_string)
    if offset_to_number >= 0:
        series_title.text=trita[0:offset_to_number-1]
        if testing:             # for testing we have to use a series from the old version of DiVA
            series_title.text="TRITA-ICT-EX"
    series_id=ET.SubElement(ti, "identifier")
    series_id.set('type', "local")
    if testing:             # for testing we have to use a series from the old version of DiVA
        series_id.text="5952"
    else:
        series_id.text="16855"    # corresponds to the series: TRITA-EECS-EX

    series_number=ET.SubElement(ti, "identifier")
    series_number.set('type', "issue number")
    series_number.text=trita[offset_to_number:]
    mods.append(relatedItem)

    # "Degree": {"Educational program": "Degree Programme in Media Technology", "Level": "2", "Course code": "DA231X", "Credits": "30.0", "Exam": "Degree of Master of Science in Engineering", "subjectArea": "Media Technology"}
    # <note type="level" lang="swe">Självständigt arbete på avancerad nivå (masterexamen)</note><note type="universityCredits" lang="swe">20 poäng / 30 hp</note><location>
    degree_info=content.get('Degree', None)
    if degree_info:
        level = ET.Element("note")
        level.set('lang', "swe")
        level.set('type', "level")
        #level.text="Självständigt arbete på avancerad nivå (masterexamen)"
        level.text="Självständigt arbete på grundnivå (kandidatexamen)"
        mods.append(level)

        # <note type="degree" lang="en">Degree of Doctor of Philosophy</note><note type="degree" lang="sv">Filosofie doktorsexamen</note><language objectPart="defence">
        exam_info=degree_info.get('Exam', None)
        degree = ET.Element("note")
        degree.set('lang', "eng")
        degree.set('type', "degree")
        degree.text=exam_info
        mods.append(degree)

        # the following is hand crafted for a test
        educational_program=ET.Element("subject")
        educational_program.set('lang', "swe")
        educational_program.set('xlink:href', "9925")
        ed_topic=ET.SubElement(educational_program, "topic")
        ed_topic.text="Teknologie kandidatexamen - Informations- och kommunikationsteknik"
        ed_topic1=ET.SubElement(educational_program, "genre")
        ed_topic1.text="Educational program"
        mods.append(educational_program)

        educational_program=ET.Element("subject")
        educational_program.set('lang', "eng")
        educational_program.set('xlink:href', "9925")
        ed_topic=ET.SubElement(educational_program, "topic")
        ed_topic.text="Bachelor of Science - Information and Communication Technology"
        ed_topic1=ET.SubElement(educational_program, "genre")
        ed_topic1.text="Educational program"
        mods.append(educational_program)

        educational_program=ET.Element("subject")
        educational_program.set('lang', "swe")
        educational_program.set('xlink:href', "10329")
        ed_topic=ET.SubElement(educational_program, "topic")
        ed_topic.text="Informations- och kommunikationsteknik"
        ed_topic1=ET.SubElement(educational_program, "genre")
        ed_topic1.text="Subject/course"
        mods.append(educational_program)
        
        educational_program=ET.Element("subject")
        educational_program.set('lang', "eng")
        educational_program.set('xlink:href', "10329")
        ed_topic=ET.SubElement(educational_program, "topic")
        ed_topic.text="Information and Communication Technology"
        ed_topic1=ET.SubElement(educational_program, "genre")
        ed_topic1.text="Subject/course"
        mods.append(educational_program)

    credits = ET.Element("note")
    credits.set('lang', "swe")
    credits.set('type', "universityCredits")
    #credits.text="20 poäng / 30 hp"
    credits.text="10 poäng / 15 hp"
    mods.append(credits)

    # <language><languageTerm type="code" authority="iso639-2b">eng</languageTerm></language><note type="venue">Ka-Sal C (Sven-Olof Öhrvik), Kistagången 16, Electrum 1, våningsplan 2, KTH Kista, Stockholm</note>
    # "Presentation": {"Date": "2021-06-18 11:00", "Language": "eng", "Room": "via Zoom https://kth-se.zoom.us/j/61684700718", "Address": "Isafjordsgatan 22 (Kistagången 16)", "City": "Stockholm"}
    #<language objectPart="defence"><languageTerm type="code" authority="iso639-2b">eng</languageTerm></language>
    presentation_info=content.get('Presentation', None)
    if presentation_info:
        lang_of_presentation=presentation_info.get('Language', None)
        if lang_of_presentation:
            language = ET.Element("language")
            language.set('objectPart', "defence")
            languageTerm=ET.SubElement(language, "languageTerm")
            languageTerm.set('type', "code")
            languageTerm.set('authority', "iso639-2b")
            languageTerm.text=lang_of_presentation
            mods.append(language)

            presentation_room=presentation_info.get('Room', None)
            presentation_address=presentation_info.get('Address', None)
            presentation_city=presentation_info.get('City', None)
            if presentation_room:
                venue = ET.Element("note")
                venue.set('type', "venue")
                venue.text=presentation_room
                if presentation_address:
                    venue.text=venue.text+','+presentation_address
                if presentation_city:
                    venue.text=venue.text+','+presentation_city
                mods.append(venue)

    # {"Partner_name": "SVT Interaktiv"},
    #    <note type="cooperation">Saab AB</note>
    cooperation_info=content.get('Cooperation', None)
    if cooperation_info:
        partner_info=cooperation_info.get('Partner_name', None)
        if partner_info:
            partner = ET.Element("note")
            partner.set('type', "cooperation")
            partner.text=partner_info
            mods.append(partner)

    #<subject lang="eng" authority="hsv" xlink:href="10201"><topic>Natural Sciences</topic><topic>Computer and Information Sciences</topic><topic>Computer Sciences</topic></subject><subject lang="swe" authority="hsv" xlink:href="10201"><topic>Naturvetenskap</topic><topic>Data- och informationsvetenskap</topic><topic>Datavetenskap (datalogi)</topic></subject><subject lang="eng" authority="hsv" xlink:href="20205"><topic>Engineering and Technology</topic><topic>Electrical Engineering, Electronic Engineering, Information Engineering</topic><topic>Signal Processing</topic></subject><subject lang="swe" authority="hsv" xlink:href="20205"><topic>Teknik och teknologier</topic><topic>Elektroteknik och elektronik</topic><topic>Signalbehandling</topic></subject>
    # National Subject Categories": "10201, 10206, 10204, 10209"}
    national_subject_categories=content.get('National Subject Categories', None)
    print("national_subject_categories={}".format(national_subject_categories))
    if national_subject_categories:
        categories=national_subject_categories.split(',')
        for c in categories:
            hsv_category=c.strip()
            cat_info=national_subject_categories_dict.get(hsv_category, None)
            if cat_info:
                subject=ET.Element("subject")
                subject.set('lang',"eng")
                subject.set('authority',"hsv")
                subject.set("xlink:href", hsv_category)

                eng_topics=cat_info.get('eng', None)
                if eng_topics:
                    num_topics=len(eng_topics)
                    if num_topics > 0:
                        for topic in eng_topics:
                            st=ET.SubElement(subject, "topic")
                            st.text=topic
                mods.append(subject)
                #
                subject=ET.Element("subject")
                subject.set('lang',"swe")
                subject.set('authority',"hsv")
                subject.set("xlink:href", hsv_category)

                eng_topics=cat_info.get('swe', None)
                if eng_topics:
                    num_topics=len(eng_topics)
                    if num_topics > 0:
                        for topic in eng_topics:
                            st=ET.SubElement(subject, "topic")
                            st.text=topic
                mods.append(subject)

    xmlData = ET.tostring(root)
    return xmlData


def main(argv):
    global Verbose_Flag
    global testing
    global course_id


    argp = argparse.ArgumentParser(description="JSON_to_MODS.py: to make a MODS file")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument("--config", type=str, default='config.json',
                      help="read configuration from file")

    argp.add_argument("-c", "--canvas_course_id", type=int,
                      # required=True,
                      help="canvas course_id")

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

    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    # If there is a course number argument, then initializae in prepartion for Canvas API calls
    # x=args["canvas_course_id"]
    # if x:
    #     if Verbose_Flag:
    #         print("baseUrl={}".format(baseUrl))

    # course_id=args["canvas_course_id"]
    # print("course_id={}".format(course_id))

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

    d=None
    json_filename=args["json"]
    if json_filename:
        with open(json_filename, 'r', encoding='utf-8') as json_FH:
            try:
                json_string=json_FH.read()
                d=json.loads(json_string)
            except:
                print("Error in reading={}".format(event_string))
                return

            if Verbose_Flag:
                print("read JSON: {}".format(d))

        if d:
            xmlData=process_dict_to_XML(d, extras)
            if xmlData:             # write out results
                with open('modsXML.xml','wb+') as filehandle:
                    filehandle.write(xmlData)
                    filehandle.close()
                    if Verbose_Flag:
                        print("wrote MODS XML: {}".format(xmlData))
    else:
        print("Unknown source for the JSON: {}".format(json_filename))
        return
    

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


def main(inputjson,outputdir):
    #os.chdir("../../../../../../../../output/parse_result")
    #print("currently mods module at directory: "+os.getcwd())

    with open('../../../../output/parse_result/cache/modsXML.xml','wb+') as filehandle:
        xmlData=modsData(inputjson)
        filehandle.write(xmlData)
        filehandle.close()
        shutil.move('../../../../output/parse_result/cache/modsXML.xml',outputdir+'/modsXML.mods')
    return os.getcwd()+'/'+outputdir+'/modsXML.mods'

        
