#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./combine_first_25_pages_v2.py input_directory output_file_name
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

import pymupdf # import PyMuPDF

pdf_files_to_ignore=['1513609-FULLTEXT03.pdf',
                     '1801116-FULLTEXT05.pdf',
                     '1456914-FULLTEXT02.pdf',
                     '1757765-FULLTEXT01.pdf',
                     '1431593-FULLTEXT01.pdf',
                     '1609615-FULLTEXT01.pdf',
                     '1656942-FULLTEXT01.pdf',
                     '1385693-FULLTEXT01.pdf',
                     '1660690-SUMMARY01.pdf',
                     '1498726-FULLTEXT02.pdf',
                     '1431484-FULLTEXT01.pdf', # Table of Contents starts on page i=11, but no text can be extracted (it is just images) - made with Adope InDesign
                     '1479861-FULLTEXT01.pdf', # TOC is image - made with <xmp:CreatorTool>Xerox DigiPath PSGen 11.0.19.0</xmp:CreatorTool>
                     '1586078-FULLTEXT01.pdf', # no text course be extracted
                     '1860317-FULLTEXT01.pdf', # an Art, Technology, and Design thesis - quite a unique layout
                     '1754147-FULLTEXT01.pdf', # TOC is strange unicode - made with <xmp:CreatorTool>Adobe Illustrator CS6 (Macintosh)</xmp:CreatorTool>       
              
]

larger_offset_to_contents={
    '1713829-FULLTEXT01.pdf': 32, # table of contents starts on page 30
    '1713829-FULLTEXT01.pdf': 33,
    '1612687-FULLTEXT01.pdf': 32, # TOC start on i=28
    '1501686-FULLTEXT01.pdf': 34,
    

}


