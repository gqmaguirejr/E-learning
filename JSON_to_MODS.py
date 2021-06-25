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



def process_dict_to_XML(content, extras):
    global testing

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

    genre= ET.Element("genre")
    mods.append(genre)
    genre.set("authority" , "diva")
    genre.set("type", "publicationType")
    genre.set("lang", "swe")
    genre.text="Studentuppsats (Examensarbete)"

    genre3= ET.Element("genre")
    mods.append(genre3)
    genre3.set("authority" , "diva")
    genre3.set("type", "publicationType")
    genre3.set("lang", "eng")
    genre3.text="Student thesis"

    genre4= ET.Element("genre")
    mods.append(genre4)
    genre4.set("authority" , "diva")
    genre4.set("type", "publicationType")
    genre4.set("lang", "nor")
    genre4.text="Oppgave"

    author_names=list()
    for i in range(1, 10):
        which_author="Author{}".format(i)
        author=content.get(which_author, None)
        if author:
            writer = ET.Element("name")
            mods.append(writer)

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

            first_name=author.get('First name', None)        
            if first_name:
                fn = ET.SubElement(writer, "namePart")
                fn.set("type", "given")
                fn.text=first_name

            role =ET.SubElement(writer , "role")
            roleTerm = ET.SubElement(role , "roleTerm")
            roleTerm.set("type" , "code")
            roleTerm.set("authority" , "marcrelator")
            roleTerm.text ="aut"
        else:                   # if there was no such author, then stop looping
            break


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

        first_name=examiner_info.get('First name', None)        
        if first_name:
            fn = ET.SubElement(examinator , "namePart")
            fn.set("type", "given")
            fn.text=first_name

        e_org=examiner_info.get('organisation')
        if e_org:
            e_org_l1=e_org.get('L1')
            e_org_l2=e_org.get('L2')
            if e_org_l1 and e_org_l2:
                organization="{0}, {1}".format(e_org_l1, e_org_l2)
            elif  e_org_l1 and not e_org_l2:
                organization="{0}".format(e_org_l1)
            else:
                organization=None

            if organization:
                org = ET.SubElement(examinator , "affiliation")
                org.text = organization
                examiner_organization=organization

        # job = ET.SubElement(examinator , "namePart")
        # job.set("type", "termsOfAddress")
        # job.text = content.get("jobTitle_examinar")

        role =ET.SubElement(examinator , "role")
        roleTerm = ET.SubElement(role , "roleTerm")
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

        year=other_info.get('Year', None)
        if year:
            originInfo = ET.Element("originInfo")
            date_issued = ET.SubElement(originInfo, "dateIssued")
            date_issued.text=year
            mods.append(originInfo)
        
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
        series_id.text="16855"

    series_number=ET.SubElement(ti, "identifier")
    series_number.set('type', "issue number")
    series_number.text=trita[offset_to_number:]
    mods.append(relatedItem)

    # "Degree": {"Educational program": "Degree Programme in Media Technology", "Level": "2", "Course code": "DA231X", "Credits": "30.0", "Exam": "Degree of Master of Science in Engineering", "subjectArea": "Media Technology"}
    # <note type="level" lang="swe">Självständigt arbete på avancerad nivå (masterexamen)</note><note type="universityCredits" lang="swe">20 poäng / 30 hp</note><location>
    level = ET.Element("note")
    level.set('lang', "swe")
    level.set('type', "level")
    level.text="Självständigt arbete på avancerad nivå (masterexamen)"
    mods.append(level)

    credits = ET.Element("note")
    credits.set('lang', "swe")
    credits.set('type', "universityCredits")
    credits.text="20 poäng / 30 hp"
    mods.append(credits)

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

        
