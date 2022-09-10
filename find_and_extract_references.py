#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./find_and_extract_references.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
#
# Purpose: Find and extract refrences pages
#
# Example:
# For a single PDF file:
# ./find_and_extract_references.py --pdf ddddddd-FULLTEXT01.pdf
#
# For all the PDF files in the spreadsheet
# ./find_and_extract_references.py -s ../eecs-2022.xlsx
# Note that this can be fund after updating the original spreadsheet with cover information
#
# To get the correct pdfminer package od:
# pip install pdfminer.six
#
# 2021-09-04 G. Q. Maguire Jr.
#
import re
import sys
# set the stdout to use UTF8 encoding
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

import json
import argparse
import os			# to make OS calls, here to get time zone info
import subprocess               # to execute a command
import shlex                    # to split a command into arguments

from io import StringIO
from io import BytesIO

import requests, time
import pprint

# Use Python Pandas to create XLSX files
import pandas as pd

import faulthandler

# from pdfminer.converter import TextConverter, HTMLConverter
# from pdfminer.layout import LAParams
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
# from pdfminer.pdfpage import PDFPage
# from pdfminer.pdfparser import PDFParser

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTLine, LAParams, LTFigure, LTImage, LTTextLineHorizontal, LTTextBoxHorizontal, LTCurve
from typing import Iterable, Any
from pdfminer.layout import LAParams, LTTextBox, LTText, LTChar, LTAnno
import pdfminer.psparser
from pdfminer.pdfdocument import PDFNoValidXRef
from pdfminer.psparser import PSEOF

