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

departments_info={
    'ABE': {
        'ARCH': {'L2': "5851",
                 'swe': 'Arkitektur',
                 'eng': 'Architecture',
                 'divisions': {'Q1a': {'L3': '5852',
                                       'swe': 'Arkitekturens historia och teori',
                                       'eng': 'History and Theory of Architecture'
                                       },
                               'Q1b': {'L3': '5853',
                                       'swe': 'Arkitektonisk gestaltning',
                                       'eng': 'Architectural Design'
                                       },
                               'Q1c': {'L3': '5854',
                                       'swe': 'Arkitekturteknik',
                                       'eng': 'Architectural Technologies'
                                       },
                               'Q1d': {'L3': '5855',
                                       'swe': 'Kritiska studier i arkitektur',
                                       'eng': 'Critical Studies in Architecture'
                                       },
                               'Q1e': {'L3': '5856',
                                       'swe': 'Stadsbyggnad',
                                       'eng': 'Urban Design'
                                       },
                               'Q1f': {'L3': '876913',
                                       'swe': 'Ljusdesign',
                                       'eng': 'Lighting Design'
                                       },
                               },
                 },
        'BYV':  {'L2': "5857",
                 'swe': 'Byggvetenskap',
                 'eng': 'Civil and Architectural Engineering',
                 'divisions': {'betong': {'L3': '5861',
                                          'swe': 'Betongbyggnad',
                                          'eng': 'Concrete Structures'
                                          },
                               'bro-och-stalbyggnad': {'L3': '10153',
                                                       'swe': 'Bro- och stålbyggnad',
                                                       'eng': 'Structural Engineering and Bridges'
                                                       },
                               'byggteknik-och-design': {'L3': '5867',
                                                         'swe': 'Byggteknik och design',
                                                         'eng': 'Building Technology and Design'
                                                         },
                               'byggtnadseknik-och-design': {'L3': '5859',
                                                             'swe': 'Byggnadsteknik',
                                                             'eng': 'Building Technology'
                                                             },
                               'byggnadsmaterial': {'L3': '5860',
                                                    'swe': 'Byggnadsmaterial',
                                                    'eng': 'Building Materials'
                                                    },
                               'hallbara-byggnader': {'L3': '881151',
                                                      'swe': 'Hållbara byggnader',
                                                      'eng': 'Sustainable Buildings'
                                                      },
                               'jord-o-bergmekanik': {'L3': '5864',
                                                      'swe': 'Jord- och bergmekanik',
                                                      'eng': 'Soil and Rock Mechanics'},

                                   'transportvetenskap': {'L3': '881700',
                                                          'swe': 'Transportplanering',
                                                          'eng': 'Transport planning'},
                               'Q1g': {'L3': '5862',
                                       'swe': 'Miljö- och resursinformation',
                                       'eng': 'Environmental and Natural Resources Information System'},
                               'Q1h': {'L3': '5865',
                                       'swe': 'Stålbyggnad',
                                       'eng': 'Steel Structures'},
                               },
                 },
        'PHILHIST': { 'phil': {'L2': '5874',
                               'swe': 'Filosofi',
                               'eng': 'Philosophy'
                               },
                      'historia': {'L2': '14702',
                                   'swe': 'Historiska studier av teknik, vetenskap och miljö',
                                   'eng': 'History of Science, Technology and Environment'},
                     },
        'FOB': {'L2': "5869",
                'swe': 'Fastigheter och byggande',
                'eng': 'Real Estate and Construction Management',
                'divisions': {'fastighetsvetenskap': {'L3': '5871',
                                                      'swe': 'Fastighetsvetenskap',
                                                      'eng': 'Real Estate Planning and Land Law'},
                              'geo': {'L3': '879656',
                                      'swe': 'Geodesi och satellitpositionering',
                                      'eng': 'Geodesy and Satellite Positioning'},
                              'fastighetsekonomi-och-finans': {'L3': '882950',
                                                               'swe': 'Fastighetsekonomi och finans',
                                                               'eng': 'Real Estate Economics and Finance'},
                              'fastighetsforetagande-och-finansiella-system': {'L3': '882951',
                                                                               'swe': 'Fastighetsföretagande och finansiella system',
                                                                               'eng': 'Real Estate Business and Financial Systems'},
                              'ledning-och-organisering-i-byggande-och-forvaltning': {'L3': '882952',
                                                                                      'swe': 'Ledning och organisering i byggande och förvaltning',
                                                                                      'eng': 'Construction and Facilities Management'},
                              }
                },
        'SEED': { 'L2': "13604",
                  'swe': 'Hållbar utveckling, miljövetenskap och teknik',
                  'eng': 'Sustainable development, Environmental science and Engineering',
                  'divisions': {
                      'Q1ö': {'L3': '878258',
                              'swe': 'Hållbarhet och miljöteknik',
                              'eng': 'Sustainability and Environmental Engineering'},
                      'hallbarhet-utvardering-och-styrning': {'L3': '878259',
                                                              'swe': 'Hållbarhet, utvärdering och styrning',
                                                              'eng': 'Sustainability Assessment and Management'},
                      'strategiska-hallbarhetsstudier': {'L3': '878260',
                                                         'swe': 'Strategiska hållbarhetsstudier',
                                                         'eng': 'Strategic Sustainability Studies'},
                      'vatten-och-miljoteknik': {'L3': '878261',
                                                 'swe': 'Vatten- och miljöteknik',
                                                 'eng': 'Water and Environmental Engineering'},
                      'resurser-energi-och-infrastruktur': {'L3': '878262',
                                                            'swe': 'Resurser, energi och infrastruktur',
                                                            'eng': 'Resources, Energy and Infrastructure'},
                  }
                 },
        'SOM': {'L2': "5884",
                'swe': 'Samhällsplanering och miljö',
                'eng': 'Urban Planning and Environment',
                'divisions': {'urbana-studier': {'L3': '5885',
                                                 'swe': 'Urbana och regionala studier',
                                                 'eng': 'Urban and Regional Studies'},
                              'gis': {'L3': '872751',
                                      'swe': 'Geoinformatik',
                                      'eng': 'Geoinformatics'},
                              'sek': {'L3': '885102',
                                      'swe': 'Transport och systemanalys',
                                      'eng': 'Transport and Systems Analysis'},
                              }
                }
    },
    'ITM': {
        'EGI': {'L2': "6024",
                'swe': 'Energiteknik',
                'eng': 'Energy Technology',
                'divisions': {'Energisystem': {'L3': '883952',
                                               'swe': 'Energisystem',
                                               'eng': 'Energy Systems'},
                              'heat-and-power-technology': {'L3': '6026',
                                                            'swe': 'Kraft- och värmeteknologi',
                                                            'eng': 'Heat and Power Technology'},
                              'applied-thermodynamics': {'L3': '6025',
                                                         'swe': 'Tillämpad termodynamik och kylteknik',
                                                         'eng': 'Applied Thermodynamics and Refrigeration'},
                              }
                },
        'INDEK': {'L2': "6030",
                  'swe': 'Industriell ekonomi och organisation (Inst.)',
                  'eng': 'Industrial Economics and Management (Dept.)',
                  'divisions': {
                      'MT': {'L3': '883956',
                             'swe': 'Management & Teknologi',
                             'eng': 'Management & Technology'},
                      'SIDE': {'L3': '883957',
                               'swe': 'Hållbarhet, Industriell dynamik & entreprenörskap',
                               'eng': 'Sustainability, Industrial Dynamics & Entrepreneurship'},
                      'AFC': {'L3': '883958',
                              'swe': 'Redovisning, Finansiering & Förändring',
                              'eng': 'Accounting, Finance & Changes'},
                  }
                  },
        'Learning': {'L2': "879306",
                     'swe': 'Lärande',
                     'eng': 'Learning',
                     'divisions': {'DL': {'L3': '883959',
                                          'swe': 'Digitalt lärande"',
                                          'eng': 'Digital Learning'},
                                   'STEM': {'L3': '883960',
                                            'swe': 'Lärande i Stem',
                                            'eng': 'Learning in Stem'},
                                   'sprak': {'L3': '883961',
                                             'swe': 'Språk och kommunikation',
                                             'eng': 'Language and communication'},
                                   'VH': {'L3': '883962', # # this is a center
                                          'swe': 'Vetenskapens hus',
                                          'eng': 'House of Science'},
                                   }
                     },
        'MMK': {'L2': "6038",
                'swe': 'Maskinkonstruktion (Inst.)',
                'eng': 'Machine Design (Dept.)',
                'divisions': {'Q1i': {'L3': '6039',
                                      'swe': 'Integrerad produktutveckling',
                                      'eng': 'Integrated Product Development'},
                              'Förbränningsmotorteknik': {'L3': '6040',
                                                          'swe': 'Förbränningsmotorteknik',
                                                          'eng': 'Internal Combustion Engines'},
                              'mechatronics': {'L3': '6041',
                                               'swe': 'Mekatronik',
                                               'eng': 'Mechatronics'},
                              'SKD': {'L3': '-1', # does not have a LADOK code 
                                      'swe': 'System- och komponentdesign',
                                      'eng': 'Systems and Component Design'},
                              'Tribologi': {'L3': '6047',
                                            'swe': 'Tribologi',
                                            'eng': 'Tribologi'},
                              'machine-elements': {'L3': '6043',
                                                   'swe': 'Maskinelement',
                                                   'eng': 'Machine Elements'},
                              'Q1j': {'L3': '6042',
                                      'swe': 'Inbyggda styrsystem',
                                      'eng': 'Embedded Control Systems'},

                                   'Q1k': {'L3': '6044',
                                           'swe': 'Maskinkonstruktion (Avd.)',
                                           'eng': 'Machine Design (Div.)'},
                              'Q1l': {'L3': '6045',
                                      'swe': 'Produktinnovationsteknik',
                                      'eng': 'Product Innovation Technology'},
                              'Q1m': {'L3': '6046',
                                      'swe': 'Produkt- och tjänstedesign',
                                      'eng': 'Product and Service Design'},
                              }
                },
        'MSE': {'L2': '6048',
                'swe': 'Materialvetenskap',
                'eng': 'Materials Science and Engineering',
                'divisions': {'process': {'L3': '883963',
                                          'swe': 'Processer',
                                          'eng': 'Process'},
                              'structures': {'L3': '883964',
                                             'swe': 'Strukturer',
                                             'eng': 'Structures'},
                              'properties': {'L3': '883965',
                                             'swe': 'Egenskaper',
                                             'eng': 'Properties'},
                              }
                },
        'IIP': {'L2': '6061',
                'swe': 'Industriell produktion',
                'eng': 'Production Engineering',
                'divisions': {'Q1n': {'L3': '883600',
                                      'swe': 'Tillverkning och mätsystem',
                                      'eng': 'Manufacturing and Metrology Systems'},
                              'Q1o': {'L3': '883601',
                                      'swe': 'Hållbara produktionssystem',
                                      'eng': 'Sustainable Production Systems'},
                              'Q1p': {'L3': '883608',
                                      'swe': 'Digital smart produktion',
                                      'eng': 'Digital Smart Production'},
                              }
                },
        'HPU': {'L2': '880900',
                'swe': 'Hållbar produktionsutveckling (ML)',
                'eng': 'Sustainable production development',
                'divisions': {'Production Management': {'L3': '883953',
                                                        'swe': 'Processledning och hållbar produktion',
                                                        'eng': 'Process management and sustainable production'},
                              'Production Logistics': {'L3': '883955',
                                                       'swe': 'Avancerad underhållsteknik och produktionslogistik',
                                                       'eng': 'Advanced maintenance technology and production logistics'},
                              # Industrial Dependability
                        }
                }
    },
    'SCI': {
        'Fysik': {'L2': '6128',
                  'swe': 'Fysik',
                  'eng': 'Physics',
                  'divisions': {'Q1q': {'L3': '6129',
                                        'swe': 'Atom- och molekylfysik',
                                        'eng': 'Atomic and Molecular Physics'},
                                'MI': {'L3': '6130',
                                       'swe': 'Medicinsk bildfysik',
                                       'eng': 'Physics of Medical Imaging'},
                                'nuclear': {'L3': '6131',
                                            'swe': 'Kärnfysik',
                                            'eng': 'Nuclear Physics'},
                                'NPS': {'L3': '6132',
                                        'swe': 'Kärnkraftssäkerhet',
                                        'eng': 'Nuclear Power Safety'},
                                'particle': {'L3': '6133',
                                             'swe': 'Partikel- och astropartikelfysik',
                                             'eng': 'Particle and Astroparticle Physics'},
                                'condensed': {'L3': '876906',
                                              'swe': 'Kondenserade materiens teori',
                                              'eng': 'Condensed Matter Theory'},
                                'Q1r': {'L3': '876907',
                                        'swe': 'Matematisk fysik',
                                        'eng': 'Mathematical Physics'},
                                'Q1s': {'L3': '876908',
                                        'swe': 'Materialteori',
                                        'eng': 'Theory of Materials'},
                                'Q1t': {'L3': '876909',
                                        'swe': 'Statistisk fysik',
                                        'eng': 'Statistical Physics'},
                                'Q1u': {'L3': '876910',
                                        'swe': 'Teoretisk biologisk fysik',
                                        'eng': 'Theoretical Biological Physics'},
                                'Q1v': {'L3': '876911',
                                        'swe': 'Teoretisk partikelfysik',
                                        'eng': 'Theoretical Particle Physics'},
                                'NE': {'L3': '880050',
                                       'swe': 'Kärnenergiteknik',
                                       'eng': 'Nuclear Engineering'},
                                'Q1w': {'L3': '880100',
                                        'swe': 'Reaktorfysik och teknologi',
                                        'eng': 'Reactor physics and technology'},
                                }
                  },
        'MATH': {'L2': "6115",
                 'swe': 'Matematik (Inst.)',
                 'eng': 'Mathematics (Dept.)',
                 'divisions': {'math': {'L3': '6116',
                                        'swe': 'Matematik (Avd.)',
                                        'eng': 'Mathematics (Div.)'},
                               'mathstat': {'L3': '6117',
                                            'swe': 'Matematisk statistik',
                                            'eng': 'Mathematical Statistics'},
                               'optsys': {'L3': '6118',
                                          'swe': 'Optimeringslära och systemteori',
                                          'eng': 'Optimization and Systems Theory'},
                               'NA': {'L3': '11800',
                                      'swe': 'Numerisk analys',
                                      'eng': 'Numerical Analysis'},
                               }
                 },
        'Mekanik': {'L2': '6119',
                    'swe': 'Mekanik',
                    'eng': 'Mechanics'
                    },
        'TEKMEK': { 'L2': "882656",
                    'swe': 'Teknisk mekanik',
                    'eng': 'Engineering Mechanics',
                    'divisions': {'Farkostteknik och Solidmekanik': {'L3': "882657",
                                                                     'swe': 'Farkostteknik och Solidmekanik',
                                                                     'eng': 'Vehicle Engineering and Solid Mechanics'},
                                  'Strömningsmekanik och Teknisk Akustik': {'L3': '882658',
                                                                            'swe': 'Strömningsmekanik och Teknisk Akustik',
                                                                            'eng': 'Fluid Mechanics and Engineering Acoustics'},
                                  }
                   },
        'APHYS': {'L2': '6108',
                  'swe': 'Tillämpad fysik',
                  'eng': 'Applied Physics',
                  'divisions': {'biox': {'L3': '6109',
                                         'swe': 'Biomedicinsk fysik och röntgenfysik',
                                         'eng': 'Biomedical and X-ray Physics'},
                                'laserphysics': {'L3': '6112',
                                                 'swe': 'Laserfysik',
                                                 'eng': 'Laser Physics'},
                                'nanophysics': {'L3': '6113',
                                                'swe': 'Nanostrukturfysik',
                                                'eng': 'Nanostructure Physics'},
                                'qeo': {'L3': '880051',
                                        'swe': 'Kvant- och biofotonik',
                                        'eng': 'Quantum and Biophotonics'},
                                'mnp': {'L3': '880052',
                                        'swe': 'Material- och nanofysik',
                                        'eng': 'Materials and Nanophysics'},
                                'photonics': {'L3': '880053',
                                              'swe': 'Fotonik',
                                              'eng': 'Photonics'},
                                'biophysics': {'L3': '880054',
                                               'swe': 'Biofysik',
                                               'eng': 'Biophysics'},
                                }
                  }
    },
    'CBH': {
        'MTH': {'L2': "879308",
                'swe': 'Medicinteknik och hälsosystem',
                'eng': 'Biomedical Engineering and Health Systems',
                'divisions': {'biomedical-imaging': {'L3': '879320',
                                                     'swe': 'Medicinsk avbildning',
                                                     'eng': 'Medical Imaging'},
                              'ergonomi': {'L3': '879322',
                                           'swe': 'Ergonomi',
                                           'eng': 'Ergonomics'},
                              'grundlaggande-naturv': {'L3': '879323',
                                                       'swe': 'Grundläggande naturvetenskap',
                                                       'eng': 'Basic Science'},
                              'health-informatics': {'L3': '880401',
                                                     'swe': 'Hälsoinformatik och logistik',
                                                     'eng': 'Health Informatics and Logistics'},
                              'Q1x': {'L3': '880402',
                                      'swe': 'Människa och Kommunikation',
                                      'eng': 'Human Communication Science'},
                              'teknisk-vardvetenska': {'L3': '880403',
                                                       'swe': 'Teknisk vårdvetenskap',
                                                       'eng': 'Technology in Health Care'},
                              'omgivningsfysiologi': {'L3': '879317',
                                                      'swe': 'Omgivningsfysiologi',
                                                      'eng': 'Environmental Physiology'},
                              'neuronik': {'L3': '879318',
                                           'swe': 'Neuronik',
                                           'eng': 'Neuronic Engineering'},
                              '': {'L3': '879319',
                                   'swe': 'Strukturell bioteknik',
                                   'eng': 'Structural Biotechnology'},
                              }
                },
        'CHE': {'L2': "879316",
                'swe': 'Kemi',
                'eng': 'Chemistry',
                'divisions': {'orgkem': {'L3': '879324',
                                         'swe': 'Organisk kemi',
                                         'eng': 'Organic chemistry'},
                              'glykovetenskap': {'L3': '879326',
                                                 'swe': 'Glykovetenskap',
                                                 'eng': 'Glycoscience'},
                              'tfk': {'L3': '879359',
                                      'swe': 'Tillämpad fysikalisk kemi',
                                      'eng': 'Applied Physical Chemistry'},
                              '': {'L3': '879325',
                                   'swe': 'Yt- och korrosionsvetenskap',
                                   'eng': 'Surface and Corrosion Science'},
                              }
                },
        'KET': {'L2': "879314",
                'swe': 'Kemiteknik',
                'eng': 'Chemical Engineering',
                'divisions': {'energy-processes': {'L3': '879328',
                                                   'swe': 'Energiprocesser',
                                                   'eng': 'Energy Processes'},
                              'resource-recovery': {'L3': '879331',
                                                    'swe': 'Resursåtervinning',
                                                    'eng': 'Resource recovery'},
                              'electrochem': {'L3': '879332',
                                              'swe': 'Tillämpad elektrokemi',
                                              'eng': 'Applied Electrochemistry'},
                              'nuclear': {'L3': '-2',
                                          'swe': 'Kärnavfallsteknik',
                                          'eng': 'Nuclear Waste Engineering'},
                              'Q1y': {'L3': '879327',
                                      'swe': 'Kemisk apparatteknik',
                                      'eng': 'Chemical Engineering'},
                              'Q1z': {'L3': '879333',
                                      'swe': 'Teknisk strömningslära',
                                      'eng': 'Transport Phenomena'},
                              'Q1å': {'L3': '879334',
                                      'swe': 'Processteknologi',
                                      'eng': 'Process Technology'},
                              'Q1ä': {'L3': '879650',
                                      'swe': 'Kemisk teknologi',
                                      'eng': 'Chemical Technology'},
                              }
                },
        'FPT': {'L2': "879315",
                'swe': 'Fiber- och polymerteknologi',
                'eng': 'Fibre- and Polymer Technology',
                'divisions': {
                    '': {'L3': '879336',
                         'swe': 'Polymerteknologi',
                         'eng': 'Polymer Technology'},
                    '': {'L3': '879337',
                         'swe': 'Polymera material',
                         'eng': 'Polymeric Materials'},
                    '': {'L3': '879338',
                         'swe': 'Ytbehandlingsteknik',
                         'eng': 'Coating Technology'},
                    '': {'L3': '879339',
                         'swe': 'Träkemi och massateknologi',
                         'eng': 'Wood Chemistry and Pulp Technology'},
                    '': {'L3': '879340',
                         'swe': 'Fiberteknologi',
                         'eng': 'Fibre Technology'},
                    '': {'L3': '879341',
                         'swe': 'Biokompositer',
                         'eng': 'Biocomposites'},
                }
                },
        'GTE': {'L2': '879312',
                'swe': 'Genteknologi',
                'eng': 'Gene Technology',
                },
        'DIB': {'L2': '879311',
                'swe': 'Industriell bioteknologi',
                'eng': 'Industrial Biotechnology'
                },
        'IIP': {'L2': '879311',
                'swe': 'Industriell bioteknologi',
                'eng': 'Industrial Biotechnology'
                },
        'PRO': {'L2': "879309",
                'swe': 'Proteinvetenskap',
                'eng': 'Protein Science',
                'divisions': {'nanobio': {'L3': '879342',
                                          'swe': 'Nanobioteknologi',
                                          'eng': 'Nano Biotechnology'},
                              'sysbio': {'L3': '879343',
                                         'swe': 'Systembiologi',
                                         'eng': 'Systems Biology'},
                              'cellular-proteomics': {'L3': '879344',
                                                      'swe': 'Cellulär och klinisk proteomik',
                                                      'eng': 'Cellular and Clinical Proteomics'},
                              'affinity-proteomics': {'L3': '879345',
                                                      'swe': 'Affinitets-proteomik',
                                                      'eng': 'Affinity Proteomics'},
                              'prot-tech': {'L3': '879346',
                                            'swe': 'Proteinteknologi',
                                            'eng': 'Protein Technology'},
                              'proteineng': {'L3': '879347',
                                             'swe': 'Proteinvetenskap',
                                             'eng': 'Protein Engineering'},
                              'drug-discovery': {'L3': '879348',
                                                 'swe': 'Läkemedelsutveckling',
                                                 'eng': 'Drug Discovery and Development'},
                              }
                },
        'TCB': {'L2': '879310',
                'swe': 'Teoretisk kemi och biologi',
                'eng': 'Theoretical Chemistry and Biology',
                'divisions': {

                        }
                }
    },
    'EECS': {
        'CS': { 'L2': "882650",
                'swe': 'Datavetenskap',
                'eng': 'Computer Science',
                'divisions': {'CoS': {'L3': '879305',
                                      'swe': 'Kommunikationssystem',
                                      'eng': 'Communication Systems'
                                      },
                              'CST': {'L3': '879225',
                                      'swe': 'Beräkningsvetenskap och beräkningsteknik',
                                      'eng': 'Computational Science and Technology'
                                      },
                              'NSE': {'L3': '879231',
                                      'swe': 'Nätverk och systemteknik',
                                      'eng': 'Network and Systems Engineering'
                                      },
                              'SCS': {'L3': '879232',
                                      'swe': 'Programvaruteknik och datorsystem',
                                      'eng': 'Software and Computer systems'
                                      },
                              'TCS': {'L3': '879237',
                                      'swe': 'Teoretisk datalogi',
                                      'eng': 'Theoretical Computer Science'
                                      },
                              }
               },
        'EE': {'L2': '882654',
               'swe': 'Elektroteknik',
               'eng': 'Electrical Engineering',
               'divisions': {'EME': {'L3': '879226',
                                     'swe': 'Elektroteknisk teori och konstruktion',
                                     'eng': 'Electromagnetic Engineering'
                                     },
                             'EPE': {'L3': '879227',
                                     'swe': 'Elkraftteknik',
                                     'eng': 'Electric Power and Energy Systems'
                                     },
                             'EES': {'L3': '879249',
                                     'swe': 'Elektronik och inbyggda system',
                                     'eng': 'Electronics and Embedded systems'},
                             'FPP': {'L3': '879228',
                                     'swe': 'Fusionsplasmafysik',
                                     'eng': 'Fusion Plasma Physics'
                                     },
                             'SPP': {'L3': '879235',
                                     'swe': 'Rymd- och plasmafysik',
                                     'eng': 'Space and Plasma Physics'
                                     },

                                 }
               },
        'IS':  {'L2': '882651',
                'swe': 'Intelligenta system',
                'eng': "Intelligent systems",
                'divisions': {'MNS': {'L3': '879230',
                                      'swe': 'Mikro- och nanosystemteknik',
                                      'eng': 'Micro and Nanosystems'
                                      },
                              'AC': {'L3': '879233',
                                     'swe': 'Reglerteknik',
                                     'eng': 'Decision and Control Systems (Automatic Control)'
                                     },
                              'RPL': {'L3': '879234',
                                      'swe': 'Robotik, perception och lärande',
                                      'eng': 'Robotics, Perception and Learning'
                                      },
                              'ISE': {'L3': '879236',
                                      'swe': 'Teknisk informationsvetenskap',
                                      'eng': 'Information Science and Engineering'
                                      },
                              'TMH': {'L3': '879302',
                                      'swe': 'Tal, musik och hörsel',
                                      'eng': 'Speech, Music and Hearing'
                                      },
                              'CAS': {'L3': '882655',
                                      'swe': 'Collaborative Autonomous Systems',
                                      'eng': 'Collaborative Autonomous Systems'
                                      },
                              }
                },
        'HCT': {'L2': '882653',
                'swe': 'Människocentrerad teknologi',
                'eng': 'Human Centered Technology',
                'divisions': {'MID': {'L3': '879229',
                                      'swe': 'Medieteknik och interaktionsdesign',
                                      'eng': 'Media Technology and Interaction Design'
                                      }
                              },
                },

        }
}

# the first argument is the acronym of the school, while the seconds is a string name of a department
def departments_acronym(l1, s2):
    for d in departments_info[l1]:
        if s2 == departments_info[l1][d]['swe'] or s2 == departments_info[l1][d]['eng']:
            return d
    return None

def acronym_from_org_id(key):
    # convert numeric values ot strings for the later lookup
    if isinstance(key, int):
        key="{}".format(key)
    #
    # look for an L2 org_id
    for school in departments_info:
        for dept in departments_info[school]:
            l2=departments_info[school][dept].get('L2')
            if l2 == key:
                return dept
    #
    for school in departments_info:
        for dept in departments_info[school]:
            if departments_info[school][dept].get('divisions'):
                for division in departments_info[school][dept]['divisions']:
                    l3=departments_info[school][dept]['divisions'][division].get('L3')
                    if l3 == key:
                        return division
    return None


#----------------------------------------------------------------------

# The following are for dealing with the data from DiVA
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

        # use departments_info to get the acronym/short name based on organisation_id (i.e., key

        x=acronym_from_org_id(key)
        if x:
            entry['organisation_acronym_short_name']=x
            print("key={0}, x={1}, entry={2}".format(key, x, entry))

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
