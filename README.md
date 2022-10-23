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

### Purpose
To setup a degree project course.

### Input
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

### Output
(Very limited unless in verbose mode)

### Notes
Note that the program can generate the course code list, course names, and examiner information for any of KTH's schools (as it takes the data from KOPPS) [However, I have only tried it thus far for SCI.]

Note it is not designed to be run multipe times. If you want to run it again you need to delete the things (modules, assignments, and quiz) that were created. Programs to help with this can be found at [https://github.com/gqmaguirejr/Canvas-tools](https://github.com/gqmaguirejr/Canvas-tools)

For the survey, the code collects information about all of the exjobb courses owned by a given school and adds all of these to a pull-down menu for the student to select which course code they want to register for. Similarly the student can suggest an examiner from a pull-down that is generated from all of the examiners for exjobbs of a given level as specified in KOPPS for the relevant courses. Note that there is no automatic transfer (yet) of the material from the survey to the custom columns. 

When generating sections, the code generates sections for each of the programs and each of the examiners to make it easy for PAs and examiners to keep track of the progress of their students.


### Examples
```
Set up the modules:
    ./setup-degree-project-course.py --config config-test.json -m 1 12683

Set up the survey:
    ./setup-degree-project-course.py --config config-test.json -s 1 12683 EECS

Set up sections for the examiners and programs
    ./setup-degree-project-course.py --config config-test.json -S 2 12683 EECS

    ./setup-degree-project-course.py --config config-test.json -S 2 12683 SCI

```

### Limitations
The contents of the Introduction pages and assignments need to be worked over. The assignments could be added to one of the modules.

Missing yet are the updated template files for 2019 and any other files in the course.

Also missing is adding the examiners automatically to the course. However, perhaps this should be left to the normal Canvas course room creation scripts.

## get-degree-project-course-data.py

### Purpose
To collects data from KOPPS use later by setup-degree-project-course-from-JSON-file.py to set up a course (these two programs are designed to be a replacement for setup-degree-project-course.py)

### Input
```
./setup-degree-project-course-from-JSON-file.py cycle_number course_id school_acronym
```
where cycle_number is either 1 or 2 (1st or 2nd cycle)

### Output
Aa file of the form course-data-{school_acronym}-cycle-{cycle_number}.json

## setup-degree-project-course-from-JSON-file.py

### Purpose
To setup a degree project course based upon collected data

### Input
Takes data from a file of the form course-data-{school_acronym}-cycle-{cycle_number}.json
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

### Output
(Very limited unless in verbose mode)

### Notes
Note that the program can generate the course code list, course names, and examiner information for any of KTH's schools (as it takes the data from KOPPS) [However, I have only tried it thus far for SCI.]

Note it is not designed to be run multipe times. If you want to run it again you need to delete the things (modules, assignments, and quiz) that were created. Programs to help with this can be found at [https://github.com/gqmaguirejr/Canvas-tools](https://github.com/gqmaguirejr/Canvas-tools)

When generating sections, the code generates sections for each of the programs and each of the examiners to make it easy for PAs and examiners to keep track of the progress of their students.

### Examples
```
Set up the modules:
    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -m 1 12683

Set up the survey:
    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -s 1 12683 EECS

Set up sections for the examiners and programs
    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -S 2 12683 EECS

    ./setup-degree-project-course-from-JSON-file.py --config config-test.json -S 2 12683 SCI

```

### Limitations
The contents of the Introduction pages and assignments need to be worked over. The assignments could be added to one of the modules.

Missing yet are the updated template files for 2019 and any other files in the course.


## SinatraTest15.rb

### Purpose
To collect data via a dynamic quiz - uses data collected from KOPPS to build the content of many selections (courses and examiners)

### Input
The data is assumed to be in a file: course-data-{school_acronym}-cycle-{cycle_number}.json

### Output
Outputs values collected are stored into the Canvas gradebooks

## progs-codes-etc.py
### Purpose
Use the new KOPPS v2 API to get information about programs and specializations

### Input
Takes as a command line argument school_acronym, but only currently uses it to form the name of the output file

### Output
Outputs program acronyms and names in English and Swedish as well as the acronyms and names in English and Swedish of specializations in a file with a name in the format: progs-codes-etc-<program_code>.xlsx

## announce-presentation.rb

### Purpose
To enable an examiner to generate an announcement for an oral presenation for a 1st or 2nd cycle degree project, make a cover, and set up a 10th month warning.

### Input
```
ruby announce-presentation.rb
```

### Output
(ideally) it will put an announcement into the Polopoly calendar for the school and insert an announcement into the Canvas course room for this degree project

## s-announce-presentation.rb

### Purpose
To enable an examiner to generate an announcement for an oral presenation for a 1st or 2nd cycle degree project, make a cover, and set up a 10th month warning. Note that this version uses HTTPS, hence there is a need to set up certificates.

### Input
```
ruby s-announce-presentation.rb
```

### Output
(ideally) it will put an announcement into the Polopoly calendar for the school and insert an announcement into the Canvas course room for this degree project


## generate_cover.rb

### Purpose
To generate (for test) a cover from fixed information via the KTH cover generator

### Input
```
ruby generate_cover.rb
```

### Output
Creates a file test1.pdf that contains the front and back covers as generated

## list_trita_tables.rb

### Purpose
Connects to the trita database and list each of the trita related tables

### Input
```
ruby list_trita_tables.rb
```

### Output
Output of the form:
ruby list_trita_tables.rb
{"schemaname"=>"public", "tablename"=>"eecs_trita_for_thesis_2019", "tableowner"=>"postgres", "tablespace"=>nil, "hasindexes"=>"t", "hasrules"=>"f", "hastriggers"=>"f", "rowsecurity"=>"f"}
{"id"=>"1", "authors"=>"James FakeStudent", "title"=>"A fake title for a fake thesis", "examiner"=>"Dejan Kostic"}
{"id"=>"2", "authors"=>"xxx", "title"=>"xxx", "examiner"=>"yyy"}
{"id"=>"3", "authors"=>"xx", "title"=>"xxx", "examiner"=>"yyy"}
...

## remove_trita_tables.rb

### Purpose
Connects to the trita database and list each of the trita related tables

### Input
```
ruby remove_trita_tables.rb
```

### Output
Output of the form (showing the tables being deleted):
ruby remove_trita_tables.rb
{"schemaname"=>"public", "tablename"=>"eecs_trita_for_thesis_2019", "tableowner"=>"postgres", "tablespace"=>nil, "hasindexes"=>"t", "hasrules"=>"f", "hastriggers"=>"f", "rowsecurity"=>"f"}
...

## get-downloads-for-diva-documents.py
### Purpose
To scrape the number of downloads of a document in DiVA.

### Input
```
./get-downloads-for-diva-documents.py diva2_ids.xlsx
```

### Output
Outputs diva-downloads.xlsx a spreadsheet of the number of downloads

### Note
The diva2_ids.xlsx must have a 'Sheet1'. The first columns of this spreadsheet should have a column heading, such as "diva2 ids". The values in the subsequent rows of this column should be of the form: diva2:dddddd, for example: diva2:1221139

### Example
```
./get-downloads-for-diva-documents.py diva2_ids.xlsx
```

## custom-data-for-users-in-course.py
### Purpose
To output custom data for each user in a course

### Input
```
./custom-data-for-users-in-course.py course_id

```
### Output
Prints the custom data for each user in a course

with the option '-C'or '--containers' use HTTP rather than HTTPS for access to Canvas
with the option -t' or '--testing' testing mode

with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program

Can also be called with an alternative configuration file:
 ./custom-data-for-users-in-course.py --config config-test.json

### Examples
```
./custom-data-for-users-in-course.py 4

./custom-data-for-users-in-course.py --config config-test.json 4

./custom-data-for-users-in-course.py -C 5

```
## edit-external-tool-for-course.py

### Purpose
Edit the text for an external tool for the given course_id

### Input
```
./edit-external-tool-for-course.py  course_id tool_id 'navigation_text'
```

### Output
Outputs information about the external tool

with the option '-C'or '--containers' use HTTP rather than HTTPS for access to Canvas
with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program

Can also be called with an alternative configuration file:
./create_fake_users-in-course.py --config config-test.json

### Examples
```
./edit-external-tool-for-course.py 4 2 'TestTool'
./edit-external-tools-for-course.py --config config-test.json 4 2 'TestTool'

./edit-external-tools-for-course.py -C 5 2 'TestTool'

 change the tool URL to https
 ./edit-external-tools-for-course.py -s -C 5 2 'TestTool'

```

##  ./cover_data.py
### Purpose
To get the information needed for covers of degree project reports (i.e., theses)

### Input
```
 ./cover_data.py school_acronym
```

"-t" or "--testing" to enable small tests to be done
 
with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program

### Output
Produces a spreadsheet containing all of the data about degree project courses
The filë́s name is of the form: exjobb_courses-{school_acronym}.xlsx

### Example
```
Can also be called with an alternative configuration file:
./setup-degree-project-course.py --config config-test.json 1 EECS

```

## list-all-custom-column-entries.py

### Purpose
To list the curstom columns entries for a course

### Input
```
./list-all-custom-column-entries.py course_id
```
 with the option '-C'or '--containers' use HTTP rather than HTTPS for access to Canvas
 with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
 Can also be called with an alternative configuration file: --config config-test.json

### Output
Outputs an xlsx file of the form containing all of the custom columns: custom-column-entries-course_id-column-column_all.xlsx
The first column of the output will be user_id.

## setup-a-degree-project-course-from-JSON-file.py

### Purpose
To setup a single specific degree project course

### Input
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

### Output
(Very limited unless in verbose mode)

### Notes
Note it is not designed to be run multipe times. If you want to run it again you need to delete the things (modules, assignments, and quiz) that were created. Programs to help with this can be found at [https://github.com/gqmaguirejr/Canvas-tools](https://github.com/gqmaguirejr/Canvas-tools)

When generating sections, the code generates sections for each of the programs and each of the examiners to make it easy for PAs and examiners to keep track of the progress of their students.


### Examples
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

### Limitations
The contents of the Introduction pages and assignments need to be worked over. The assignments could be added to one of the modules.

Missing yet are the updated template files for 2020 and any other files in the course.

Also missing is adding the examiners automatically to the course. However, perhaps this should be left to the normal Canvas course room creation scripts.


## get-school-acronyms-and-program-names-data.py

### Purpose
To generate information for use in the KTH thesis template at https://gits-15.sys.kth.se/maguire/kthlatex/tree/master/kththesis

### Input
```
./get-school-acronyms-and-program-names-data.py
```

### Output
Produces a file containing the school acronyms and all of the program names, in the format for inclusion into the thesis template

## add-url-to-button-push-for-lti.js

### Purpose
To added the URL of a page to the URL being passed to an external tool. This code is to be added to an account in Canvas as custom Javascript code.

## Adding_URL_to_call_to_external_tool.docx

### Purpose
The document Adding_URL_to_call_to_external_tool.docx describes how to add the page where an external LTI tool is invoked to the URL passed to the LTI application (for the Javascript add-url-to-button-push-for-lti.js).


## insert_teachers_grading_standards.py
Purpose
To insert examiners names into a grading scale for use with an assignment to keep track of who the examiner for a student is. The example code will be used as the name of the grading scale.

The documentation of this program is in Abusing_grading_schemes.docx.

### Input
```
./insert_teachers_grading_standards.py -a account_id cycle_number school_acronym course_code
./insert_teachers_grading_standards.py   course_id cycle_number school_acronym course_code

```

### Example
```
./insert_teachers_grading_standards.py -v 11 2 EECS II246X
```

## insert_YesNo_grading_standards.py
### Purpose
To insert a grading scale for use with a Yes/Now result (the Yes or No "grade" is reported in the Gradebook by the teacher). 

### Input
```
./insert_YesNo_grading_standards.py -a account_id
./insert_YesNo_grading_standards.py   course_id

```

### Example
```
./insert_YesNo_grading_standards.py -v 11
```

## add_language_global_nav_item.js

### Purpose
To insert a menu item into the Canvas global navigation menu and if you click on this buttom it toggles between English ("en") and Swedish ("sv").

The details are document in Better_language_support.docx

## get-all-degree-project-examiners.py
### Purpose
To get information about all of the degree project courses and their examiners from KOPPS

### Input
```
./get-all-degree-project-examiners.py cycle_number
```
cycle_number is either 1 or 2

### Output
Outputs a file of the names: KTH_examiners-cycle-1.json or KTH_examiners-cycle-2.json

## check_degree_projects_from_DiVA.py
### Purpose
To check the examiner name against the list of degree project examiners

### Input
```
./check_degree_projects_from_DiVA.py diva_shreadsheet.xlsx
```

### Output
Outputs and updated spreadsheet

## get_user_by_orcid.py
### Purpose
To get information about a KTH user based on their orcid

### Input
```
./get_user_by_orcid.py orcid_of_user
```

### Output
Outputs JSON

### Example
```
./get_user_by_orcid.py 0000-0002-6066-746X
user={'kthId': 'u1d13i2c', 'username': 'maguire', 'emailAddress': 'maguire@kth.se', 'firstName': 'Gerald Quentin', 'lastName': 'Maguire Jr'}
```

## get_user_by_orcid.py
### Purpose
To get information about a KTH user based on their orcid

### Input
```
./get_user_by_kthid.py KTHID_of_user
```

### Output
Outputs JSON

### Example
```
./get_user_by_orcid.py 0000-0002-6066-746X
user={'defaultLanguage': 'en',
      'acceptedTerms': True,
      'isAdminHidden': False,
      'avatar': {'visibility': 'public'},
      '_id': 'u1d13i2c', 'kthId': 'u1d13i2c', 'username': 'maguire',
      'homeDirectory': '\\\\ug.kth.se\\dfs\\home\\m\\a\\maguire',
      'title': {'sv': 'PROFESSOR', 'en': 'PROFESSOR'},
      'streetAddress': 'ISAFJORDSGATAN 26',
      'emailAddress': 'maguire@kth.se',
      'telephoneNumber': '',
      'isStaff': True, 'isStudent': False, 
      'firstName': 'Gerald Quentin', 'lastName': 'Maguire Jr',
      'city': 'Stockholm', 'postalCode': '10044',
      'remark': 'COMPUTER COMMUNICATION LAB',
      'lastSynced': '2020-10-28T13:36:56.000Z',
      'researcher': {'researchGate': '', 'googleScholarId': 'HJgs_3YAAAAJ', 'scopusId': '8414298400', 'researcherId': 'G-4584-2011', 'orcid': '0000-0002-6066-746X'},

      'courses': {
         'visibility': 'public',
	 'codes': ['II2202', 
	       ...
	          ],
         'items': [{'title': {'sv': 'Forskningsmetodik och vetenskapligt skrivande', 'en': 'Research Methodology and Scientific Writing'}, 'roles': ['examiner', 'courseresponsible', 'teachers'], 'code': 'II2202', 'koppsUrl': 'https://www.kth.se/student/kurser/kurs/II2202', 'courseWebUrl': 'https://www.kth.se/social/course/II2202/'}, 
	 ...
	 ]},
	 'worksFor': {'items': [{'key': 'app.katalog3.J.JH', 'path': 'j/jh', 'location': '', 'name': 'CS DATAVETENSKAP', 'nameEn': 'DEPARTMENT OF COMPUTER SCIENCE'}, {'key': 'app.katalog3.J.JH.JHF', 'path': 'j/jh/jhf', 'location': 'KISTAGÅNGEN 16, 16440 KISTA', 'name': 'KOMMUNIKATIONSSYSTEM', 'nameEn': 'DIVISION OF COMMUNICATION SYSTEMS'}]},
	 'pages': [],
	 'links': {'visibility': 'public', 'items': [{'url': 'http://people.kth.se/~maguire/', 'name': 'Personal web page at KTH'}, {'url': 'https://www.ae-info.org/ae/Member/Maguire_Jr._Gerald_Quentin', 'name': 'page at Academia Europaea'}]}, 'description': {'visibility': 'public', 'sv': '<p>Om du verkligen vill kontakta mig eller hitta information om mig, se min hemsida:\xa0<a href="http://people.kth.se/~maguire/">http://people.kth.se/~maguire/</a></p>\r\n', 'en': '<p>If you actually want to contact me or find information related to me, see my web page:\xa0<a href="http://people.kth.se/~maguire/">http://people.kth.se/~maguire/</a></p>\r\n'},
'images': {'big': 'https://www.kth.se/social/files/576d7ae3f2765459470e7b0e/chip-identicon-52e6e0ae2260166c91cd528ba0c72263_large.png', 'visibility': 'public'},
	  'room': {'placesId': 'fad3809a-344b-4572-9795-5b423e0a9b2a', 'title': '4478'},
	  'socialId': '55564',
	  'createdAt': '2006-01-09T13:13:59.000Z',
	  'visibility': 'public'}
```

## get-school-acronyms-and-program-names-data-3rd-cycle.py
### Purpose
To get the school acronyms and the acroynms and names of the 3rd cycle programs to be used when making a 3rd cycle thesis/dissertation

### Input
```
get-school-acronyms-and-program-names-data-3rd-cycle.py
```

### Output
Outputs the LaTeX code on standard output and in a file schools_and_programs_3rd_cycle.ins 

### Example
```
./get-school-acronyms-and-program-names-data-3rd-cycle.py

cmdp=\newcommand{\programcode}[1]{%
  \ifinswedish
  \IfEqCase{#1}{%
    {KTHARK}{\programme{Arkitektur}}%
    {KTHBIO}{\programme{Bioteknologi}}%
    {KTHBYV}{\programme{Byggvetenskap}}%
    {KTHDAT}{\programme{Datalogi }}%
    {KTHEST}{\programme{Elektro- och systemteknik}}%
    {KTHEGI}{\programme{Energiteknik och -system}}%
    {KTHFTK}{\programme{Farkostteknik}}%
    {KTHFYS}{\programme{Fysik}}%
    {KTHGEO}{\programme{Geodesi och Geoinformatik}}%
    {KTHHFL}{\programme{Hållfasthetslära}}%
    {KTHIEO}{\programme{Industriell ekonomi och organisation}}%
    {KTHIIP}{\programme{Industriell produktion}}%
    {KTHIKT}{\programme{Informations- och kommunikationsteknik}}%
    {KTHKEV}{\programme{Kemivetenskap}}%
    {KTHKON}{\programme{Konst, teknik och design}}%
    {KTHMAT}{\programme{Matematik}}%
    {KTHKOM}{\programme{Medierad kommunikation }}%
    {KTHPBA}{\programme{Planering och beslutsanalys}}%
    {KTHSHB}{\programme{Samhällsbyggnad: Management, ekonomi och juridik}}%
    {KTHTMV}{\programme{Teknisk materialvetenskap}}%
    {KTHMEK}{\programme{Teknisk Mekanik}}%
    {KTHTKB}{\programme{Teoretisk kemi och biologi}}%
  }[\typeout{program's code not found}]
  \else
  \IfEqCase{#1}{%
    {KTHARK}{\programme{Architecture}}%
    {KTHBIO}{\programme{Biotechnology}}%
    {KTHBYV}{\programme{Civil and Architectural Engineering}}%
    {KTHDAT}{\programme{Computer Science}}%
    {KTHEST}{\programme{Electrical Engineering}}%
    {KTHEGI}{\programme{Energy Technology and Systems}}%
    {KTHFTK}{\programme{Vehicle and Maritime Engineering}}%
    {KTHFYS}{\programme{Physics}}%
    {KTHGEO}{\programme{Geodesy and Geoinformatics}}%
    {KTHHFL}{\programme{Solid Mechanics}}%
    {KTHIEO}{\programme{Industrial Economics and Management}}%
    {KTHIIP}{\programme{Production Engineering}}%
    {KTHIKT}{\programme{Information and Communication Technology}}%
    {KTHKEV}{\programme{Chemical Science and Engineering}}%
    {KTHKON}{\programme{Art, Technology and Design }}%
    {KTHMAT}{\programme{Mathematics}}%
    {KTHKOM}{\programme{Mediated Communication}}%
    {KTHPBA}{\programme{Planning and Decision Analysis}}%
    {KTHSHB}{\programme{The Built Environment and Society: Management, Economics and Law}}%
    {KTHTMV}{\programme{Engineering Materials Science}}%
    {KTHMEK}{\programme{Engineering Mechanics}}%
    {KTHTKB}{\programme{Theoretical Chemistry and Biology}}%
  }[\typeout{program's code not found}]
  \fi
}

```

## JSON_to_calendar.py
### Purpose
The program creates an event entry:
             from a JSON file (input event type 0),
             from a MODS file (input event type 3), or
             from fixed data (input event type 2).

This event will be inserted into the KTH Cortina Calendar (unless the --nocortina flag is set or the user does not have a Cortina access key).
The program also generates an announcement in the indicated Canvas course room and creates a calendar entry in the Canvas calendar for this course room.

It can also modify (using PUT) an existing Cortina Calendar entry.

### Input
```
./JSON_to_calendar.py -c course_id [--nocortina] --event 0|2|3 [--json file.json] [--mods file.mods]
```

### Note
Note that the initial fixed entry (i.e., a built in event) verison put an entry in for a thesis and then gets it, then modifies the English language "lead" for the event and modifies the entry. Finally, it gets the entry and outputs it.

The program evolved to take in events from other sources and also to generate an announcement in a Canvas course room and also to generate a Canvas Calendar event for this course room.

## extract_pseudo_JSON-from_PDF.py

### Purpose
Extract data from the end of a PDF file that has been put out by my LaTeX template for use when inserting a thesis into DiVA.
	 The formalt of this data is pseudo JSON.

	 Use the Python package pdfminer to extract the data from the PDF file. See https://github.com/pdfminer/pdfminer.six

### Input
```
extract_pseudo_JSON-from_PDF.py
```

### Output
Outputs by default calendar_event.json
	You can also specifiy another output file name.

### Note
Note that unless you specify the option "-l" or "--ligature" and of the common ligatures will be replaced by the letter combination, rather than left as a single code point. This is primarily to prevent problems later with ligatures in title, subtitles, abstracts, etc.

### Example
```
./extract_pseudo_JSON-from_PDF.py --pdf test5.pdf

./extract_pseudo_JSON-from_PDF.py --pdf test5.pdf --json event.json

./extract_pseudo_JSON-from_PDF.py --pdf oscar.pdf --json event.json
```

## JSON_to_cover.py

### Purpose
The program creates a thesis cover using the information from the arguments and a JSON file.
	 The JSON file can be produced by extract_pseudo_JSON-from_PDF.py

### Input
```
./JSON_to_cover.py [-c course_id] --json file.json [--cycle 1|2] [--credits 7.5|15.0|30.0|50.0] [--exam 1|2|3|4|5|6|7|8 or or the name of the exam] [--area area_of_degree] [--area2 area_of_second_degree] [--trita trita_string] [--school ABE|CBH|EECS|ITM|SCI]  [--file thesis_file.pdf] [--diva 1|2...]
```

### Output
Outputs the cover in a file: cover.pdf
	and splits the cover.pdf into two pages: cover_pages-1 and cover_pages-2

### Note
The file name if give must end in ".pdf".
      Still experimental

#### As of 2021-12-13 the KTH cover generator does not work (as they replaced it with a DOCX template).

### Example
```
./JSON_to_cover.py -c 11  --json event.json --testing --exam 4
```
For a file (oscar.pdf) without For DIVA pages:
```
./JSON_to_cover.py --json event.json --testing --exam 4 --file oscar.pdf
```
For a file (oscar.pdf) with two(2) For DIVA pages:
```
./JSON_to_cover.py --json event.json --testing --exam 4 --file oscar.pdf --diva 2
```
## Announcing a thesis

Assuming that a student has submitted a thesis with the information in the For DIVA pages (at the end of it) that include the information about the opponent(s) and presenation.
1. Save the PDF file, for example: oscar.pdf
2. Extract the For DIVA information as JSON
   ```
   ./extract_pseudo_JSON-from_PDF.py --pdf oscar.pdf --json oscar.json
   ```
3. Make the announcement for a course (with course_id 11):
   ```
   ./JSON_to_calendar.py -c 11 --nocortina --json oscar.json
   ```

The --nocortina flag says do not put into the KTH calendar (even if you have permssions to do so). At the moment the Cortina functionality is not available in production.

## Making covers and applying them to a thesis

Assuming that a student has submitted a thesis with the information in the For DIVA pages (at the end of it) that includes the information for the DIVA entry and the examiner has approved the thesis.
1. Save the PDF file, for example: oscar.pdf
2. Extract the For DIVA information as JSON
   ```
   ./extract_pseudo_JSON-from_PDF.py --pdf oscar.pdf --json oscar.json
   ```
3. Make the covers and apply them. For a file (oscar.pdf) with two(2) For DIVA pages:
   ```
   ./JSON_to_cover.py --json oscar.json --testing --exam 4 --file oscar.pdf --diva 2
   ```

It is also possible in the 3rd step to just make the cover.pdf, cover-pages-1 and cover-pages-2 files -- simply do not provide the --file and --diva arguments.

## fill_in_template.py

### Purpose
To fill in a KTH cover template with data from a JSON file 

### Input
```
./fill_in_template.py --pdf template.pdf --json data.json
```

### Output
Outputs a pdf file named "output.pdf" (currently a fixed name)

### Example
```
 ./fill_in_template.py --pdf "KTH_Omslag_Exjobb_Formulär_Final_dummy_EN-20210623.pdf" --json jussi.json --trita "TRITA-EECS-EX-2021:330"
```
Note that the new template is net yet ready for prime time and this program is a simple hack to see if I can mechanically generate the new format of cover. Once both the template and the program are more mature the code should get integrated into JSON_to_cover.py - with a new option to specify whether you want to "new" or "old" cover.

## JSON_to_MODS.py
### Purpose
The program creates a MODS file using the information from the arguments and a JSON file.

The input JSON file can be produced by extract_pseudo_JSON-from_PDF.py

### Input
```
 ./JSON_to_MODS.py [-c course_id] --json file.json [--cycle 1|2] [--credits 7.5|15.0|30.0|50.0] [--exam 1|2|3|4|5|6|7|8 or or the name of the exam] [--area area_of_degree] [--area2 area_of_second_degree] [--trita trita_string] [--school ABE|CBH|EECS|ITM|SCI]
```
### Output
Outputs the MODS file: MODS.pdf

### Example
```
./JSON_to_MODS.py -c 11   --json jussi.json --trita "TRITA-EECS-EX-2021:219" --testing
or
./JSON_to_MODS.py -c 11   --json test12.json --trita "TRITA-EECS-EX-2021:219" --testing
```
Note that currentlt the Canvas course information is not used.

## JSON_to_ladok.py

### Purpose
The program makes an entry in LADOK for the indicate course_code and moment
          using the information from the arguments and a JSON file.
The JSON file can be produced by extract_pseudo_JSON-from_PDF.py

### Input
```
 ./JSON_to_ladok.py [-c course_id] --json file.json --code course_code [--which 1|2] [--date 2021-07-14] [--grade [P|F|A|B|C|D|E|Fx|F”] -gradeScale ["PF"|"AF"] [--date YYYY-MM-DD]
```
### Note
Note that which == 3 means both authors, while 1 is hte first author only and 2 is the second author only
The deault (0) is to report the result for both authors or the only author (if there is just one author).

If the exam date is not specified, it defaults to today.

An assumption is that there is only one moment that requires a project title, i.e., 'KravPaProjekttitel' is True


### Output
Misc. messages - mostly an error message including "Hinder mot skapa resultat påträffat: Rapporteringsrättighet saknas"
 as I do not have permission to register these course results

### Example
```
./JSON_to_ladok.py -c 11   --json experiment.json --code DA213X
```
### Note
This is very much a work in progress, since I have not really been able to test it completely. It uses the ladok3 python library, but extends it with some features that are not (yet) in the library.

## thesis_titles.py

### Purpose
The program extracts the thesis title from LADOK for all the students in the specified canvas_course.

### Input
```
./thesis_titles.py -c course_id
```

An assumption is that there is only one moment that requires a project title, i.e., 'KravPaProjekttitel' is True

### Output
Spreadsheeet with the data

### Example
```
./thesis_titles.py -c 25434
```

## thesis_titles_by_school.py
### Purpose
The program extracts the thesis title from LADOK for all the students in the canvas_course.

### Input
```
./thesis_titles_by_school.py -s school_acronym
```

An assumption is that there is only one moment that requires a project title, i.e., 'KravPaProjekttitel' is True

### Output: spreadsheeet with the data in the a file with a name of the form: titles-all-school_acronym.xlsx
such as: titles-all-EECS.xlsx

### Example
```
./thesis_titles_by_school.py -s EECS
```
## MODS_to_titles_and_subtitles.py
### Purpose
The program outputs a spreadsheet of titles and subtitles split by language from the input MODS file.

### Input
```
./MODS_to_titles_and_subtitles.py --mods file.mods
```

### Output
Outputs a file of the form: titles-from-{}.xlsx where {} is replace by the input filename without extension

### Example
```
./MODS_to_titles_and_subtitles.py --mods file.mods
```

## extract_customDocProperties.py
### Purpose
Extract document information and properties from a DOCX file to make a JSON output

### Input
```
./extract_customDocProperties.py filename.docx
```

### Output
Outputs JSON for the DOCX file, in the form to be used for other program. If the output file is not specified the data is output to a file named output.json.

### Example
```
./extract_customDocProperties.py test.docx --json output.json

Pretty print the resulting JSON
 ./extract_customDocProperties.py Template-thesis-English-2021-with-for-DiVA.docx --pretty

force English as the language of the body of the document
 ./extract_customDocProperties.py Template-thesis-English-2021-with-for-DiVA.docx --English

force Swedish as the language of the body of the document
 ./extract_customDocProperties.py Template-thesis-English-2021-with-for-DiVA.docx --Swedish


```

## cleanup_pseudo_JSON-from_LaTeX.py 
### Purpose
Extract data from the pseudo JSON file that has been produced by my LaTeX template and cleanit up, so that it can be used with my other program (to create claendar entries, MODS file, and insert titles into LADOK).

### Input
```
 ./cleanup_pseudo_JSON-from_LaTeX.py --json fordiva.json [--acronyms acronyms.tex]
```

### Output
Outputs a new cleaned up JSON file in a file with the name augmented by "-cleaned"

### Example
```
 ./cleanup_pseudo_JSON-from_LaTeX.py --json fordiva.json [--acronyms acronyms.tex]
```

## degree_project_course_codes_by_school.py
### Purpose
The program extracts the thesis title from LADOK for all the students in the canvas_course.

### Input
```
./degree_project_course_codes_by_school.py -s school_acronym
```
An assumption is that there is only one moment that requires a project title, i.e., 'KravPaProjekttitel' is True

### Output
Spreadsheeet with the data

## teachers-in-course-kthid-and-other-profile-data.py
### Purpose
Outputs XLSX spreadsheet with teachers in the course and add some KTH profile information

### Input
```
./teachers-in-course-kthid-and-other-profile-data.py -c course_id
```

### Output
Outputs a file with a name of the form teachers-COURSE_ID.xlsx

### Example
```
./teachers-in-course-kthid-and-other-profile-data.py   --config config-test.json -c 25434
```

## courses_grades_by_school.py

### Purpose
To collect the course moment information and number of students in course instances since a given starting year (by default 2020)

### Input
```
./courses_grades_by_school.py -s school_code
```

### Output
Outputs a spreadsheet with a name of the form: courses-in-XXXX.xlsx

### Example
```
./courses_grades_by_school.py -s EECS
```

## augment_course_data.py

### Purpose
To augment a spreadsheet produced by courses_grades_by_school.py

### Input
```
./augment_course_data.py -s school_acronym
```

reads in course data from courses-in-{}.xlsx

### Output
Outputs an updated spreadsheet courses-in-{}-augmented.xlsx

### Example
```
./augment_course_data.py -s EECS

dept_names=['EECS/Computer Science', 'EECS/Electrical Engineering', 'EECS/Human Centered Technology', 'EECS/Intelligent Systems']
dept_colors={'EECS/Computer Science': {'name': 'EECS/Computer Science', 'color': {'color': 'blue', 'transparency': 50}}, 'EECS/Electrical Engineering': {'name': 'EECS/Electrical Engineering', 'color': {'color': 'red', 'transparency': 50}}, 'EECS/Human Centered Technology': {'name': 'EECS/Human Centered Technology', 'color': {'color': 'green', 'transparency': 50}}, 'EECS/Intelligent Systems': {'name': 'EECS/Intelligent Systems', 'color': {'color': 'magenta', 'transparency': 50}}}
max_number_of_students_in_a_course=400
total_students=29817
max_row=8, cats=='cy1 degree name'!C2:C9, values=("='cy1 degree name'!$E2:$E9",)
Uses a Pie in Pie chart to show this data (sheetname=cy2 degree name)
max_row=33, cats=='cy2 degree name'!C2:C34, values=("='cy2 degree name'!$E2:$E34",)
```

## JSON_to_DOCX_cover.py
### Purpose
The program creates a thesis cover using the information from the arguments and a JSON file.
	 The JSON file can be produced by extract_pseudo_JSON-from_PDF.py

### Input
```
./JSON_to_DOCX_cover.py --json file.json [--cycle 1|2] [--credits 7.5|15.0|30.0|50.0] [--exam 1|2|3|4|5|6|7|8 or or the name of the exam] [--area area_of_degree] [--area2 area_of_second_degree] [--trita trita_string] [--file cover_template.docx] [--picture]
```

### Output
Outputs the cover in a file: <input_filename>-modified.docx

### Note
Only one test json file has been run.

### Examples
```
#  enter data from a JSON file
./JSON_to_DOCX_cover.py --json event.json

./JSON_to_DOCX_cover.py --json event.json --testing --exam 4

./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx
#    produces za5-modified.docx with the optional picture removed

# Manually specifying the level and number of credits
./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx --cycle 1 --credits 7.5
./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx --cycle 1 --credits 10.0
./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx --cycle 1 --credits 15.0
# it will even work with
./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx --cycle 1 --credits 15

./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx --cycle 2 --credits 15.0
./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx --cycle 2 --credits 30.0
./JSON_to_DOCX_cover.py --json fordiva-cleaned.json --file za5.docx --cycle 2 --credits 60.0
```


## DiVA_organization_info.py
### Purpose
The program creates a XLSX file of orgniazation data based upon the DiVA cora API for Organisationsmetadata

### Input
```
./DiVA_organization_info.py [--orgid org_id] [--orgname organization_name] [--json filename.json] [--csv]
```

### Output
Output: outputs a file with a name of the form DiVA_org_id_date.xlsx

	The columns of the spread sheet are organisation_id, organisation_name_sv, organisation_name_en, organisation_type_code, organisation_type_name, organisation_parent_id, closed_date, organisation_code

### Note
The command has --verbose and --testing optional arguments for more information and more limiting the number of records processed.

### Examples
```
#  get data from a JSON file
./DiVA_organization_info.py --orgid 177 --json UUB-20211210-get.json

#  get data from a JSON file with out specifying the orgid, it will take this from the topOrganisation
./DiVA_organization_info.py --json UUB-20211210-get.json

#  get date via the organization name
./DiVA_organization_info.py --orgname kth

# ouput a CSV file rather than a XLSX file
./DiVA_organization_info.py --json UUB-20211210-get.json --csv

```

## extract_custom_DOCX_properties.py

### Purpose
The program extract the list of custom docproperties and their values from a DOCX file

### Input:
```
./extract_custom_DOCX_properties.py [--file filename.docx]
```

### Output:
Outputs the properties in a JSON file: <input_filename>-extracted.json

### Note
The custom DOCPROPETIES are in a file (with in the ZIP archive DOCX file) with the name docProps/custom.xml

### Example
```
./extract_custom_DOCX_properties.py --file zb1.docx
```

## customize_DOCX_file.py

### Purpose

The program produces a customized DOCX by setting the custom DOCPROPERIYES to the values from the JSON file
The JSON file can be produced by extract_custom_DOCX_properties.py

### Input
```
./customize_DOCX_file.py --json file.json [--file cover_template.docx]
```

### Output
Outputs a customized DOCX file: <input_filename>-modified.docx

### Note 

Use of the two programs (customize_DOCX_file.py and extract_custom_DOCX_properties.py) is explained in the document: Modifying_DOCX_properties.docx

### Example
```
 ./customize_DOCX_file.py --json custom_values.json --file za5.docx
#    produces za5-modified.docx
```

## customize_LaTeX_project.py

### Purpose
The program produces a customized ZIP of a LaTeX project based upon the values in the JSON file

### Input
```
./customize_LaTeX_project.py --json file.json [--file latex_project.zip] [--initialize]
```

### Output
Outputs a customized LaTeX project ZIP file: <input_filename>-modified.zip

### Note 
If the --initialize command line argument is given, then the existing custom content is ignored.
Otheriwse, if the length of the existing content is longer thane 0, the new customizeation is added at the end of the existing customization.

Only limited testing has been done.

## create_customized_JSON_file.py

### Purpose
The program creates a JSON file of customization information

### Input
```
./create_customized_JSON_file.py  [-c CANVAS_COURSE_ID]
				  [-j JSON]
				  [--language LANGUAGE]
				  [--author AUTHOR]
				  [--author2 AUTHOR2]
				  [--school SCHOOL]
				  [--courseCode COURSECODE]
				  [--programCode PROGRAMCODE]
				  [--cycle CYCLE]
				  [--credits CREDITS]
				  [--area AREA]
				  [--area2 AREA2]
				  [--numberOfSupervisors NUMBEROFSUPERVISORS]
				  [--Supervisor SUPERVISOR]
				  [--Supervisor2 SUPERVISOR2]
				  [--Supervisor3 SUPERVISOR3]
				  [--Examiner EXAMINER]
```
### Output
Outputs a JSON file with customized content: by default: customize.json

### Note 

The code assumes that students are in a section in the course with the course code in the section name. The code will also take advantage of students being in project groups, so you only have to give the user name for one of the students. If the Examiner and Supervisor "assignments" exist the code will use the examiner/superviors name from the "grade" of these assignments to get the data for the examiner and supervisor(s). Note that this code only supports getting information for KTH supervisors, for industrial supervisors you can just use a user name such as xxx - that does not exist as a KTH user name and the code will generate fake informaiton as a place holder for the external supervisor.

The code uses the course code to guess what national subject catergory the thesis will fall into. Note that in some cases, the course name suggests multiple categories - so these are added and then there is a note about which category codes correspond to what - so that a human can edit the resulting JSON file to have a suitable list of category codes in it.

If you specify a value, such as --courseCode COURSECODE it will override the course code detected from the section that the student is in. This is both for testing purposes and can be used if the student is not yet in the Canvas course.


### Example
```
./create_customized_JSON_file.py --canvas_course_id 32733 --author vvvvv --language eng --programCode TCOMK --courseCode EA275X --Examiner maguire --Supervisor vastberg --Supervisor2 xxx
```

If the examiner and supervisor are known in the course, then the input could be as simple as:
```
./create_customized_JSON_file.py --canvas_course_id 22156 --author aaaaaa --language eng --programCode TCOMK  
```
In the above case, the actual student behind the obscured user name 'aaaaaa' was in a two person first cycle degree project and the code will correctly find the other student (if they are in a project group together in the course).

## degree_project_courses_subjects.py
### Purpose
Purpose to collect information about the subjects of the various degree project courses using the information from KOPPS.

### Input
```
./degree_project_courses_subjects.py
```

### Output
Outpus the result as an XLSX file with a name:  degree_project_courses_info.xlsx
and a JSON file with the name: degree_project_courses_info.json

## add_dropdows_to_DOCX_file.py

### Purpose
The program modifies the KTH cover (saved as a DOCX file) by inserting drop-down menus and other configuration for a particular exam and main subject/field of technology/...

### Input
```
./add_dropdows_to_DOCX_file.py [--file cover_template.docx]
```

### Output
outputs a modified DOCX file: <input_filename>-modified.docx
More specifically the 'word/document.xml' within the DOCX file is modified.

### Note 
Depends on the new KTH cover files not being changed.

### Example
```
If z6.docx contains an English cover:
./add_dropdows_to_DOCX_file.py --file z6.docx --exam kandidatexamen

If z7.docx contains a Swedish cover:
./add_dropdows_to_DOCX_file.py --file z7.docx --exam kandidatexamen --language sv

The various exams in English and Swedish
./add_dropdows_to_DOCX_file.py --file z6.docx --exam kandidatexamen
./add_dropdows_to_DOCX_file.py --file z7.docx --exam kandidatexamen --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam högskoleingenjörsexamen
./add_dropdows_to_DOCX_file.py --file z7.docx --exam högskoleingenjörsexamen --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam civilingenjörsexamen
./add_dropdows_to_DOCX_file.py --file z7.docx --exam civilingenjörsexamen --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam magisterexamen
./add_dropdows_to_DOCX_file.py --file z7.docx --exam magisterexamen --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam masterexamen
./add_dropdows_to_DOCX_file.py --file z7.docx --exam masterexamen --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam arkitektexamen
./add_dropdows_to_DOCX_file.py --file z7.docx --exam arkitektexamen --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam ämneslärarexamen
./add_dropdows_to_DOCX_file.py --file z7.docx --exam ämneslärarexamen --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam CLGYM
./add_dropdows_to_DOCX_file.py --file z7.docx --exam CLGYM --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam KPULU
./add_dropdows_to_DOCX_file.py --file z7.docx --exam KPULU --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam both
./add_dropdows_to_DOCX_file.py --file z7.docx --exam both  --language sv

./add_dropdows_to_DOCX_file.py --file z6.docx --exam same
./add_dropdows_to_DOCX_file.py --file z7.docx --exam same --language sv

```
### Note
There is a script to create a directory (Some_examples) of examples:
```
create_some_dropdown_cover_examples.bash
```

## cluster_degree_projects.py

### Purpose
Reads in data from a XLSX file of degree project courses with their subjects and computers overlaps. The end goal is to be able to cluser the degree project courses by subject.

### Input
```
./cluster_degree_projects.py --file xxx.xlsx
```

### Output
    Various outputs, such as:
```
overlap_combinations=[{'ABE', 'CBH'}, {'EECS', 'ABE'}, {'ABE', 'ITM'}, {'SCI', 'ABE'}, {'EECS', 'CBH'}, {'ITM', 'CBH'}, {'SCI', 'CBH'}, {'STH', 'CBH'}, {'EECS', 'ITM'}, {'SCI', 'EECS'}, {'SCI', 'ITM'}]
overlapping_subjects={'Physics', 'Information and Communication Technology', 'Information Technology', 'Electrical Engineering', 'Computer Science and Engineering', 'Environmental Engineering', 'Technology and Economics', 'Engineering Physics', 'Materials Science and Engineering', 'Technology and Health', 'Mechanical Engineering', 'Industrial Management', 'Materials Science'}
                                             	ABE	CBH	EECS	ITM	SCI	STH
Computer Science and Engineering             	 	 	X	X	 	 
Electrical Engineering                       	 	X	X	X	 	 
Engineering Physics                          	 	 	X	X	X	 
Environmental Engineering                    	X	 	 	X	 	 
Industrial Management                        	X	 	 	X	 	 
Information Technology                       	 	X	 	 	 	X
Information and Communication Technology     	 	X	 	 	 	X
Materials Science                            	 	X	 	X	 	 
Materials Science and Engineering            	 	X	 	X	 	 
Mechanical Engineering                       	X	 	X	X	X	 
Physics                                      	 	X	 	 	X	 
Technology and Economics                     	X	 	 	X	 	 
Technology and Health                        	X	X	 	 	 	 
```

### Note
This is very much a work in progress.

### Example
```
./cluster_degree_projects.py --file degree_project_courses_info-sorted.xlsx
```

## Some_reasons_for_a_standard_thesis_template-for-DOCX.docx

A document about using the DOCX templates and their associated programs.


## add_subject_credits_title_etc_to_cover.py

### Purpose

Add the the information from the JSON file to the cover (fron and back).

### Input
```
./add_subject_credits_title_etc_to_cover.py --file  filename.docx --json filename.json --exam examname
```

### Example
```
./add_subject_credits_title_etc_to_cover.py --file  Omslag_Exjobb_Eng_en-20220325.docx --json calendar_event.json --exam kandidatexamen
```

## backcover.py

### Purpose
Create a KTH back cover with a TRITA number

### Input
```
./backcover.py --school xxx [--year yyyy] --number 00 --pdf output.pdf
```

### Output
Outputs a PDF page as a back cover.

### Example
```
./backcover.py --school EECS --year 2022 --number 00 --pdf output.pdf
```

## check_for_new_cover.py

### Purpose check for a New KTH cover versus old KTH cover

### Input
```
./check_for_new_cover.py [--pdf test.pdf] [-s spreadhseet.xlsx]
```

### Output
If given a pdf file name it outputs some 

If given a spreadsheet it ouputs some information about what PDFminer fins on the page and whether this is an old cover or incorrect degree project major subject and produces an updated spreadsheet augment with the information it got from the PDF files.

If you make a directory to put the thesis PDFs into, such as
```
mkdir EECS_theses_in_DIVA
```

the you can get the spreadsheet with:
```
wget -O eecs-2022.csv 'https://kth.diva-portal.org/smash/export.jsf?format=csvall2&addFilename=true&aq=[[]]&aqe=[]&aq2=[[{"dateIssued":{"from":"2022","to":"2022"}},{"organisationId":"879223","organisationId-Xtra":true},{"publicationTypeCode":["studentThesis"]}]]&onlyFullText=false&noOfRows=5000&sortOrder=title_sort_asc&sortOrder2=title_sort_asc'

wget -O sci-2022.csv 'https://kth.diva-portal.org/smash/export.jsf?format=csvall2&addFilename=true&aq=[[]]&aqe=[]&aq2=[[{"dateIssued":{"from":"2022","to":"2022"}},{"organisationId":"6091","organisationId-Xtra":true},{"publicationTypeCode":["studentThesis"]}]]&onlyFullText=false&noOfRows=5000&sortOrder=title_sort_asc&sortOrder2=title_sort_asc'

wget -O itm-2022.csv 'https://kth.diva-portal.org/smash/export.jsf?format=csvall2&addFilename=true&aq=[[]]&aqe=[]&aq2=[[{"dateIssued":{"from":"2022","to":"2022"}},{"organisationId":"6023","organisationId-Xtra":true},{"publicationTypeCode":["studentThesis"]}]]&onlyFullText=false&noOfRows=5000&sortOrder=title_sort_asc&sortOrder2=title_sort_asc'

wget -O abe-2022.csv 'https://kth.diva-portal.org/smash/export.jsf?format=csvall2&addFilename=true&aq=[[]]&aqe=[]&aq2=[[{"dateIssued":{"from":"2022","to":"2022"}},{"organisationId":"5850","organisationId-Xtra":true},{"publicationTypeCode":["studentThesis"]}]]&onlyFullText=false&noOfRows=5000&sortOrder=title_sort_asc&sortOrder2=title_sort_asc'

wget -O cbh-2022.csv 'https://kth.diva-portal.org/smash/export.jsf?format=csvall2&addFilename=true&aq=[[]]&aqe=[]&aq2=[[{"dateIssued":{"from":"2022","to":"2022"}},{"organisationId":"879224","organisationId-Xtra":true},{"publicationTypeCode":["studentThesis"]}]]&onlyFullText=false&noOfRows=5000&sortOrder=title_sort_asc&sortOrder2=title_sort_asc'
```
You have to convert the CSV file to XLSX file.

Now you can run a script to get all the files from the spdreasheet:
```
get_full_text_from_diva.py eecs-2022.xlsx 
```

Now that you have the files locally, you can run the program with the -s option and give the name of the spreadsheet, scuh as:
```
/z3/maguire/E-learning/check_for_new_cover.py -s eecs-2022.xlsx
```

This will produce a file: eecs-2022with_coverinfo.xlsx

## get_full_text_from_diva.py
### Purpose
Fetch the full text of theses from DiVA using the URL in the field FullTextLink in the spreadsheet.

### Input
```
./get_full_text_from_diva.py filename.xlsx
```

### Output
Outputs the files to the current directory with a name of the form <PID>-FULLTEXT.pdf where <PID> is the publication ID from the first column of the spreadsheet.

## find_For_DIVA_page.py
### Purpose

    check for and determina the page within the PDF file where the "For DIVA" data begins

### Input
```
./find_For_DIVA_page.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
```

### Output
If run on a single PDF file, it either outputs a line of the form:
```
   Found for DIVA page at 117 in dddddddd-FULLTEXT01.pdf
```
or nothing

If run on a spreadsheet it outputs a new spreadsheet (whose name ends with 'with_forDIVA_info.xlsx) augmented with a column: 'For DIVA page(s) present'
it also outputs instances of found "For DiVA" pages saying:
```
Found for DIVA page at 96 in dddddddd-FULLTEXT01.pdf by author(s) X, Y (KTH [177], Skolan för elektroteknik och datavetenskap (EECS) [879223])
```

### Example
For a single PDF file:
```
 ./find_For_DIVA_page.py --pdf ddddddd-FULLTEXT01.pdf
```

 For all the PDF files in the spreadsheet
```
 ./find_For_DIVA_page.py -s ../eecs-2022with_coverinfo.xlsx
```
Note that this can be fund after updating the original spreadsheet with cover information

## find_back_cover_page.py
### Purpose
Check for and determina the page within the PDF file where the back cover is
Note that this also checks for old covers.

### Input
```
./find_back_cover_page.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
```

### Output

Depending on the -v or --testing options there is various levels of output and
in the case of a spreadsheet, the program produces a spreadsheet augmented
with data about the back cover. The column 'Back cover' will contain the page
number of the back cover that was found, while the column 'Back cover version'
will contain 'Old' or 'New' to indicate which version of the cover was found.

The new spreadsheet filename will end with 'with_back_cover_info.xlsx'.

### Note 

### Example
For a single PDF file:
```
./find_back_cover_page.py --pdf ddddddd-FULLTEXT01.pdf
```

For all the PDF files in the spreadsheet:
```
# ./find_back_cover_page.py -s ../eecs-2022with_coverinfo.xlsx
```
Note that this can be fund after updating the original spreadsheet with cover information


## frontcover.py

### Purpose
Make a front cover (in PDF) using the information in a JSON file.


### Input
```
./frontcover.py --json input.json --pdf output.pdf --year YYYY
```

### Output
The PDF file is generated in the specified output file (by default "test.pdf").

### Note 
This is a work in progress.

### Example
```
./frontcover.py -v --json fordiva-example-cleaned.json --pdf output.pdf --year 2022
```
## testing-frontcover.bash

### Purpose
Try to make a number of different types of covers based on JSON files using frontpage.py

### Input
Needs a set of JSON files:

fordiva-example-högskoleexamen-tekink-swedish.json
fordiva-example-högskoleingenjörsexamen-elektronik_och_datorteknik-swedish.json
fordiva-example-kandidate-tekink-swedish.json
fordiva-example-högskoleingenjörsexamen-elektronik_och_datorteknik-swedish.json
fordiva-example-civilingenjörsexamen-elektrotekink-swedish.json
fordiva-example-magisterexamen-swedish.json
fordiva-example-masters-TCOMM.json
fordiva-example-arkitektexamen-swedish.json
fordiva-example-ämneslärarexamen-Technology_and_Learning.json
fordiva-example-CLGYM-Technology_and_Learning.json
fordiva-example-KPULU.json
fordiva-example-both.json
fordiva-example-same.json


### Output
Creates output file in a subdirectory "Some_examples_of_covers"

## find_and_extract_references.py
### Purpose
Find and extract refrences pages


### Input
```
./find_and_extract_references.py [--pdf test.pdf] [--spreadsheet filename.xlsx]
```

### Output
Ouptuts files eith file names ending with "-refpages.pdf"

### Example
```
path_to_executable/find_and_extract_references.py -s ../eecs-2022.xlsx
```

## customize_tex_from_nbconvert.py

### Purpose
Take the tex file produced by nbconvert and customize it


### Input
```
./customize_tex_from_nbconvert.py filename.tex [customization.tex]
```

### Output
Outputs a file with a name of the form filenam-customized.tex

## Example
1. The useer first produces LaTeX from a Jupyter notebook

      jupyter nbconvert --to latex Notebook_5-EECS.ipynb

2. Customize the resulting Notebook_5-EECS.tex file

      customize_tex_from_nbconvert.py --tex Notebook_5-EECS.tex


## compare_onedrive_folder_with_directory.py
### Purpose
Compare the files in a local directory to the files in a OneDriver folder

The spradsheet is obtained from the Onedrive folder by exporting it to Excel.
To do this you go to OneDrive and change to the classic interface and then export to Excel - which gives me a query.iqy file (i.e., a Microsoft Internet Query file) 

This query.iqy has to be openned in a desktop version of Excel (it did not seem possible to open it via https://www.office.com/).
Once you do yet another login, it does give a spreadsheet of the files.

Oddly it does not say how large the files are but rather gives a "Huvudantal" column.  Now I will just have to figure out out to compare this with the results of "ls" and then figure out which files are missing.

The preadhsheet is assumed to have the columns: 'Namn', 'Ändrat', 'Huvudantal', 'Ändrades av', 'Objekttyp', 'Sökväg'

With the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program

### Input
```
./compare_onedrive_folder_with_directory.py local_directory onedrive_spreadsheetFile
```

### Example
```
./compare_onedrive_folder_with_directory.py   II2202-for-Wouter  II2202-for-wouler-spreadsheet.xlsx
```

### Output
```
spreadsheetColumns=['Namn', 'Ändrat', 'Huvudantal', 'Ändrades av', 'Objekttyp', 'Sökväg']
skipping a file wihout a valid name
skipping a file wihout a valid name
Missing file: /z3/maguire/II2202-for-Wouter/#z9#
Due to a invalid charcter (:) in a OneDriver filename, missing file: II2202-for-Wouter/2020/Figures_for_Canvas_pages/Thumbs.db:encryptable
Due to a invalid charcter (:) in a OneDriver filename, missing file: II2202-for-Wouter/Green_networks/Thumbs.db:encryptable
Due to a invalid charcter (:) in a OneDriver filename, missing file: II2202-for-Wouter/Modules-2021/Modules/Quality_assurance/Thumbs.db:encryptable
...
Due to a invalid charcter (:) in a OneDriver filename, missing file: II2202-for-Wouter/Images/Thumbs.db:encryptable
Missing file: II2202-for-Wouter/Images/-topleve-sustainabilioty-quiz-Screenshot_20220324_182126.png
Missing file: II2202-for-Wouter/Images/-student-rights-Screenshot_20220222_152448.png
Due to a invalid charcter (:) in a OneDriver filename, missing file: /z3/maguire/II2202-for-Wouter/Images/KTH Library: Databases.jpg
```

Note that the two files:
   II2202-for-Wouter/Images/-topleve-sustainabilioty-quiz-Screenshot_20220324_182126.png
   II2202-for-Wouter/Images/-student-rights-Screenshot_20220222_152448.png
correspond to the two files that were skipped, they are actually in OneDrive but there is a problem with the interpretation of the value in the "Namn" cell in the spreadsheet.

<!--
## yyy.py

### Purpose

### Input
```
./xxx.py KTHID_of_user
```

### Output


### Note 

### Example
```
./xxx.py u1d13i2c
```

You can xxxx, for example:
```

```
-->
