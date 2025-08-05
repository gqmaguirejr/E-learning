#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./request-ISBN-with-JSON.py [--json fordiva.json]
#
# Using data from the fordiva.json file, request an ISBN
# from the web service
#
# Output:
#   outputs image files and data about the images
#
# Examples:
#     ./request-ISBN-with-JSON.py --testing --json /tmp/fordiva.json 
#     ./request-ISBN-with-JSON.py --json /tmp/fordiva.json
#
# expected response document is of the form:
# <!DOCTYPE html PUBLIC "-//w3c//DTD XHTMLm 1.0 Transitional//EN" 
# "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

# <! Författare: Cecilia Wiklander>
# <! Syfte: ISBN-hantering>
# <! Ändringar: >

# <head>

#     <meta charset="utf-8">

#     <title>ISBN REQUEST</title>
	
#     <link href="Site_utan.css" rel="stylesheet"> 
    	
# </head>

# <body>

# Your request for ISBN is registrered: 978-91-8106-369-1 Message has been sent.
		
# <br /><br /><br />

#     <input type="button" value="Back" onClick="history.go(-1);">
								
# 	</body>
# </html>
 

import re
import sys

import json
import optparse
import os			# to make OS calls, here to get time zone info
#import time
import pprint
import requests
import logging


# The URL of the web service that processes the form
#url = 'https://httpbin.org/post'  # httpbin.org is a great service for testing requests
#url = 'https://www.kth.se/en/biblioteket/publicera-analysera/vagledning-for-publicering/bestall-isbn-1.854778'
url = 'https://apps.lib.kth.se/PI/ISBN/spara_eng.php'

schools=['ABE', 'CBH', 'EECS', 'ITM', 'SCI']

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

def schools_acronym(s1):
    for s in schools_info:
        if s1 == schools_info[s]['swe'] or s1 == schools_info[s]['eng']:
            return s
    return None


# org is of the form "organisation":
# {"L1": "School of Electrical Engineering and Computer Science", "L2": "Computer Science"}
# {"L1": "School of Electrical Engineering and Computer Science (EECS)", "L2": "Computer Science"}
# {"L1": "School of Electrical Engineering and Computer Science (EECS)", "L2": "Computer Science (CS)"}
def orgization_to_full_organization_and_acronyms(org):
    org_l1=None
    org_l1_acronym=None
    if org:
        # for all KTH associated people KTH is the L1 organization
        if org.get('L1'):
            org_l1=org.get('L1').strip()
            #
            # Look for the school's acronym in parentheses in the L1
            acronym_offset=org_l1.find('(')
            if acronym_offset >= 0:
                # if the school's name is in parentheses
                end_acronym_offset=org_l1[acronym_offset+1:].find(')')
                if end_acronym_offset >= 0:
                    org_l1_acronym=org_l1[acronym_offset+1:acronym_offset+1+end_acronym_offset]
                    # check for valid acronym
                    if org_l1_acronym in schools_info:
                        org_l1=schools_info[org_l1_acronym]['eng']
                        org_l1="{0} ({1})".format(org_l1, org_l1_acronym)
                        print("found acronym in L1 org_l1={}".format(org_l1))
                    else:
                        print("Error in author's L1 organization acronym for author: {0}, {1}: {2}".format(last_name, first_name, org_l1_acronym))

            else:
                # if no, then look up the name (in either Enlish or Swedish) 
                org_l1_acronym=schools_acronym(org_l1)
                print(f"org_l1={org_l1}, org_l1_acronym={org_l1_acronym}")
                if org_l1_acronym:
                    org_l1=f"{org_l1} ({org_l1_acronym})"
                    print(f"did not find acronym in L1, but looked up school name org_l1={org_l1}")
                else:
                    print(f"Error in author's L1 organization for author in {org_l1}")
    return org_l1_acronym



