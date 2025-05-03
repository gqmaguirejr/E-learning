#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./extract_embedded_files_from_PDF.py input_directory {output_directory]
#
# For each PDF file in the input directory, extract the embedded files
#
# Output:
#   If output_directory is not given, it creates an output_directory in the input_directory
#   otherwise it creates the output_directory if it does not already exist
#
#   In both cases a target directory is created in the output directory based on the basename of the input file with ".pdf" removed and extended with "_embeded_files"
#
#   The program outputs each of the embedded files into the target directory
#
#
# G. Q. Maguire Jr.
#
#
# 2025-05-03
#

import pprint
import optparse
import sys
import os

import faulthandler

import pymupdf # import PyMuPDF


def get_embedded_pdfs(input_pdf_path, output_path): 
    global Verbose_Flag
    # input_path = "/".join(input_pdf_path.split('/')[:-1])
    print(f"{input_pdf_path=}, {output_path=}")

    doc = pymupdf.open(input_pdf_path)
    if Verbose_Flag:
        print(f"{doc=}")
        print(f"{len(doc)=}")

        #print(f"{doc.embfile_count()=}")
        #print(f"{doc.embfile_names()=}")
        
    annots = doc.has_annots()
    if not annots:              # if not annotations, then nothing to do
        return

    # create target directory if necessary
    if not output_path: 
        # create in the same directory as the input file
        target_directory= os.path.split(input_pdf_path)[0] + os.sep + os.path.basename(input_pdf_path)[:-4] + "_embeded_files/"
        print(f"path 1: {target_directory=}")
    else:
        target_directory = os.path.join(output_path, os.path.basename(input_pdf_path)[:-4] + "_embeded_files/")
        print(f"path 2: {target_directory=}")

    if Verbose_Flag:
        print(f"{target_directory=}")
    if os.path.exists(target_directory):
        if Verbose_Flag:
            print('target directory exists')
    else:
        try:
            os.mkdir(target_directory)
        except OSError as error:
            print(error)   
        if Verbose_Flag:
            print(f'created target directory: {target_directory}')

    # attached files (as annotations) are accessed via the page they are attached to
    for page in doc:
        for annot in page.annots(types=[pymupdf.PDF_ANNOT_FILE_ATTACHMENT]):
            if Verbose_Flag:
                print(f"{annot=}")
                print(f"{annot.file_info=}")
            attached_file_name=annot.file_info['filename']
            attached_file_size=annot.file_info['size']
            print(f"processing attached file: {attached_file_name} {attached_file_size} bytes")
            # compute the output file name
            out_file_name = os.path.join(target_directory, attached_file_name)
            # get file contents
            attached_file=annot.get_file()
            if False: # Verbose_Flag
                print(f"{attached_file=}")
            # save attached file
            with open(out_file_name, 'wb') as outfile: 
                outfile.write(attached_file)



def main():
    global Verbose_Flag

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
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))

    if (len(remainder) < 1):
        print("Insuffient arguments - input_directory")
        sys.exit()
    elif (len(remainder) == 1):
        input_directory=remainder[0]
        output_directory=None
    elif (len(remainder) == 2):
        input_directory=remainder[0]
        output_directory=remainder[1]
    else:
        print("Give arguments - input_directory [output_directory]")
        sys.exit()

    if output_directory and not os.path.exists(output_directory):
        try:
            os.mkdir(output_directory)
        except OSError as error:
            print(error)   
        if Verbose_Flag:
            print(f'created output directory: {output_directory}')


    for filename in os.listdir(input_directory):
        if filename.endswith(".pdf"):
            filepath = os.path.join(input_directory, filename)

            if Verbose_Flag:
                print(f"Working on {filename}")
            try:
                get_embedded_pdfs(filepath, output_directory)

            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                continue

if __name__ == "__main__": main()