font_families_and_names={
    # font_name style
    # family: Computer Modern Text Fonts - info from http://mirrors.ibiblio.org/CTAN/systems/win32/bakoma/fonts/fonts.html
    'cmr': 'Roman',
    'cmti': 'Text Italic',
    'cmsl': 'Text Slanted',
    'cmbx': 'Bold Extended',
    'cmb': 'Bold',
    'cmbxti': 'Bold Extended Italic',
    'cmbxsl': 'Bold Extended Slanted',
    'cmcsc': 'Small Caps',
    'cmtt': 'Typewriter',
    'cmitt': 'Typewriter Italic',
    'cmsltt': 'Typewriter Slanted',
    'cmss': 'SansSerif',
    'cmssbx': 'SansSerif Bold',
    'cmssdc': 'SansSerif DemiCondensed',
    'cmssi': 'SansSerif Italic',
    'cmssq': 'SansSerif Quoted',
    'cmssqi': 'SansSerif Quoted Italic',
    'cminch': 'Large font',
    # family: Computer Modern Math Fonts
    'cmmi': 'Math Italic',
    'cmmib': 'Math Bold Italic',
    'cmsy': 'Math Symbols',
    'cmbsy': 'Math Bold Symbols',
    'cmex': 'Math Extension',
    # family: Computer Modern Exotic Fonts:
    'cmdunh': 'Dunhill Roman',
    'cmff': 'Funny Roman',
    'cmfi': 'Funny Italic',
    'cmfib': 'Roman Fibonacci',
    'cmtcsc': 'Typewriter Caps and Small Caps',
    'cmtex': 'TeX extended ASCII',
    'cmu': 'Unslanted Italic',
    'cmvtt': 'Variable-Width Typewriter',
    # family: METAFONT Logo Fonts
    'logo': 'Roman',
    'logobf': 'Bold',
    'logosl': 'Slanted',
    # family: LaTeX Fonts
    'circle': 'Circle Drawing',
    'circlew': 'Circle Drawing',
    'line': 'Line Drawing',
    'linew': 'Line Drawing',
    'lasy': 'LaTeX Symbols',
    'lasyb': 'LaTeX Bold Symbols',
    'lcmss': 'SliTeX Sans Serif',
    'lcmssb': 'SliTeX Sans Serif Bold',
    'lcmssi': 'SliTeX Sans Serif Italic',
    # AMS Fonts
    # family: Euler Font Family
    'euex': 'Extension',
    'eufm': 'Fraktur Medium',
    'eufb': 'Fraktur Bold',
    'eurm': 'Roman Medium',
    'eurb': 'Roman Bold',
    'eusm': 'Script Medium',
    'eusb': 'Script Bold',
    # family: Extra Math Symbol Fonts
    # these are amsfonts – TEX fonts from the American Mathematical Society - https://www.ctan.org/pkg/amsfonts
    'msam': 'First font',
    'msbm': 'Second font',
    # family: Computer Modern Cyrillic Fonts
    'cmcyr': 'Roman',
    'cmcti': 'Text Italic',
    'cmcsl': 'Text Slanted',
    'cmcbx': 'Bold Extended',
    'cmcb': 'Bold',
    'cmcbxti': 'Bold Extended Italic',
    'cmcbxsl': 'Bold Extended Slanted',
    'cmccsc': 'Small Caps',
    'cmctt': 'Typewriter',
    'cmcitt': 'Typewriter Italic',
    'cmcsltt': 'Typewriter Slanted',
    'cmcss': 'SansSerif',
    'cmcssbx': 'SansSerif Bold',
    'cmcssdc': 'SansSerif DemiCondenced',
    'cmcssi': 'SansSerif Italic',
    'cmcssq': 'SansSerif Quoted',
    'cmcssqi': 'SansSerif Quoted Italic',
    'cmcinch': 'Large font',
    # family: Concrete Fonts
    'ccr': 'Roman',
    'ccsl': 'Slanted',
    'ccslc': 'Condensed Slanted',
    'ccti': 'Text Italic',
    'cccsc': 'Small Caps',
    'ccmi': 'Math Italic',
    'ccmic': 'Math Italic',
    'eorm': 'Roman',
    'eosl': 'Slanted',
    'eocc': 'Small Caps',
    'eoti': 'Text Italic',
    'torm': 'Roman',
    'tosl': 'Slanted',
    'toti': 'Text Italic',
    'tcssdc': 'SansSerif Condensed',
    'xccam': 'Regular',
    'xccbm': 'Regular',
    'xccmi': 'Math Italic',
    'xccsy': 'Math Symbols',
    'xccex': 'Math Extension',
    # family: EC/TC Fonts
    'ecrm': 'Roman Medium',
    'ecti': 'Text Italic',
    'ecbi': 'Bold Extended Text Italic',
    'ecbl': 'Bold Extended Slanted Roman',
    'ecbx': 'Bold Extend Roman',
    'ecsl': 'Roman Slanted',
    'ecci': 'Text Classical Serif Italic',
    'ecrb': 'Roman Bold (Non-Extended)',
    'ecui': 'Unslanted Italic',
    'eccc': 'Caps and Small Caps',
    'ecsc': 'Slanted Caps and Small Caps',
    'ecxc': 'Bold Extended Caps and Small Caps',
    'ecoc': 'Bold Extended Slanted Caps and Small Caps',
    'ecss': 'Sans Serif',
    'ecsi': 'Sans Serif Inclined',
    'ecsx': 'Sans Serif Bold Extended',
    'ecso': 'Sans Serif Bold Extended Oblique',
    'ectt': 'Typewriter Text',
    'ecit': 'Italic Typewriter Text',
    'ecst': 'Slanted Typewriter Text',
    'ectc': 'Typewriter Caps and Small Caps',
    'ecvi': 'Variable Width Italic Typewriter Text',
    'ecvt': 'Variable-Width Typewriter Text',
    'ecdh': 'Dunhill Roman',
    # family: LH Fonts
    'larm': 'Roman Medium',
    'lati': 'Text Italic',
    'labi': 'Bold Extended Text Italic',
    'labl': 'Bold Extended Slanted Roman',
    'labx': 'Bold Extend Roman',
    'lasl': 'Roman Slanted',
    'laci': 'Text Classical Serif Italic',
    'larb': 'Roman Bold (Non-Extended)',
    'laui': 'Unslanted Italic',
    'lacc': 'Caps and Small Caps',
    'lasc': 'Slanted Caps and Small Caps',
    'laxc': 'Bold Extended Caps and Small Caps',
    'laoc': 'Bold Extended Slanted Caps and Small Caps',
    'lass': 'Sans Serif',
    'lasi': 'Sans Serif Inclined',
    'lasx': 'Sans Serif Bold Extended',
    'laso': 'Sans Serif Bold Extended Oblique',
    'latt': 'Typewriter Text',
    'lait': 'Italic Typewriter Text',
    'last': 'Slanted Typewriter Text',
    'latc': 'Typewriter Caps and Small Caps',
    'lavi': 'Variable Width Italic Typewriter Text',
    'lavt': 'Variable-Width Typewriter Text',
    # family: T1 Encoded Fonts (Complete Emulation of the EC fonts)
    't1r': 'Roman',
    't1ti': 'Text Italic',
    't1sl': 'Text Slanted',
    't1bx': 'Bold Extended',
    't1b': 'Bold',
    't1bxti': 'Bold Extended Italic',
    't1bxsl': 'Bold Extended Slanted',
    't1csc': 'Small Caps',
    't1tt': 'Typewriter',
    't1itt': 'Typewriter Italic',
    't1sltt': 'Typewriter Slanted',
    't1ss': 'SansSerif',
    't1ssbx': 'SansSerif Bold',
    't1ssdc': 'SansSerif DemiCondenced',
    't1ssi': 'SansSerif Italic',
    # family: T2 Encoded Fonts (Partial Emulation of the LH/LA fonts)
    't2r': 'Roman',
    't2ti': 'Text Italic',
    't2sl': 'Text Slanted',
    't2bx': 'Bold Extended',
    't2b': 'Bold',
    't2bxti': 'Bold Extended Italic',
    't2bxsl': 'Bold Extended Slanted',
    't2csc': 'Small Caps',
    't2tt': 'Typewriter',
    't2itt': 'Typewriter Italic',
    't2sltt': 'Typewriter Slanted',
    't2ss': 'SansSerif',
    't2ssbx': 'SansSerif Bold',
    't2ssdc': 'SansSerif DemiCondenced',
    't2ssi': 'SansSerif Italic',
    # Font ZOO
    # family: Ralph Smith's Formal Script: (converted at end of 1997)
    'rsfs': 'Script',
    # Diagram Drawing Fonts
    # family: LamsTeX Commutative Diagram Drawing Fonts (converted at end of 1997)
    'lams1': 'Line drawing',
    'lams2': 'Line drawing',
    'lams3': 'Line drawing',
    'lams4': 'Line drawing',
    'lams5': 'Line drawing',
    # family: Xy-Pic Drawing Fonts
    'xyatip': 'upper arrow tips (technical style)',
    'xybtip': 'lower arrow tips (technical style)',
    'xycmat': 'upper arrow tips (Computer Modern style)',
    'xycmbt': 'lower arrow tips (Computer Modern style)',
    'xyeuat': 'upper arrow tips (Euler style)',
    'xyeubt': 'lower arrow tips (Euler style)',
    'xybsql': 'lower squiggles/quarter circles',
    'xycirc': '1/8 circles with varying radii',
    'xydash': 'dashes',
    'xyline': 'line segments',
    'xymisc': 'miscellaneous characters',
    'xyqc': 'quarter circles',
    # MusixTeX Fonts
    'mx': '',
    'xsld': '',
    'xslhd': '',
    'xslhu': '',
    'xslu': '',
    'xslz': '',
    'xslhz': '',
    'mxsps': '',
    # Timing Diagram Fonts
    'timing1': '',
    'timing1s': '',
    'timing2': '',
    'timing2s': '',
    # Miscelaneous Diagram Drawing Fonts
    'arrsy10': '',
    'newcirc': '',
    'ulsy10': '',
    'bbding10': '',
    'dingbat': '',
    'umranda': '',
    'umrandb': '',
    'karta15': '',
    'china10': '',
    'cchess46': '',

    # family: latex-cjk-chinese-arphic-bsmi00lp
    'bsmiu4f': '',
    'bsmiu52': '',
    'bsmiu6b': '',
    'bsmiu6c': '',
    'bsmiu79': '',
    'bsmiu82': '',
    'bsmiu86': '',
    'bsmiu88': '',
    'bsmiu90': '',
    'bsmiu96': '',
    'bsmiu99': '',

    # family: newtx
    'NewTXMI': 'Math Italic',
    'ntxtmri': '',              # unknown

    # family: stmaryrd – St Mary Road symbols for theoretical computer science
    'stmary10': '',

    # family: TX Fonts - see https://tug.org/FontCatalogue/txfonts/
    'txsya': '',    
    'txsyb': '',
    'txsys': '',
    'txmiaX': '',
    'txmiaSTbb': '',
    'txexs': '',
    'tx1tt': '',
    'tx1btt': 'Bold',
    't1xtt-Slant_167': 'Slanted',
    't1xbtt': '',
    't1xtt': '',

    # family: 
    '.SFNS-Bold': 'Bold',

    # family: 
    '3MCircularTT-Bold': 'BoldTypewriter',
    '3MCircularTTBook': 'BookTypewriter',
    '3MCircularTT-Book': 'BookTypewriter',
    '3MCircularTTLight': 'LightTypewriter',

    # family: 
    'ACaslonPro-Bold': 'Bold',
    'ACaslonPro-BoldItalic': 'BoldItalic',
    'ACaslonPro-Italic': 'Italic',
    'ACaslonPro-Regular': '',

    # family: 
    'AcuminVariableConcept': '',

    # family: 
    'AdobeSongStd-Light': 'Light',

    # family: 
    'AdvOT2bda31c3.B': '',
    'AdvOT35387326.B': '',
    'AdvOT3b30f6db.B': '',
    'AdvOT46dcae81': '',
    'AdvOT5fcf1b24': '',
    'AdvOTce3d9a73': '',


    # family: 
    'AGaramond-Italic': 'Italic',
    'AGaramondPro-Italic': 'Italic',
    'AGaramondPro-Regular': '',
    'AGaramond-Regular': '',

    # family: 
    'Aharoni': '',
    'Aharoni,Bold': 'Bold',

    # family: 
    'Akhand-Black': 'Black',

    # family: 
    'AlternateGotNo3D': '',

    # family: 
    'Amasis': '',

    # family: 
    'AmbroiseStd-Light': 'Light',

    # family: 
    'AnkoPersonalUse-RegularItalic': 'Italic',

    # family: ITC Avant Garde Gothic Demi
    'AvantGardeITCbyBT-Demi': 'Demi',

    # family: Boondox Calligraphic
    'BoondoxCalligraphic-Regular': '',
    # family: DokChampa
    'DokChampa': '',

    # family: Computer Modern
    # Computer Modern Roman
    'SFRM1000': '',
    'SFRM1200': '',
    'SFRM1728': '',
    'SFRB1000': '',
    'SFRB1200': '',
    'SFRB1440': '',
    'SFRM0500': '',
    'SFRM0600': '',
    'SFRM0700': '',
    'SFRM0800': '',
    'SFRM0900': '',
    'SFRM1095': '',
    'SFRM1440': '',
    'SFRM2074': '',

    # Computer Modern Bold Italics
    'SFBI0800': 'BoldItalics',
    'SFBI0900': 'BoldItalics',
    'SFBI1000': 'BoldItalics',
    'SFBI1200': 'BoldItalics',
    'SFBI1728': 'BoldItalics',
    'SFBI2488': 'BoldItalics',


    # Computer Modern Bold Extended
    'SFBX0700': 'Bold',
    'SFBX0800': 'Bold',
    'SFBX1000': 'Bold',
    'SFBX1095': 'Bold',
    'SFBX1200': 'Bold',
    'SFBX1440': 'Bold',
    'SFBX1728': 'Bold',
    'SFBX2074': 'Bold',
    'SFBX2488': 'Bold',
    # Computer Modern Caps and Small Caps
    'SFCC1000': 'Caps',
    'SFCC0800': 'Caps',
    'SFCC1200': 'Caps',
    'SFCC1440': 'Caps',
    'SFCC2074': 'Caps',

    # Computer Modern Sans Serif
    'SFSS1200': '',
    'SFSI1000': '',
    'SFSI1200': '',
    'SFSO1000': '',
    'SFSS0600': '',
    'SFSS1000': '',
    'SFSS1728': '',

    # Computer Modern Italic
    'SFIT0800': '',

    # Computer Modern Italic
    'SFTI1000': 'Italic',
    'SFTI1200': 'Italic',
    'SFTI0800': '',
    'SFTI0900': '',
    'SFTI1095': '',
    'SFTI1440': '',
    'SFTI1728': '',

    'SFTT0800': 'Typewriter',
    'SFTT1095': 'Typewriter',
    'SFTT1200': 'Typewriter',
    'SFTT1440': 'Typewriter',

    # Computer Modern Slanted
    'SFSL1000': '',
    'SFSL1200': '',

    # Computer Modern Typewriter
    'SFTT0900': '',
    'SFTT1000': '',

    'SFSX1000': '',

    'SFXC1728': '',

    # family: Arial MT
    'ArialMT': '',
    'Arial-BoldItalicMT': 'BoldItalic',
    'Arial-BoldMT': 'Bold',
    'Arial-ItalicMT': 'Italic',

    'Arial': '',
    'Arial,Bold': 'Bold',
    'Arial,Italic': 'Italic',
    'ArialNarrow': 'Narrow',
    'ArialNarrow-Bold': 'NarrowBold',
    'ArialNova': '',
    'ArialNova-Bold': 'Bold',
    'ArialRegular': '',
    'ArialRoundedMTBold': 'Bold',
    'ArialUnicodeMS': '',

    # family: 
    'arrow': '',

    # family: 
    'ArtifaktElement-Book': 'Book',
    'ArtifaktElement-Italic': 'Italic',
    'ArtifaktElement-Regular': '',

    # family: 
    'Athelas-Regular': '',

    # family: 
    'Avenir-Book': 'Book',
    'AvenirLTStd-Book': 'Book',
    'AvenirNext-Bold': 'Bold',
    'AvenirNextLTPro,Bold': 'Bold',
    'AvenirNextLTPro-Demi': 'Demi',
    'AvenirNextLTPro-Regular': '',
    'AvenirNext-Regular': '',
    'AvenirNext-UltraLight': 'UltraLight',
    'AvenirNext-UltraLightItalic': 'UltraLightItalic',

    # family: 
    'Bahnschrift': '',
    'Bahnschrift-LightCondensed': 'LightCondensed',
    'Bahnschrift-SemiBoldCondensed': 'SemiBoldCondensed',

    # family: 
    'BankGothicBT-Medium': 'Medium',

    # family: 
    'Baskerville': '',
    'Baskerville-Bold': 'Bold',
    'Baskerville-Italic': 'Italic',
    'Baskerville-SemiBold': 'SemiBold',

    # family: 
    'BBOLD10': '',

    # family: 
    'BCAlphapipeRB-Regular': '',

    # family: 
    'BeraSansMono-Bold': 'Bold',
    'BeraSansMono-Roman': '',

    # family: 
    'BerlinSansFB-Reg': '',

    # family: 
    'Bierstadt': '',
    'Bierstadt,Bold': 'Bold',
    'Bierstadt,BoldItalic': 'BoldItalic',
    'Bierstadt,Italic': 'Italic',
    'BitterThin-Regular': 'Thin',

    # family: 
    'BritannicBold': 'Bold',

    # family: 
    'Calibri': '',
    'Calibri-Bold': 'Bold',
    'Calibri-Italic': 'Italic',
    'Calibri-Light': '',
    'Calibri,Bold': 'Bold',
    'Calibri,BoldItalic': 'BoldItalic',
    'Calibri,Italic': 'Italic',
    'Calibri-BoldItalic': 'BoldItalic',
    'Calibri-LightItalic': 'LightItalic',

    # family: 
    'CalifornianFB-Bold': 'Bold',
    'CalifornianFB-Reg': '',

    # family: 
    'Cambria': '',
    'Cambria-Bold': 'Bold',
    'Cambria-Italic': 'Italic',
    'Cambria-BoldItalic': 'BoldItalic',
    'CambriaMath': '',

    # family: 
    'Candara': '',
    'Candara-Bold': 'Bold',
    'Candara-BoldItalic': 'BoldItalic',
    'Candara-Italic': 'Italic',
    'Candara-LightItalic': 'LightItalic',

    # family: 
    'Cavolini,Bold': 'Bold',

    # family: 
    'CenturyGothic': '',
    'CenturyGothic-Bold': 'Bold',
    'CenturyGothic-BoldItalic': 'BoldItalic',
    'CenturyGothic-Italic': 'Italic',

    # family: 
    'Cera-Bold': 'Bold',
    'CeraCY-Black': 'Black',
    'Cera-Thin': 'Thin',
    'Cera-ThinItalic': 'ThinItalic',

    # family: 
    'CharterBT-Bold': 'Bold',
    'CharterBT-Italic': 'Italic',
    'CharterBT-Roman': '',
    'CharterBT-Roman-Slant_167': 'Slanted',

    # family: 
    'CIDFont': '',

    # family: 
    'CircularPro-Bold': 'Bold',
    'CircularPro-Book': 'Book',
    'CircularPro-BookItalic': 'BookItalic',
    'CircularPro-Medium': 'Medium',

    # family: 
    'cochBMI': '',
    'cochMI': '',
    'cochMRM': '',

    # family: 
    'Cochineal-Bold': 'Bold',
    'Cochineal-Italic': 'Italic',
    'Cochineal-Roman': '',

    # family: 
    'ComicMono': '',
    'ComicSansMS': '',

    # family: 
    'Consolas': '',
    'ConsolasRegular': '',
    'ConsolasBold': 'Bold',
    'Consolas-Bold': 'Bold',

    # family: 
    'Corbel': '',
    'Corbel-Bold': 'Bold',
    'Corbel-BoldItalic': 'BoldItalic',
    'Corbel-Italic': 'Italic',
    'CorbelLight': 'Light',
    'Corbel-Light': 'Light',
    'CorbelLight-Italic': 'LightItalic',

    # family: 
    'CormorantGaramond-SemiBold': 'SemiBold',
    'CormorantGaramond-SemiBoldItalic': 'SemiBoldItalic',

    # family: 
    'Courier': '',
    'CourierNew': '',
    'CourierNew,Bold': 'Bold',
    'CourierNew-Italic': 'Italic',
    'CourierNewPS-BoldItalicMT': 'BoldItalic',
    'CourierNewPS-BoldMT': 'Bold',
    'CourierNewPS-ItalicMT': 'Italic',
    'CourierNewPSMT': '',
    'CourierStd-Bold': 'Bold',

    # family: 
    'DejaVuSans': '',
    'DejaVuSans-Bold': 'Bold',
    'DejaVuSans-BoldOblique': 'BoldOblique',
    'DejaVuSansMono': '',
    'DejaVuSansMono-Bold': 'Bold',
    'DejaVuSans-Oblique': 'Oblique',

    'Dingbats': '',

    'DengXian': '',
    'DengXian-Regular': '',
    'DroidSans-Bold': 'Bold',
    'DroidSans-Regular': '',
    'DroidSerif-Bold': 'Bold',
    'DroidSerif-Regular': '',

    # family: Double stroke Math font - https://ctan.uib.no/fonts/doublestroke/dsdoc.pdf
    'dsrom10': '',
    'dsrom12': '',
    
    # family: 
    'EB': '',
    'EBGaramond-Bold': 'Bold',
    'EBGaramond-BoldItalic': 'BoldItalic',
    'EBGaramond-Italic': 'Italic',
    'EBGaramond-Italic-Identity-H': 'Italic',
    'EBGaramond-Medium': 'Medium',
    'EBGaramond-MediumItalic': 'MediumItalic',
    'EBGaramond-Regular': '',
    'EBGaramond-Regular-Identity-H': '',
    'EBGaramondRoman-Bold': 'Bold',
    'EBGaramond-SemiBold': 'SemiBold',
    'EBGaramond-SemiBold-Identity-H': 'SemiBold',

    # family: 
    'EdwardianScriptITC': '',

    # family: 
    'erewMI': '',
    'erewMR': '',

    # family: 
    'EricssonHilda-Light': 'Light',

    # family: ETH
    'ETH-SemiBold': 'Bold',

    # family: eufrak - an AMS fractur font
    'EUFM10': '',

    # family: 
    'FjallaOne-Regular': '',

    # family: Font Awesome 5 Brands - these are various icons
    'FontAwesome': '',
    'FontAwesome5Brands-Regular': '',
    'FontAwesome5Free-Solid': '',

    # family: 
    'Fourier-Math-Extension': '',
    'Fourier-Math-Symbols': '',
    'FournierMT': '',
    'FournierMT-Italic': 'Italic',
    'FournierMT-TallCaps': 'Caps',

    # family: 
    'FranklinGothic-Demi': 'Demi',

    # family: 
    'FreeSerif': '',
    'FreestyleScript-Regular': '',

    # family: 
    'FrutigerLT-Bold': 'Bold',
    'FrutigerLT-Light': 'Light',
    'FrutigerLT-Roman': '',

    # family: 
    'Futura-Bold': 'Bold',
    'Futura-Book': 'Book',
    'FuturaBT-BoldCondensed': 'BoldCondensed',
    'FuturaBT-Heavy': 'Heavy',
    'FuturaBT-LightCondensed': 'LightCondensed',
    'FuturaBT-Medium': 'Medium',
    'FuturaBT-MediumCondensed': 'MediumCondensed',
    'Futura-CondensedLight': 'LightCondensed',
    'Futura-Medium': 'Medium',
    'Futura-MediumItalic': 'MediumItalic',
    'FuturaPT-Bold': 'Bold',
    'FuturaPT-Bold-SC700': 'Bold',
    'FuturaPT-Book': 'Book',
    'FuturaPT-Demi': 'Demi',
    'FuturaPT-DemiObl': 'Demi',
    'FuturaPT-Heavy': 'Heavy',
    'FuturaPT-Light': 'Light',
    'FuturaPT-Light-SC700': 'Light',
    'FuturaPT-Medium': 'Medium',
    'FuturaPT-Medium-SC700': 'Medium',

    # family: 
    'Gadugi': '',

    # family: 
    'Garamond': '',
    'Garamond-Bold': 'Bold',
    'Garamond-BoldItalic': 'BoldItalic',
    'Garamond-Italic': 'Italic',

    # family: 
    'Gautami': '',

    # family: 
    'GENISO': '',

    # family: 
    'Geogrotesque-Light': 'Light',
    'Geogrotesque-LightItalic': 'LightItalic',
    'Geogrotesque-Medium': 'Medium',
    'Geogrotesque-Regular': '',
    'Geogrotesque-RegularItalic': 'Italic',
    'Geogrotesque-UltraLight': 'UltraLight',
    'Geogrotesque-UltraLightItalic': 'UltraLightItalic',

    # family: 
    'Georgia': '',
    'Georgia-Bold': 'Bold',
    'Georgia-BoldItalic': 'BoldItalic',
    'Georgia-Italic': 'Italic',
    'Georgia,Bold': 'Bold',
    'Georgia,BoldItalic': 'BoldItalic',
    'Georgia,Italic': 'Italic',
    'GeorgiaPro-Bold': 'Bold',
    'GeorgiaPro-Italic': 'Italic',
    'GeorgiaPro-Regular': '',

    # family: 
    'Gibson': '',
    'Gibson-Italic': 'Italic',
    'Gibson-LightItalic': 'LightItalic',
    'Gibson-SemiBold': 'SemiBold',
    'Gibson-SemiBoldItalic': 'SemiBoldItalic',

    # family: 
    'GillSans': '',
    'GillSans-Bold': 'Bold',
    'GillSans-Light': 'Light',
    'GillSansMT': '',
    'GillSansMT-Bd': '',
    'GillSansMT-BdIt': '',
    'GillSansMT-Bk': '',
    'GillSansMT-Bold': 'Bold',
    'GillSansMT-BoldItalic': 'BoldItalic',
    'GillSansMT-Italic': 'Italic',
    'GillSansMT-Lt': '',
    'GillSansMT-LtIt': '',
    'GillSansMT-Md': '',

    # family: 
    'Gineso-NorLig': '',

    # family: 
    'GreekS': '',

    # family: fonts/greek/cbfonts/fonts/source/cbgreek - https://ctan.org/tex-archive/fonts/greek/cbfonts/fonts/source/cbgreek
    'grmn1000': '',
    'grmn1200': '',

    # family: 
    'Gungsuh': '',

    # family: 
    'Helvetica': '',
    'Helvetica,Bold': 'Bold',
    'Helvetica-Bold': 'Bold',
    'Helvetica-Oblique': 'Oblique',
    'Helvetica-BoldOblique': 'BoldOblique',
    'Helvetica-Light': 'Light',
    'HelveticaNeue': '',
    'HelveticaNeue-Bold': 'Bold',
    'HelveticaNeue-BoldItalic': 'BoldItalic',
    'HelveticaNeue-CondensedBold': 'BoldCondensed',
    'HelveticaNeue-Italic': 'Italic',
    'HelveticaNeue-Light': 'Light',
    'HelveticaNeue-LightItalic': 'LightItalic',
    'HelveticaNeueLTStd-BdCn': 'BoldCondensed',
    'HelveticaNeueLTStd-Cn': 'Condensed',
    'HelveticaNeue-Medium': 'Medium',
    'HelveticaNeue-MediumItalic': 'MediumItalic',
    'HelveticaNeue-Roman': '',
    'HelveticaNeue-Thin': 'Thin',
    'HelveticaNeue-ThinItalic': 'ThinItalic',

    # family: 
    'Heuristica-Bold': 'Bold',
    'Heuristica-Italic': 'Italic',
    'Heuristica-Regular': '',

    # family: 
    'HomemadeApple-Regular': '',

    # family: Inconsolata - inconsolata-zi4 - CTAN fonts/inconsolata-zi4 - https://ctan.org/tex-archive/fonts/inconsolata-zi4
    'Inconsolatazi4-Regular': '',
    'Inconsolatazi4-Bold': 'Bold',
    'Inconsolata-zi4b': 'Bold',
    'Inconsolata-zi4r': '',

    # family: 
    'Inter-Light': 'Light',
    'Inter-Medium': 'Medium',
    'Inter-Regular': '',

    # family: 
    'Interstate-ThinItalic': 'ThinItalic',

    # family: 
    'Inter-Thin': 'Thin',

    # family: 
    'ISOCPEUR': '',

    # family: Josefin
    'JosefinSans': '',
    'JosefinSans-Bold': 'Bold',
    'JosefinSans-Italic': 'Italic',
    'JosefinSans-Light': 'Light',
    'JosefinSans-LightItalic': 'LightItalic',
    'JosefinSans-SemiBold': 'SemiBold',
    'JosefinSans-Thin': 'Thin',
    'JosefinSans-ThinItalic': 'ThinItalic',
    'Josefin-Sans-Light-Roman': '',

    # family: 
    'Juhl-Bold': 'Bold',
    'Juhl-Heavy': 'Heavy',
    'Juhl-Light': 'Light',
    'Juhl-LightItalic': 'LightItalic',
    'Juhl-Medium': 'Medium',
    'Juhl-Thin': 'Thin',

    # family: 
    'KelveticaNobis': '',

    # family: 
    'LatinModernMath-Regular-Identity-H': '',

    # family: 
    'Lato': '',
    'Lato,Bold': 'Bold',
    'Lato,BoldItalic': 'BoldItalic',
    'Lato,Italic': 'Italic',
    'Lato-Bold': 'Bold',
    'Lato-Heavy': 'Heavy',
    'Lato-Italic': 'Italic',
    'Lato-Regular': '',

    # family: Liberation
    'Liberation': '',
    'LiberationSans': '',
    'LiberationSans-Bold': 'Bold',
    'LiberationSans-Italic': 'Italic',

    # family: 
    'LibertineMathMI5': '',
    'LibertineMathMI7': '',
    'LibertinusT1Math': '',


    # family: Linux Libertine
    'LinLibertineT': '',
    'LinLibertineTB': 'Bold',
    'LinLibertineTI': 'Italic',
    'LinBiolinumTB':  'Bold',
    'LinBiolinumTI':  'Italic',
    'LibertineMathMI': 'Italic',
    'LinLibertineMT': '',
    'LinLibertineTBI': 'BoldItalicTypewrite',

    # family: Latin Modern - CTAN lm-math
    'LMMath-Regular': '',
    'LMMathExtension10-Regular': '',
    'LMMathItalic10-Regular': '',
    'LMMathItalic12-Regular': '',
    'LMMathItalic6-Regular': '',
    'LMMathItalic7-Regular': '',
    'LMMathItalic8-Regular': '',
    'LMMathItalic9-Regular': '',
    'LMMathItalic10-Bold': 'BoldItalic',
    'LMMathItalic5-Regular': 'Italic',

    'LMMathSymbols5-Regular': '',
    'LMMathSymbols6-Regular': '',
    'LMMathSymbols7-Regular': '',
    'LMMathSymbols8-Regular': '',
    'LMMathSymbols9-Regular': '',
    'LMMathSymbols10-Regular': '',

    # family: Latin Modern Mono - https://tug.org/FontCatalogue/latinmodernmono/
    'LMMono8-Regular': '',
    'LMMono8-Regular-Identity-H': '',
    'LMMono9-Regular': '',
    'LMMono10-Regular': '',
    'LMMono10-Regular-Identity-H': '',
    'LMMono10-Italic-Identity-H': 'Italic',
    'LMMono12-Regular': '',
    'LMMono12-Regular-Identity-H': '',
    'LMMonoLt10-Bold': 'Bold',
    'LMMonoLt10-Bold-Identity-H': 'Bold',
    'LMMonoSlant10-Regular': 'Slanted',
    'LMMonoSlant10-Regular-Identity-H': 'Slanted',

    # family: Latin Modern Roman - https://tug.org/FontCatalogue/latinmodernroman/
    'LMRoman5-Regular': '',
    'LMRoman6-Regular': '',
    'LMRoman6-Regular-Identity-H': '',
    'LMRoman7-Italic': 'Italic',
    'LMRoman7-Regular': '',
    'LMRoman7-Regular-Identity-H': '',
    'LMRoman8-Bold': 'Bold',
    'LMRoman8-Bold-Identity-H': 'Bold',
    'LMRoman8-Italic': 'Italic',
    'LMRoman8-Italic-Identity-H': 'Italic',
    'LMRoman8-Regular': '',
    'LMRoman8-Regular-Identity-H': '',
    'LMRoman9-Bold': 'Bold',
    'LMRoman9-Italic': 'Italic',
    'LMRoman9-Regular': '',
    'LMRoman10-Bold': 'Bold',
    'LMRoman10-Bold-Identity-H': 'Bold',
    'LMRoman10-BoldItalic': '',
    'LMRoman10-Italic': 'Italic',
    'LMRoman10-Italic-Identity-H': 'Italic',
    'LMRoman10-Regular': '',
    'LMRoman10-Regular-Identity-H': '',
    'LMRoman10-Regular2': '',
    'LMRoman12-Bold': 'Bold',
    'LMRoman12-Bold-Identity-H': 'Bold',
    'LMRoman12-Italic': 'Italic',
    'LMRoman12-Italic-Identity-H': 'Italic',
    'LMRoman12-Regular': '',
    'LMRoman12-Regular-Identity-H': '',
    'LMRoman17-Regular': '',
    'LMRomanCaps10-Regular': '',
    'LMRomanCaps10-Regular-Identity-H': 'Caps',
    'LMRomanDemi10-Regular': '',
    'LMRomanDemi10-Regular-Identity-H': 'Demi',
    'LMRomanSlant10-Regular': 'Slanted',
    'LMRomanSlant12-Regular': 'Slanted',
    'LMRomanSlant12-Regular-Identity-H': 'Slanted',

    # family: Latin Modern Sans - https://tug.org/FontCatalogue/latinmodernsans/
    'LMSans10-Bold': 'Bold',
    'LMSans10-Bold-Identity-H': 'Bold',
    'LMSans10-Regular': '',
    'LMSans12-Oblique': 'Oblique',
    'LMSans12-Oblique-Identity-H': 'Oblique',
    'LMSans12-Regular': '',
    'LMSans12-Regular-Identity-H': '',
    'LMSans17-Regular-Identity-H': '',
    'LMSans8-Regular': '',
    'LMSansDemiCond10-Regular': 'Demi',

    # family: 
    'Lora-Regular': '',

    # family: 
    'LucidaBright': '',
    'LucidaConsole': '',
    'LucidaGrande-Bold': 'Bold',
    'LucidaSans-Demi': 'Demi',
    'LucidaSans-Italic': 'Italic',
    'LucidaSansUnicode': '',

    # family: 
    'MaiandraGD-Regular': '',
    'MalgunGothicBold': 'Bold',
    'MalgunGothicRegular': '',

    # family: 
    'Mangal': '',
    'Mangal,Bold': 'Bold',
    'MarVoSym': '',

    # family: 
    'MathcadUniMathPrime': '',
    'MathcadUniMathPrime-Italic': 'Italic',

    # family: 
    'MathematicaSans': '',

    # family: 
    'Memento': '',

    # family: 
    'Menlo-Bold': 'Bold',
    'Menlo-BoldItalic': 'BoldItalic',
    'Menlo-Italic': 'Italic',
    'Menlo-Regular': '',

    # family: 
    'Merriweather': '',
    'Merriweather,Italic': 'Italic',

    # family: 
    'MicrosoftJhengHeiRegular': '',
    'MicrosoftJhengHeiUIBold': 'Bold',
    'MicrosoftJhengHeiUILight': 'Light',
    'MicrosoftJhengHeiUIRegular': '',
    'MicrosoftSansSerif': '',
    'MicrosoftYaHei': '',
    'MicrosoftYaHei-Bold': 'Bold',
    'MicrosoftYaHeiLight': 'Light',

    # family: MinionPro
    'MinionPro-Regular': '',
    'MinionPro-BoldCn': 'BoldCondensed',

    # family: 
    'Montserrat': '',
    'Montserrat-Bold': 'Bold',
    'Montserrat-Regular': '',
    'Montserrat-Thin': 'Thin',

    # family: 
    'mplus-2p-bold': 'Bold',
    'mplus-2p-light': 'Light',
    'mplus-2p-medium': 'Medium',
    'mplus-2p-regular': '',

    # family: 
    'MS-Gothic': '',
    'MS-Mincho': '',
    'MS-PGothic': '',
    'MS-PMincho': '',

    # family: 
    'MTMI': '',
    'MTSY': '',

    # family: 
    'Muli-Bold': 'Bold',
    'Muli-ExtraLight': 'ExtraLight',
    'Muli-Light': 'Light',

    # family: 
    'Muro-Regular': '',

    # family: 
    'MuseoSans-100': '',
    'MuseoSans-300': '',
    'MuseoSans-500': '',
    'MuseoSans-700': '',
    'MuseoSlab-500': '',

    # family: 
    'mwb_cmmi10': '',
    'mwb_cmsy10': '',

    # family: MyriadPro
    'MyriadPro-BoldIt': 'BoldItalic',
    'MyriadPro-It': 'Italic',
    'MyriadPro-Regular': '',
    'MyriadPro-Bold': 'Bold',
    'MyriadPro-Regular-Identity-H': '',

    # family: 
    'NanumBarunGothic': '',

    # family: 
    'NeutraDisp-BoldAlt': 'Bold',
    'NeutraDisp-LightAlt': 'Light',
    'NeutraDisp-MediumAlt': 'Medium',
    'NeutraText-Bold': 'Bold',
    'NeutraText-BoldAlt': 'Bold',
    'NeutraText-BookAlt': 'Book',
    'NeutraText-BookItalic': 'BookItalic',
    'NeutraText-Demi': 'Demi',
    'NeutraText-DemiAlt': 'Demi',
    'NeutraText-DemiItalic': 'DemiItalic',
    'NeutraText-DemiItalicAlt': 'DemiItalic',
    'NeutraText-LightAlt': 'Light',
    'NeutraText-LightItalicAlt': 'LightItalic',

    # family: 
    'NewTXMI7': '',

    # family: Nimbus
    'NimbusMonL-Regu': '',
    'NimbusRomNo9L-Medi': '',
    'NimbusRomNo9L-MediItal': 'Italic',
    'NimbusRomNo9L-Regu': '',
    'NimbusRomNo9L-ReguItal': 'Italic',
    'NimbusRomNo9L-Regu-Slant_167': 'Slanted',
    'NimbusSanL-Bold': 'Bold',
    'NimbusSanL-BoldCond': 'Bold Condensed',
    'NimbusSanL-Regu': '',
    'NimbusSanL-ReguItal': 'Italic',
    'NimbusSanL-ReguCond': 'Condensed',

    # family: 
    'NirmalaUI': '',

    # family: 
    'Noto': '',
    'NotoSans-Bold': 'Bold',
    'NotoSansCJKjp-Light': 'Light',
    'NotoSansCJKjp-Regular-Identity-H': '',
    'NotoSans-Regular': '',

    # family: 
    'Nunito-Bold': 'Bold',
    'Nunito-Italic': 'Italic',
    'Nunito-Regular': '',

    # family: 
    'ObjektivMk3-Bold': 'Bold',
    'ObjektivMk3-BoldItalic': 'BoldItalic',
    'ObjektivMk3-Italic': 'Italic',
    'ObjektivMk3-Light': 'Light',
    'ObjektivMk3-Medium': 'Medium',
    'ObjektivMk3-MediumItalic': 'MediumItalic',
    'ObjektivMk3-Regular': '',
    'ObjektivMk3-XBold': 'Bold',

    # family: 
    'OmnesLight': 'Light',

    # family: 
    'Open': '',

    # family: 
    'OpenSans': '',
    'OpenSans-Regular': '',
    'OpenSans-Bold': 'Bold',
    'OpenSans-Italic': 'Italic',
    'OpenSans-Medium': 'Medium',
    'OpenSans-SemiBold': 'SemiBold',
    'OpenSans-SemiBoldItalic': 'SemiBoldItalic',

    # family: 
    'Palatino-Bold': 'Bold',
    'Palatino-BoldItalic': 'BoldItalic',
    'Palatino-Italic': 'Italic',
    'PalatinoLinotype-Bold': 'Bold',
    'PalatinoLinotype-Italic': 'Italic',
    'PalatinoLinotype-Roman': '',
    'Palatino-Roman': '',

    # family: Pazo Math fonts - CTAN mathpazo
    'PazoMath': '',
    'PazoMath-Italic': 'Italic',
    'PazoMath-Bold': 'Bold',
    'PazoMath-BoldItalic': 'BoldItalic',
    'PazoMathBlackboardBold': 'Bold',

    # family: 
    'Perpetua': '',
    'Perpetua-Bold': 'Bold',
    'Perpetua-Italic': 'Italic',

    # family: 
    'PingFangTC-Regular': '',

    # family: 
    'Playfair': '',

    # family: 
    'PMingLiU': '',

    # family: 
    'Poppins': '',
    'Poppins,Bold': 'Bold',
    'Poppins-Bold': 'Bold',
    'Poppins-Italic': 'Italic',
    'Poppins-Regular': '',

    # family: 
    'ProximaNova-Regular': '',

    # family: 
    'Quasimoda-HairLine': '',

    # family: 
    'QuattrocentoSans': '',

    # family: 
    'Quicksand': '',
    'Quicksand-Light': 'Light',

    # family: 
    'RageItalic': 'Italic',

    # family: 
    'Roboto': '',
    'Roboto,Bold': 'Bold',
    'Roboto-Bold': 'Bold',
    'Roboto-BoldItalic': 'BoldItalic',
    'Roboto-Italic': 'Italic',
    'Roboto-Light': 'Light',
    'Roboto-Medium': 'Medium',
    'Roboto-Regular': '',
    'RobotoSlab-Bold': 'Bold',
    'RobotoSlab-Thin': 'Thin',
    'Roboto-Thin': 'Thin',
    'Roboto-ThinItalic': 'ThinItalic',

    # family: 
    'Rockwell': '',

    # family: 
    'RomanD': '',
    'RomanS': '',
    'RomanT': '',

    # family: 
    'RotisSansSerifStd-Light': 'Light',

    # family: 
    'Sabon-Italic': 'Italic',
    'Sabon-ItalicOsF': 'Italic',
    'Sabon-Roman': '',
    'Sabon-RomanOsF': '',
    'Sabon-RomanSC': '',

    # family: 
    'Salome': '',

    # family: 
    'Segoe': '',
    'SegoeUI': '',
    'SegoeUI-Bold': 'Bold',
    'SegoeUIEmoji': '',
    'SegoeUI-Light': 'Light',
    'SegoeUI-Semilight': 'LightSemi',
    'SegoeUISymbol': '',

    # family; SimSun & NSimSun is a Simplified Chinese font features mincho (serif) stroke style-https://docs.microsoft.com/sv-se/typography/font-list/simsun
    'SimSun': '',
    'NSimSun': '',

    # family: 
    'SolidEdgeISO1Symbols': '',

    # family: 
    'SourceCodePro-Regular': '',
    'SourceCodeVariable-Roman': '',
    'SourceSansPro-Black': 'Black',
    'SourceSansPro-Regular': '',
    'SourceSansVariable-Roman': '',

    # family: 
    'STIXGeneral-Italic': 'Italic',
    'STIXGeneral-Regular': '',
    'STIXMathCalligraphy-Regular': '',

    # family: 
    'Swiss721BT-Bold': 'Bold',
    'Swiss721BT-BoldItalic': 'BoldItalic',
    'Swiss721BT-Italic': 'Italic',
    'Swiss721BT-Roman': '',

    'StandardSymL': '',
    'StandardSymL-Slant_167': 'Slanted',

    # family: 
    'Sylfaen': '',

    # family: 
    'Symbol': '',
    'SymbolMT': '',

    # family: 
    'Tahoma': '',
    'Tahoma-Bold': 'Bold',

    # family: 
    'TakenbyVulturesAlternatesDe': '',

    # family: 
    'TaylorSwiftHandwriting': '',


    # family: TeXGyreCursor - CTAN tex-gyre-cursor – A font that extends URW Nimbus Mono L
    'TeXGyreCursor-Regular': '',
    'TeXGyreCursor-Regular-Identity-H': '',
    'TeXGyreCursor-Bold': 'Bold',
    'TeXGyreCursor-Bold-Identity-H': '',
    'TeXGyreCursor-Italic': 'Italic',
    'TeXGyreCursor-Italic-Identity-H': 'Italic',
    # family: TeXGyreHeros - CTAN tex-gyre-heros – A font family that extends URW Nimbus Sans L
    'TeXGyreHeros-Regular': '',
    'TeXGyreHeros-Regular-Identity-H': '',
    'TeXGyreHeros-Bold': 'Bold',
    'TeXGyreHeros-Bold-Identity-H': 'Bold',
    'TeXGyreHeros-BoldItalic': 'BoldItalic',
    'TeXGyreHeros-Italic': 'Italic',
    # family: TeXGyreTermes- CTAN tex-gyre-termes – A font family that extends URW Nimbus Roman
    'TeXGyreTermes-Regular': '',
    'TeXGyreTermes-Regular-Identity-H': '',
    'TeXGyreTermes-Bold': 'Bold',
    'TeXGyreTermes-Bold-Identity-H': 'Bold',
    'TeXGyreTermes-BoldItalic': 'BoldItalic',
    'TeXGyreTermes-BoldItalic-Identity-H': 'BoldItalic',
    'TeXGyreTermes-Italic': 'Italic',
    'TeXGyreTermes-Italic-Identity-H': 'Italic',
    # family: TeXGyreTermesX
    'TeXGyreTermesX-Regular': '',
    'TeXGyreTermesX-Bold': 'Bold',
    'TeXGyreTermesX-BoldItalic': 'BoldItalic',
    'TeXGyreTermesX-Italic': 'Italic',
    # family: Trade Gothic LT
    'TradeGothicLTStd-BdCn20': 'BoldCondensed',

    # family: 
    'Times': '',
    'Times,Bold': 'Bold',
    'Times,BoldItalic': 'BoldItalic',
    'Times,Italic': 'Italic',
    'Times-Bold': 'Bold',
    'Times-BoldItalic': 'BoldItalic',
    'Times-Italic': 'Italic',
    'Times-Roman': '',
    'TimesLTPro-Bold': 'Bold',
    'TimesLTPro-Italic': 'Italic',
    'TimesLTPro-Roman': '',
    'TimesNewRoman': '',
    'TimesNewRoman,Bold': 'Bold',
    'TimesNewRoman,Italic': 'Italic',
    'TimesNewRomanPS-BoldItalicMT': 'BoldItalic',
    'TimesNewRomanPS-BoldMT': 'Bold',
    'TimesNewRomanPS-ItalicMT': 'Italic',
    'TimesNewRomanPSMT': '',

    # family: 
    'TradeGothic-Bold': 'Bold',

    # family: 
    'Trajan-Bold': 'Bold',
    'TrajanPro-Bold': 'Bold',
    'TrajanPro-Regular': '',

    # family: 
    'TrebuchetMS': '',
    'TrebuchetMS-Bold': 'Bold',
    'TrebuchetMS-Italic': 'Italic',

    # family: 
    'TwCenMT-Regular': '',


    # family: 
    'URWPalladioL-Bold': '',
    'URWPalladioL-Ital': '',
    'URWPalladioL-Roma': '',
    'URWPalladioL-Roma-Slant_167': 'Slanted',


    # family: 
    'Utopia-Regular': '',
    'Utopia-Bold': 'Bold',
    'Utopia-BoldItalic': 'BoldItalic',
    'Utopia-Italic': 'Italic',

    # family: 
    'Verdana': '',
    'Verdana-Bold': 'Bold',
    'Verdana-BoldItalic': 'BoldItalic',
    'Verdana-Italic': 'Italic',

    # family: 
    'Wingdings-Regular': '',
    'Wingdings3': '',

    # family: 
    'wasy10': '',

    # family: 
    'Yellowtail-Regular': '',

    # family: 
    'Yhcmex': '',

    # family: 
    'Yrsa-Regular': '',

    # family: 
    'YuGothicUI-Light': 'Light',
    'YuGothicUI-Regular': '',
    'YuGothicUI-Semibold': 'SemiBold',
    'YuGothicUI-Semilight': 'LightSemi',

    # family: 
    'zihun152hao-jijiachaojihei': '',

    # 'f-1-0': '',
    # 'F1': '',
    # 'F2': '',
    # 'F3': '',
    # 'F4': '',
    # 'F5': '',
    # 'F6': '',
    # 'F7': '',
    # 'F8': '',
    # 'F9': '',
    # 'F10': '',
    # 'F11': '',
    # 'F12': '',
    # 'F13': '',
    # 'F14': '',
    # 'F15': '',
    # 'F16': '',
    # 'F17': '',
    # 'F18': '',
    # 'F19': '',

    # 'FdSymbolA-Book': 'Book',
    # 'FdSymbolB-Book': 'Book',
    # 'FdSymbolE-Book': 'Book',
    # 'FdSymbolF-Book': 'Book',

    # 'font0000000028416bc6': '',
    # 'font0000000028416bce': '',
    # 'font000000002848d5b3': '',
    # 'font000000002848d5fb': '',
    # 'font00000000284f872d': '',
    # 'font000000002850e7e1': '',

}

