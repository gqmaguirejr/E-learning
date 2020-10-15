#!/usr/bin/python3
#
# ./insert_teachers_grading_standards.py -a account_id cycle_number school_acronym course_code
# ./insert_teachers_grading_standards.py   course_id cycle_number school_acronym course_code
#
# Generate a "grading standard" scale with the names of teachers as the "grades".
# Note that if the grading scale is already present, it does nothing unless the "-f" (force) flag is set.
# In the latter case it adds the grading scale.
#
# G. Q. Maguire Jr.
#
# 2020.09.24
#
# Test with
#  ./insert_teachers_grading_standards.py -v 11 2 EECS II246X
#  ./insert_teachers_grading_standards.py -v --config config-test.json 11 2 EECS II246X
# 
#

import csv, requests, time
import optparse
import sys
import json


#############################
###### EDIT THIS STUFF ######
#############################

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests

# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(options):
       global baseUrl, header, payload

       # styled based upon https://martin-thoma.com/configuration-files-in-python/
       if options.config_filename:
              config_file=options.config_filename
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


##############################################################################
## ONLY update the code below if you are experimenting with other API calls ##
##############################################################################

def create_grading_standard(course_or_account, id, name, scale):
       global Verbose_Flag
       # Use the Canvas API to create an grading standard
       # POST /api/v1/accounts/:account_id/grading_standards
       # or
       # POST /api/v1/courses/:course_id/grading_standards

       # Request Parameters:
       #Parameter		        Type	Description
       # title	Required	string	 The title for the Grading Standard.
       # grading_scheme_entry[][name]	Required	string	The name for an entry value within a GradingStandard that describes the range of the value e.g. A-
       # grading_scheme_entry[][value]	Required	integer	 -The value for the name of the entry within a GradingStandard. The entry represents the lower bound of the range for the entry. This range includes the value up to the next entry in the GradingStandard, or 100 if there is no upper bound. The lowest value will have a lower bound range of 0. e.g. 93

       if course_or_account:
              url = "{0}/courses/{1}/grading_standards".format(baseUrl, id)
       else:
              url = "{0}/accounts/{1}/grading_standards".format(baseUrl, id)

       if Verbose_Flag:
              print("url: {}".format(url))

       payload={'title': name,
                'grading_scheme_entry': scale
       }
    
       if Verbose_Flag:
              print("payload={0}".format(payload))

       r = requests.post(url, headers = header, json=payload)
       if r.status_code == requests.codes.ok:
              page_response=r.json()
              print("inserted grading standard")
              return True
       print("r.status_code={0}".format(r.status_code))
       return False

def get_grading_standards(course_or_account, id):
       global Verbose_Flag
       # Use the Canvas API to get a grading standard
       # GET /api/v1/accounts/:account_id/grading_standards
       # or
       # GET /api/v1/courses/:course_id/grading_standards

       # Request Parameters:
       #Parameter		        Type	Description
       if course_or_account:
              url = "{0}/courses/{1}/grading_standards".format(baseUrl, id)
       else:
              url = "{0}/accounts/{1}/grading_standards".format(baseUrl, id)

       if Verbose_Flag:
              print("url: " + url)

       r = requests.get(url, headers = header)
       if r.status_code == requests.codes.ok:
              page_response=r.json()
              return page_response
       return None

