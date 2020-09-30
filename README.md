# E-learning
This repository consists of tools for use with KTH's LMS and other systems to facilitate e-learning activities of faculty, students, and staff.

These tools are intended to be examples of how one can use the Canvas Restful API and to
provide some useful functionality (mainly for teachers).

Programs can be called with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program.

Additionally, programs can be called with an alternative configuration file using the syntax: --config FILE

for example:  --config config-test.json

See the default-config.json file for an example of the structure of this file. Replace the string xxx by your access token and replace the string yyy.instructure.com with the name of the server where your Canvas LMS is running.

======================================================================
## setup-degree-project-course.py

Purpose: To setup a degree project course.

Input:
```
./setup-degree-project-course.py cycle_number course_id school_acronym
 cycle_number is either 1 or 2 (1st or 2nd cycle)

 "-m" or "--modules" set up the two basic modules (Gatekeeper module 1 and Gatekeeper protected module 1)
 "-p" or "--page" set up the two basic pages for the course
 "-s" or "--survey" set up the survey
 "-S" or "--sections" set up the sections for the examiners and programs
 "-c" or "--columns" set up the custom columns
 "-p" or "--pages" set up the pages
 "-a" or "--assignments" set up the assignments (proposal, alpha and beta drafts, active listner, self-assessment, etc.)

 "-A" or "--all" set everything up (sets all of the above options to true)

 with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
 Can also be called with an alternative configuration file:
     ./setup-degree-project-course.py --config config-test.json 1 12683
```

Output: (Very limited unless in verbose mode)

### Notes:
Note that the program can generate the course code list, course names, and examiner information for any of KTH's schools (as it takes the data from KOPPS) [However, I have only tried it thus far for SCI.]