def remove_fontname_prefix(fontname):
    if len(fontname) > 7 and fontname[6] == '+':
        return fontname[7:]
    else:
        print(f"in removed_fontname_prefix fontname ({fontname}) is too short, but be at longer than 7 characters")
        return None
    
def style_given_font_name(fontname):
    style=None
    # extract root name
    # first try mixed case version, then try lowercasing it
    style=font_families_and_names.get(fontname, None)
    if style:
        return style
    style=font_families_and_names.get(fontname.lower(), None)
    if style:
        return style
    # trim digits off if they exist
    if len(fontname) > 2:
        if fontname[-1].isdigit():
            shortened_name=fontname[:-1]
            style=style_given_font_name(shortened_name.lower())
    return style

def check_for_emphasis_style(fontname, styles):
    fontname=remove_fontname_prefix(fontname)
    if fontname:
        style=style_given_font_name(fontname)
        if style:
            for s in styles:
                if style.lower().find(s.lower()) >= 0:
                    return True
    return False

def show_ltitem_hierarchy(o: Any, depth=0):
    """Show location and text of LTItem and all its descendants"""
    if depth == 0:
        print('element                        x1  y1  x2  y2   text')
        print('------------------------------ --- --- --- ---- -----')

    print(
        f'{get_indented_name(o, depth):<30.30s} '
        f'{get_optional_bbox(o)} '
        f'{get_optional_text(o)}'
    )

    if isinstance(o, Iterable):
        for i in o:
            show_ltitem_hierarchy(i, depth=depth + 1)