def combine_first_25_pages(input_dir, output_filename):
    """Combines the first 25 pages of all PDFs in a directory into a single PDF.

    Args:
      input_dir: The directory containing the PDF files.
      output_filename: The filename for the combined PDF.
    """
    global Verbose_Flag
    global Filter_flag
    global Anonymous_flag

    # create new empty document
    output_document = pymupdf.open(None)

    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(input_dir, filename)

            # skip files with know problems
            if filename in pdf_files_to_ignore:
                continue

            if filename in larger_offset_to_contents:
                max_pages_to_check=larger_offset_to_contents[filename]
            else:
                max_pages_to_check=25

            if Verbose_Flag:
                print(f"Working on {filename}")
            try:
                doc = pymupdf.open(filepath)
                num_pages = len(doc)
                references_found=False
                contents_found=False
                skip_last_page=False
                for i in range(min(num_pages, max_pages_to_check)):
                    # get page
                    page=doc[i]
                    # always output the cover page (or first page)
                    if i == 0 and not Anonymous_flag:
                        output_document.insert_pdf(doc, from_page=i, to_page=i)
                        continue

                    # extract text

                    txt=page.get_text()
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
                        print(f"{contents_found=} -- found TOC")

                    if i > 1 and ("Innehållsförteckning" in txt or "INNEHÅLLSFÖRTECKNING" in txt):
                        contents_found=True
                        print(f"{contents_found=} -- found TOC (Swedish)")

                    if (filename.find('1430432') >= 0  or filename.find('1501686')  >= 0 or filename.find('1501686')  >= 0 or filename.find('1813632')  >= 0 or filename.find(' 1530592')  >= 0) and i > 1 and "Table of content" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")

                    if (filename.find('1598473') >= 0 or filename.find('1598473')  >= 0 or filename.find(' 1611997')  >= 0) and i > 1 and "Table of c ontents" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")

                    if filename.find('1427220') >= 0 and i == 10 and "Content" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")
                        
                    if filename.find('1704847') >= 0 and i == 2 and "Content" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")
                        
                    if filename.find('1626735') >= 0 and i == 7 and "Content" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")
                        
                    if filename.find('1656258') >= 0 and i == 13 and "Content" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")
                        
                    if filename.find('1733649') >= 0 and i == 11 and "Content" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")
                        
                    if filename.find('1563869') >= 0 and i == 13 and "CONTENT" in txt:
                        contents_found=True
                        print(f"{contents_found=} -- special")
                        

                    if filename.find('1656355') >= 0 and i == 11 and txt.startswith("C O N T E N T S"):
                        contents_found=True
                        print(f"{contents_found=} -- special")

                    if filename.find('1656355') >= 0 and i == 13 and txt.startswith("C O N T E N T S"):
                        contents_found=True
                        print(f"{contents_found=} -- special")


                    # in 1754147-FULLTEXT01.pdf the Contents page is just hex codes - not recognizable as normal character, but starts with "􀀋􀀞􀀝􀀢􀀕􀀝􀀢􀀡􀀁"
                    if filename.find('1754147') >= 0 and i == 14:
                        contents_found=True
                        print(f"{contents_found=} -- special")
                        
                    if (filename.find('1389270') >= 0 or filename.find('1557578') >= 0) and i > 1 and (txt.startswith("Index") or txt.startswith("Index") or "Index" in txt or "Index" in txt):
                        contents_found=True
                        print(f"{contents_found=} - found Index")

                    # special processing for a thesis that uses the singular rather than the plural
                    if (filename.find('1648564') >= 0 or filename.find('1528058') >= 0) and i > 1 and ("Reference" in txt or "REFERENCE" in txt):
                        references_found=True
                        print(f"{references_found=} - found reference")

                    # Reference literature
                    if (filename.find('1733649') >= 0 or filename.find('1464302') >= 0) and i == 13 and "Reference":
                        references_found=True
                        print(f"{references_found=} - found reference")

                    # 1650507-FULLTEXT03.pdf uses REFERENCE LIST
                    if i > 1 and ("References" in txt or "REFERENCES" in txt or "REFERENCE LIST" in txt):
                        references_found=True
                        print(f"{references_found=} . References")

                    if i > 2 and ("Bibliography" in txt or "BIBLIOGRAPHY" in txt):
                        references_found=True
                        print(f"{references_found=} -- found Bibliography")

                    if i > 2 and ("Tryckta källor" in txt or "Elektroniska källor" in txt or "Referenser" in txt):
                        references_found=True
                        print(f"{references_found=} -- found Tryckta/Elektroniska källor")

                    # If we reach "Chapter 1" without encountering the references, then assue that we should stop copying
                    if i > 0 and (txt.startswith("Chapter 1") or txt.startswith("CHAPTER 1")):
                        references_found=True
                        print(f"{references_found=} -- found Chapter 1")
                        skip_last_page=True

                    # special case - the table of contents refers to "Sources" and following the TOC is "CHAPTER 1"
                    if filename.find('1400295') >= 0 and i == 14:
                        references_found=True
                        print(f"{references_found=} ** special")

                    # special case - 1654893
                    if filename.find('1654893') >= 0 and i == 13 and "1 \n Chapter 1" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True
                        
                    # special case
                    if filename.find('1735246') >= 0 and i == 17 and "1\nChap\nter 1" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True
                        
                    # special case
                    if filename.find('1501920') >= 0 and i == 17 and "1 Introduction" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True

                    # special case - TOC has "REFEREN CES"
                    if filename.find('1643849') >= 0 and i == 13 and "INTRODUCTION" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True

                    # special case
                    if filename.find('1646381') >= 0 and i == 15 and "1 Introduction" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True
                        
                    # special case as the string appears as "Reference s"
                    if filename.find('1756272') >= 0 and i > 0 and "This first chapter" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True
                        
                    # special case as the string appears as "Reference s"
                    if filename.find('1703858') >= 0 and i > 0 and "I give a general overview of drug delivery to the lung" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True

                    if filename.find('1501689') >= 0 and i == 11 and "Under  mitten av 1990 -talet arbetade jag som skiftgående me kanisk reparatör" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")
                        skip_last_page=True

                    # special case as the string appears as "Referenc es"
                    if filename.find('1530592') >= 0 and i == 12 and "Referenc es" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")

                    # special case as the string appears as "Refe r\nences"
                    if filename.find('1596193') >= 0 and i == 13 and "Refe r\nences" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")

                    # special case as the string appears as "REFERENCE S"
                    if filename.find('1528058') >= 0 and i == 9 and "REFERENCE S" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")

                    # special case
                    if filename.find('1751042') >= 0 and i == 10 and "Refe r\nences" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")

                    # special case
                    if filename.find('1660342') >= 0 and i == 12 and "R\neferences" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")


                    # special case
                    if filename.find('1704847') >= 0 and i == 4 and "Preface" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")


                    # The TOC shows "BIBLIOGRAPHY" but the text is actually "bibliography"
                    if filename.find('1557397') >= 0 and i == 7 and "bibliography" in txt:
                        references_found=True
                        print(f"{references_found=} ** special")


                    # special processing - a TOC has been seen .- now we see a LIST OFIGURES, ...
                    if contents_found and "LIST OF" in txt:
                        references_found=True
                        print(f"{references_found=} - found LIST OF")
                        skip_last_page=True

                    if contents_found:
                        if len(txt) > 0: # no need to write empty pages, i.e., those without (extractable) text
                            if not skip_last_page:
                                output_document.insert_pdf(doc, from_page=i, to_page=i)

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
            
    output_document.save(output_filename)


def main():
    global Verbose_Flag
    global Filter_flag
    global Anonymous_flag

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

    parser.add_option('-a', '--anonymous',
                      dest="anonymous",
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
    Anonymous_flag=options.anonymous
    if (len(remainder) < 2):
        print("Insuffient arguments - input_directory output_file.pdf")
        sys.exit()
    else:
        input_directory=remainder[0]
        output_file_name=remainder[1]

        combine_first_25_pages(input_directory, output_file_name)


if __name__ == "__main__": main()