Note it is not designed to be run multipe times. If you want to run it again you need to delete the things (modules, assignments, and quiz) that were created. Programs to help with this can be found at [https://github.com/gqmaguirejr/Canvas-tools](https://github.com/gqmaguirejr/Canvas-tools)

For the survey, the code collects information about all of the exjobb courses owned by a given school and adds all of these to a pull-down menu for the student to select which course code they want to register for. Similarly the student can suggest an examiner from a pull-down that is generated from all of the examiners for exjobbs of a given level as specified in KOPPS for the relevant courses. Note that there is no automatic transfer (yet) of the material from the survey to the custom columns. 

When generating sections, the code generates sections for each of the programs and each of the examiners to make it easy for PAs and examiners to keep track of the progress of their students.


### Examples:
```
Set up the modules:
    ./setup-degree-project-course.py --config config-test.json -m 1 12683

Set up the survey:
    ./setup-degree-project-course.py --config config-test.json -s 1 12683 EECS

Set up sections for the examiners and programs
    ./setup-degree-project-course.py --config config-test.json -S 2 12683 EECS

    ./setup-degree-project-course.py --config config-test.json -S 2 12683 SCI

```

### Limitations:
The contents of the Introduction pages and assignments need to be worked over. The assignments could be added to one of the modules.

Missing yet are the updated template files for 2019 and any other files in the course.

Also missing is adding the examiners automatically to the course. However, perhaps this should be left to the normal Canvas course room creation scripts.

## get-degree-project-course-data.py

Purpose: To collects data from KOPPS use later by setup-degree-project-course-from-JSON-file.py to set up a course (these two programs are designed to be a replacement for setup-degree-project-course.py)

Input: 
```
./setup-degree-project-course-from-JSON-file.py cycle_number course_id school_acronym
```
where cycle_number is either 1 or 2 (1st or 2nd cycle)

Output: a file of the form course-data-{school_acronym}-cycle-{cycle_number}.json

## setup-degree-project-course-from-JSON-file.py

Purpose: To setup a degree project course based upon collected data

Input: takes data from a file of the form course-data-{school_acronym}-cycle-{cycle_number}.json
```
./setup-degree-project-course-from-JSON-file.py cycle_number course_id school_acronym
 cycle_number is either 1 or 2 (1st or 2nd cycle)

 "-m" or "--modules" set up the two basic modules (Gatekeeper module 1 and Gatekeeper protected module 1)
 "-p" or "--page" set up the two basic pages for the course
 "-s" or "--survey" set up the survey
 "-S" or "--sections" set up the sections for the examiners and programs
 "-c" or "--columns" set up the custom columns
 "-p" or "--pages" set up the pages
 "-a" or "--assignments" set up the assignments (proposal, alpha and beta drafts, active listner, self-assessment, etc.)

 "-A" or "--all" set everything up (sets all of the above options to true)

 with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
 Can also be called with an alternative configuration file:
     ./setup-degree-project-course.py --config config-test.json 1 12683
```

Output: (Very limited unless in verbose mode)

### Notes:
Note that the program can generate the course code list, course names, and examiner information for any of KTH's schools (as it takes the data from KOPPS) [However, I have only tried it thus far for SCI.]

Note it is not designed to be run multipe times. If you want to run it again you need to delete the things (modules, assignments, and quiz) that were created. Programs to help with this can be found at [https://github.com/gqmaguirejr/Canvas-tools](https://github.com/gqmaguirejr/Canvas-tools)

When generating sections, the code generates sections for each of the programs and each of the examiners to make it easy for PAs and examiners to keep track of the progress of their students.

### Examples:
```
Set up the modules:
    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -m 1 12683

Set up the survey:
    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -s 1 12683 EECS

Set up sections for the examiners and programs
    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -S 2 12683 EECS

    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -S 2 12683 SCI

```

### Limitations:
The contents of the Introduction pages and assignments need to be worked over. The assignments could be added to one of the modules.

Missing yet are the updated template files for 2019 and any other files in the course.


## SinatraTest15.rb

Purpose: To collect data via a dynamic quiz - uses data collected from KOPPS to build the content of many selections (courses and examiners)

Input: The data is assumed to be in a file: course-data-{school_acronym}-cycle-{cycle_number}.json

Output: outputs values collected are stored into the Canvas gradebooks

## progs-codes-etc.py
Purpose:  use the new KOPPS v2 API to get information about programs and specializations

Input: takes as a command line argument school_acronym, but only currently uses it to form the name of the output file

Output: outputs program acronyms and names in English and Swedish as well as the acronyms and names in English and Swedish of specializations in a file with a name in the format: progs-codes-etc-<program_code>.xlsx

## announce-presentation.rb

Purpose: To enable an examiner to generate an announcement for an oral presenation for a 1st or 2nd cycle degree project, make a cover, and set up a 10th month warning.

Input:
```
ruby announce-presentation.rb
```

Output: (ideally) it will put an announcement into the Polopoly calendar for the school and insert an announcement into the Canvas course room for this degree project

## s-announce-presentation.rb

Purpose: To enable an examiner to generate an announcement for an oral presenation for a 1st or 2nd cycle degree project, make a cover, and set up a 10th month warning. Note that this version uses HTTPS, hence there is a need to set up certificates.

Input:
```
ruby s-announce-presentation.rb
```

Output: (ideally) it will put an announcement into the Polopoly calendar for the school and insert an announcement into the Canvas course room for this degree project


## generate_cover.rb

Purpose: To generate (for test) a cover from fixed information via the KTH cover generator

Input:
```
ruby generate_cover.rb
```

Output: creates a file test1.pdf that contains the front and back covers as generated

## list_trita_tables.rb

Purpose: Connects to the trita database and list each of the trita related tables

Input:
```
ruby list_trita_tables.rb
```

Output: Output of the form:
ruby list_trita_tables.rb
{"schemaname"=>"public", "tablename"=>"eecs_trita_for_thesis_2019", "tableowner"=>"postgres", "tablespace"=>nil, "hasindexes"=>"t", "hasrules"=>"f", "hastriggers"=>"f", "rowsecurity"=>"f"}
{"id"=>"1", "authors"=>"James FakeStudent", "title"=>"A fake title for a fake thesis", "examiner"=>"Dejan Kostic"}
{"id"=>"2", "authors"=>"xxx", "title"=>"xxx", "examiner"=>"yyy"}
{"id"=>"3", "authors"=>"xx", "title"=>"xxx", "examiner"=>"yyy"}
...

## remove_trita_tables.rb

Purpose: Connects to the trita database and list each of the trita related tables

Input:
```
ruby remove_trita_tables.rb
```

Output: Output of the form (showing the tables being deleted):
ruby remove_trita_tables.rb
{"schemaname"=>"public", "tablename"=>"eecs_trita_for_thesis_2019", "tableowner"=>"postgres", "tablespace"=>nil, "hasindexes"=>"t", "hasrules"=>"f", "hastriggers"=>"f", "rowsecurity"=>"f"}
...

## get-downloads-for-diva-documents.py
Purpose: To scrape the number of downloads of a document in DiVA.

Input:
```
./get-downloads-for-diva-documents.py diva2_ids.xlsx
```

Output: outputs diva-downloads.xlsx a spreadsheet of the number of downloads

Note the diva2_ids.xlsx must have a 'Sheet1'. The first columns of this spreadsheet should have a column heading, such as "diva2 ids". The values in the subsequent rows of this column should be of the form: diva2:dddddd, for example: diva2:1221139

Example:
```
./get-downloads-for-diva-documents.py diva2_ids.xlsx
```

## custom-data-for-users-in-course.py
Purpose: To output custom data for each user in a course

Input:
```
./custom-data-for-users-in-course.py course_id

```
Output: prints the custom data for each user in a course

with the option '-C'or '--containers' use HTTP rather than HTTPS for access to Canvas
with the option -t' or '--testing' testing mode

with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program

Can also be called with an alternative configuration file:
 ./custom-data-for-users-in-course.py --config config-test.json

Examples:
```
./custom-data-for-users-in-course.py 4

./custom-data-for-users-in-course.py --config config-test.json 4

./custom-data-for-users-in-course.py -C 5

```
## edit-external-tool-for-course.py

Purpose: edit the text for an external tool for the given course_id

Input:
```
./edit-external-tool-for-course.py  course_id tool_id 'navigation_text'
```

Output: outputs information about the external tool

with the option '-C'or '--containers' use HTTP rather than HTTPS for access to Canvas
with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program

Can also be called with an alternative configuration file:
./create_fake_users-in-course.py --config config-test.json

Examples:
```
./edit-external-tool-for-course.py 4 2 'TestTool'
./edit-external-tools-for-course.py --config config-test.json 4 2 'TestTool'

./edit-external-tools-for-course.py -C 5 2 'TestTool'

 change the tool URL to https
 ./edit-external-tools-for-course.py -s -C 5 2 'TestTool'

```

##  ./cover_data.py

Purpose: To get the information needed for covers of degree project reports (i.e., theses)

Input:
```
 ./cover_data.py school_acronym
```

"-t" or "--testing" to enable small tests to be done
 
with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program

Output: produces a spreadsheet containing all of the data about degree project courses
The filë́s name is of the form: exjobb_courses-{school_acronym}.xlsx

Example:
```
Can also be called with an alternative configuration file:
./setup-degree-project-course.py --config config-test.json 1 EECS

```

## list-all-custom-column-entries.py

Purpose: To list the curstom columns entries for a course

Input:
```
./list-all-custom-column-entries.py course_id
```
 with the option '-C'or '--containers' use HTTP rather than HTTPS for access to Canvas
 with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
 Can also be called with an alternative configuration file: --config config-test.json

Output: Outputs an xlsx file of the form containing all of the custom columns: custom-column-entries-course_id-column-column_all.xlsx
The first column of the output will be user_id.

## setup-a-degree-project-course-from-JSON-file.py

Purpose: To setup a single specific degree project course

Input:
```
./setup-a-degree-project-course-from-JSON-file.py cycle_number course_id school_acronym course_code program_code
 cycle_number is either 1 or 2 (1st or 2nd cycle)

 "-m" or "--modules" set up the two basic modules (does nothing in this program)
 "-p" or "--page" set up the two basic pages for the course
 "-s" or "--survey" set up the survey
 "-S" or "--sections" set up the sections for the examiners and programs
 "-c" or "--columns" set up the custom columns
 "-p" or "--pages" set up the pages
 "-a" or "--assignments" set up the assignments (proposal, alpha and beta drafts, active listner, self-assessment, etc.)

 "-A" or "--all" set everything up (sets all of the above options to true)

 with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
 Can also be called with an alternative configuration file:
     ./setup-degree-project-course.py --config config-test.json 1 12683
```

Output: (Very limited unless in verbose mode)

### Notes:
Note it is not designed to be run multipe times. If you want to run it again you need to delete the things (modules, assignments, and quiz) that were created. Programs to help with this can be found at [https://github.com/gqmaguirejr/Canvas-tools](https://github.com/gqmaguirejr/Canvas-tools)

When generating sections, the code generates sections for each of the programs and each of the examiners to make it easy for PAs and examiners to keep track of the progress of their students.


### Examples:
```
# Create custom colums:
./setup-a-degree-project-course-from-JSON-file.py -c 1 19885 EECS IA150X CINTE

# Create sections for examiners and programs:
./setup-a-degree-project-course-from-JSON-file.py -S 1 19885 EECS IA150X CINTE
 
# Create assignments:
./setup-a-degree-project-course-from-JSON-file.py -a 1 19885 EECS IA150X CINTE

# Create pages for the course:
./setup-a-degree-project-course-from-JSON-file.py -p 1 19885 EECS IA150X CINTE

# Create objectives:
./setup-a-degree-project-course-from-JSON-file.py -o 1 19885 EECS IA150X CINTE

```

### Limitations:
The contents of the Introduction pages and assignments need to be worked over. The assignments could be added to one of the modules.

Missing yet are the updated template files for 2020 and any other files in the course.

Also missing is adding the examiners automatically to the course. However, perhaps this should be left to the normal Canvas course room creation scripts.


## get-school-acronyms-and-program-names-data.py

Purpose: To generate information for use in the KTH thesis template at https://gits-15.sys.kth.se/maguire/kthlatex/tree/master/kththesis

Input:
```
./get-school-acronyms-and-program-names-data.py
```

Output: produces a file containing the school acronyms and all of the program names, in the format for inclusion into the thesis template

## add-url-to-button-push-for-lti.js

Purpose: To added the URL of a page to the URL being passed to an external tool. This code is to be added to an account in Canvas as custom Javascript code.

## Adding_URL_to_call_to_external_tool.docx

Purpose: The document Adding_URL_to_call_to_external_tool.docx describes how to add the page where an external LTI tool is invoked to the URL passed to the LTI application (for the Javascript add-url-to-button-push-for-lti.js).


## insert_teachers_grading_standards.py
Purpose: To insert examiners names into a grading scale for use with an assignment to keep track of who the examiner for a student is. The example code will be used as the name of the grading scale.

The documentation of this program is in Abusing_grading_schemes.docx.

Input:
```
./insert_teachers_grading_standards.py -a account_id cycle_number school_acronym course_code
./insert_teachers_grading_standards.py   course_id cycle_number school_acronym course_code

```

Example:
```
./insert_teachers_grading_standards.py -v 11 2 EECS II246X
```

## insert_YesNo_grading_standards.py
Purpose: To insert a grading scale for use with a Yes/Now result (the Yes or No "grade" is reported in the Gradebook by the teacher). 

Input:
```
./insert_YesNo_grading_standards.py -a account_id
./insert_YesNo_grading_standards.py   course_id

```

Example:
```
./insert_YesNo_grading_standards.py -v 11
```

## add_language_global_nav_item.js

Purpose: To insert a menu item into the Canvas global navigation menu and if you click on this buttom it toggles between English ("en") and Swedish ("sv").

The details are document in Better_language_support.docx

<!--
## yyy.py

Purpose: To 

Input:
```
./xxx.py KTHID_of_user
```

Output: outputs 

Note 

Example:
```
./xxx.py u1d13i2c
```

You can xxxx, for example:
```

```
-->