def get_indented_name(o: Any, depth: int) -> str:
    """Indented name of LTItem"""
    return '  ' * depth + o.__class__.__name__


def get_optional_bbox(o: Any) -> str:
    """Bounding box of LTItem if available, otherwise empty string"""
    if hasattr(o, 'bbox'):
        return ''.join(f'{i:<4.0f}' for i in o.bbox)
    return ''


def get_optional_text(o: Any) -> str:
    """Text of LTItem if available, otherwise empty string"""
    if hasattr(o, 'get_text'):
        return o.get_text().strip()
    return ''

def rough_comparison(a, b):
    if abs(a-b) < 0.1:
        return True
    return False


global found_references_page
references_place_y=630.0
#heading_size_min=19.0      # 24.79
heading_size_min=13.9      # 24.79

found_references_page=False
global found_last_references_page
found_last_references_page=False

# heading rule
# LTLine                       70.87   785.34  524.41  785.34   
page_heading_place_y=780.0
page_heading_size_min=10.0  #10.91
global found_heading_rule
found_heading_rule=False


global found_appendix_page
found_appendix_page=False

global found_TOC_page
found_TOC_page=False

# Match against targets including an all caps version of target with a vertical bar
def check_for_one_target_string_alone(txt, targets):
    txt=txt.strip()
    for t in targets:
        # find target along in a section/chapter heading
        if txt.find(t) >= 0 and len(txt) == len(t):
            return True
        # find target in a page heading
        if txt.find('|') > 0 and (txt.find(t) >= 0 or txt.find(t.upper()) >= 0):
            return True
        if txt.find(t) >= 0 and txt.find(t) < 10:
            print("Possible heading {0} in {1} with len(txt)={2}".format(t, txt, len(txt)))
            return True
        if txt.find(t.upper()) >= 0 and txt.find(t.upper()) < 10:
            print("Possible heading {0} in {1} with len(txt)={2}".format(t, txt, len(txt)))
            return True
    return False

