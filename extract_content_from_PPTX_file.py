#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./extract_content_from_PPTX_file.py --file filename --dir target_directory
#
# Purpose: The program takes in a PPTX file and extracts the images and slide contents
#
# Output: outputs files and information to the target_directory
#
# Example:
# ./extract_content_from_PPTX_file.py --file Lecture-4-4-tiled-matrix-multiplication-kernel.pptx --dir Lecture-4-4-tiled-matrix-multiplication-kernel-contents
#
#
#
# 
# 2023-01-19 G. Q. Maguire Jr.
#
import re
import sys
import subprocess

import json
import argparse
import os			# to make OS calls, here to get time zone info

import time

import pprint

from collections import defaultdict


import datetime
import isodate                  # for parsing ISO 8601 dates and times
import pytz                     # for time zones
from dateutil.tz import tzlocal

# for dealing with the DOCX file - which is a ZIP file
import zipfile

# for creating files and directories
from pathlib import Path

# for parsing the XML
from lxml import etree

# for computing hashes
import hashlib

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED

modes = { zipfile.ZIP_DEFLATED: 'deflated',
          zipfile.ZIP_STORED:   'stored',
          }

# extract text "<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US"/><a:t>Tiled </a:t></a:r><a:r><a:rPr lang="en-US" dirty="0"/><a:t>Matrix Multiplication Kernel</a:t></a:r></a:p></p:txBody></p:sp><p:sp><p:nvSpPr><p:cNvPr id="3" name="Title 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="1121520" y="3601595"/><a:ext cx="5439300" cy="397032"/></a:xfrm></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="2200" dirty="0"/><a:t>Module 4.4 - Memory and Data Locality</a:t></a:r></a:p></p:txBody>

def extract_text(xml_content):
    nsmap ={
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
    }

    root = etree.fromstring(xml_content)
    print(f'{root=}')
    sp_txt_list=[b for b in root.iterfind(".//p:sp", nsmap) ]

    accumulated_sph_type=[]
    accumulated_txt_list=[]
    for sp in sp_txt_list:
        sph_txt_list=[b for b in sp.iterfind(".//p:ph", nsmap) ]
        print("sph_txt_list={}".format(sph_txt_list))

        sph_type=[b.get('type') for b in sph_txt_list]
        accumulated_sph_type.append(sph_type)

        txtBody_txt_list=[b for b in sp.iterfind(".//p:txBody", nsmap) ]

        txt_body=''
        for pb in txtBody_txt_list:
            pb_txt_list=[b for b in pb.iterfind(".//a:p", nsmap) ]
            new_txt_list=''
            for p in pb_txt_list:
                txt_list=[b.text for b in p.iterfind(".//a:t", nsmap) ]
                for t in txt_list:
                    new_txt_list=new_txt_list+' '+t
                if len(txt_body) == 0:
                    txt_body=new_txt_list
                else:
                    txt_body=txt_body+'\n'+new_txt_list
                new_txt_list=''
            accumulated_txt_list.append(txt_body)

    return {'types': accumulated_sph_type, 'text': accumulated_txt_list}

def clean_xml(txt):
    if not isinstance(txt, str):
        print("type is {}".format(type(txt)))
        print("expected a string in clean_txt() but got {}".format(txt))
        return txt.text

    return txt

def txt_list_to_string(txt_list):
    # take txt_list and put new lines between the parts of it
    ret_text=''
    for txt in txt_list:
        if isinstance(txt, list):
            for t1 in txt:
                ret_text=ret_text+'\n'+"{}".format(clean_xml(t1))
        ret_text=ret_text+'\n'+"{}".format(clean_xml(txt))

    return ret_text

