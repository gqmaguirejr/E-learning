#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./extract_content_from_PPTX_file.py -c course_id --file filename --dir target_directory
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
global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(options):
    global baseUrl, header, payload

    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    if options.get('config_filename'):
        config_file=options.get('config_filename')
    else:
        config_file='config.json'

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            access_token=configuration["canvas"]["access_token"]
            baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"
            
            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}
    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()


def list_modules(course_id):
    modules_found_thus_far=[]
    # Use the Canvas API to get the list of modules for the course
    #GET /api/v1/courses/:course_id/modules

    url = "{0}/courses/{1}/modules".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting modules: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            modules_found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of modules
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links.get('next', False):
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting modules for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    modules_found_thus_far.append(p_response)

    return modules_found_thus_far

def list_module_items(course_id, module_id):
    module_items_found_thus_far=[]
    # Use the Canvas API to get the list of modules for the course
    # GET /api/v1/courses/:course_id/modules/:module_id/items

    url = "{0}/courses/{1}/modules/{2}/items".format(baseUrl, course_id, module_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting module items: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            module_items_found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of modules
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links.get('next', False):
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting modules for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    module_items_found_thus_far.append(p_response)

    return module_items_found_thus_far


def create_module(course_id, module_name):
    global Verbose_Flag
    # Use the Canvas API to create a module
    #POST /api/v1/courses/:course_id/modules

    # Request Parameters:
    # module[name]	Required	string	The name of the module
    # module[unlock_at]		DateTime The date the module will unlock
    # module[position]		integer	The position of this module in the course (1-based)
    # module[require_sequential_progress]		boolean	Whether module items must be unlocked in order
    # module[prerequisite_module_ids][]		string	IDs of Modules that must be completed before this one is unlocked. Prerequisite modules must precede this module (i.e. have a lower position value), otherwise they will be ignored
    # module[publish_final_grade]		boolean	Whether to publish the student's final grade for the course upon completion of this module.

    url = "{0}/courses/{1}/modules".format(baseUrl,course_id)
    if Verbose_Flag:
       print("url: " + url)

    payload={'module[name]': module_name}

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of create module: {}".format(r.text))
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return True
    return False

def list_folders(course_id):
    folders_found_thus_far=[]
    # Use the Canvas API to get the list of folders for the course
    #GET /api/v1/courses/:course_id/folders

    url = "{0}/courses/{1}/folders".format(baseUrl, course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    if Verbose_Flag:
        print("result of getting folders: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            folders_found_thus_far.append(p_response)

            # the following is needed when the reponse has been paginated
            # i.e., when the response is split into pieces - each returning only some of the list of assignments
            # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
            while r.links.get('next', False):
                r = requests.get(r.links['next']['url'], headers=header)  
                if Verbose_Flag:
                    print("result of getting folders for a paginated response: {}".format(r.text))
                page_response = r.json()  
                for p_response in page_response:  
                    folders_found_thus_far.append(p_response)

    return folders_found_thus_far

def create_folder(course_id, name, parent_folder_id):
    global Verbose_Flag
    # Use the Canvas API to create a file
    #POST /api/v1/courses/:course_id/folders

    # Request Parameters:
    # name	Required	string	The name of the folder
    # parent_folder_id		string	The id of the folder to store the new folder in. An error will be returned if this does not correspond to an existing folder. If this and parent_folder_path are sent an error will be returned. If neither is given, a default folder will be used.
    # parent_folder_path		string	The path of the folder to store the new folder in. The path separator is the forward slash `/`, never a back slash. The parent folder will be created if it does not already exist. This parameter only applies to new folders in a context that has folders, such as a user, a course, or a group. If this and parent_folder_id are sent an error will be returned. If neither is given, a default folder will be used.
    # lock_at		DateTime	The datetime to lock the folder at
    # unlock_at		DateTime	The datetime to unlock the folder at
    # locked		boolean		Flag the folder as locked
    # hidden		boolean		Flag the folder as hidden
    # position		integer	 	Set an explicit sort position for the folder

    url = "{0}/courses/{1}/folders".format(baseUrl,course_id)
    if Verbose_Flag:
       print("url: " + url)

    payload={'name': name,
             'parent_folder_id': parent_folder_id}

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of create folder: {}".format(r.text))
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return True
    return False

def create_file(course_id, filename, parent_folder_id, content_type):
    global Verbose_Flag
    global pp

    with open(filename, 'rb') as file_handle:
        file_contents = file_handle.read()
    file_size=len(file_contents)
    if Verbose_Flag:
        print(f'{file_size=}')
    
    # Use the Canvas API to create a file
    # Step 1:
    #POST /api/v1/courses/:course_id/files

    # Request Parameters:
    # name The filename of the file. Any UTF-8 name is allowed. Path components such as `/` and `\` will be treated as part of the filename, not a path to a sub-folder.
    # size The size of the file, in bytes. This field is recommended, as it will let you find out if there's a quota issue before uploading the raw file.
    # content_type The content type of the file. If not given, it will be guessed based on the file extension.
    # parent_folder_id The id of the folder to store the file in. An error will be returned if this does not correspond to an existing folder. If this and parent_folder_path are sent an error will be returned. If neither is given, a default folder will be used.
    # parent_folder_path The path of the folder to store the file in. The path separator is the forward slash `/`, never a back slash. The folder will be created if it does not already exist. This parameter only applies to file uploads in a context that has folders, such as a user, a course, or a group. If this and parent_folder_id are sent an error will be returned. If neither is given, a default folder will be used.
    # folder [deprecated] Use parent_folder_path instead.
    # on_duplicate How to handle duplicate filenames. If `overwrite`, then this file upload will overwrite any other file in the folder with the same name. If `rename`, then this file will be renamed if another file in the folder exists with the given name. If no parameter is given, the default is `overwrite`. This doesn't apply to file uploads in a context that doesn't have folders.
    # success_include[] An array of additional information to include in the upload success response. See Files API for more information.

    url = "{0}/courses/{1}/files".format(baseUrl,course_id)
    if Verbose_Flag:
       print("url: " + url)

    payload={'name': filename,
             'size': file_size,
             'content_type': content_type,
             'parent_folder_id': parent_folder_id}

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of create file step #1: {}".format(r.text))
    if r.status_code == requests.codes.ok:
        page_response=r.json()

        # The response will look like
        # {
        #     "upload_url": "https://some-bucket.s3.amazonaws.com/",
        #     "upload_params": {
        #         "key": "/users/1234/files/profile_pic.jpg",
        #         <unspecified parameters; key above will not necesarily be present either>
        #     }
        # }

        # Step 2:
        # Use the upload_url to actually upload the file
        url = page_response['upload_url']

        if Verbose_Flag:
            print("url: " + url)

        payload=page_response['upload_params']

        # Note that the access token is _not_ sent with this request
        upload_header={}
        r = requests.post(url, headers = upload_header, data=payload, files={"file": open(filename, 'rb')})
        if Verbose_Flag:
            print("result of file create step #2: {}".format(r.text))
            print(f'{r.status_code=}')
        if 300 <= r.status_code and r.status_code < 400:
            page_response=r.json()

            # Step 3: Confirm the upload's success
            # If Step 2 is successful, the response will be either a 3XX redirect or 201 Created with a Location header set as normal.
            # In the case of a 3XX redirect, the application needs to perform a GET to this location in order to complete the upload, otherwise the new file may not be marked as available. (Note: While a POST would be truer to REST semantics, a GET is required for forwards compatibility with the 201 Created response described below.) This request is back against Canvas again, and needs to be authenticated using the normal API access token authentication.
            file_id=page_response['id']
            urL=page_response['location']
            print("file_id={0}, url={1}".format(file_id, url))

            if Verbose_Flag:
                print("url: " + url)

            payload={'Content-Length': 0}
            r = requests.post(url, headers = header, data=payload)
            if Verbose_Flag:
                print("result of create file step #3: {}".format(r.text))
            if r.status_code == requests.codes.ok:
                page_response=r.json()
                return True
        elif 200 <= r.status_code and r.status_code < 300:
            page_response=r.json()

            # In the case of a 201 Created, the upload has been complete and the Canvas JSON representation of the file can be retrieved with a GET from the provided Location.
            if Verbose_Flag:
                pp.pprint(page_response)
            file_id=page_response['id']
            file_url=page_response['url']
            if Verbose_Flag:
                print("file_id={0}, file_url={1}".format(file_id, file_url))

            r = requests.get(file_url, headers = header, data=payload)
            if Verbose_Flag:
                print("result of create file step #3: {}".format(r.text))
            if r.status_code == requests.codes.ok:
                return True
        else:
            return False
    return False



def create_page(course_id, title, body):
    # Create a new wiki page
    # POST /api/v1/courses/:course_id/pages 
    # Request Parameters:
    # Parameter		Type	Description
    # wiki_page[title]	Required	string	The title for the new page.
    # wiki_page[body]		string	The content for the new page.
    # wiki_page[editing_roles]		string	Which user roles are allowed to edit this page. Any combination of these roles is allowed (separated by commas).
    # “teachers”	Allows editing by teachers in the course.
    # “students”	Allows editing by students in the course.
    # “members”	For group wikis, allows editing by members of the group.
    # “public” Allows editing by any user. Allowed values: teachers, students, members, public
    # wiki_page[notify_of_update]		boolean	Whether participants should be notified when this page changes.
    # wiki_page[published]		boolean	Whether the page is published (true) or draft state (false).
    # wiki_page[front_page]		boolean	Set an unhidden page as the front page (if true)
    # wiki_page[publish_at]		DateTime	Schedule a future date/time to publish the page. This will have no effect unless the “Scheduled Page Publication” feature is enabled in the account. If a future date is supplied, the page will be unpublished and wiki_page will be ignored.

    global Verbose_Flag

    url = "{0}/courses/{1}/pages".format(baseUrl,course_id)
    if Verbose_Flag:
       print("url: " + url)

    payload={'wiki_page[title]': title,
             'wiki_page[body]': body,
             'wiki_page[published]': False,
             'wiki_page[editing_roles]': "teachers",
             'wiki_page[front_page]': False
             }

    r = requests.post(url, headers = header, data=payload)
    if Verbose_Flag:
        print("result of create page: {}".format(r.text))
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return None



nsmap ={
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

relationships_namp={None: 'http://schemas.openxmlformats.org/package/2006/relationships'}

known_hashes={
    # from GPU Tool Kit
    'e43fa5d98216bdfe2a19e819d0e2fd4c': {'known_file_name': 'gray_horizontal_parallelagram', 'type': 'png'},
    'c31da9d04513260c9b071e125760742e': {'known_file_name': 'gray_horizontal_parallelagram2', 'type': 'png'},
    '1b459c6db80e4b4664bd4073d17b6fd2': {'known_file_name': 'nvidia_logo_gray', 'type': 'png'},
    '8f6a5566e73115c6f79d1c9815881df8': {'known_file_name': 'Illinois_I_logo', 'type': 'png'},
    'df1038d40000d87428f55827e9f2395f': {'known_file_name': 'Illinois_logo', 'type': 'png'},
    'efda0b94249d0eb1277b0f0f1d2f3a78': {'known_file_name': 'burnished_steel_slide', 'type': 'jpg'},
    '9e982c2b9f79fd737a8710e1a6fdf530': {'known_file_name': 'green_horizontal_parallelagram', 'type': 'png'},
    'd251cf20807a37c01fdac05a1d4538d4': {'known_file_name': 'Nvidia_logo_white', 'type': 'png'},
    '03003cc581e2035a9269db6c1bb96708': {'known_file_name': 'orange_semi_parallelagram', 'type': 'png'},
    '06057826ced78bd7ff4569bc56f41845': {'known_file_name': 'Large_Illinois_I_logo', 'type': 'png'},
    '4dfe8e3657bdc730a5bf2007a7fd4e88': {'known_file_name': 'Illinois_logo_univ_name', 'type': 'png'},
    '2a291aa013fadaddda5c9eddc12c82d6': {'known_file_name': 'Large_Illinois_I_logo_gray', 'type': 'jpeg'},
    '6c238a7c740d7aa1b6550a60f1bccd86': {'known_file_name': 'speaker_with_output', 'type': 'jpeg'},
    '100a81a4371f03c063fdd30819b4318c': {'known_file_name': 'CC-BY-NC', 'type': 'png'},
    '25753f61bc746049c38d56d61167a8e9': {'known_file_name': 'NVIDIVA logo', 'type': 'png'},
    'b22c34132331a4a1079265cccf8911ce': {'known_file_name': 'NVIDIVA logo', 'type': 'svg'},
    'd494f2d16b97f830bfbce49e40a3874b': {'known_file_name': 'University of Deleware logo', 'type': 'png'},
    '5ad1fe8213c200ea0b2600e66ded73a4': {'known_file_name': 'University of Deleware logo', 'type': 'svg'},
    '58119b82a4e0bae79aa218e52bbcff8c': {'known_file_name': 'UD logo', 'type': 'png'},
    '56b41990ef454102491f02d6cdf58cf7': {'known_file_name': 'UD logo', 'type': 'svg'},
    # from Deeplearning Tool Kit
    '96a0e82c1157d6864e232072c127ca57': {'known_file_name': 'gray bar fading on both sides', 'type': 'png'},
    '1f52ef2b087c865ec0dd9460a9b573d7': {'known_file_name': 'gray bar fading on both sides (v2)', 'type': 'png'},
    '015c7d44b146211cc0af7a1804b43e1f': {'known_file_name': 'Nvidia logo white on black', 'type': 'png'},
    'e61594249fc1ab34975c6500826c4787': {'known_file_name': 'NYU logo white on black', 'type': 'png'},
    '6763d641823d7ab822f47c1f411d0dfe': {'known_file_name': 'burnished_steel_slide v2', 'type': 'png'},
    '97d8aa17c2170d98fb5d4c1f438fda4c': {'known_file_name': 'green parallelogram', 'type': 'png'},
    '22c08d11e1ae5223422d3e801414b65e': {'known_file_name': 'large Nvidia logo white on black', 'type': 'png'},
    'f5298a88113327144a0ef99a44dcf0ad': {'known_file_name': 'NYU purple semi-parallelagram', 'type': 'png'},
    'b1f7c94f87f29106e316052dad7cecb5': {'known_file_name': 'New York University logo white on black', 'type': 'png'},
    '22817c4694175e602fca75b177e9c32a': {'known_file_name': 'CC-BY-NC', 'type': 'png'},
    '1115c750cb2dacd21e39e817e01d5c93': {'known_file_name': 'Nvidia Deep Learning Institute logo', 'type': 'png'},
    '1ffa9b71a52a023af19c1fbe518e52ec': {'known_file_name': 'Nvidia Deep Learning Institute logo (small)', 'type': 'png'},

    # from Data science Tool Kit
    '13ce4d51b8728df1d8f626f288c813fe': {'known_file_name': 'Georgia Tech logo', 'type': 'png'}, 
    '2fe5bedc2b8adc74412ee49707b50dce': {'known_file_name': 'Deep Learniing Institue logo', 'type': 'png'}, 
    '4a0f69e2524423229026623149d60360': {'known_file_name': 'Prarie View A and M logo', 'type': 'png'}, 
    'cbb236dabbd66dcd5e7b754766a717ca': {'known_file_name': 'CC-BY-NC', 'type': 'png'},
    '4f5e464e5c675a8a8adc39af655a380a': {'known_file_name': 'Foster_Provost_and_Tom_Fawcett_book_cover', 'type': 'jpg'},
    '75f0282b9768bc35a55106d0ec2343b7': {'known_file_name': 'GTx logo', 'type': 'png'}, 
    'd83814607fc9ab2f1bb9af45c56ca23f': {'known_file_name': 'Prarie View A and M logo 2', 'type': 'png'},

    # from Edge AI and Robotics Tool Kit
    '62ca6a42339ac8e25babd989634577ee': {'known_file_name': 'University of Oxford logo', 'type': 'png'},
    '0920eefda5642b0a35aced57897395f9': {'known_file_name': 'UMBC logo', 'type': 'png'},
    '5e41322ffb0a2e1686a7033c7392ae07': {'known_file_name': 'Nvidia (long) logo', 'type': 'png'},
    'd5a6cd8d35dc573e209ddd9852cd223d': {'known_file_name': 'Nvidia (long) logo 2', 'type': 'png'},

    '5e8290dc23f960539d49deeee65ba05b': {'known_file_name': 'Edge_AI_and_Robotics_logo_1', 'type': 'png'},
    '478a898e3ba4a059993e29ed4dfcd2eb': {'known_file_name': 'Edge_AI_and_Robotics_logo_2', 'type': 'png'},
    'd413c59ee8b514f99c7d60954c64eb9d': {'known_file_name': 'Nvidia DLI Teaching KIt Robots logo', 'type': 'png'},
    
    #  from Creating Digital Human
    'ada7be695d20f2115b05fd2c5c97063e': {'known_file_name': 'Nvidia logo', 'type': 'png'},
    '86cb5eb7e74b393f725ee7c5e0c55023': {'known_file_name': 'Nvidia logo (small)', 'type': 'png'},
    '7645806756e1ab9fa92b7e62efa06b8a': {'known_file_name': 'Nvidia logo (small) v2', 'type': 'png'},
    '532f6db3457f8f104efea3dfd2bdfba6': {'known_file_name': 'Nvidia logo green and white without text', 'type': 'png'},
    'cc014f424ec605933e396cd7bc196842': {'known_file_name': 'Nvidia logo green and white without text v2', 'type': 'png'},
    '7a0b24cba92d1cebe9409694380dba0c': {'known_file_name': 'Nvidia logo green and white without text v3', 'type': 'png'},
    'e1398f370e337b05c5ced9fecffdb856': {'known_file_name': 'Nvidia logo with particle flow around it', 'type': 'png'},
    '3335d896f4deddd1ab8d9f3b2d020f42': {'known_file_name': 'Nvidia swirl with tiles', 'type': 'jpeg'},
    '1305df171099f5ef33444c412b05327a': {'known_file_name': 'Nvidia swirl with tiles partially grayed', 'type': 'png'},
    '2369588f28c589bec18a2f7a68493c2c': {'known_file_name': 'Nvidia swirl with tiles (zoomed into part of it)', 'type': 'jpeg'},
    '66e1085bf9cfb4f344fc94c5b55e312c': {'known_file_name': 'Nvidia swirl with tiles low to the plane', 'type': 'jpeg'},
    'ac84a145cad9448fabb15107d6f29858': {'known_file_name': 'Nvidia_DLI_Teaching_Kits_graphics_and_Omniverse', 'type': 'png'},
    '1cda1b7790116ffd102053597024a267': {'known_file_name': 'Nvidia_DLI_Enhance_Your_Curriculum', 'type': 'png'},
    'e2bc2f72e8e2ed709fe5482b5656b327': {'known_file_name': 'Nvidia_DLI_Teaching_Kits_graphics_and_Omniverse', 'type': 'jpg'},
    'cb26d3679db63c47d7d4847a696cc7eb': {'known_file_name': 'Introducing NVIDIA Sans. Our new font for every thing NVIDIA.', 'type': 'png'},
    '809298ff157f70057ffcba88533d62ac': {'known_file_name': 'speaker_icon', 'type': 'png'},    
    'b7c9d3fb2f2392696a47a108006e3749': {'known_file_name': 'USD log with shadow', 'type': 'png'},
    'f9eb14d64de63699f502a04865dcaa17': {'known_file_name': 'gray gear', 'type': 'png'},
    '0b0f5f3950fab07f73ee69fd85c5b09d': {'known_file_name': 'two gray gears', 'type': 'png'},
    '59b17409728df0cbd5dc1cd5af5ee6da': {'known_file_name': 'light bulb', 'type': 'png'},
    '99b90fbba8bbec89b6c0c08bb37820ae': {'known_file_name': 'multiple colored light bulbs', 'type': 'png'},
    '16e84b58642e1c04f8926a18945b85fd': {'known_file_name': 'two light bulb puzzle pieces stacked', 'type': 'png'},
    'd24ba5ed2f51d4dab67e672ede3d6633': {'known_file_name': 'two extension puzzle pieces stacked', 'type': 'png'},

    #  from Industrial Metaverse Omniverse Teaching Kit
    '72422d2485013e6dbd4fbde20a9b242f': {'known_file_name': 'Nvidia swirl with tiles', 'type': 'jpeg'},
    '2d94853ea01aa4ac7b7b9bc15a86da36': {'known_file_name': 'Nvidia swirl with tiles (partial zoomed)', 'type': 'jpeg'},
    '1d1e16899a3a0964105a8565332cbb7d': {'known_file_name': 'Nvidia swirl with tiles (partial zoomed) gray overlay', 'type': 'jpeg'},
    'b3b0efa59a299e02e1d201545c7301df': {'known_file_name': 'Nvidia swirl with tiles (close in zoom)', 'type': 'jpeg'},
    'e6622b8056a30a0a07e72adfdaafbf8d': {'known_file_name': 'Nvidia logo green and white without text', 'type': 'png'},
    '58ccc3a03a7676a56b257240479ec4f5': {'known_file_name': 'Nvidia logo green and white without text v2', 'type': 'png'},
    '0cf82dff433e25c8e48ef5b878851918': {'known_file_name': 'Nvidia logo glass - particle faling', 'type': 'png'},
    '8cc58375ccc4930ac7c46a9ec9b8e1c4': {'known_file_name': 'Nvidia logo glass - particle faling (left)', 'type': 'jpeg'},
    'dea146fc7ec5d42248dae3957d3fb38e': {'known_file_name': 'Nvidia logo glass - particle faling (left) v2', 'type': 'jpeg'},
    'a3babb41bbcb7cad3cf41fe7df43079e': {'known_file_name': 'Nvidia logo glass - particle faling (left) v3', 'type': 'jpeg'},
    'c6ee1153e13e275a9733898eb4363e5b': {'known_file_name': 'Green start triangle', 'type': 'png'},
    '6c238a7c740d7aa1b6550a60f1bccd86': {'known_file_name': 'DLI Graphics and Entertainment logo', 'type': 'png'},
    '8dfba98c9d9de083e0330761232dfdd7': {'known_file_name': 'DLI Graphics and Entertainment logo', 'type': 'png'},
}



# to be indexed by slide filename
relationships=dict()

# extract text "<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US"/><a:t>Tiled </a:t></a:r><a:r><a:rPr lang="en-US" dirty="0"/><a:t>Matrix Multiplication Kernel</a:t></a:r></a:p></p:txBody></p:sp><p:sp><p:nvSpPr><p:cNvPr id="3" name="Title 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="1121520" y="3601595"/><a:ext cx="5439300" cy="397032"/></a:xfrm></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="2200" dirty="0"/><a:t>Module 4.4 - Memory and Data Locality</a:t></a:r></a:p></p:txBody>

def clean_for_html(txt):
    if txt is None:
        return ''
    txt=txt.replace('&', '&amp,')
    txt=txt.replace('<', '&lt,')
    txt=txt.replace('>', '&gt,')
    txt=txt.replace('←', '&larr,')
    txt=txt.replace('→', '&rarr,')
    return txt

def extract_text(xml_content):
    global nsmap
    global Verbose_Flag

    root = etree.fromstring(xml_content)
    if Verbose_Flag:
        print(f'{root=}')
    sp_txt_list=[b for b in root.iterfind(".//p:sp", nsmap) ]

    accumulated_sph_type=[]
    accumulated_txt_list=[]
    accumulated_typeface_list=[]
    accumulated_levels_list=[]
    for sp in sp_txt_list:
        sph_txt_list=[b for b in sp.iterfind(".//p:ph", nsmap) ]
        if Verbose_Flag:
            print("sph_txt_list={}".format(sph_txt_list))

        sph_type=[b.get('type') for b in sph_txt_list]
        accumulated_sph_type.append(sph_type)

        txtBody_txt_list=[b for b in sp.iterfind(".//p:txBody", nsmap) ]

        txt_body=''
        for pb in txtBody_txt_list:
            pb_txt_list=[b for b in pb.iterfind(".//a:p", nsmap) ]
            type_face=[]
            new_typeface_list=''
            new_levels_list=''
            new_txt_list=''
            for p in pb_txt_list:
                typeface_list=[b.get('typeface') for b in p.iterfind(".//a:latin", nsmap) ]
                # for t in typeface_list:
                #     new_typeface_list=new_typeface_list+t+','
                levels_list=[b.get('lvl') for b in p.iterfind(".//a:pPr", nsmap) ]
                # for l in levels_list:
                #     new_levels_list=new_levels_list+f'{l}'+','

                txt_list=[b.text for b in p.iterfind(".//a:t", nsmap) ]
                # for t in txt_list:
                #     if len(new_txt_list) > 0:
                #         # new_txt_list=new_txt_list+' '+clean_for_html(t)
                #         new_txt_list=new_txt_list+clean_for_html(t)
                #     else:
                #         new_txt_list=clean_for_html(t)
                # if len(txt_body) == 0:
                #     txt_body=new_txt_list
                # else:
                #     txt_body=txt_body+'\n'+new_txt_list
                # new_txt_list=''

                accumulated_typeface_list.append(typeface_list)
                accumulated_levels_list.append(levels_list)
                accumulated_txt_list.append(txt_list)

    return {'types': accumulated_sph_type, 'text': accumulated_txt_list, 'typeface': accumulated_typeface_list, 'levels': accumulated_levels_list}

def clean_xml(txt):
    if not isinstance(txt, str):
        print("type is {}".format(type(txt)))
        print("expected a string in clean_txt() but got {}".format(txt))
        return txt.text

    return txt

def txt_list_to_string(txt_list):
    print("txt_list_to_string({}".format(txt_list))
    # take txt_list and put new lines between the parts of it
    ret_text=''
    for txt in txt_list:
        if isinstance(txt, list):
            for t1 in txt:
                ret_text=ret_text+'\n'+"{}".format(clean_for_html(t1))
        else:
            ret_text=ret_text+'\n'+"{}".format(clean_for_html(txt))

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

# <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
# <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
# <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout2.xml"/>
# <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio" Target="../media/media10.m4a"/>
# <Relationship Id="rId1" Type="http://schemas.microsoft.com/office/2007/relationships/media" Target="../media/media10.m4a"/>
# <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image13.png"/>
# <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image14.jpeg"/>
# </Relationships>

def extract_relationships(slide_name, s):
    global relationships
    global relationships_namp
    global Verbose_Flag

    if Verbose_Flag:
        print("extract_relationships({0}, {1})".format(slide_name, s))
    relationships_for_slide=dict()

    root = etree.fromstring(s)
    if Verbose_Flag:
        print(f'{root=}')
    lr=[b for b in root.iterfind(".//Relationship", relationships_namp) ]
    if Verbose_Flag:
        print(f'{lr=}')
    for r in lr:
        for name, value in sorted(r.items()):
            if Verbose_Flag:
                print("name: {0}, value={1}".format(name, value))
            if name in [ 'Type', 'Target']:
                ln = value.split('/')[-1] # take the last (localname) part of the value
                # ln will be 'slideLayout', 'audio', 'media', 'image'
                if Verbose_Flag:
                    print(f'{ln=}')
                relationships_for_slide[name]=ln
            else:
                relationships_for_slide[name]=value

    relationships[slide_name]=relationships_for_slide

    return relationships_for_slide

def main(argv):
    global Verbose_Flag
    global testing
    global Keep_picture_flag
    global known_hashes
    global relationships
    
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

    argp.add_argument('-c', '--course_id',
                      type=int,
                      default=False,
                      help="course_id"
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

    argp.add_argument("--config",
                      dest="config_filename",
                      help="read configuration from FILE"
                      )



    args = vars(argp.parse_args(argv))

    Verbose_Flag=args["verbose"]

    options=dict()
    if args["config_filename"]:
        options['config_filename']=args["config_filename"]

    initialize(options)

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

    course_id=args["course_id"]
    if course_id:
        print(f'{course_id=}')

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
        if Verbose_Flag:
            print(f'{split_fn=}')

        # Ignore files under _rels, customXml, docProps
        if split_fn[0] in ['_rels', 'customXml', 'docProps']:
            continue

        if len(split_fn) >= 2 and split_fn[0] == 'ppt' and split_fn[1] in ['theme' 'viewProps.xml', 'presProps.xml', 'tableStyles.xml', 'commentAuthors.xml', 'presentation.xml', 'notesMasters']:
            continue

        # Ignore files under the substrees indicated
        if len(split_fn) >= 2 and split_fn[0] == 'ppt' and split_fn[1] in ['_rels', 'slideLayouts', 'slideMasters']:
            continue

        # process files of the form split_fn=['ppt', 'slides', '_rels', 'slide4.xml.rels']
        # ppt/slides/_rels/slide1.xml.rels
        if len(split_fn) == 4 and split_fn[0] == 'ppt' and split_fn[1] == 'slides' and split_fn[2] ==  '_rels':
            file_contents = document.read(fn)
            extract_relationships(split_fn[3][:-5], file_contents)
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
            print(f'{split_fn[2]} {e_text_list=}')
            e_text=txt_list_to_string(e_text_list['text'])
            # {'types': accumulated_sph_type, 'text': accumulated_txt_list, 'typeface': accumulated_typeface_list, 'levels': accumulated_levels_list}
            html_for_page=''
            start_of_indent=False
            last_p_level=0
            for i in range(0,len(e_text_list['text'])):
                # use pop(0) to get the first item in the list
                if len(e_text_list['types']) > 0:
                    p_type=e_text_list['types'].pop(0)
                else:
                    p_type=None

                if len(e_text_list['text']) > 0:
                    p_text=e_text_list['text'].pop(0)
                else:
                    p_text=''
                if len(e_text_list['typeface']) > 0:
                    p_typeface=e_text_list['typeface'].pop(0)
                else:
                    p_typeface=None
                if len(e_text_list['levels']) > 0:
                    p_level=e_text_list['levels'].pop(0)
                else:
                    p_level=None
                print(f'{p_type=} {p_text=} {p_typeface=} {p_level=}')

                # remove any instances of None from p_text
                p_text = list(filter(lambda item: item is not None, p_text))
                if isinstance(p_text, list):
                    p_text=''.join(p_text)
                print(f'after join {p_type=} {p_text=} {p_typeface=} {p_level=}')

                th=None
                if p_type and isinstance(p_type, list) and len(p_type) >= 1:
                    th=p_type[0]
                else:
                    th=None

                # if th == 'sldNum':                # skip slide numbers
                #     continue
                if th == 'title':
                    html_for_page=html_for_page+'<h1>{}</h1>'.format(p_text)
                    continue
                if th == 'subTitle':
                    html_for_page=html_for_page+'<h2>{}</h2>'.format(p_text)
                    continue

                # at this point th should be 'body' or None
                print(f'{th=}')
                current_p_level=None
                if p_level and isinstance(p_level, list) and len(p_level) > 0:
                    current_p_level=p_level.pop(0)

                print(f'{current_p_level=}')

                if current_p_level is None:
                    if start_of_indent:
                        start_of_indent=False
                        html_for_page=html_for_page+'</ul>'
                    html_for_page=html_for_page+'<p>{}</p>'.format(p_text)
                    continue
                if isinstance(current_p_level, str) and current_p_level == '1':
                    if not start_of_indent:
                        start_of_indent=True
                        html_for_page=html_for_page+'<ul>'
                    if len(p_text) > 0:
                        html_for_page=html_for_page+'<li>{}</li>'.format(p_text)
                    continue

                print("using final case as p_type was not a list")
                html_for_page=html_for_page+'<p>{}</p>'.format(p_text)

            # at end of body be sure to end the list, if one is being output
            if start_of_indent:
                start_of_indent=False
                html_for_page=html_for_page+'</ul>'

            print(f'{html_for_page=}')
            with open(output_filename+'.txt','w') as f:
                f.write(e_text)
            with open(output_filename+'.html','w') as f:
                f.write(html_for_page)


        # extract slides such as split_fn=['ppt', 'notesSlides', 'notesSlide1.xml']
        if len(split_fn) == 3 and split_fn[0] == 'ppt' and split_fn[1] == 'notesSlides':
            file_contents = document.read(fn)
            output_filename=f'{target_directory}/{split_fn[2]}'
            with open(output_filename,'wb') as f:
                f.write(file_contents)

            #xml_content = document.read(fn).decode('utf-8')
            xml_content = file_contents 
            e_text_list=extract_text(xml_content)
            print(f'{split_fn[2]} {e_text_list=}')
            e_text=txt_list_to_string(e_text_list['text'])
            # {'types': accumulated_sph_type, 'text': accumulated_txt_list, 'typeface': accumulated_typeface_list, 'levels': accumulated_levels_list}
            html_for_page=''
            start_of_indent=False
            last_p_level=0
            for i in range(0,len(e_text_list['text'])):
                # use pop(0) to get the first item in the list
                if len(e_text_list['types']) > 0:
                    p_type=e_text_list['types'].pop(0)
                else:
                    p_type=None

                if len(e_text_list['text']) > 0:
                    p_text=e_text_list['text'].pop(0)
                else:
                    p_text=''
                if len(e_text_list['typeface']) > 0:
                    p_typeface=e_text_list['typeface'].pop(0)
                else:
                    p_typeface=None
                if len(e_text_list['levels']) > 0:
                    p_level=e_text_list['levels'].pop(0)
                else:
                    p_level=None
                print(f'{p_type=} {p_text=} {p_typeface=} {p_level=}')

                # remove any instances of None from p_text
                p_text = list(filter(lambda item: item is not None, p_text))
                if isinstance(p_text, list):
                    p_text=''.join(p_text)
                print(f'after join {p_type=} {p_text=} {p_typeface=} {p_level=}')

                th=None
                if p_type and isinstance(p_type, list) and len(p_type) >= 1:
                    th=p_type[0]
                else:
                    th=None

                # if th == 'sldNum':                # skip slide numbers
                #     continue
                if th == 'title':
                    html_for_page=html_for_page+'<h1>{}</h1>'.format(p_text)
                    continue
                if th == 'subTitle':
                    html_for_page=html_for_page+'<h2>{}</h2>'.format(p_text)
                    continue

                # at this point th should be 'body' or None
                print(f'{th=}')
                current_p_level=None
                if p_level and isinstance(p_level, list) and len(p_level) > 0:
                    current_p_level=p_level.pop(0)

                print(f'{current_p_level=}')

                if current_p_level is None:
                    if start_of_indent:
                        start_of_indent=False
                        html_for_page=html_for_page+'</ul>'
                    html_for_page=html_for_page+'<p>{}</p>'.format(p_text)
                    continue
                if isinstance(current_p_level, str) and current_p_level == '1':
                    if not start_of_indent:
                        start_of_indent=True
                        html_for_page=html_for_page+'<ul>'
                    if len(p_text) > 0:
                        html_for_page=html_for_page+'<li>{}</li>'.format(p_text)
                    continue

                print("using final case as p_type was not a list")
                html_for_page=html_for_page+'<p>{}</p>'.format(p_text)

            # at end of body be sure to end the list, if one is being output
            if start_of_indent:
                start_of_indent=False
                html_for_page=html_for_page+'</ul>'

            print(f'{html_for_page=}')
            with open(output_filename+'.txt','w') as f:
                f.write(e_text)
            with open(output_filename+'.html','w') as f:
                if split_fn[1] == 'notesSlides':
                    f.write("<hr>\n<h3>Slide Notes</h3>\n")
                f.write(html_for_page)



        # Extract media files, such as ppt/media/image10.png
        if len(split_fn) == 3 and split_fn[0] == 'ppt' and split_fn[1] == 'media':
            try:
                file_contents = document.read(fn)
            except Exception as e:
                print("Error {0} encountered when processing: {1}".format(e.args, fn))
                continue        # process the next package item

            file_hash = hashlib.md5(file_contents).hexdigest()
            print("file: {0} with hash {1}".format(split_fn[2], file_hash))
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