# Note that we have to set the globals to the page index (pgnumber)
def check_for_references(o: Any, pgnumber):
    global found_references_page
    global found_last_references_page
    global found_appendix_page
    global Verbose_Flag
    target_strings=['References', 'Bibliography', 'References and Bibliography']
    appendix_strings=['Appendix', 'Appendices']

    txt=o.get_text().strip()
    # This check for the target alone is to avoid the instance of the target in the Table of Contents
    if check_for_one_target_string_alone(txt, target_strings):
        if Verbose_Flag or True:
            print("Found references starting at page:{}".format(pgnumber))
        if not found_references_page:
            found_references_page=pgnumber
        else:
            found_last_references_page=pgnumber
    elif check_for_one_target_string_alone(txt, appendix_strings):
        if Verbose_Flag or True:
            print("Found appendix/appendices at page:{0} - {1}".format(pgnumber, txt))
        if found_references_page:
            print("found_appendix_page={0} found_last_references_page={1}".format(found_appendix_page, found_last_references_page))
            if not found_appendix_page and not found_last_references_page:
                found_appendix_page=True
                found_last_references_page=pgnumber-1
    else:
        return
    return

# check for section/chapter heading being some variant of References
def check_for_references_in_section_heading(o: Any, pgnumber):
    global found_references_page
    global found_last_references_page
    global found_TOC_page
    global found_appendix_page
    global Verbose_Flag
    target_strings=['References', 'Bibliography']
    appendix_strings=['Appendix', 'Appendices']
    toc_strings=['Contents', 'Table of contents']
    max_toc_length = 5          #  note that this is an arbitrary value, just to avoid finding "References" in the TOC

    txt=o.get_text().strip()
    newline_offset=txt.find('\n') # if there is an embedded new line, then just take the part before the newline
    if newline_offset >=0 :
        txt=txt[:newline_offset]
    if check_for_one_target_string_alone(txt, target_strings):
        if Verbose_Flag or True:
            print("in check_for_references_in_section_heading found references starting at page:{}".format(pgnumber))
        nbc=count_bold_characters(o)
        print("checking for heading in {0} - nbc={1}".format(txt, nbc))
        if nbc > len(txt)/2:
            # try to avoid the instance of "References" in the table of contents
            if not found_TOC_page:
                found_references_page=pgnumber
                print("First case in check_for_references_in_section_heading")
            elif found_TOC_page + max_toc_length < pgnumber:
                print("Second case in check_for_references_in_section_heading")
                if not found_references_page:
                    found_references_page=pgnumber
                else:
                    found_last_references_page=pgnumber
            else:
                print("Third case in check_for_references_in_section_heading")
                return
    elif check_for_one_target_string_alone(txt, appendix_strings):
        if Verbose_Flag or True:
            print("Found appendix/appendices at page:{0} - {1}".format(pgnumber, txt))
        if found_references_page:
            print("found_appendix_page={0} found_last_references_page={1}".format(found_appendix_page, found_last_references_page))
            if not found_appendix_page and not found_last_references_page:
                found_appendix_page=True
                found_last_references_page=pgnumber #  as this could be on the same page as the refrences
    elif check_for_one_target_string_alone(txt, toc_strings):
        if Verbose_Flag or True:
            print("Found table of contents at page:{0} - {1}".format(pgnumber, txt))
        # found_TOC_page will be the last page with a Contents page heading
        found_TOC_page=pgnumber
    else:
        return
    return