#      <p:sp>
# 	<p:nvSpPr>
# 	  <p:cNvPr id="12" name="Subtitle 11"/>
# 	  <p:cNvSpPr>
# 	    <a:spLocks noGrp="1"/>
# 	  </p:cNvSpPr>
# 	  <p:nvPr>
# 	    <p:ph type="subTitle" idx="1"/>
# 	  </p:nvPr>
# 	</p:nvSpPr>
# 	<p:spPr/>
# 	<p:txBody>
# 	  <a:bodyPr/>
# 	  <a:lstStyle/>
# 	  <a:p>
# 	    <a:r>
# 	      <a:rPr lang="en-US" smtClean="0"/>
# 	      <a:t>Convolution
# 	      </a:t>
# 	    </a:r>
# 	    <a:endParaRPr lang="en-US" dirty="0"/>
# 	  </a:p>
# 	</p:txBody>
#       </p:sp>
#       <p:sp>
# 	<p:nvSpPr>
# 	  <p:cNvPr id="11" name="Title 10"/>
# 	  <p:cNvSpPr>
# 	    <a:spLocks noGrp="1"/>
# 	  </p:cNvSpPr>
# 	  <p:nvPr>
# 	    <p:ph type="title"/>
# 	  </p:nvPr>
# 	</p:nvSpPr>
# 	<p:spPr>
# 	  <a:xfrm>
# 	    <a:off x="1121520" y="3684695"/>
# 	    <a:ext cx="5439300" cy="313932"/>
# 	  </a:xfrm>
# 	</p:spPr>
# 	<p:txBody>
# 	  <a:bodyPr/>
# 	  <a:lstStyle/>
# 	  <a:p>
# 	    <a:r>
# 	      <a:rPr lang="it-IT" sz="1600" dirty="0"/>
# 	      <a:t>Module 
# 	      </a:t>
# 	    </a:r>
# 	    <a:r>
# 	      <a:rPr lang="it-IT" sz="1600" dirty="0" smtClean="0"/>
# 	      <a:t>8.1 – 
# 	      </a:t>
# 	    </a:r>
# 	    <a:r>
# 	      <a:rPr lang="it-IT" sz="1600" dirty="0"/>
# 	      <a:t>Parallel Computation Patterns 
# 	      </a:t>
# 	    </a:r>
# 	    <a:r>
# 	      <a:rPr lang="it-IT" sz="1600" dirty="0" smtClean="0"/>
# 	      <a:t>(Stencil)
# 	      </a:t>
# 	    </a:r>
# 	    <a:endParaRPr lang="en-US" sz="1600" dirty="0"/>
# 	  </a:p>
# 	</p:txBody>
#       </p:sp>
      


def know_image_hash(file_hash, known_hashes):
    p=known_hashes.get(file_hash, None)
    if p:
        return "{0}.{1}".format(p['known_file_name'], p['type'])
    return None

