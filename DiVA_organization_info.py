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
              'eng': "Master's Programme, Urbanism Studies, 60 credits"},
    'TSKKM': {'cycle': 2,
	      'swe': 'Masterprogram, systemkonstruktion på kisel',
              'eng': 'Master’s Programme, System-on-Chip Design'}
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

#
# Helper functions for dealing witt the XML file
#
#<w:sdtPr><w:alias w:val="Ämnesområde"/><w:tag w:val="Ämnesområde"/>
def control_box_string(name):
    return '<w:sdtPr><w:alias w:val="{0}"/><w:tag w:val="{0}"/>'.format(name)

def run_of_text(txt):
    return '<w:r><w:t>{0}</w:t></w:r>'.format(txt)

#<w:sdtContent><w:r w:rsidR="001D0C1B"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>Klicka h</w:t></w:r><w:r w:rsidR="00F7482B"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">är </w:t></w:r><w:r w:rsidR="001D0C1B"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">för att ange </w:t></w:r><w:r w:rsidR="00CE6D56"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>ditt ämnesområde</w:t></w:r><w:r w:rsidR="00F7482B"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">. </w:t></w:r><w:r w:rsidR="00F7482B" w:rsidRPr="00F7482B"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>T</w:t></w:r><w:r w:rsidR="00CE6D56" w:rsidRPr="00F7482B"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t xml:space="preserve">.ex. </w:t></w:r><w:r w:rsidR="00CE6D56" w:rsidRPr="00F7482B"><w:rPr><w:rStyle w:val="PlaceholderText"/><w:i/><w:iCs/></w:rPr><w:t>Examensarbete inom teknik och lärande</w:t></w:r><w:r w:rsidR="00CE6D56" w:rsidRPr="00F7482B"><w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr><w:t>).</w:t></w:r></w:sdtContent>
def remove_existing_place_holder_text(txt, control_box):
    if control_box in ['Ämnesområde', 'Nivä_och_hp', 'TRITA', 'År']:
        starting_marker='<w:sdtContent>'
        starting_offset=txt.find(starting_marker)
        if starting_offset >= 0:
            pre_text=txt[:starting_offset+len(starting_marker)]
            return pre_text
    if control_box in ['Title', 'Subtitle', 'Author']:
        starting_marker='</w:pPr>'
        starting_offset=txt.find(starting_marker)
        if starting_offset >= 0:
            pre_text=txt[:starting_offset+len(starting_marker)]
            return pre_text
    else:
        starting_marker='</w:pPr>'
    ending_marker='</w:sdtContent>'
    starting_offset=txt.find(starting_marker)
    if starting_offset >= 0:
        pre_text=txt[:starting_offset+len(starting_marker)]
        end_offset=txt.find(ending_marker)
        post_text=txt[end_offset:]
        return pre_text+post_text
    return txt

def clean_content(txt, control_box):
    global Verbose_Flag

    if Verbose_Flag:
        print("initial txt length={}".format(len(txt)))
    # remove the marker to show place holder text
    txt=txt.replace('<w:showingPlcHdr/>', '')
    # remove placeholder text
    if Verbose_Flag:
        print("txt: {}".format(txt))
    txt=remove_existing_place_holder_text(txt, control_box)
    if Verbose_Flag:
        print("final txt={0}\n length={1}".format(txt, len(txt)))
    return txt


def enter_field(content, control_box, value):
    print("processing control_box: {}".format(control_box))
    pattern=control_box_string(control_box)
    offset_to_pattern=content.find(pattern)
    if offset_to_pattern >= 0:
        # found pattern - now look for end of paragraph
        if control_box in ['Ämnesområde', 'Nivä_och_hp', 'Title', 'Subtitle', 'Author', 'TRITA', 'År']:
            end_marker='</w:sdtContent></w:sdt>'
        else:
            end_marker='</w:p></w:sdtContent></w:sdt>'
        offset_end_of_paragraph=content.find(end_marker, offset_to_pattern+len(pattern)+1)
        # insert the value
        if offset_end_of_paragraph >= 0:
            pre_text=content[:(offset_to_pattern+len(pattern))]
            if Verbose_Flag:
                print("pre_text={}".format(pre_text))
            post_text=content[offset_end_of_paragraph:]
            if control_box in ['Ämnesområde', 'Nivä_och_hp', 'TRITA', 'År']:
                content=pre_text + clean_content(content[(offset_to_pattern+len(pattern)):offset_end_of_paragraph], control_box) + run_of_text(value) + post_text
            elif control_box in ['Title', 'Subtitle', 'Author']:
                content=pre_text + clean_content(content[(offset_to_pattern+len(pattern)):offset_end_of_paragraph], control_box) + run_of_text(value) + '</w:p>' + post_text
            else:
                content=pre_text + clean_content(content[(offset_to_pattern+len(pattern)):offset_end_of_paragraph], control_box) + run_of_text(value) + '</w:p>' + post_text
            return content
    else:
        print("Did not field control box for {}".format(control_box))
    return content

def remove_optionalPicture(content):
    global Verbose_Flag
    if Verbose_Flag:
        print("Removing optionalPicture")

    control_box='OptionalPicture'
    pattern=control_box_string(control_box)
    offset_to_pattern=content.find(pattern)
    if offset_to_pattern >= 0:
        # now search backwards for '<w:p w:rsidR' (in this case the last instance of this string before the pattern
        paragraph_start=content.rfind('<w:p ', 0, offset_to_pattern)
        pargraph_end_marker='</w:p>'
        paragraph_end=content.find(pargraph_end_marker, offset_to_pattern)
        # now remove this paragraph
        pre_text=content[:paragraph_start]
        post_text=content[paragraph_end+len(pargraph_end_marker):]
        new_middle_text='<w:p><w:r><w:br w:type="page"/></w:r></w:p>' #  to provide the page break
        return pre_text+new_middle_text+post_text
    return content

# ----------------------------------------------------------------------
def transform_file(content, dict_of_entries):
    global Keep_picture_flag

    for control_box in dict_of_entries:
        # 'language' is a pseudo control box, it reflects the language of the thesis title
        # We use it to change the language for the address on the cover
        if control_box == 'language' and  dict_of_entries['language'] != 'swe':
            content=content.replace('Stockholm, Sverige', 'Stockholm, Sweden')
        else:
            value=dict_of_entries[control_box]
            content=enter_field(content, control_box, value)
    if not Keep_picture_flag:
        # remove the optional picture
        content=remove_optionalPicture(content)
    return content

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
