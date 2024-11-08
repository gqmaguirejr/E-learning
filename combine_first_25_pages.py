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

pdf_files_to_ignore=['1513609-FULLTEXT03.pdf',
                     '1801116-FULLTEXT05.pdf',
                     '1456914-FULLTEXT02.pdf',
                     '1757765-FULLTEXT01.pdf',
                     '1431593-FULLTEXT01.pdf',
                     '1609615-FULLTEXT01.pdf',
                     '1656942-FULLTEXT01.pdf',
                     '1385693-FULLTEXT01.pdf',
                     '1660690-SUMMARY01.pdf',
                     '1498726-FULLTEXT02.pdf'
]

larger_offset_to_contents=[
    '1713829-FULLTEXT01.pdf', # table of contents starts on page 30

]


def combine_first_25_pages(input_dir, output_filename):
    """Combines the first 25 pages of all PDFs in a directory into a single PDF.

    Args:
      input_dir: The directory containing the PDF files.
      output_filename: The filename for the combined PDF.
    """
    global Verbose_Flag
    global Filter_flag
    
    writer = PdfWriter()
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(input_dir, filename)

            # skip files with know problems
            if filename in pdf_files_to_ignore:
                continue

            if filename in larger_offset_to_contents:
                max_pages_to_check=32
            else:
                max_pages_to_check=25

            if Verbose_Flag:
                print(f"Working on {filename}")
            try:
                reader = PdfReader(filepath)
                num_pages = len(reader.pages)
                references_found=False
                contents_found=False
                for i in range(min(num_pages, max_pages_to_check)):
                    # get page
                    page=reader.pages[i]
                    # always output the cover page (or first page)
                    if i == 0:
                        writer.add_page(reader.pages[i])
                        continue

                    # extract text
                    txt=page.extract_text()
                    # skip the Printed by pages.
                    if i > 0 and "Printed by" in txt:
                        continue
                    if i > 0 and "Universitetsservice US-AB" in txt:
                        continue
                    if i > 0 and "public defense" in txt:
                        continue
                    if i > 0 and "public defence" in txt:
                        continue
                    # if i > 1 and ("Abstract" in txt or "ABSTRACT" in txt):
                    #     continue
                    # if i > 1 and ("Sammanfattning" in txt or "SAMMANFATTNING" in txt):
                    #     continue
                    if i > 1 and (txt.startswith("Contents") or txt.startswith("CONTENTS") or "Contents" in txt or "CONTENTS" in txt):
                        contents_found=True
                        print(f"{contents_found=} - found Contents")

                    if i > 1 and ("Table of contents" in txt or "Table of Contents" in txt):
                        contents_found=True
                        print(f"{contents_found=} -- found TOS")

                    if (filename.find('1430432') or filename.find('1501686')) and i > 1 and "Table of content" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")

                    if filename.find('1598473') and i > 1 and "Table of c ontents" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")

                        

                    if filename.find('1389270') and i > 1 and (txt.startswith("Index") or txt.startswith("Index") or "Index" in txt or "Index" in txt):
                        contents_found=True
                        print(f"{contents_found=} - found Index")

                    # special processing for a thesis that uses the singular rather than the plural
                    if filename.find('1648564') >= 0 and i > 1 and ("Reference" in txt or "REFERENCE" in txt):
                        references_found=True
                        print(f"{references_found=} - found reference")
                        
                    # 1650507-FULLTEXT03.pdf uses REFERENCE LIST
                    if i > 1 and ("References" in txt or "REFERENCES" in txt or "REFERENCE LIST" in txt):
                        references_found=True
                        print(f"{references_found=} . References")

                    if i > 2 and ("Bibliography" in txt or "BIBLIOGRAPHY" in txt):
                        references_found=True
                        print(f"{references_found=} -- found Bibliography")

                    # If we reach "Chapter 1" without encountering the references, then assue that we should stop copying
                    if i > 0 and txt.startswith("Chapter 1"):
                        references_found=True
                        print(f"{references_found=} -- found Chapter 1")

                    # special case as the string appears as "Reference s"
                    if filename.find('1756272') >= 0 and i > 0 and "This first chapter" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        
                    # special case as the string appears as "Reference s"
                    if filename.find('1703858') >= 0 and i > 0 and "I give a general overview of drug delivery to the lung" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")

                    if contents_found:
                        writer.add_page(reader.pages[i])
                    # stop copying pages when you have processed a page with "References" on it.
                    if references_found:
                        print(f"[stopping at page {i}; {contents_found=} ")
                        break

                    if i >= max_pages_to_check - 1:
                        print(f"[stopping at page {i}; {contents_found=}; {references_found=}")
                        break

            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                continue
            
    with open(output_filename, "wb") as output_file:
        writer.write(output_file)

def main():
    global Verbose_Flag
    global Filter_flag

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )

    parser.add_option('-f', '--filter',
                      dest="filter",
                      default=False,
                      action="store_true",
                      help="filter out some pages"
    )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))

    Filter_flag=options.filter

    if (len(remainder) < 2):
        print("Insuffient arguments - input_directory output_file.pdf")
        sys.exit()
    else:
        input_directory=remainder[0]
        output_file_name=remainder[1]

        combine_first_25_pages(input_directory, output_file_name)


if __name__ == "__main__": main()

