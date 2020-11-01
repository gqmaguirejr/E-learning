#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ./get_user_by_orcid.py orcid
#
# Output: user information
#
#
# "-t" or "--testing" to enable small tests to be done
# 
#
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./setup-degree-project-course.py "0000-0002-6066-746X"
#
# Example:
#
#   ./get_user_by_orcid.py --config config-test.json "0000-0002-6066-746X"
#
# ./get_user_by_orcid.py "0000-0002-6066-746X"
# user={'kthId': 'u1d13i2c', 'username': 'maguire', 'emailAddress': 'maguire@kth.se', 'firstName': 'Gerald Quentin', 'lastName': 'Maguire Jr'}
#
# or
# ./get_user_by_orcid.py 0000-0002-6066-746X
#
# G. Q. Maguire Jr.
#
#
# 2020.11.01
#

import requests, time
import pprint
import optparse
import sys
import json

# Use Python Pandas to create XLSX files
import pandas as pd

global host	# the base URL
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# 
def initialize(options):
       global host, header, payload

       # styled based upon https://martin-thoma.com/configuration-files-in-python/
       if options.config_filename:
              config_file=options.config_filename
       else:
              config_file='config.json'

       try:
              with open(config_file) as json_data_file:
                     configuration = json.load(json_data_file)
                     key=configuration["KTH_API"]["key"]
                     host=configuration["KTH_API"]["host"]
                     header = {'api_key': key, 'Content-Type': 'application/json', 'Accept': 'application/json' }
                     payload = {}
       except:
              print("Unable to open configuration file named {}".format(config_file))
              print("Please create a suitable configuration file, the default name is config.json")
              sys.exit()


def get_user_by_orcid(orcid):
       # Use the KTH API to get the user information give an orcid
       #"#{$kth_api_host}/profile/v1/kthId/#{kthid}"

       url = "{0}/profile/v1/orcid/{1}".format(host, orcid)
       if Verbose_Flag:
              print("url: {}".format(url))

       r = requests.get(url, headers = header)
       if Verbose_Flag:
              print("result of getting profile: {}".format(r.text))

       if r.status_code == requests.codes.ok:
              page_response=r.json()
              return page_response
       return []


def main():
    global Verbose_Flag

    default_picture_size=128

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )
    parser.add_option("--config", dest="config_filename",
                      help="read configuration from FILE", metavar="FILE")

    parser.add_option('-t', '--testing',
                      dest="testing",
                      default=False,
                      action="store_true",
                      help="execute test code"
    )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))
        print("Configuration file : {}".format(options.config_filename))

    initialize(options)

    if (len(remainder) < 1):
        print("Insuffient arguments - must provide orcid")
        sys.exit()
    else:
        orcid=remainder[0] # note that cycle_number is a string with the value '1' or '2'
    if options.testing:
        print("testing for orcid={}".format(orcid))

    user=get_user_by_orcid(orcid)
    print("user={}".format(user))

if __name__ == "__main__": main()

