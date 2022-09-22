#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./customize_tex_from_nbconvert.py filename.tex [customization.tex]
#
# Purpose: Take the tex file produced by nbconvert and customize it
#
# Example:
# 1. The useer first produces LaTeX from a Jupyter notebook
#      jupyter nbconvert --to latex Notebook_5-EECS.ipynb
# 2. Customize the resulting Notebook_5-EECS.tex file
#      customize_tex_from_nbconvert.py --tex Notebook_5-EECS.tex
#
# 2022-09-22 G. Q. Maguire Jr.
#
import re
import sys
# set the stdout to use UTF8 encoding
#sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

import json
import optparse
import os			# to make OS calls, here to get time zone info


def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )


    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose

    if Verbose_Flag:
        print(options)
        print(remainder)

    if len(remainder) > 1:
        filename=remainder[0]
    if len(remainder) > 2:
        customization_filename=remainder[1]
    else:
        customization_filename='customization.tex'

    if Verbose_Flag:
        print("filename={}".format(filename))
        print("customization_filename={}".format(customization_filename))


    with open(customization_filename, 'r') as in_file:
        print(f"Opening customization file {customization_filename}")
        replacement_beginning=in_file.read()

    with open(filename, 'r') as in_file:
        print(f"Opening file {filename}")
        contents=in_file.read()
        # change option to use A4 paper
        contents=contents.replace("\documentclass[11pt]{article}", "\documentclass[11pt,a4paper]{article}")
        begin_str="\\begin{document}"
        begin_offset=contents.find(begin_str)
        makefile_str="\\maketitle"
        makefile_offset=contents.find(makefile_str)
        if begin_offset > 0:
            prefix_str=contents[:begin_offset]
        if makefile_offset > begin_offset+len(begin_str):
            postfix_str=contents[makefile_offset+len(makefile_str):]
        print("begin_offset={0}, makefile_offset={1}".format(begin_offset, makefile_offset))

        new_contents=prefix_str+replacement_beginning+postfix_str


    output_filename=filename[:-4]+'-customized.tex'
    print(f"writing out customized file: {output_filename}")
    with open(output_filename, 'w') as out_file:
        out_file.write(new_contents)
    
    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