def check_for_references_page_header(o: Any, pgnumber):
    global found_references_page
    global found_last_references_page
    global found_appendix_page
    global found_TOC_page
    global Verbose_Flag
    target_strings=['References', 'Bibliography', 'References and Bibliography']
    appendix_strings=['Appendix', 'Appendices']
    toc_strings=['Contents', 'Table of contents']

    txt=o.get_text().strip()
    print("check for page header in {0} on page {1}".format(txt, pgnumber))

    # in this case there is a new page header, so stop including the pages in the set of reference pages
    if found_references_page and not check_for_one_target_string_alone(txt, target_strings):
        if not found_last_references_page:
            if Verbose_Flag:
                print("Change in page headers at page:{0} - {1}".format(pgnumber, txt))
            found_last_references_page=pgnumber-1
    # This check for the target alone is to avoid the instance of the target in the Table of Contents
    elif check_for_one_target_string_alone(txt, target_strings):
        if Verbose_Flag:
            print("Found references starting at page:{}".format(pgnumber))
        if not found_references_page:
            found_references_page=pgnumber
        else:
            found_last_references_page=pgnumber
    elif check_for_one_target_string_alone(txt, appendix_strings):
        if Verbose_Flag:
            print("Found appendix/appendices at page:{0} - {1}".format(pgnumber, txt))
        if found_references_page:
            print("found_appendix_page={0} found_last_references_page={1}".format(found_appendix_page, found_last_references_page))
            if not found_appendix_page and not found_last_references_page:
                found_appendix_page=True
                found_last_references_page=pgnumber-1
    elif check_for_one_target_string_alone(txt, toc_strings):
        if Verbose_Flag:
            print("Found table of contents at page:{0} - {1}".format(pgnumber, txt))
        # found_TOC_page will be the last page with a Contents page heading
        found_TOC_page=pgnumber
    else:
        return
    return