def main(argv):
    global Verbose_Flag
    global testing
    global course_id

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )

    parser.add_option('-t', '--testing',
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    parser.add_option('-w', '--writing',
                      default=False,
                      action="store_true",
                      help="execute write operation"
                      )

    parser.add_option('-j', '--json',
                      type=str,
                      default="fordiva.json",
                      help="JSON file for extracted data"
                      )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))


    d=None                      # where the JSON data will be put
    json_filename=options.json
    if json_filename:
        try:
            with open(json_filename, 'r', encoding='utf-8') as json_FH:
                json_string=json_FH.read()
                d=json.loads(json_string)
        except FileNotFoundError:
            print("File not found: {json_filename}".format(json_filename))
            return

        if Verbose_Flag:
            print("read JSON: {}".format(d))
    else:
        print("Unknown source for the JSON: {}".format(json_filename))
        return

    valid_thesis_series =["TRITA-ABE-DLT",
                          "TRITA-CBH-FOU",
                          "TRITA-EECS-AVL",
                          "TRITA-ITM-AVL",
                          "TRITA-SCI-FOU"]


    # check the data before submitting
    title=d.get('Title', None)
    if not title:
        print("You need to provide title!")
        return
    thesis_main_title=title.get('Main title', None)
    if len(thesis_main_title) < 10:
        print("Title is too short")
        return

    author=d.get('Author1', None)
    if not author:
        print("Must have author information")

    # get an check kthid
    kthid=author.get('Local User Id')
    if not kthid or len(kthid) != 8 or kthid[0] != 'u' or kthid[1] != '1':
        print("KTH id begins with a u. You will find it on your profile page.")
        return

    last_name=author.get('Last name', None)
    if not last_name or len(last_name) < 2:
        print("You need to fill in author's last name!");
        return

    first_name=author.get('First name', None)        
    if not first_name or len(first_name) < 2:
        print("You need to fill in author's first name!")
        return

    email=author.get('E-mail', None)
    if not email or email.count('@') != 1 or not email.endswith( "kth.se"):
        print("The e-mail address must be a KTH address!");
        return

    a_org=author.get('organisation')
    if not a_org:
        print(f"Error processing author organization: {a_org}")
        return
    a_org_l1_acronym=orgization_to_full_organization_and_acronyms(a_org)
    if a_org_l1_acronym not in schools:
        print("Most provide an organization that maps to one of the schools")
        return

    series_info=d.get('Series', None)
    if not series_info:
        print("Must provide series information")
        return
    
    title_of_series=series_info.get('Title of series', None)
    if title_of_series:
        if title_of_series.find('--') > 0:
            title_of_series=title_of_series.replace('--', '-')
        if title_of_series.find(' - ') > 0:
            title_of_series=title_of_series.replace(' - ', '-')
        if Verbose_Flag:
            print(f"{title_of_series=}")
        if title_of_series not in valid_thesis_series:
            print(f"Invallid series: {title_of_series}")
            return

    number_in_series=series_info.get('No. in series', None)
    if not number_in_series:
        print("Number in series not specified")
        return
    if number_in_series.find(':') != 4:
        print("Number in series format is not valid")
        return

    year, issue = number_in_series.split(':')
    if int(issue) < 1:
        print("Invalid issue number")
        return
    
    # The data you want to send, as a dictionary
    # The keys should match the 'name' attributes of the form's input fields
    ISBNForm_form_data = {
        'Typ': 'Doktorsavhandling',
        'Titel': thesis_main_title,
        'KTHid': kthid,
        'Enamn': last_name,
        'Fnamn': first_name,
        'Epost': email,
        'TRITA': title_of_series,
        'TRITA_nr': number_in_series,
        'soek': 'Send'
    }


    # if tseing, do not submit the form
    if options.testing:
        print(f"{ISBNForm_form_data=}")
        return

    # --- Enable Debug Logging for Requests ---
    # This is the key part. It tells Python to show detailed logs from the requests library.
    # try:
    #     import http.client as http_client
    # except ImportError:
    #     # Python 2
    #     import httplib as http_client
    # http_client.HTTPConnection.debuglevel = 1

    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("requests.packages.urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True
    # -----------------------------------------

    # submit form
    print(f"{ISBNForm_form_data=}")
    try:
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml',
                   'Accept-Encoding': 'gzip, deflate, br, zstd',
                   'Accept-Language': 'en-US,en;q=0.9',
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                   'Upgrade-Insecure-Requests': '1',
                   } 
        # Send the POST request with the form data
        response = requests.post(url, data=ISBNForm_form_data, headers=headers,  timeout=15)
        print(f"{response.status_code}")

        # Check if the request was successful (HTTP status code 200)
        response.raise_for_status()
            
        # Print the server's response
        print("POST request successful!")
        if Verbose_Flag:
            print(f"Response: {response.text}")

        msg=response.text
        # need to parse the line of the response that lloks like:
        # Your request for ISBN is registrered: 978-91-8106-369-1 Message has been sent.
        target_string='Your request for ISBN is registrered: '
        end_target_string=' Message has been sent.'
        start_offset=msg.find(target_string)
        end_offset=msg.find(end_target_string)
        if start_offset < 0 or end_offset < 0:
            print("Expected response string was not found")
            return

        isbn_str=msg[start_offset+len(target_string):end_offset]
        print(f"{isbn_str=}")
        d['ISBN']=isbn_str.strip()
        if Verbose_Flag:
            print("new JSON: {d}")

        output_json_filename=json_filename[:-5]+"-with-ISBN.json"
        try:
            with open(output_json_filename, 'w', encoding='utf-8') as json_FH:
                json_string=json.dumps(d, indent=2)
                json_FH.write(json_string)

            print(f"wrote new JSN file to {output_json_filename}")

        except FileNotFoundError:
            print("Could not write file: {output_json_filename}")
            return


    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


    print("Finished")

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
