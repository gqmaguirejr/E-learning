#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./backcover.py --school xxx [--year yyyy] --number 00 --pdf output.pdf
#
# Purpose: create KTH back cover with TRITA number
#
# Example:
#
# ./backcover.py --school EECS --year 2022 --number 00 --pdf output.pdf
#
# To get the correct fpdf package od:
# pip install fpdf
#
# 2021-07-15 G. Q. Maguire Jr.
#
import re
import sys

import json
import argparse
import os			# to make OS calls, here to get time zone info

from datetime import datetime
from fpdf import FPDF 

# \newcommand{\kthbackcover}{
# % Note that the values have only been adjusted for A4 paper!
# \newgeometry{top=65mm,bottom=30mm,left=74pt, right=35mm}


# \thispagestyle{empty}

# % Generate the back cover with the TRITA number and the fixed graphical elements
# \begin{textblock*}{5cm}(38.83pt, {\paperheight - 72pt}) % {block width} (coords) 
# \noindent{\fontsize{10}{12}\coverlfont 
#     \ifx\@thesisSeries\@empty %\relax
#         TRITA xxxx:yyy
#         \else
#         	\@thesisSeries-
#         	\ifx\@thesisSeriesNumber\@empty\relax
#             \else
#             \@thesisSeriesNumber
#              \fi
#     \fi\\
# }
# \end{textblock*}
# \begin{textblock*}{5cm}(38.83pt, {\paperheight - 44pt})
# \noindent{\fontsize{8}{9}\coverlfont
#     \textcolor{kth-blue}{www.kth.se}
# }
# \end{textblock*}
# \begin{textblock*}{510pt}(19pt, {\paperheight - 34pt})
# \begin{tikzpicture}
# \draw[kth-blue, line width=1.0 pt] (0pt,0pt) -- (510pt,0pt);
# \end{tikzpicture}
# \end{textblock*}
# \restoregeometry
# \null\newpage
# }
# \trita{TRITA-EECS-EX}{2022:00}

def main(argv):
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global testing

    argp = argparse.ArgumentParser(description="extract_pseudo_JSON-from_PDF.py: Extract the pseudo JSON from the end of the thesis PDF file")

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

    argp.add_argument('-s', '--school',
                      type=str,
                      default="EECS",
                      help="school acronym"
                      )

    argp.add_argument('-y', '--year',
                      type=str,
                      default="{}".format(datetime.today().year),
                      help="read PDF file"
                      )

    argp.add_argument('-n', '--number',
                      type=str,
                      help="number in series"
                      )


    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    filename=args["pdf"]
    if Verbose_Flag:
        print("filename={}".format(filename))

    year=args["year"]
    if Verbose_Flag:
        print("year={}".format(year))

    trita_num=args["number"]
    if Verbose_Flag:
        print("trita_num={}".format(trita_num))

    school=args["school"]
    if Verbose_Flag:
        print("school={}".format(school))

    # TRITA-EECS-EX}{2022:00
    schools=['ABE', 'EECS', 'ITM', 'CBH', 'SCI']
    if school in schools:
        trita_series=f"TRITA-{school}-EX"
    else:
        print(f"{school} not a valid school acronyms")
        return

    trita_string=f"{trita_series}-{year}:{trita_num}"
    print(f"trita_string={trita_string}")


    pdf = FPDF(orientation = 'P', unit = 'pt', format='A4')
    pdf.add_page()

    # insert the texts in pdf 
    paperheight=842

    pdf.set_font("Arial", size = 10) 
    pdf.set_text_color(0, 0, 0) # black
    pdf.text(38.83, paperheight - 64, trita_string) 

    pdf.set_font("Arial", size = 8) 
    pdf.set_text_color(25, 84, 166) # kth-blue
    pdf.text(38.83, paperheight - 38, "www.kth.se") 

    pdf.set_draw_color(25, 84, 166) # kth-blue
    pdf.set_line_width(1.0)
    pdf.line(36.03, paperheight - 34, 19+510, paperheight - 34)

    pdf.output(filename)

    return

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