# If there are heading rules, update the expected location for page headings
def check_for_heading_rule(o: Any):
    global page_heading_place_y
    global found_heading_rule
    if found_heading_rule:
        return
    if (o.bbox[1] == o.bbox[3]) and (o.bbox[2] - o.bbox[0]) > 400.0 and (o.bbox[1] > page_heading_place_y):
        found_heading_rule=True
        page_heading_place_y=o.bbox[1]
        print("Found heading rule at {0} - the page heading should be above this".format(page_heading_place_y))

    return

def count_bold_characters(o: Any):
    global Verbose_Flag

    count=0
    if isinstance(o, LTTextContainer):
        print("in count_bold_characters({})".format(o.get_text()))
        for text_line in o:
            for character in text_line:
                if isinstance(character, LTAnno): #  if you hit a new line or similar return
                    return count
                if isinstance(character, LTChar):
                    if Verbose_Flag:
                        print("character.fontname={0}, size={1}, ncs={2}, graphicstate={3}, character={4}".format(character.fontname, character.size, character.ncs, character.graphicstate, character))
                    if 'Bold' in character.fontname:
                        count=count+1
                    elif 'Demi' in character.fontname:
                        count=count+1
                    else:
                        if check_for_emphasis_style(character.fontname, ['slanted', 'bold', 'oblique', 'caps']):
                            count=count+1
    return count