kth_examiners=["Åberg Wennerholm, Malin",
               "Åbom, Mats",
               "Abtahi, Seyedfarhad",
               "Ahmadian, Afshin",
               "Åkermo, Malin",
               "Alfredsson, Bo",
               "Alfredsson, Henrik",
               "Alfredsson, P. Henrik",
               "Amelin, Mikael",
               "Andén-Pantera, Joakim",
               "Andersson, John",
               "Andersson, Kristina",
               "Angelis, Jannis",
               "Annadotter, Kerstin",
               "Ansell, Anders",
               "Archenti, Andreas",
               "Arias Hurtado, Jaime",
               "Arias, Jaime",
               "Artho, Cyrille",
               "Artman, Henrik",
               "Arvidsson, Niclas",
               "Arvidsson, Niklas",
               "Azizpour, Hossein",
               "Baalsrud Hauge, Jannicke",
               "Bäbler, Matthäus",
               "Bagheri, Shervin",
               "Bälter, Olle",
               "Bälter, Olof",
               "Ban, Yifang",
               "Barman, Linda",
               "Barsoum, Zuheir",
               "Battini, Jean-Marc",
               "Baudry, Benoit",
               "Bayard, Ove",
               "Becker, Matthias",
               "Bejhem, Mats",
               "Bellgran, Monica",
               "Bengtsson, Mats",
               "Ben Slimane, Slimane",
               "Berggren, Björn",
               "Berglund, Lars",
               "Berglund, Per",
               "Berg, Mats",
               "Bertling, Lina",
               "Besenecker, Ute",
               "Beskow, Jonas",
               "Bhattacharya, Prosun",
               "Bjerklöv, Kristian",
               "Björk, Folke",
               "Björklund, Anna",
               "Björkman, Mårten",
               "Blomgren, Henrik",
               "Bodén, Hans",
               "Bogdan, Cristian M",
               "Bohbot, Zeev",
               "Boij, Susann",
               "Boman, Magnus",
               "Borgenstam, Annika",
               "Borgström, Sara",
               "Boström, Henrik",
               "Bradley, Karin",
               "Brandão, Miguel",
               "Brandt, Luca",
               "Braunerhjelm, Pontus",
               "Bresin, Roberto",
               "Brismar, Hjalmar",
               "Brokking Balfors, Berit",
               "Broström, Anders",
               "Brown, Terrence",
               "CAJANDER, Anders",
               "Cappel, Ute B.",
               "Cappel, Ute/Docent",
               "Casanueva, Carlos",
               "Cavdar, Cicek",
               "Ceccato, Vania",
               "Cetecioglu Gurol, Zeynep",
               "Cetecioglu, Zeynep",
               "Chacholski, Wojciech",
               "Chachólski, Wojciech",
               "Chang, Yong Jun",
               "Chatterjee, Saikat",
               "Chen, Dejiu",
               "Chen, De-Jiu",
               "Chen, DeJiu",
               "Chen, Jiajia",
               "Chiu, Justin",
               "Chiu, Justin Ning-Wei",
               "Chiu, Justin NingWei",
               "Chiu, Ningwei Justin",
               "Chunliang, Wang",
               "Claesson, Joachim",
               "Claesson, Per",
               "Colarieti Tosti, Massimiliano",
               "Comber, Rob",
               "Comber, Robert",
               "Cornell, Ann",
               "Cronhjort, Andreas",
               "Cvetkovic, Vladimir",
               "Dahlberg, Leif",
               "Dahlqvist, Patric",
               "Damjanovic, Danijela",
               "Dam, Mads",
               "Dán, György",
               "Danielsson, Mats",
               "Dimarogonas, Dimos V.",
               "Di Rocco, Sandra",
               "Djehiche, Boualem",
               "Dominguez, Isabel",
               "Drugge, Lars",
               "Dubrova, Elena",
               "Duits, Maurice",
               "Edin Grimheden, Martin",
               "Edin, Hans Ezz",
               "Edlund, Ulrica",
               "Ekbäck, Peter",
               "Ekeberg, Örjan",
               "Ek, Monica",
               "Ekstedt, Mathias",
               "Eliasson, Anders",
               "Emmer, Åsa",
               "Engström, Susanne",
               "Engvall, Klas",
               "Engwall, Mats",
               "Engwall, Olov",
               "Enqvist, Per",
               "Eriksson, Andrea",
               "Ersson, Mikael",
               "Fahlstedt, Madelen",
               "Faleskog, Jonas",
               "Fan, Huaan",
               "Farshid, Mana",
               "Feng, Lei",
               "Fernaeus, Ylva",
               "Finne Wistrand, Anna",
               "Finnveden, Göran",
               "Fischione, Carlo",
               "Flierl, Markus",
               "Fodor, Gabor",
               "Fodor, Viktória",
               "Folkesson, Johan",
               "Folkesson, John",
               "Forsberg, Kerstin",
               "Forsgren, Anders",
               "Forsman, Mikael",
               "Fransén, Erik",
               "Franson, Per",
               "Fuglesang, Christer",
               "Furó, István",
               "Fuso Nerini, Francesco",
               "Fuso-Nerini, Francesco",
               "Galjic, Fadil",
               "Gardner, James",
               "Garme, Karl",
               "Gasser, Christian",
               "Gasser, T. Christian",
               "Geschwind, Lars",
               "Ghandari, Mehrdad",
               "Gidofalvi, Gyözö",
               "Girdzijauskas, Sarunas",
               "Glaser, Bjoern",
               "Göransson, Peter",
               "Gräslund, Torbjörn",
               "Grimheden, Martin",
               "Grishenkov, Dmitry",
               "Gröndahl, Fredrik",
               "Guanciale, Roberto",
               "Gudmundsson, Kjartan",
               "Gullberg, Annica",
               "Gulliksen, Jan",
               "Gustafson, Joakim",
               "Gustafsson, Joakim",
               "Gustafsson, Jon Petter",
               "Gustavsson, Johan",
               "Gutierrez-Farewik, Elena",
               "Haas, Tigran",
               "Ha, Claes, Hansson",
               "Hagström, Peter",
               "Håkansson, Anne",
               "Håkansson, Cecilia",
               "Håkansson, Maria",
               "Håkanssson, Maria",
               "Hallén, Anders",
               "Hallström, Stefan",
               "Hammar, Mattias",
               "Hanke, Michael",
               "Hansson, Claes",
               "Haridi, Seif",
               "Hårsman, Björn",
               "Håstad, Johan",
               "Hatef, Madani",
               "Havenvid, Malena",
               "Havenvid, Malena Ingemansson",
               "Hedenqvist, Mikael",
               "Hedenqvist, Mikael S.",
               "Hedman, Anders",
               "Hedström, Peter",
               "Hellgren Kotaleski, Jeanette",
               "Hemani, Ahmed",
               "Herman, Pawel",
               "Hesamzadeh, Mohammad Reza",
               "Hidell, Markus",
               "Hilber, Patrik",
               "Hoffman, Johan",
               "Högfeldt, Anna-Karin",
               "Högselius, Per",
               "Höjer, Mattias",
               "Holgersson, Charlotte",
               "Höök, Kristina",
               "Howells, Mark",
               "Hsieh, Yves",
               "Hult, Henrik",
               "Hu, Xiaoming",
               "Isaksson, Karolina",
               "Isaksson, Teresa",
               "Jacobsen, Elling W.",
               "Jaldén, Joakim",
               "Janerot Sjöberg, Birgitta",
               "Janssen, Anja",
               "Jansson, Magnus",
               "Jayasuriya, Jeevan",
               "Jenelius, Erik",
               "Jensfelt, Patric",
               "Jerbrant, Anna",
               "Jerrelind, Jenny",
               "Johansson, Anders",
               "Johansson, Fredrik",
               "Johansson, Hans",
               "Johansson, Hans Bengt",
               "Johansson, Karl H.",
               "Johansson Landén, Camilla",
               "Johansson, Lars",
               "Johansson, Mats",
               "Johansson, Mikael",
               "Johnson, Magnus",
               "Johnson, Pontus",
               "Jonsson, B. Lars G.",
               "Jonsson, Mats",
               "Jönsson, Pär",
               "Jonsson, Stefan",
               "Kadefors, Anna",
               "Kajko Mattsson, Mira Miroslawa",
               "Kajko-Mattsson, Mira Miroslawa",
               "Källblad Nordin, Sigrid",
               "Kann, Viggo",
               "Kantarelis, Efthymios",
               "Karlgren, Jussi",
               "Karlsson, Bo",
               "Karlsson, Johan",
               "Karlsson, Tomas",
               "Karlström, Anders",
               "Karoumi, Raid",
               "Karrbom Gustavsson, Tina",
               "karvonen, Andrew",
               "Karvonen, Andrew",
               "Kaulio, Matti",
               "Kaulio, Matti A.",
               "Khatiwada, Dilip",
               "Kilander, Fredrik",
               "Kjellström, Hedvig",
               "Kleiven, Svein",
               "Korenivski, Vladislav",
               "Korhonen, Jouni",
               "Korzhavyi, Pavel  A.",
               "Koski, Timo",
               "Kostic, Dejan",
               "Kozma, Cecilia",
               "Kragic, Danica",
               "Kragic Jensfelt, Danica",
               "Kramer Nymark, Tanja",
               "Kramer Nymark, Tanya",
               "Kringos, Nicole",
               "Kristina, Nyström",
               "Kulachenko, Artem",
               "Kullen, Anita",
               "Kumar, Arvind",
               "Kusar, Henrik",
               "Kuttenkeuler, Jacob",
               "Lagergren, Carina",
               "Lagerström, Robert",
               "Landén, Camilla",
               "Lange, Mark",
               "Lansner, Anders",
               "Lantz, Ann",
               "Larsson, Matilda",
               "Larsson, Per-Lennart",
               "Larsson, Stefan",
               "Laumert, Björn",
               "Laure, Erwin",
               "Leander, John",
               "Lennholm, Helena",
               "Li, Haibo",
               "Lindbäck, Leif",
               "Lindbergh, Göran",
               "Lindgren, Monica",
               "Lindström, Mikael",
               "Lindwall, Greta",
               "Linusson, Svante",
               "Lööf, Hans",
               "Lundberg, Joakim",
               "Lundell, Fredrik",
               "Lundevall, Fredrik",
               "Lundgren, Berndt",
               "Lundqvist, Per",
               "Lu, Zhonghai",
               "Lu, Zonghai",
               "Madani, Hatef",
               "Madani Laijrani, Hatef",
               "Madani Larijani, Hatef",
               "Maffei, Antonio",
               "Maguire Jr., Gerald Q.",
               "Malkoch, Michael",
               "Malm, B. Gunnar",
               "Malmquist, Anders",
               "Malmström, Eva",
               "Malmström Jonsson, Eva",
               "Malmström, Maria",
               "Maniette, Louise",
               "Månsson, Daniel",
               "Mariani, Raffaello",
               "Markendahl, Jan",
               "Markendahl, Jan Ingemar",
               "Mårtensson, Jonas",
               "Martinac, Ivo",
               "Martin, Andrew",
               "Martin, Andrew R.",
               "Martinsson, Gustav",
               "Martin, Viktoria",
               "Mats, Bejhem",
               "Matskin, Mihhail",
               "Mats, Nilsson",
               "Mattson, Helena",
               "Mattsson, Helena",
               "Meijer, Sebastiaan",
               "Mendonca Reis Brandao, Miguel",
               "Metzger, Jonathan",
               "m, Helena",
               "Molin, Bengt",
               "Monperrus, Martin",
               "Montelius, Johan",
               "Moreno, Rodrigo",
               "Mörtberg, Ulla",
               "Navarrete Llopis, Alejandra",
               "Nee, Hans-Peter",
               "Nerini, Francesco Fuso",
               "Neumeister, Jonas",
               "Niklaus, Frank",
               "Nilson, Mats",
               "Nilsson, Måns",
               "Nilsson, Mats",
               "NILSSON, MATS",
               "Ning-Wei Chiu, Justin",
               "Nissan, Albania",
               "Nordström, Lars",
               "Norgren, Martin",
               "Norlin, Bert",
               "Norrga, Staffan",
               "Norström, Per",
               "Nuur, Cali",
               "Nybacka, Mikael",
               "Nyquist, Pierre",
               "Nyström, Kristina",
               "Nyström, Kristina",
               "Öberg, Johnny",
               "Odqvist, Joakim",
               "Oechtering, Tobias J.",
               "Olofson, Bo",
               "Olofsson, Bo",
               "Olsson, Håkan",
               "Olsson, Jimmy",
               "Olsson, Mårten",
               "Olsson, Monika",
               "Olssonn, Monika",
               "Ölundh Sandström, Gunilla",
               "Onori, Mauro",
               "O'Reilly, Ciarán J.",
               "Orhan, Ibrahim",
               "Österling, Lisa",
               "Östlund, Sören",
               "Östlund, Sörenn",
               "Otero, Evelyn",
               "Packendorff, Johann",
               "Palm, Björn",
               "Papadimitratos, Panagiotis",
               "Pargman, Daniel",
               "Pauletto, Sandra",
               "Pavlenko, Tatjana",
               "Payberah, Amir H.",
               "Pears, Arnold",
               "Peter Ekbäck,",
               "Petrie-Repar, Paul",
               "Petrova, Marina",
               "Petrov, Miroslav",
               "Pettersson, Lars",
               "Plaza, Elzbieta",
               "Pontus, Braunerhjelm",
               "Quevedo-Teruel, Oscar",
               "Rashid, Amid",
               "Rashid, Amir",
               "Rasmussen, Lars Kildehöj",
               "Riml, Joakim",
               "Ringertz, Ulf",
               "Ritzén, Sofia",
               "Rodriguez, Saul",
               "Rojas, Cristian R.",
               "Romero, Mario",
               "Rönngren, Robert",
               "Rosén, Anders",
               "Rosenqvist, Christopher",
               "Roxhed, Niclas",
               "Rundgren, Carl-Johan",
               "Runting, Helen",
               "Rusu, Ana",
               "Rutland, Mark W.",
               "Said, Elias",
               "Sallnäs, Eva-Lotta",
               "Sander, Ingo",
               "Säve-Söderbergh, Per Jörgen",
               "Savolainen, Peter",
               "Sawalha, Samer",
               "Scheffel, Jan",
               "Schlatter, Philipp",
               "Schnelli, Kevin",
               "Schulte, Christian",
               "Scolamiero, Martina",
               "Selleby, Malin",
               "Sellgren, Ulf",
               "Semere, Daniel",
               "Shirabe, Takeshi",
               "Silfwerbrand, Johan",
               "Silveira, Semida",
               "Sjödin, Peter",
               "Sjögren, Anders",
               "Sjöland, Thomas",
               "Sjöland, Tomas",
               "Slimane, Ben",
               "Smedby, Örjan",
               "Smith, Mark",
               "Smith, Mark T.",
               "Solus, Liam",
               "Sörensson, Tomas",
               "Stadler, Rolf",
               "Ståhlgren, Stefan",
               "Ståhl, Patrik",
               "Stenbom, Stefan",
               "Stenius, Ivan",
               "Sturm, Bob",
               "Subasic, Nihad",
               "Sundberg, Cecilia",
               "Swalaha, Samer",
               "Ternström, Sten",
               "Tesfamariam Semer, Daniel",
               "Tesfamariam Semere, Daniel",
               "Thobaben, Ragnar",
               "Thottappillil, Rajeev",
               "Tibert, Gunnar",
               "Tilliander, Anders",
               "Tisell, Claes",
               "Tollmar, Konrad",
               "Törngren, Martin",
               "Troubitsyna, Elena",
               "Ulfvengren, Pernilla",
               "Uppvall, Lars",
               "Urban, Frauke",
               "Urciuoli, Luca",
               "Usher, William",
               "Vania, Ceccato",
               "van Maris, Antonius",
               "Vanourek, Gregg",
               "Västberg, Anders",
               "Viklund, Fredrik",
               "Viklund, Martin",
               "Vilaplana, Francisco",
               "Vinuesa, Ricardo",
               "Viveka, Palm",
               "Vlassov, Vladimir",
               "Vogt, Ulrich",
               "Wågberg, Lars",
               "Wahl, Anna",
               "Wahlberg, Bo",
               "Wålinder, Magnus",
               "Wallmark, Oskar",
               "Wang, Chunliang",
               "Wang, Lihui",
               "Wang, Xi Vincent",
               "Weinkauf, Tino",
               "Wennerholm, Malin",
               "Wennhage, Per",
               "Westlund, Hans",
               "Wikander, Jan",
               "Wiklund, Martin",
               "Wiktorsson, Magnus",
               "Willén, Jonas",
               "Wingård, Lars",
               "Wingård, Lasse",
               "Wingquist, Erik",
               "W. Lange, Mark",
               "W.Lange, Mark",
               "Wörman, Anders",
               "Xiao, Ming",
               "Zetterling, Carl-Mikael",
               "Zhou, Qi",
               "Zwiller, Val"]


