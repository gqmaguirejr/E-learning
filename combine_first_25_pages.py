#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./combine_first_25_pages input_directory output_file_name
#
# Combine the first 25 pages of the PDF files in the input directory into a single PDF file
#
# Output:
#   outputs a single file with all of the extracted pages
#
#
# G. Q. Maguire Jr.
#
#
# 2024-11-07
#

import pprint
import optparse
import sys
import os

import faulthandler

from PyPDF2 import PdfReader, PdfWriter

def combine_first_25_pages(input_dir, output_filename):
    """Combines the first 25 pages of all PDFs in a directory into a single PDF.

    Args:
      input_dir: The directory containing the PDF files.
      output_filename: The filename for the combined PDF.
    """
    global Verbose_Flag
    
    writer = PdfWriter()
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(input_dir, filename)
            if Verbose_Flag:
                print(f"Working on {filename}")
            try:
                reader = PdfReader(filepath)
                num_pages = len(reader.pages)
                for i in range(min(num_pages, 25)):
                    writer.add_page(reader.pages[i])
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                continue
            
    with open(output_filename, "wb") as output_file:
        writer.write(output_file)

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

    if (len(remainder) < 2):
        print("Insuffient arguments - input_directory output_file.pdf")
        sys.exit()
    else:
        input_directory=remainder[0]
        output_file_name=remainder[1]

        combine_first_25_pages(input_directory, output_file_name)


if __name__ == "__main__": main()