def process_element(o: Any, pgnumber):
    global extracted_data
    last_x_offset=None
    last_x_width=None
    last_y_offset=None            # y_offset of text characters

    if isinstance(o, LTTextBoxHorizontal):
        for text_line in o:
            if hasattr(text_line, 'bbox'):
                last_x_offset=text_line.bbox[0]
                last_y_offset=text_line.bbox[1]
                last_x_width=text_line.bbox[2]-text_line.bbox[0]
            if Verbose_Flag:
                print(f'text_line={text_line}')
            if hasattr(text_line, 'size'):
                font_size=text_line.size
            else:
                font_size=0
            if isinstance(text_line, LTAnno):
                print("found an LTAnno")

        # Check in page heading
        # LTTextBoxHorizontal          402.96  783.59  496.06  794.50   REFERENCES | 69
        # LTTextLineHorizontal       402.96  783.59  496.06  794.50   REFERENCES | 69
        if (o.bbox[1]-page_heading_place_y) >= 0.0: # and (o.bbox[3]-o.bbox[1]) >= page_heading_size_min:
            check_for_references_page_header(o, pgnumber)
        #
        #LTTextBoxHorizontal          127.56  638.43  261.19  663.22   References
        #LTTextLineHorizontal       127.56  638.43  261.19  663.22   References
        # elif (o.bbox[1]-references_place_y) > 0.0 and (o.bbox[3]-o.bbox[1]) >= heading_size_min:
        #     check_for_references(o, pgnumber)
        else:
            # check for section/chapter heading
            check_for_references_in_section_heading(o, pgnumber)
            return

    elif isinstance(o, LTTextContainer):
        if Verbose_Flag:
            print("element is LTTextContainer")
        for text_line in o:
            if Verbose_Flag:
                print(f'text_line={text_line}')
            if isinstance(text_line, LTAnno):
                if Verbose_Flag:                
                    print("found an LTAnno")
            else:
                font_size=text_line.size
                if Verbose_Flag:
                    print("font_size of text_line={}".format(text_line.size))
            if hasattr(text_line, 'bbox'):
                last_x_offset=text_line.bbox[0]
                last_y_offset=text_line.bbox[1]
                last_x_width=text_line.bbox[2]-text_line.bbox[0]
        extracted_data.append([font_size, last_x_offset, last_y_offset, last_x_width, (o.get_text())])
    elif isinstance(o, LTLine): #  a line
        #  LTLine                       70.87   785.34  524.41  785.34   
        check_for_heading_rule(o)
        return
    elif isinstance(o, LTFigure):
        if isinstance(o, Iterable):
            for i in o:
                process_element(i, pgnumber)
    elif isinstance(o, LTImage):
        return
        
    elif isinstance(o, LTChar):
        if Verbose_Flag:
            print("found LTChar: {}".format(o.get_text()))
        if hasattr(o, 'bbox'):
            last_x_offset=o.bbox[0]
            last_y_offset=o.bbox[1]
            last_x_width=o.bbox[2]-o.bbox[0]
            font_size=o.size
        extracted_data.append([font_size, last_x_offset, last_y_offset, last_x_width, (o.get_text())])
    elif isinstance(o, LTAnno):
        return
    elif isinstance(o, LTCurve): #  a curve
        return
    else:
        print(f'unprocessed element: {o}')
        if isinstance(o, Iterable):
            for i in o:
                process_element(i, pgnumber)

def process_file(filename):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global set_of_errors
    global set_of_evidence_for_new_cover
    global extracted_data
    global cycle
    global found_references_page
    global found_last_references_page
    global found_appendix_page


    extracted_data=[]
    set_of_errors=set()
    set_of_evidence_for_new_cover=set()
    major_subject=None            # the major subject
    cycle=None                    # the cycle number
    place=None                    # the place from the cover
    font_size=None                # the latest font size
    last_x_offset=None
    last_x_width=None
    last_y_offset=None            # y_offset of text characters

    found_references_page=False
    found_last_references_page=False
    found_TOC_page=False
    found_appendix_page=False

    page_index = 0
    try:
        for page in extract_pages(filename):
            page_index=page_index+1
            if Verbose_Flag:
                print(f'Processing page={page_index}')

            if testing:
                show_ltitem_hierarchy(page)
                print(page)
                continue

            for element in page:
                if Verbose_Flag:
                    print(f'{element}')
                process_element(element, page_index)

    except (PDFNoValidXRef, PSEOF, pdfminer.pdfdocument.PDFNoValidXRef, pdfminer.psparser.PSEOF) as e:
        print(f'Unexpected error in processing the PDF file: {filename} with error {e}')
        return False
    except Exception as e:
        print(f'Error in PDF extractor: {e}')
        return False

    if found_references_page:
        if not found_appendix_page and not found_last_references_page:
            found_last_references_page=page_index-1
            print("Assuming references end on page {}".format(found_last_references_page))
    return True


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing
    global set_of_errors
    global set_of_evidence_for_new_cover
    global extracted_data
    global cycle
    global found_references_page
    global found_last_references_page

    argp = argparse.ArgumentParser(description='find_and_extract_references.py: FInd reference page(s) within the PDF file')

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

    argp.add_argument('-s', '--spreadsheet',
                      type=str,
                      default=False,
                      help="spreadsheet file"
                      )

    argp.add_argument('-n', '--nth',
                      type=int,
                      default=False,
                      help="Number of rows to skip"
                      )

    argp.add_argument('-d', '--dump',
                      default=False,
                      action="store_true",
                      help="dump font information"
                      )


    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]
    testing=args["testing"]

    if args["dump"]:
        print("dumping the font information")
        # output fonts
        for font in font_families_and_names:
            print(f"{font}")
        return


    if not args["spreadsheet"]:
        filename=args["pdf"]
        if Verbose_Flag:
            print("filename={}".format(filename))

        if not process_file(filename):
            return
        if found_references_page:
            print("Found references page at {0} in {1}".format(found_references_page, filename))
        if not found_last_references_page:
            print("found_last_references_page was not set, setting it to found_references_page={}".format(found_references_page))
            found_last_references_page=found_references_page

        if found_last_references_page:
            print("Last references page at {0}".format(found_last_references_page))
            
            if filename.endswith('.pdf'):
                output_filename="{0}-refpages.pdf".format(filename[:-4])
            else:
                output_filename="output.pdf"

            cmd="qpdf {0} --pages . {1}-{2} -- {3}".format(filename, found_references_page, found_last_references_page, output_filename)
            if Verbose_Flag or True:
                print("cmd: {0}".format(cmd))

            with subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE) as proc:
                cmd_ouput=proc.stdout.read()
                if len(cmd_ouput) > 0:
                    print(cmd_ouput)
            return found_references_page
        else:
            return -1
    
    # the following handles the case of processing the available files based upon a spreadsheet
    spreadsheet_name=args["spreadsheet"]
    if not spreadsheet_name.endswith('.xlsx'):
        print("must give the name of a .xlsx spreadsheet file")
        return

    skip_to_row=args['nth']

    diva_df=pd.read_excel(open(spreadsheet_name, 'rb'))

    column_names=list(diva_df)
    # add columns for new information


    # this column is used to record the starting page numer of the For DIVA pages that have NOT been removed
    diva_df['For DIVA page(s) present'] = pd.NaT


    for idx, row in diva_df.iterrows():
        found_references_page=False
        found_last_references_page=False
        if skip_to_row and idx < skip_to_row:
            continue
        url=row['FullTextLink']
        author=row['Name']
        pid=row['PID']
        if pd.isna(url):
            print("no full text for thesis by {}".format(author))
        else:
            print(f'{idx}: {author}  {url}')
            last_slash_in_url=url.rfind('/')
            if last_slash_in_url < 0:
                print("Cannot find file name in URL")
                continue
            filename="{0}-{1}".format(pid, url[last_slash_in_url+1:])
            print(f'reading file {filename}')

            if not process_file(filename):
                diva_df.loc[idx, 'Unexpected error when processing file']=filename
                continue

            if found_references_page:
                print("Found references page at {0} in {1} by author(s) {2}".format(found_references_page, filename, row['Name']))
                if found_last_references_page:
                    diva_df.loc[idx, 'References page(s) present'] = "{0}-{1}".format(found_references_page, found_last_references_page)
                else:
                    diva_df.loc[idx, 'References page(s) present'] = "{0}".format(found_references_page)

                if filename.endswith('.pdf'):
                    output_filename="{0}-refpages.pdf".format(filename[:-4])
                else:
                    output_filename="{0}-refpages.pdf".format(filename)

                if found_last_references_page:
                    cmd="qpdf {0} --pages . {1}-{2} -- {3}".format(filename, found_references_page, found_last_references_page, output_filename)
                else:
                    cmd="qpdf {0} --pages . {1} -- {2}".format(filename, found_references_page, output_filename)
                if Verbose_Flag:
                    print("cmd: {0}".format(cmd))

                with subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE) as proc:
                    cmd_ouput=proc.stdout.read()
                    if len(cmd_ouput) > 0:
                        print(cmd_ouput)

        if args["testing"]:
            break

    # the following was inspired by the section "Using XlsxWriter with Pandas" on http://xlsxwriter.readthedocs.io/working_with_pandas.html
    # set up the output write
    output_spreadsheet_name=spreadsheet_name[:-5]+'with_references_info.xlsx'
    writer = pd.ExcelWriter(output_spreadsheet_name, engine='xlsxwriter')
    diva_df.to_excel(writer, sheet_name='ReferencesInfo')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