def main():
       global Verbose_Flag
       global Use_local_time_for_output_flag
       global Force_appointment_flag

       Use_local_time_for_output_flag=True

       parser = optparse.OptionParser()

       parser.add_option('-v', '--verbose',
                         dest="verbose",
                         default=False,
                         action="store_true",
                         help="Print lots of output to stdout"
       )

       parser.add_option('-a', '--account',
                         dest="account",
                         default=False,
                         action="store_true",
                         help="Apply grading scheme to indicated account"
       )

       parser.add_option('-f', '--force',
                         dest="force",
                         default=False,
                         action="store_true",
                         help="Replace existing grading scheme"
       )

       parser.add_option('-t', '--testing',
                         dest="testing",
                         default=False,
                         action="store_true",
                         help="execute test code"
       )

       parser.add_option("--config", dest="config_filename",
                         help="read configuration from FILE", metavar="FILE")



       options, remainder = parser.parse_args()

       Verbose_Flag=options.verbose
       Force_Flag=options.force

       if Verbose_Flag:
              print('ARGV      :', sys.argv[1:])
              print('VERBOSE   :', options.verbose)
              print('REMAINING :', remainder)
              print("Configuration file : {}".format(options.config_filename))

       course_or_account=True
       if options.account:
              course_or_account=False
       else:
              course_or_account=True

       if Verbose_Flag:
              print("Course or account {0}: course_or_account = {1}".format(options.account,
                                                                            course_or_account))

       if (not options.testing) and (len(remainder) < 4):
              print("Insuffient arguments must provide a course_id|account_id cycle_number school_acronym course_code\n")
              return
       if (options.testing) and (len(remainder) < 3):
              print("Insuffient arguments must provide a course_id|account_id cycle_number school_acronym\n")
              return

       initialize(options)

       canvas_course_id=remainder[0]
       if Verbose_Flag:
              if course_or_account:
                     print("course_id={0}".format(canvas_course_id))
              else:
                     print("account_id={0}".format(canvas_course_id))

       cycle_number=remainder[1] # note that cycle_number is a string with the value '1' or '2'
       school_acronym=remainder[2]

       if (not options.testing):
              course_code=remainder[3]

       inputfile_name="course-data-{0}-cycle-{1}.json".format(school_acronym, cycle_number)
       try:
              with open(inputfile_name) as json_data_file:
                     all_data=json.load(json_data_file)
       except:
              print("Unable to open course data file named {}".format(inputfile_name))
              print("Please create a suitable file by running the program get-degree-project-course-data.py")
              sys.exit()
                   
       cycle_number_from_file=all_data['cycle_number']
       school_acronym_from_file=all_data['school_acronym']
       if not ((cycle_number_from_file == cycle_number) and (school_acronym_from_file == school_acronym)):
              print("mis-match between data file and arguments to the program")
              sys.exit()

       programs_in_the_school_with_titles=all_data['programs_in_the_school_with_titles']
       dept_codes=all_data['dept_codes']
       all_course_examiners=all_data['all_course_examiners']

       canvas_grading_standards=dict()
       available_grading_standards=get_grading_standards(True, canvas_course_id)
       if available_grading_standards:
              for s in available_grading_standards:
                     old_id=canvas_grading_standards.get(s['title'], None)
                     if old_id and s['id'] < old_id: # use only the highest numbered instance of each scale
                            continue
       else:
              canvas_grading_standards[s['title']]=s['id']
              if Verbose_Flag:
                     print("title={0} for id={1}".format(s['title'], s['id']))

       if Verbose_Flag:
              print("canvas_grading_standards={}".format(canvas_grading_standards))

       if (options.testing):
              potential_grading_standard_id=canvas_grading_standards.get("All examiners", None)
              if Force_Flag or (not potential_grading_standard_id):
                     name="All examiners"
                     scale=[]
                     all_examiners=set()
                     for course in all_course_examiners:
                            for examiner in all_course_examiners[course]:
                                   all_examiners.add(examiner)

                     # the following is for extreme testing
                     # all_examiners=kth_examiners

                     number_of_examiners=len(all_examiners)
                     print("number_of_examiners={}".format(number_of_examiners))

                     index=0
                     for e in sorted(all_examiners):
                            i=number_of_examiners-index
                            d=dict()
                            d['name']=e
                            d['value'] =(float(i)/float(number_of_examiners))*100.0
                            print("d={0}".format(d))
                            scale.append(d)
                            index=index+1
                     scale.append({'name': 'none selected', 'value': 0.0})

                     print("scale is {}".format(scale))
                     status=create_grading_standard(course_or_account, canvas_course_id, name, scale)
                     print("status={0}".format(status))
                     if Verbose_Flag and status:
                            print("Created new grading scale: {}".format(name))

       else:
              potential_grading_standard_id=canvas_grading_standards.get(course_code, None)
              if Force_Flag or (not potential_grading_standard_id):
                     name=course_code
                     scale=[]
                     number_of_examiners=len(all_course_examiners[course_code])
                     index=0
                     for e in all_course_examiners[course_code]:
                            i=number_of_examiners-index
                            d=dict()
                            d['name']=e
                            d['value'] =(float(i)/float(number_of_examiners))*100.0
                            print("d={0}".format(d))
                            scale.append(d)
                            index=index+1
                     scale.append({'name': 'none selected', 'value': 0.0})

                     status=create_grading_standard(course_or_account, canvas_course_id, name, scale)
                     print("status={0}".format(status))
                     if Verbose_Flag and status:
                            print("Created new grading scale: {}".format(name))

if __name__ == "__main__": main()