def main(argv):
    global Verbose_Flag
    global testing
    global Keep_picture_flag

    known_hashes={
        'e43fa5d98216bdfe2a19e819d0e2fd4c': {'known_file_name': 'gray_horizontal_parallelagram', 'type': 'png'},
        'c31da9d04513260c9b071e125760742e': {'known_file_name': 'gray_horizontal_parallelagram2', 'type': 'png'},
        '1b459c6db80e4b4664bd4073d17b6fd2': {'known_file_name': 'nvidia_logo_gray', 'type': 'png'},
        '8f6a5566e73115c6f79d1c9815881df8': {'known_file_name': 'Illinois_I_logo', 'type': 'png'},
        'df1038d40000d87428f55827e9f2395f': {'known_file_name': 'Illinois_logo', 'type': 'png'},
        'efda0b94249d0eb1277b0f0f1d2f3a78': {'known_file_name': 'burnished_stell', 'type': 'jpg'},
        '9e982c2b9f79fd737a8710e1a6fdf530': {'known_file_name': 'green_horizontal_parallelagram', 'type': 'png'},
        'd251cf20807a37c01fdac05a1d4538d4': {'known_file_name': 'Nvidia_logo_white', 'type': 'png'},
        '03003cc581e2035a9269db6c1bb96708': {'known_file_name': 'orange_semi_parallelagram', 'type': 'png'},
        '06057826ced78bd7ff4569bc56f41845': {'known_file_name': 'Large_Illinois_I_logo', 'type': 'png'},
        '4dfe8e3657bdc730a5bf2007a7fd4e88': {'known_file_name': 'Illinois_logo_univ_name', 'type': 'png'},
        '2a291aa013fadaddda5c9eddc12c82d6': {'known_file_name': 'Large_Illinois_I_logo_gray', 'type': 'jpeg'},
        '6c238a7c740d7aa1b6550a60f1bccd86': {'known_file_name': 'speaker_with_output', 'type': 'jpeg'},
        '100a81a4371f03c063fdd30819b4318c': {'known_file_name': 'CC-BY-NC', 'type': 'png'},
    }
    

    argp = argparse.ArgumentParser(description="extract_content_from_PPTX_file.py: to extract data from a PPTX file")

    argp.add_argument('-v', '--verbose', required=False,
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout")

    argp.add_argument('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    argp.add_argument('--file',
                      type=str,
                      help="DOCX template"
                      )

    argp.add_argument('-d', '--dir',
                      type=str,
                      default=False,
                      help="target directory"
                      )



    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    testing=args["testing"]
    if Verbose_Flag:
        print("testing={}".format(testing))
    input_filename=args["file"]
    if not input_filename.endswith('.pptx'):
        print("Input filename must end in .pptx")
        return

    target_directory=args["dir"]
    if not target_directory:
        target_directory=input_filename[:-5]+'-contents'
        print("No target directory specified, using: {}".format(target_directory))


    print(f'Creating directory: {target_directory}')
    Path(target_directory).mkdir(parents=True, exist_ok=True)

    document = zipfile.ZipFile(input_filename)
    file_names=document.namelist()
    if Verbose_Flag:
        print("File names in ZIP zip file: {}".format(file_names))

    for fn in file_names:
        if Verbose_Flag:
            print("processing file: {}".format(fn))

        # files to ignore
        if fn == '[Content_Types].xml':
            continue

        split_fn=fn.split('/')
        print(f'{split_fn=}')

        # Ignore files under _rels, customXml, docProps
        if split_fn[0] in ['_rels', 'customXml', 'docProps']:
            continue

        if len(split_fn) >= 2 and split_fn[0] == 'ppt' and split_fn[1] in ['theme' 'viewProps.xml', 'presProps.xml', 'tableStyles.xml', 'commentAuthors.xml', 'presentation.xml', 'notesMasters']:
            continue

        # Ignore files under the substrees indicated
        if len(split_fn) >= 2 and split_fn[0] == 'ppt' and split_fn[1] in ['_rels', 'slideLayouts', 'slideMasters']:
            continue

        # ignore files of the form split_fn=['ppt', 'slides', '_rels', 'slide4.xml.rels']
        if len(split_fn) == 4 and split_fn[0] == 'ppt' and split_fn[1] == 'slides' and split_fn[2] ==  '_rels':
            continue

        # extract slides such as split_fn=['ppt', 'slides', 'slide12.xml']
        if len(split_fn) == 3 and split_fn[0] == 'ppt' and split_fn[1] == 'slides':        
            file_contents = document.read(fn)
            output_filename=f'{target_directory}/{split_fn[2]}'
            with open(output_filename,'wb') as f:
                f.write(file_contents)

            #xml_content = document.read(fn).decode('utf-8')
            xml_content = file_contents 
            e_text_list=extract_text(xml_content)
            print(f'{e_text_list=}')
            e_text=txt_list_to_string(e_text_list['text'])
            with open(output_filename+'.txt','w') as f:
                f.write(e_text)


        # Extract media files, such as ppt/media/image10.png
        if len(split_fn) == 3 and split_fn[0] == 'ppt' and split_fn[1] == 'media':
            file_contents = document.read(fn)
            file_hash = hashlib.md5(file_contents).hexdigest()
            print("{0}: {1}".format(split_fn[2], file_hash))
            know_name=know_image_hash(file_hash, known_hashes)
            if know_name:
                output_filename=f'{target_directory}/{split_fn[2]}-{know_name}'
            else:
                output_filename=f'{target_directory}/{split_fn[2]}'
            with open(output_filename,'wb') as f:
                f.write(file_contents)


        # # copy existing file to archive
        # if fn not in [word_docprop_custom_file_name, word_document_file_name]:
        #     file_contents = document.read(fn)
        # else:
        #     if Verbose_Flag:
        #         print("processing {}".format(fn))
        #     xml_content = document.read(fn).decode('utf-8')
        #     if fn == word_docprop_custom_file_name:
        #         file_contents = transform_file(xml_content, dict_of_entries)
        #     elif fn == word_document_file_name:
        #         file_contents = mark_first_field_as_dirty(xml_content)
        #     else:
        #         print("Unknown file {}".format(fn))
        # # in any case write the file_contents out
        # zipOut.writestr(fn, file_contents,  compress_type=compression)

    document.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

