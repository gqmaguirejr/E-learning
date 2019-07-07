# coding: utf-8
#
# Program to help an examiner to:
# claim students to be examiner for,
# assign adviser,
# announce a degree project presenations, and
# report a thesis in DiVA.
#
#
require 'sinatra'
require 'json'
require 'httparty'
require 'oauth'
require 'oauth/request_proxy/rack_request'
require 'date'
require 'nitlink'
require 'net/http'
require 'pg'                    # required to access the database of TRITA assignments
require 'net/http/post/multipart'
require 'open-uri'

set :port, 3597                   # an port to use
load 'sinatra_ssl.rb'
set :ssl_certificate, "/home/maguire/certificates_for_canvas_docker/server.crt"
set :ssl_key, "/home/maguire/certificates_for_canvas_docker/server.key"

$link_parser = Nitlink::Parser.new # for use with paginated replies

$oauth_key = "test"
$oauth_secret = "secret"

# mark the student's selection of potential examiner with ⚠⚠
$potential_marker="⚠⚠"
$limited_choices_maker="⚄⚄"

$with_contraints=true           # determine the course/program file to be read

config = JSON.parse(File.read('config.json'))
#puts "config: #{config}"

access_token = config['canvas']['access_token']
#puts "access_token: #{access_token}"

host = config['canvas']['host']
puts "host: #{host}"

# a global variable to help the hostname
$canvas_host=host

$header = {'Authorization': 'Bearer ' "#{access_token}", 'Content-Type': 'application/json', 'Accept': 'application/json'}
puts "$header: #{$header}"

disable :protection
# enable sessions so we can remember the launch info between http requests, as
# the user takes the assessment
enable :sessions

$eecs_meeting_rooms=[
'csc_lv24_522 Fantum, Lindstedtsvägen 24',
'csc_lv24_527 F0, Lindstedtsvägen 24',
'csc_lv3_1440 Biblioteket, Lindstedtsvägen 3',
'csc_lv3_1448, Lindstedtsvägen 3',
'csc_lv3_1535, Lindstedtsvägen 3',
'csc_lv3_1537, Lindstedtsvägen 3',
'csc_lv3_1625, Lindstedtsvägen 3',
'csc_lv5_4423, Lindstedtsvägen 5',
'csc_lv5_4523, Lindstedtsvägen 5',
'csc_lv5_4532, Lindstedtsvägen 5',
'csc_lv5_4632 Usability, Lindstedtsvägen 5',
'csc_lv5_4633 MoCap, Lindstedtsvägen 5',
'csc_tmh_139 Källarstudion, Lindstedtsvägen 24',
'csc_tmh_431a Nedre biblioteket, Lindstedtsvägen 24',
'csc_tmh_503 Övre biblioteket, Lindstedtsvägen 24',
'csc_tmh_535 Seminarierummet, Lindstedtsvägen 24',
'csc_tr14_523, Teknikringen 14',
#'csc_vc_webmeet',
'eecs_control_meetingroom_center, Malvinas backe 10, plan 6',
'eecs_control_meetingroom_entrance, Malvinas backe 10, plan 6',
'eecs_ov10_a822_studentrum, Malvinas backe 10',
'eecs_ov10_plan2_a213, Malvinas backe 10 plan2',
'eecs_ov10_plan4_motesrum, Malvinas backe 10',
'eecs_ov10_plan5_motesrum, Malvinas backe 10, plan 5',
'eecs_ov10_plan8_motesrum, Malvinas backe 10',
'eecs_ov10_sip_conferenceroom, Malvinas backe 10',
'eecs_ov6_plan5_motesrum, Malvinas backe 6',
'eecs_tr29_meetingroom_studentworkshop, Teknikringen 29',
'eecs_tr29_rum_5409, Teknikringen 29, rum 5409',
'eecs_tr31_gretawoxen, Teknikringen 31',
'eecs_tr31_gustafdahlander, Teknikringen 31',
'eecs_tr33_annicatiger, Teknikringen 33, plan 3, rum 2315',
'eecs_tr33_datorsal_frances_hugle, Teknikringen 33, Plan 3, rum 2314',
'eecs_tr33_goranandersson, Teknikringen 33, Plan 4 rum 3418',
'eecs_tr33_janisbubenko, Teknikringen 33, Plan 4 rum 3439',
'eecs_tr33_stenvelander, Teknikringen 33, Plan 4 rum 3412',
'eecs_tr35_4437, Teknikringen 35',
'ict_adele (4), Kistagången 16, East, Floor 4',
'ict_aktivitetsrum, Kistagången 16, West, Floor 3',
'ict_alain (8), Kistagången 16, East, Floor 4',
'ict_alonzo (10), Kistagången 16, East, Floor 4',
'ict_amiga (20), Kistagången 16, West, Floor 3',
'ict_atari (6), Kistagången 16, West, Floor 3',
'ict_commodore_64 (10), Kistagången 16, West, Floor 3',
'ict_darlington (18), Kistagången 16, West, Floor 4',
'ict_early (8), Kistagången 16, West, Floor 4',
'ict_grimeton (14), Kistagången 16, East, Floor 4',
'ict_grove (12), Kistagången 16, West, Floor 4',
#'ICT_KANSLI_F7309',
'ict_ledningscentralen (20), Kistagången 16, West, Floor 3',
'ict_lounge, Isafjordsgatan',
'ict_moore (16), Kistagången 16, West, Floor 2',
'ict_motala (14), Kistagången 16, East, Floor 4',
'ict_palo_alto (8), Kistagången 16, East, Floor 4',
'ict_reno (6), Kistagången 16, East, Floor 4',
#'ICT_STUD_KISTAN',
'ict_tahoe (10), Kistagången 16, East, Floor 4'
]

# get configuration data',
if $with_contraints
  all_data=JSON.parse(File.read('course-data-EECS-cycle-2c.json'))
else
  all_data=JSON.parse(File.read('course-data-EECS-cycle-2.json'))
end

cycle_number=all_data['cycle_number']
puts "cycle_number is #{cycle_number} and it has class #{cycle_number.class}"
$school_acronym=all_data['school_acronym']
puts "school_acronym is #{$school_acronym}"


programs_in_the_school_with_titles=all_data['programs_in_the_school_with_titles']

def programs_in_cycle(cycle_number, programs)
  cycle=cycle_number.to_i
  #puts("in programs_in_cycle cycle is #{cycle}")
  relevant_programs={}
  #puts("programs is #{programs}")
  programs.each do |prog_code, prog_value| # you have to iterate this way as programs is a hash
    #puts("prog_code is #{prog_code}")
    #puts("prog_value is #{prog_value}")
    @program_name = prog_code
    #puts("@program_name is #{@program_name}")
    @credits = programs[@program_name]['credits'].to_i
    #puts("@credits is #{@credits}")
    @title_sv = programs[@program_name]['title_sv']

    if (@credits >= 270) and ((cycle == 1) or (cycle == 2))
      #puts("Found Civ. ing. program")
      relevant_programs[prog_code]=prog_value
    elsif (@credits == 180) and (cycle == 1)
      #puts("Found Hög. ing. program")
      relevant_programs[prog_code]=prog_value
    elsif (@credits == 120) and (cycle == 2)
      relevant_programs[prog_code]=prog_value
    elsif (@credits == 30) and (cycle == 0)
      relevant_programs[prog_code]=prog_value
    elsif (@credits == 60) and (cycle == 0) and (@title_sv.include? 'Tekniskt basår')
      relevant_programs[prog_code]=prog_value
    elsif (@credits == 60) and (cycle == 0) and (@title_sv.include? 'Tekniskt basår')
      relevant_programs[prog_code]=prog_value
    elsif (@credits == 60) and (cycle == 2) and (@title_sv.include? 'Magisterprogram')
      relevant_programs[prog_code]=prog_value
    else
      # nothing to do
    end
  end
  return relevant_programs
end

# filter out the programs that are not at the desired cucle
$programs_in_the_school_with_titles=programs_in_cycle(cycle_number, programs_in_the_school_with_titles)
#puts("filtered $programs_in_the_school_with_titles is #{$programs_in_the_school_with_titles}")

$dept_codes=all_data['dept_codes']
$all_course_examiners=all_data['all_course_examiners']
AF_courses=all_data['AF_courses']
PF_courses=all_data['PF_courses']
$relevant_courses_English=all_data['relevant_courses_English']
$relevant_courses_Swedish=all_data['relevant_courses_Swedish']
if $with_contraints
  $PF_course_codes_by_program=all_data['PF_course_codes_by_program']
  #puts("$PF_course_codes_by_program is #{$PF_course_codes_by_program}")
  $AF_course_codes_by_program=all_data['AF_course_codes_by_program']
  #puts("$AF_course_codes_by_program is #{$AF_course_codes_by_program}")
end

def list_custom_columns(course_id)
  custom_columns_found=[]
  # Use the Canvas API to get the list of custom column for this course
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns"
  puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header )
  #puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  links = $link_parser.parse(@getResponse)
  if links.empty?                  # if not paginated, simply return the result of the request
    return @getResponse
  end

  # there was a paginated response
  @getResponse.parsed_response.each do |r|
    custom_columns_found.append(r)
  end

  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      custom_columns_found.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  return custom_columns_found
end

def lookup_column_number(column_name, list_of_existing_columns)
  list_of_existing_columns.each do |col|
    #puts("col: #{col}")
    if col['title'] == column_name
      return col['id']
    end
  end
  return -1
end

def get_custom_column_entries_all(course_id, column_name, list_of_existing_columns)
  # extended to handle paginated responses
  column_entries=[]
  @column_number=lookup_column_number(column_name, list_of_existing_columns)
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #GET /api/v1/courses/:course_id/custom_gradebook_columns/:id/data
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{@column_number}/data"
  #puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header )
  #puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  links = $link_parser.parse(@getResponse)
  #puts("in get_grade_for_assignment links is #{links}")

  if links.empty?                  # if not paginated, simply return the result of the request
    column_entries=@getResponse.parsed_response
  else
    # there was a paginated response
    @getResponse.parsed_response.each do |r|
      column_entries.append(r)
    end

    while links.by_rel('next')
      lr=links.by_rel('next').target
      #puts("links.by_rel('next').target is #{lr}")
      @getResponse= HTTParty.get(lr, :headers => $header )
      #puts("next @getResponse is #{@getResponse}")
      @getResponse.parsed_response.each do |r|
        column_entries.append(r)
      end

      links = $link_parser.parse(@getResponse)
    end
  end

  return column_entries
end

def get_custom_column_entries(course_id, column_name, user_id, list_of_existing_columns)
  # extended to handle paginated responses
  column_entries=[]
  @column_number=lookup_column_number(column_name, list_of_existing_columns)
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #GET /api/v1/courses/:course_id/custom_gradebook_columns/:id/data
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{@column_number}/data"
  #puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header )
  #puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  links = $link_parser.parse(@getResponse)
  #puts("in get_grade_for_assignment links is #{links}")

  if links.empty?                  # if not paginated, simply return the result of the request
    column_entries=@getResponse.parsed_response
  else
    # there was a paginated response
    @getResponse.parsed_response.each do |r|
      column_entries.append(r)
    end

    while links.by_rel('next')
      lr=links.by_rel('next').target
      #puts("links.by_rel('next').target is #{lr}")
      @getResponse= HTTParty.get(lr, :headers => $header )
      #puts("next @getResponse is #{@getResponse}")
      @getResponse.parsed_response.each do |r|
        column_entries.append(r)
      end

      links = $link_parser.parse(@getResponse)
    end
  end

  column_entries.each do |u|
    #puts("u is #{u}")
    #puts("u['user_id'] is #{u['user_id']}")
    if u['user_id'].to_i == user_id.to_i
      entry=u['content']
      #puts("u['content'] is #{entry}")
      return u['content'].strip
    end
  end
  return []
end

def put_custom_column_entries_by_name(course_id, column_name, user_id, data_to_store, list_of_existing_columns)
  @column_number=lookup_column_number(column_name, list_of_existing_columns)
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #PUT /api/v1/courses/:course_id/custom_gradebook_columns/:id/data/:user_id

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{@column_number}/data/#{user_id}"
  #puts "@url is #{@url}"
  #puts("data_to_store is #{data_to_store} and of class #{data_to_store.class}")

  @payload={'column_data': {'content': data_to_store}}
  puts("@payload is #{@payload}")
  @putResponse = HTTParty.put(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  puts("custom columns putResponse.code is  #{@putResponse.code} and putResponse is #{@putResponse}")
  return @putResponse
end

def put_custom_column_entry(course_id, column_number, user_id, data_to_store)
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #PUT /api/v1/courses/:course_id/custom_gradebook_columns/:id/data/:user_id

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{column_number}/data/#{user_id}"
  #puts "@url is #{@url}"
  #puts("data_to_store is #{data_to_store} and of class #{data_to_store.class}")

  @payload={'column_data': {'content': data_to_store}}
  puts("@payload is #{@payload}")
  @putResponse = HTTParty.put(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  puts("custom columns putResponse.code is  #{@putResponse.code} and putResponse is #{@putResponse}")
  return @putResponse
end

def   filter_courses_for_a_program(program_code, cycle_number, grading_scale, courses)
  cycle_code='cycle'+cycle_number
  puts("cycle_code is #{cycle_code}")

  relevant_courses=[]
  if $with_contraints
    if grading_scale == 'AF'
      relevant_course_codes=$AF_course_codes_by_program[cycle_code][program_code]
    else
      relevant_course_codes=$PF_course_codes_by_program[cycle_code][program_code]
    end

    if not relevant_course_codes
      puts("no relevant course codes found for #{program_code} in cycle #{cycle_number}")
      return courses            # if there are no course codes, then do not filter
    end

    puts("relevant course_codes for #{program_code} in cycle #{cycle_number} are #{relevant_course_codes}")

    courses.each do |course_code| # you have to iterate this way as programs is a hash
      puts("course_code is #{course_code}")
      if relevant_course_codes.include?(course_code)
        relevant_courses << course_code
      end
    end

    puts("relevant #{grading_scale} courses for #{program_code} in cycle #{cycle_number} are #{relevant_courses}")
    if relevant_courses.length > 0
      return relevant_courses
    else
      return courses            # if there are no course codes left, then do not filter
    end
  else                          #  if not $with_contraints do not filter
    return courses
  end
end 

def list_assignments(course_id)
  assignments=[]
  # Use the Canvas API to get the list of assignments for the course
  #GET /api/v1/courses/:course_id/assignments
  @url_to_use = "http://#{$canvas_host}/api/v1/courses/#{course_id}/assignments"
  puts("url_to_use is #{@url_to_use}")
  @getResponse = HTTParty.get(@url_to_use, :headers => $header )
  # puts("assignments request response is: #{@getResponse}")
  # puts("assignments request response.response is: #{@getResponse.response}")
  # puts("assignments request response.headers is: #{@getResponse.headers}")
  links = $link_parser.parse(@getResponse)
  if links.empty?                  # if not paginated, simply return the result of the request
    return @getResponse
  end

  # there was a paginated response
  @getResponse.parsed_response.each do |r|
    assignments.append(r)
  end

  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      assignments.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  #puts("Assignments in course #{course_id} are #{assignments}")
  return assignments
end


def get_submission(course_id, assignment_id, user_id)
  submissions=[]
  # Use the Canvas API to get the submission of a uuser for a specifici assignment in a course
  #GET /api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id
  @url_to_use = "http://#{$canvas_host}/api/v1/courses/#{course_id}/assignments/#{assignment_id}/submissions/#{user_id}"
  puts("url_to_use is #{@url_to_use}")
  @getResponse = HTTParty.get(@url_to_use, :headers => $header )
  puts("Student submission is: #{@getResponse}")
  links = $link_parser.parse(@getResponse)
  if links.empty?                  # if not paginated, simply return the result of the request
    return @getResponse
  end

  # there was a paginated response

  @getResponse.parsed_response.each do |r|
    submissions.append(r)
  end


  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      submissions.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  return submissions
end

def get_grade_for_assignment(course_id, assignment_id, user_id)
  grades_for_assignment=[]
  # Use the Canvas API to get assigned grade for an assignment
  #GET /api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id
  # Request Parameters:
  # include[] string	Associations to include with the group.
  #                   Allowed values: submission_history, submission_comments, rubric_assessment, visibility, course, user
  @url_to_use = "http://#{$canvas_host}/api/v1/courses/#{course_id}/assignments/#{assignment_id}/submissions/#{user_id}"
  @payload={:include => ['submission_comments']}
  puts("@payload is #{@payload}")
  @getResponse = HTTParty.get(@url_to_use, 
                              :body => @payload.to_json,
                              :headers => $header )
  links = $link_parser.parse(@getResponse)
  #puts("in get_grade_for_assignment links is #{links}")

  if links.empty?                  # if not paginated, simply return the result of the request
    puts("in get_grade_for_assignment for non-paginated response")
    return @getResponse
  end

  # there was a paginated response
  @getResponse.parsed_response.each do |r|
    grades_for_assignment.append(r)
  end

  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      grades_for_assignment.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  return grades_for_assignment
end
    
def list_peer_review_assignments(course_id, assignment_id)
  peer_review_assignments=[]
  # Use the Canvas API to get the list of peer reviewing assignments
  # a given assignment for a course:
  #GET /api/v1/courses/:course_id/assignments/:assignment_id/peer_reviews
  @url_to_use = "http://#{$canvas_host}/api/v1/courses/#{course_id}/assignments/#{assignment_id}/peer_reviews"
  puts("url_to_use is #{@url_to_use}")
  @getResponse = HTTParty.get(@url_to_use, :headers => $header )
  puts("list_peer_review_assignments request response is: #{@getResponse}")
  # puts("assignments request response.response is: #{@getResponse.response}")
  # puts("assignments request response.headers is: #{@getResponse.headers}")
  links = $link_parser.parse(@getResponse)
  if links.empty?                  # if not paginated, simply return the result of the request
    return @getResponse
  end

  # there was a paginated response
  @getResponse.parsed_response.each do |r|
    peer_review_assignments.append(r)
  end

  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      peer_review_assignments.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  return peer_review_assignments
end


def create_announcement(course_id, title, message)
  # Use the Canvas API to create a discussion topic item of type: is_announcement
# POST /api/v1/courses/:course_id/discussion_topics

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/discussion_topics"
  puts "@url is #{@url}"
  @payload={'title': title,
            'message': message,
            'published': 'true',
            'is_announcement': 'true'
           }
  puts("@payload is #{@payload}")
  @postResponse = HTTParty.post(@url,
                              :body => @payload.to_json,
                              :headers => $header )
  puts(" POST to create an announcement has Response.code is  #{@postResponse.code} and postResponse is #{@postResponse}")
  return @postResponse
end


def create_calendar_event(user_id, date, title, description)
  # Use the Canvas API to create a calendar event
  # POST /api/v1/calendar_events
  context_code="user_#{user_id}"
  puts("context_code=#{context_code}")
  localtime=Time.now
  date_time_start=DateTime.iso8601(date, Date::ENGLAND) # DateTime
  date_time_start.new_offset(localtime.zone)
  date_time_end=date_time_start
  puts("date_time_start is #{date_time_start}")

  @url = "http://#{$canvas_host}/api/v1/calendar_events?as_user_id=#{user_id}"
  puts "@url is #{@url}"
  @payload={'calendar_event': {
                               'context_code': context_code,
                               'title': title,
                               'description': description,
                               'start_at': date_time_start,
                               'end_at':   date_time_end
                              }
           }
  puts("@payload is #{@payload}")
  @postResponse = HTTParty.post(@url,
                              :body => @payload.to_json,
                              :headers => $header )
  puts(" POST to create a calendar has Response.code is  #{@postResponse.code} and postResponse is #{@postResponse}")
  return @postResponse
end




def extract_thesis_info_pdf(authors, url)
  thesis_info={'title' => 'A fake title for a fake thesis',
               'subtitle' => 'A short subtitle',
               'en_abstract' => '''This is a long multiple line English abstract. It should ultimately be: This fake research seeks to find out whether apples fall under gravity. The project assumes that the apple tree is located at sea-level on the equator and the force of gravity is fix to a constant. An apple was released from a branch by cutting the its stem with a laser – so as not to introduce any forces on the apple other than gravity.
The experiment was repeated 100 time and a high speed camera (1000 frames per second) was used to record the apple’s fall. A calibrated scale traceable to the U.S. Bureau of Fake Weights and Standards was placed parallel to the apple’s path and included in the images. The scale was carefully aligned to that it was normal to the earth. The results show that apples to fall under the influence of gravity and that the measured force was constant and equal to g. The apples that were used in the experiment were made into an apple pie so as not to waste them.''',
               'en_keywords' => 'English keywords',
               'sv_abstract' => 'Swedish abstract',
               'sv_keywords' => 'Swedish keywords',
              }
  return thesis_info
end

#from spreadsheet: FÖRFATTARE, PERSONNR, FÖRFATTARE EMAIL, KOMMENTARER, PROGRAM, PUB, KURS, EXAMINATOR, EXAMINATOR EMAIL, HANDLEDARE, HANDLEDARE EMAIL, START (of project), PDF (available - flag), BETYG (graded A-F or P/F flag), PUBLICERAD I DIVA (flag), TRITA GAVS UT (date TRITA was assigned), AV (assigned by)
def get_TRITA_string(school, thesis_other_flag, year, authors, title, examiner)
  con = PG.connect :hostaddr => "172.18.0.2", :dbname => 'trita', :user => 'postgres'
  #con = PG.connect :host => "postgress.canvas.docker", :dbname => 'trita', :user => 'postgres'
  #puts con.server_version

  database_table_name="#{school}_trita_for_thesis_#{year}"
  # create the table if it does not exist
  rs=con.exec "CREATE TABLE IF NOT EXISTS #{database_table_name} (
       -- make the 'id' column a primary key; this also creates
       -- a UNIQUE constraint and a b+-tree index on the column
       id    SERIAL PRIMARY KEY,
       authors  TEXT,
       title    TEXT,
       examiner TEXT)"

  authors_str=authors.join(" and ")
  rs=con.exec "INSERT INTO #{database_table_name}(authors, title, examiner) VALUES ('#{authors_str}', '#{title}', '#{examiner}') RETURNING id"
  #puts(rs[0])
  id=rs[0]['id']

  prefixes={
    'ABE' => 'TRITA-ABE-MBT',
    'CBH' => 'TRITA-CBH-GRU',
    'EECS' => 'TRITA-EECS-EX',
    'ITM' => 'TRITA-ITM-EX',
    'SCI' => 'TRITA-SCI-GRU'
  }
  school_prefix=prefixes[school]
  puts("school_prefix is #{school_prefix}")
  trita_string="#{school_prefix}-#{year}:#{id}"
  return trita_string
end

def select_from_list_by_name(target_name, full_list)
  full_list.each do |elem|
    if elem['name'] == target_name
      return elem
    end
  end
end

def make_cover(cover_language, cycle_number, year_of_thesis,  cover_degree, cover_exam, cover_area, cover_school, authors, thesis_info_title, thesis_info_subtitle, trita_string)
  
  # @result = HTTParty.post(@urlstring_to_post.to_str, 
  #                         :body => { :degree => cover_degree,
  #                                    :exam => cover_exam,
  #                                    :area => cover_area,
  #                                    :title => thesis_info_title, 
  #                                    :secondaryTitle => thesis_info_subtitle,
  #                                    :author => authors,
  #                                    :trita => trita_string,
  #                                    :year => year_of_thesis
  #                                  }.to_json,
  #                         :headers => { 'Content-Type' => "multipart/form-data" } ) ¤ 'application/json'

  uri_for_cover = URI("https://intra.kth.se/kth-cover/kth-cover.pdf")
  n = Net::HTTP.new(uri_for_cover.host, uri_for_cover.port)
  n.use_ssl =  (uri_for_cover.scheme == 'https')
  #n.set_debug_output($stdout)

  if cover_language == 'English'
    cover_area = cover_area[:en]
    cover_school = cover_school[:en]
  else
    cover_area = cover_area[:sv]
    cover_school = cover_school[:sv]
  end
  
  parm={:degree => cover_degree,
        :exam => cover_exam,
        :area => cover_area,
        :school => cover_school,
        :year => year_of_thesis,
        :title=> thesis_info_title,
        :secondaryTitle => thesis_info_subtitle,
        :author => authors,
        :trita => trita_string,
        :model=>"1337-brynjan!"}

  puts("parm is #{parm}")
  req = Net::HTTP::Post::Multipart.new(uri_for_cover, parm)
  if cover_language == 'English'
    puts("Make English cover")
    req['Referer']="https://intra.kth.se/kth-cover?l=en"
    req['Origin']='https://intra.kth.se'
    req['Cookie'] = "PLAY_LANG=en"
  else
    puts("Make Swedish cover")
    req['Referer']="https://intra.kth.se/kth-cover"
    req['Origin']='https://intra.kth.se'
    req['Cookie'] = "PLAY_LANG=sv"
  end

  req['Accept-Encoding']="gzip, deflate, br"
  req['Accept-Language']="en-US,en;q=0.9"
  req['Accept']="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"

  res = n.start do |http|
    result = http.request(req) # Net::HTTPResponse object
    puts("post to create course cover returned #{result}")
    puts("result.code is #{result.code}")
    puts("cookie = #{result['Set-Cookie']}")
    puts("result is #{result}")
    puts("Content-Disposition is #{result['Content-Disposition']}")
    puts("result.body.length is #{result.body.length}")
    #file = File.open("test1.pdf", "w")
    #file.puts("#{result.body}")
    #file.close

    return result.body
  end
  
end

def sections_in_course(course_id)
  sections_found_thus_far=[]
  # Use the Canvas API to get the list of sections for this course
  #GET /api/v1/courses/:course_id/sections

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/sections"
  #puts "@url is #{@url}"

  @getResponse = HTTParty.get(@url, :headers => $header )
  #puts("sections getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  links = $link_parser.parse(@getResponse)
  if links.empty?                  # if not paginated, simply return the result of the request
    return @getResponse
  end

  # there was a paginated response
  @getResponse.parsed_response.each do |r|
    sections_found_thus_far.append(r)
  end

  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      sections_found_thus_far.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  return sections_found_thus_far
end

def create_section_in_course(course_id, section_name)
  # Use the Canvas API to create a new section in the course
  #POST /api/v1/courses/:course_id/sections
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/sections"
  #puts "@url is #{@url}"

  @payload={'course_section': {'name': section_name}}
  puts("@payload is #{@payload}")
  @putResponse = HTTParty.post(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  puts("create section POST Response.code is  #{@putResponse.code} and putResponse is #{@putResponse}")
  return @putResponse
end


def section_with_name(course_id, existing_sections, target_section_name)
  existing_sections.each do |s|
    if (s['name'] == target_section_name)
        return s['id']
    end
  end
  # otherwise there is no such section - so create one
  new_section=create_section_in_course(course_id, target_section_name)
  return new_section['id']
end

def section_id_with_name(target_section_name, existing_sections)
  existing_sections.each do |s|
    if (s['name'] == target_section_name)
        return s['id']
    end
  end
end


def enroll_user_in_section(course_id, user_id, role, section_id)
  # Request Parameters:
  #Parameter		Type	Description
  # enrollment[user_id]	Required	string	The ID of the user to be enrolled in the course.
  # enrollment[type]	Required	string	Enroll the user as a student, teacher, TA, observer, or designer. If no value is given, the type will be inferred by enrollment if supplied, otherwise 'StudentEnrollment' will be used.
  #                                           Allowed values:
  #                                            StudentEnrollment, TeacherEnrollment, TaEnrollment, ObserverEnrollment, DesignerEnrollment
  # enrollment[enrollment_state]		string	If set to 'active,' student will be immediately enrolled in the course. Otherwise they will be required to accept a course invitation. Default is 'invited.'.
  # If set to 'inactive', student will be listed in the course roster for teachers, but will not be able to participate in the course until their enrollment is activated.
  #                                           Allowed values: active, invited, inactive
  # enrollment[notify]		boolean	If true, a notification will be sent to the enrolled user. Notifications are not sent by default.

  # Use the Canvas API to create an enrollment
  # POST /api/v1/courses/:course_id/enrollments

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/enrollments"
  #puts "@url is #{@url}"

  @payload={'enrollment': {'user_id': user_id,
                           'type': role,
                           'enrollment_state': 'active', # make the person automatically active in the course
                           'course_section_id': section_id
                          }
           }
  puts("@payload is #{@payload}")
  @putResponse = HTTParty.post(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  puts("Enrollment POST Response.code is  #{@putResponse.code} and putResponse is #{@putResponse}")
  return @putResponse
end

def add_student_to_sections(course_id, user_id, list_of_section_names)
  puts("course_id is #{course_id}, user_id is #{user_id}, list_of_section_names is #{list_of_section_names}")
  existing_sections=sections_in_course(course_id)
  puts("existing_sections is #{existing_sections}")

  list_of_section_names.each do |s|
    puts("s is #{s}")
    section_id=section_with_name(course_id, existing_sections, s)
    puts("section_id is #{section_id}")
    enroll_user_in_section(course_id, user_id, 'StudentEnrollment', section_id)
  end
end

def list_enrollments_in_section(section_id)
  #GET /api/v1/sections/:section_id/enrollments
  @url = "http://#{$canvas_host}/api/v1/sections/#{section_id}/enrollments"
  #puts("@url is #{@url}")

  @payload={'type': ['StudentEnrollment'],
            'role': ['StudentEnrollment']
           }
  #puts("@payload is #{@payload}")
  @getResponse = HTTParty.get(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  #puts("Enrollment GET Response.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  return @getResponse

end

def remove_user_from_section(course_id, enrollment_id, section_id)
  # Request Parameters:
  # DELETE /api/v1/courses/:course_id/enrollments/:id

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/enrollments/#{enrollment_id}"
  #puts "@url is #{@url}"

  @payload={'task': 'delete'}
  puts("@payload is #{@payload}")
  @putResponse = HTTParty.delete(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  puts("Enrollment delete Response.code is  #{@putResponse.code} and putResponse is #{@putResponse}")
  return @putResponse
end

def get_user_info_from_sis_id(sis_id)
  #puts("sis_id is #{sis_id}")
  #GET /api/v1/users/:id
  @url_to_use = "http://#{$canvas_host}/api/v1/users/sis_user_id:#{sis_id}"
  puts "url_to_use is #{@url_to_use}"
  @getResponse = HTTParty.get(@url_to_use,:body => @payload.to_json, :headers => $header )
  if @getResponse.code > 200
    puts("The user does not exist.")
    return Nil
  end

  return @getResponse
end

def get_user_info_from_user_id(user_id)
  #GET /api/v1/users/:id
  @url_to_use = "http://#{$canvas_host}/api/v1/users/#{user_id}"
  puts "url_to_use is #{@url_to_use}"
  @getResponse = HTTParty.get(@url_to_use,:body => @payload.to_json, :headers => $header )
  if @getResponse.code > 200
    puts("The user does not exist.")
    return Nil
  end

  return @getResponse
end

##### start of routes

post '/start' do

  begin
    signature = OAuth::Signature.build(request, :consumer_secret => $oauth_secret)
    signature.verify() or raise OAuth::Unauthorized
  rescue OAuth::Signature::UnknownSignatureMethod,
         OAuth::Unauthorized
    return %{unauthorized attempt. make sure you used the consumer secret "#{$oauth_secret}"}
  end

  puts "In start - signature = #{signature}"
  # make sure this is an assignment tool launch, not another type of launch.
  # only assignment tools support the outcome service, since only they appear
  # in the Canvas gradebook.
  unless params['lis_outcome_service_url'] && params['lis_result_sourcedid']
    return %{It looks like this LTI tool wasn't launched as an assignment, or you are trying to take it as a teacher rather than as a a student. Make sure to set up an external tool assignment as outlined <a target="_blank" href="https://github.com/instructure/lti_example">in the README</a> for this example.}
  end

  # store the relevant parameters from the launch into the user's session, for
  # access during subsequent http requests.
  # note that the name and email might be blank, if the tool wasn't configured
  # in Canvas to provide that private information.
  %w(lis_outcome_service_url lis_result_sourcedid lis_person_name_full lis_person_contact_email_primary 
  lis_person_sourcedid custom_canvas_course_id custom_canvas_user_id custom_coursecode 
  ).each { |v| session[v] = params[v] }

  puts("session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}")
  puts("session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}")
  puts("session['custom_coursecode'] is #{params['custom_coursecode']}")
  puts("session is #{session}")

  redirect to("/getURL")
end

post '/' do
  puts("in route for /")
  custom_loc=params['custom_loc']
  puts("custom_loc is #{custom_loc}")
  @str1=request['custom_loc']
  puts("request['custom_loc'] is #{@str1}")
  path_info=request.path_info 
  puts("request.path_info is #{path_info}")
  path=request.path
  puts("request.path is #{path}")

  ref=request.referer
  puts("request.referer is #{ref}")


  puts "params are #{params}"

  begin
  signature = OAuth::Signature.build(request, :consumer_secret => $oauth_secret)
  signature.verify() or raise OAuth::Unauthorized
  rescue OAuth::Signature::UnknownSignatureMethod,
         OAuth::Unauthorized
    return %{unauthorized attempt. make sure you used the consumer secret "#{$oauth_secret}"}
  end

  # store the relevant parameters from the launch into the user's session, for
  # access during subsequent http requests.
  # note that the name and email might be blank, if the tool wasn't configured
  # in Canvas to provide that private information.
  %w(lis_outcome_service_url lis_result_sourcedid lis_person_name_full lis_person_contact_email_primary 
  lis_person_sourcedid custom_canvas_course_id custom_canvas_user_id custom_sis_id
  custom_user_sis_id custom_coursecode
  ).each { |v| session[v] = params[v] }

  puts "session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}"
  puts "session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}"
  puts "session['custom_sis_id'] is #{session['custom_sis_id']}"
  puts "session['custom_user_sis_id'] is #{session['custom_user_sis_id']}"

  <<-HTML 
          <form action="/gotURL" method="post">
          <h2>Enter URL of student's People page</span> | <span lang="sv">Ange webbadressen till studentens sidan från Personer i kursen?</span></h2>
          <input name='s_URL' type='text' width='1000' id='s_URL' />
          <br><button type="cancel" onclick="window.location='getURL';return false;">Cancel</button>
          <input type='submit' value='Submit' />

          </form>
   HTML


  #redirect to("/getURL")
end

post '/announce' do
  puts("in POST route for /announce")
  custom_loc=params['custom_loc']
  puts("custom_loc is #{custom_loc}")
  @str1=request['custom_loc']
  puts("request['custom_loc'] is #{@str1}")
  path_info=request.path_info 
  puts("request.path_info is #{path_info}")
  path=request.path
  puts("request.path is #{path}")

  ref=request.referer
  puts("request.referer is #{ref}")


  puts "params are #{params}"

  begin
  signature = OAuth::Signature.build(request, :consumer_secret => $oauth_secret)
  signature.verify() or raise OAuth::Unauthorized
  rescue OAuth::Signature::UnknownSignatureMethod,
         OAuth::Unauthorized
    return %{unauthorized attempt. make sure you used the consumer secret "#{$oauth_secret}"}
  end

  # store the relevant parameters from the launch into the user's session, for
  # access during subsequent http requests.
  # note that the name and email might be blank, if the tool wasn't configured
  # in Canvas to provide that private information.
  %w(lis_outcome_service_url lis_result_sourcedid lis_person_name_full lis_person_contact_email_primary 
  lis_person_sourcedid custom_canvas_course_id custom_canvas_user_id custom_sis_id
  custom_user_sis_id custom_coursecode
  ).each { |v| session[v] = params[v] }

  puts("params are #{params}")
  puts("session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}")
  puts("session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}")
  puts("session['custom_sis_id'] is #{session['custom_sis_id']}")
  puts("session['custom_user_sis_id'] is #{session['custom_user_sis_id']}")
  puts("session['custom_coursecode'] is #{session['custom_coursecode']}")
  puts("session is #{session}")

  #gqmjr
  <<-HTML 
          <form action="/gotURL" method="post">
          <h2>Enter URL of student's People page</span> | <span lang="sv">Ange webbadressen till studentens sidan från Personer i kursen?</span></h2>
          <input name='s_URL' type='text' style="width: 600px;" id='s_URL' />
          <br><button type="cancel" onclick="window.location='getURL';return false;">Cancel</button>
          &nbsp;&nbsp;&nbsp;&nbsp;<input type='submit' name='action' value='Claim students' />
          <input type='submit' value='Submit' />

          </form>
          <script type='text/javascript'>
            document.getElementById('s_URL').value = document.referrer;
            </script>
   HTML

  # redirect to("/getURL")
end

get '/announce' do
  puts("in GET route for /announce")
  
  custom_loc=params['custom_loc']
  puts("custom_loc is #{custom_loc}")
  @str1=request['custom_loc']
  puts("request['custom_loc'] is #{@str1}")
  path_info=request.path_info 
  puts("request.path_info is #{path_info}")
  path=request.path
  puts("request.path is #{path}")
  ref=request.referer
  puts("request.referer is #{ref}")

  puts "params are #{params}"

  # store the relevant parameters from the launch into the user's session, for
  # access during subsequent http requests.
  # note that the name and email might be blank, if the tool wasn't configured
  # in Canvas to provide that private information.
  %w(lis_outcome_service_url lis_result_sourcedid lis_person_name_full lis_person_contact_email_primary 
  lis_person_sourcedid custom_canvas_course_id custom_canvas_user_id custom_sis_id
  custom_user_sis_id
  ).each { |v| session[v] = params[v] }

  puts "session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}"
  puts "session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}"
  puts "session['custom_sis_id'] is #{session['custom_sis_id']}"
  puts "session['custom_user_sis_id'] is #{session['custom_user_sis_id']}"

  "Hello World for an /announce"
end


get '/getURL' do

  puts("In /getURL")
  <<-HTML 
  <html > 
	<head ><title ><span lang="en">Which student?</span> | <span lang="sv">Vilken elev?</span></title ></head > 
	<body >
          <form action="/gotURL" method="post">
          <h2>Enter URL of student's People page</span> | <span lang="sv">Ange webbadressen till studentens sidan från Personer i kursen?</span></h2>
          <input name='s_URL' type='text' width='1000' id='s_URL' />
          <br><button type="cancel" onclick="window.location='getURL';return false;">Cancel</button>
          &nbsp;&nbsp;&nbsp;&nbsp;<input type='submit' name='action' value='Claim students' />
          <input type='submit' value='Submit' />

          </form>
	</body >
   </html > 
   HTML

end

post '/gotURL' do
  if params.has_key?('action') 
    action=params['action']
    if action == 'Claim students'
      redirect to("/claimStudents")
    end
  end

   s_URL=params['s_URL']
   if !s_URL || s_URL.empty?
     redirect to("/getURL")
    end
   session['s_URL']=s_URL
   puts("s_URL is #{s_URL}")

   referrer_url=params['referrer_url']
   session['referrer_url']=referrer_url
   puts("referrer_url is #{referrer_url}")

   redirect to("/processDataForStudent")
end

get '/processDataForStudent' do
  puts("In /processDataForStudent")
  # The URL should be of the form:
  #    http://canvas.docker/courses/5/grades/7#tab-assignments
  #    http://canvas.docker/courses/5/users/7

  # get the student's user_id from the URL that was entered
  s_URL=session['s_URL']
  elements=s_URL.split('/')

  #remove empty elements
  elements.delete_if{|e| e.length == 0}
  puts("elements are #{elements}")

  # produces ["http:", "canvas.docker", "courses", "5", "users", "7"]
  # produces ["http:", "canvas.docker", "courses", "5", "grades", "7"]
  puts("elements[2] is #{elements[2]}")
  
  if elements[2] != "courses"
    puts("Do not know what to do with the URL, it is not using a courses URL")
    redirect to("/getURL")
  end

  html_to_render =  <<-HTML 
  <html > 
	<head ><title ><span lang="en">Nothing to do for this student</span> | <span lang="sv">Inget att göra för den här studenten</span></title ></head > 
	<body >
	<p><span lang="en">Nothing to do for this student</span> | <span lang="sv">Inget att göra för den här studenten</span></p >
	</body >
   </html > 
   HTML


  @url_to_use = "http://#{$canvas_host}/api/v1/users/#{elements[5]}/profile"
  puts("url_to_use is #{@url_to_use}")
  @getResponse = HTTParty.get(@url_to_use, :headers => $header )
  puts("Student is: #{@getResponse}")
  user_id=elements[5]
  session['target_user_id']=user_id

  course_id=elements[3]
  session['course_id']=course_id
  assignments_in_course=list_assignments(course_id)
  a=select_from_list_by_name("Examensarbete inlämnande/Final thesis submission", assignments_in_course)
  if a
    assignment_id=a['id']
    puts("id=#{a['id']} and name=#{a['name']}")
    final_thesis=get_grade_for_assignment(course_id, assignment_id, user_id)
    puts("final thesis submission is #{final_thesis}")
    # id=13 and name=Examensarbete inlämnande/Final thesis submission
    # @payload is {:include=>["submission_comments"]}
    #final thesis submission is {"id":151,"body":null,"url":null,"grade":null,"score":null,"submitted_at":null,"assignment_id":13,"user_id":7,"submission_type":null,"workflow_state":"unsubmitted","grade_matches_current_submission":true,"graded_at":null,"grader_id":null,"attempt":null,"cached_due_date":null,"excused":null,"late_policy_status":null,"points_deducted":null,"grading_period_id":null,"late":false,"missing":false,"seconds_late":0,"entered_grade":null,"entered_score":null,"preview_url":"http://canvas.docker/courses/5/assignments/13/submissions/7?preview=1\u0026version=0","submission_comments":[],"anonymous_id":"yj1GA"}
    if (final_thesis['workflow_state'] == "graded") and (final_thesis['entered_grade'] =="complete")
      session['assignment_id']=assignment_id
      session['final_thesis']=final_thesis.parsed_response
      puts("time to prepare approved thesis #{session['final_thesis']}")
      today=Time.new
      current_year=today.year
      previous_year=current_year-1
      next_year=current_year+1
      potential_year_options="<option value='#{previous_year}'>#{previous_year}</option><option value='#{current_year}' selected='selected'>#{current_year}</option><option value='#{next_year}'>#{next_year}</option>'"
      # get date, time, and place for oral presenation
      html_to_render =  <<-HTML 
          <html>
              <head ><title ><span lang="en">Which year should the thesis be reported in?</span> | <span lang="sv">Vilket år ska avhandlingen rapporteras?</span></title ></head > 
              <body >
              <p><span lang="en">In some cases a thesis that is approved at the start of the year, might actually be a thesis that is being reported for the previous year. Potentially,  a thesis that is being approved late in the year might actually be for the next calendar year.</span>/<span lang="sv">I vissa fall kan en avhandling som godkänts i början av året faktiskt vara en avhandling som rapporteras för föregående år. Potentiellt kan en avhandling som godkänns sent på året faktiskt vara för nästa kalenderår.</span></p>
              <form name="thesis_year" action="/approveThesisStep1" method="post">
              <h2><span lang="en">Year of thesis</span>/<span lang="sv">År av avhandlingen</span></h2>
              <label for="year">Year|År:</label>
              <select name="year_of_thesis" id="year_of_thesis">
              #{potential_year_options}
              </select><br>
              <h2><span lang="en">Language for thesis cover</span>/<span lang="sv">Språk för avhandlingen täcka</span></h2>
              <select name="cover_language" id="cover_language">
               <option value='English'>English | Engelsk</option>
               <option value='Swedish'>Swedish | Svensk</option>
               </select><br>
               <br><input type='submit' value='Submit' />
               </form>
               </body>
          </html > 
       HTML
      return html_to_render
    end
  end                         # end for final_thesis

  a=select_from_list_by_name("Utkast till/Draft for opponent", assignments_in_course)
  if a
    assignment_id=a['id']
    puts("id=#{assignment_id} and name=#{a['name']}")
    opponent_version=get_grade_for_assignment(course_id, assignment_id, user_id)
    puts("draft to opponent is #{opponent_version}")
    puts("about to check opponent_version['workflow_state'] = #{opponent_version['workflow_state']} and opponent_version['entered_grade'] = #{opponent_version['entered_grade']}")
    if (opponent_version['workflow_state'] == "graded") and (opponent_version['entered_grade'] =="complete")
      # prepare announcement
      session['assignment_id']=assignment_id
      session['opponent_version']=opponent_version.parsed_response
        
      puts("time to prepare announcement")
      planned_start_today=Time.new
      planned_start_min=planned_start_today + (3*24*60*60)  #  3 days in the future
      planned_start_max=planned_start_today + (30*24*60*60) # 30 days in the future

      # add location of presentation
      potential_locations=''
      $eecs_meeting_rooms.each do |room|
        split_room=room.split(',')
        potential_locations << '<option value="'+split_room[0]+'">'+room+'</option>'
      end


      # get date, time, and place for oral presenation
      html_to_render =  <<-HTML 
      	<html> 
        <head ><title ><span lang="en">Which student?</span> | <span lang="sv">Vilken elev?</span></title ></head > 
        <body >
        <form name="oralpresentationDateTime" action="/prepareAnnouncementStep1" method="post">
        <h2><span lang="en">Date for oral presentation</span>/<span lang="sv">Datum för muntlig presentation</span></h2>
        <label for="start">Date/Datum:</label>
        <input type="date" id="oral_presenation" name=oral_presentation_date
        value=#{planned_start_today}
        min=#{planned_start_min}
        max=#{planned_start_max}>
        <!-- <input type="time" name="oral_presentation_time" id="oral_presentation_time"> -->
        <select name="oral_presentation_time" id="oral_presentation_time">
        <option value="08:00">08:00</option>
        <option value="09:00">09:00</option>
        <option value="10:00">10:00</option>
        <option value="11:00">11:00</option>
        <option value="12:00">12:00</option>
        <option value="12:00">13:00</option>
        <option value="13:00">14:00</option>
        <option value="15:00">15:00</option>
        <option value="16:00">16:00</option>
        <option value="17:00">17:00</option>
        <option value="18:00">18:00</option>
        <option value="19:00">19:00</option>
        <option value="20:00">20:00</option>
        </select><br>
        <label for="presentation_language">Language | Språk: </label><br>
        <input type="radio" name="language" value="presentation_language_en" checked="checked">English | Engelsk<br>
        <input type="radio" name="language" value="presentation_language_sv">Swedish | Svensk<br>
        <h2><span lang="en">Location</span>/<span lang="sv">Lokal</span></h2>
        <select name="oral_presentation_location" id="oral_presentation_location">
        #{potential_locations}
        </select><br>
        
        
        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html > 
       HTML
      return html_to_render
    end
  end                         # end for draft to opponent
  a=select_from_list_by_name("Projekt Plan/Project plan", assignments_in_course)
  if a
    assignment_id=a['id']
    puts("id=#{assignment_id} and name=#{a['name']}")
    project_plan_assignment=get_grade_for_assignment(course_id, assignment_id, user_id)
    puts("project_plan_assignment is #{project_plan_assignment}")
    if (project_plan_assignment['workflow_state'] == "graded") and (project_plan_assignment['entered_grade'] =="complete")
      # prepare calendar event(s)
      session['assignment_id']=assignment_id
      session['project_plan_assignment']=project_plan_assignment.parsed_response
        
      puts("time to prepare calendar events")
      today=Time.new
      month_10_date=today + (10*30*24*60*60)  #  10 months in the future
      month_10_min=today + (10*30*24*60*60)  #  10 months in the future
      month_10_max=today + (12*30*24*60*60) # 12 months in the future

      # get date, time, and place for oral presenation
      html_to_render =  <<-HTML 
      	<html> 
        <head ><title ><span lang="en">Key dates</span> | <span lang="sv">Viktiga datum</span></title ></head > 
        <body >
        <form name="KeyDates" action="/KeyDates" method="post">
        <h2><span lang="en">Month 10 reminder date</span>/<span lang="sv">Månad 10 påminnelsedatum</span></h2>
        <label for="start">Date/Datum:</label>
        <input type="date" id="month_10" name="month_10"
        value=#{month_10_date}
        min=#{month_10_min}
        max=#{month_10_max}>
        <br>
        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html > 
       HTML
      return html_to_render
    end
  end                         # end for project plan

  html_to_render
end

post "/KeyDates" do
  month_10_reminder_date=params['month_10']
  puts("params are #{params}")
  target_user_id=session['target_user_id']
  create_calendar_event(target_user_id, month_10_reminder_date, 'Month 10 reminder', 'Reminder that 10 months have elapsed and you should finish you degree project before the 12th month')
  <<-HTML 
        <html> 
        <head ><title ><span lang="en">Thanks for setting the key dates</span> | <span lang="sv">Tack för att ställa in viktiga datum</span></title ></head > 
        <body >
        <h2><span lang="en">Thanks for setting the key date(s)</span> | <span lang="sv">Tack för att ställa in viktiga datum</span></h2>
        </body>
        </html > 
       HTML

end

# prepare the announcement for an oral presentation
post "/prepareAnnouncementStep1" do
  puts("in route /prepareAnnouncementStep1")
  puts("params are #{params}")
  oral_presentation_date=params['oral_presentation_date']
  oral_presentation_time=params['oral_presentation_time']
  language=params['language']
  oral_presentation_location=params['oral_presentation_location']
   if !oral_presentation_date || oral_presentation_date.empty? || !oral_presentation_time || oral_presentation_time.empty?
     puts("Date: #{params['oral_presentation_date']} Time: #{params['oral_presentation_time']}")
     redirect to("/processDataForStudent")
    end
   session['oral_presentation_date']=oral_presentation_date
   session['oral_presentation_time']=oral_presentation_time
   session['language']=language
   session['oral_presentation_location']=oral_presentation_location
   puts("oral_presentation_date and time is #{oral_presentation_date} #{oral_presentation_time}")
   redirect to("/prepareAnnouncementStep2")
end

get "/prepareAnnouncementStep2" do
  puts("in route /prepareAnnouncementStep2")
  opponent_version=session['opponent_version'] 
  course_id=session['course_id']
  assignment_id=session['assignment_id']
  user_id=session['target_user_id']

  # get list of peer reviwers - as these will be the opponents
  # if there are no peer reviwers - remind the examiner to assign at least one opponent
  peer_reviewers={}
  peer_reviewers_names={}
  assigned_peer_reviews=list_peer_review_assignments(course_id, assignment_id)
  # [{"id":1,"user_id":7,"asset_id":99,"asset_type":"Submission","workflow_state":"assigned","assessor_id":12}]
  puts("assigned_peer_reviews are #{assigned_peer_reviews}")
  assigned_peer_reviews.each do |review_assigment|
    assessor_id=review_assigment['assessor_id']
    @url_to_use = "http://#{$canvas_host}/api/v1/users/#{assessor_id}/profile"
    @getResponse=HTTParty.get(@url_to_use, :headers => $header )
    peer_reviewers[assessor_id]=@getResponse.parsed_response
    peer_reviewers_names[assessor_id]=peer_reviewers[assessor_id]['name']
    puts("peer reviewer is: #{peer_reviewers}")
  end

  puts("peer_reviewers are #{peer_reviewers}")
  session['peer_reviewers']=peer_reviewers
  session['peer_reviewers_names']=peer_reviewers_names
  
  list_of_peer_reviwers=""
  peer_reviewers_names.each do |id, name| # you have to iterate this way as programs is a hash
    list_of_peer_reviwers << "<p>"+name+"</p>"
  end
  
  @url_to_use = "http://#{$canvas_host}/api/v1/users/#{user_id}/profile"
  @getResponse=HTTParty.get(@url_to_use, :headers => $header )
  author_info=@getResponse.parsed_response
  puts("author_info is #{author_info}")
  authors=[]
  authors << author_info['name']
  session['authors']=authors

  # if this was join work (in the case of a 1st cycle thesis) look up the other member of the group
  list_of_authors ="<p>"+author_info['name']+"</p>"

  puts("author(s) is/are: #{authors}")


  # extract title, subtitle, abstracts and list of keywords
  # "attachments":[{"id":18,"uuid":"8hghdLuepnAjrxDd7dtFjU8KLjzqoFTtcSfuxQxw","folder_id":20,"display_name":"Fake_student_thesis-20190220.pdf","filename":"1550670816_107__Fake_student_thesis-20190220.pdf","workflow_state":"processed","content-type":"application/pdf","url":"http://canvas.docker/files/18/download?download_frd=1\u0026verifier=8hghdLuepnAjrxDd7dtFjU8KLjzqoFTtcSfuxQxw","size":265203,"created_at":"2019-02-20T13:53:35Z","updated_at":"2019-02-20T13:53:37Z","unlock_at":null,"locked":false,"hidden":false,"lock_at":null,"hidden_for_user":false,"thumbnail_url":null,"modified_at":"2019-02-20T13:53:35Z","mime_class":"pdf","media_entry_id":null,"locked_for_user":false,"preview_url":null}]

  @thesis_info=""
  attachments=opponent_version['attachments']
  if attachments
    attachments.each do |attachment|
      puts("process the PDF file named #{attachment['filename']}")
      @thesis_info=extract_thesis_info_pdf(authors, attachment['url'] )
      puts("@thesis_info is #{@thesis_info}")
    end
  end

  @thesis_info_title=@thesis_info['title']
  puts("@thesis_info_title is #{@thesis_info_title}")
  @thesis_info_subtitle=@thesis_info['subtitle']
  @thesis_info_en_abstract=@thesis_info['en_abstract']
  @thesis_info_en_keywords=@thesis_info['en_keywords']
  @thesis_info_sv_abstract=@thesis_info['sv_abstract']
  @thesis_info_sv_keywords=@thesis_info['sv_keywords']

  language=session['language']
  if language == "presentation_language_sv"
    present_lang='''<label for="presentation_language">Language | Språk: </label><br>
 <input type="radio" name="language" value="presentation_language_en">English | Engelsk<br>
 <input type="radio" name="language" value="presentation_language_sv" checked>Swedish | Svensk<br>
'''
  else
    present_lang='''<label for="presentation_language">Language | Språk: </label><br>
 <input type="radio" name="language" value="presentation_language_en" checked>English | Engelsk<br>
 <input type="radio" name="language" value="presentation_language_sv">Swedish | Svensk<br>
'''
  end

  # add location of presentation
  oral_presentation_location=session['oral_presentation_location']
  potential_locations=''
  $eecs_meeting_rooms.each do |room|
    split_room=room.split(',')
    if split_room[0] == oral_presentation_location 		# marked the previously selected room as selected
      potential_locations << '<option selected="selected" value="'+split_room[0]+'">'+room+'</option>'
    else
      potential_locations << '<option value="'+split_room[0]+'">'+room+'</option>'
    end
  end


  # show to examiner for approval or modifications
  <<-HTML 
  <html > 
	<head ><title ><span lang="en">Tentative oral presentation information</span> | <span lang="sv">Tentativ muntlig presentationsinformation</span></title ></head > 
	<body >
          <form action="/approveAnnouncementData" method="post">
          <h2><span lang="en">Tentative oral presentation information - Do you approve?</span> | <span lang="sv">Tentativ muntlig presentationsinformation - Godkänner du?</span></h2>
          <label for="start">Date &amp; Time | Datum och Tid:</label>
          <input type="date" id="oral_presenation" name=oral_presentation_date value=#{session['oral_presentation_date']}>
          <input type="time" id="oral_presenation" name=oral_presentation_time value=#{session['oral_presentation_time']} pattern="[0-9]{2}:[0-9]{2}"><br>
          #{present_lang}
          <p><span lang="en">Location</span>/<span lang="sv">Lokal</span></p>
          <select name="oral_presentation_location" id="oral_presentation_location">
          #{potential_locations}
          </select><br>

          <h3><span lang="en">Author(s)</span> | <span lang="sv">Författare(r)</span></h3>
          #{list_of_authors}

          <h3>Opponent(s)</h3>
          #{list_of_peer_reviwers}

          <h3><span lang="en">Title</span> | <span lang="sv">titel</span>:</h3>
          <textarea rows="4" cols="80" name='Title' id='Title' />#{@thesis_info_title}</textarea>

          <h3><span lang="en">Subtitle</span> | <span lang="sv">Undertitel</span>:></h3>
          <textarea rows="4" cols="80" name='Subtitle' id='Subtitle' />#{@thesis_info_subtitle}</textarea>

          <h3><span lang="en">English abstract</span> | <span lang="sv">Engelska abstrakt</span>:</h3>
          <textarea rows="10" cols="80" name='English_abstract' id='English_abstract' />#{@thesis_info_en_abstract}</textarea>
          <h3><span lang="en">English keywords</span> | <span lang="sv">Engelska nyckelord</span>:</h3>
          <textarea rows="4" cols="80" name='English_keywords' id='English_keywords' />#{@thesis_info_en_keywords}</textarea>
          <h3><span lang="en">Swedish abstract</span> | <span lang="sv">Svensk abstrakt</span>:</h3>
          <textarea rows="10" cols="80" name='Swedish_abstract' id='Swedish_abstract' />#{@thesis_info_sv_abstract}</textarea>
          <h3><span lang="en">Swedish keywords</span> | <span lang="sv">Svensk nyckelord</span>:</h3>
          <textarea rows="4" cols="80" name='Swedish_keywords' id='Swedish_keywords' />#{@thesis_info_sv_keywords}</textarea>


          <p><input type='button' onclick="window.location='processDataForStudent';return false;">Cancel</button>
          <input type='submit' value='Approve' /></p>
          </form>
	</body >
   </html > 
   HTML

end

post "/approveAnnouncementData" do
  puts("in route /approveAnnouncementData")
  puts "params are #{params}"
  # store the information on date&time, location, and lanugage of presenation for later use with DiVA
  # compose Announcement for in Canvas course - then insert
  course_id=session['course_id']

  # note that we take the params version of the values, since they could have been changed by the examiner before approving the publication of the announcement
  title=params['Title']
  subtitle=params['Subtitle']
  english_abstract=params['English_abstract']
  english_keywords=params['English_keywords']
  swedish_abstract=params['Swedish_abstract']
  swedish_keywords=params['Swedish_keywords']
  language=params['language']
  oral_presentation_date=params['oral_presentation_date']
  oral_presentation_time=params['oral_presentation_time']
  oral_presentation_location=params['oral_presentation_location']

  puts("oral_presentation_location is #{oral_presentation_location}")

  if cycle_number.to_i == 2
    announcementTitle="Second cycle thesis presentation #{oral_presentation_date} at #{oral_presentation_time}"
  else
    announcementTitle="First cycle thesis presentation #{oral_presentation_date} at #{oral_presentation_time}"
  end

  if  language == "presentation_language_sv"
    lang="Swedish | Svensk"
  else
    lang="English | Engelsk"
  end

  peer_reviewers_names=session['peer_reviewers_names']
  list_of_peer_reviwers=[]
  peer_reviewers_names.each do |id, name| # you have to iterate this way as programs is a hash
    list_of_peer_reviwers.append(name)
  end
  if list_of_peer_reviwers.length > 1
    opponents=list_of_peer_reviwers.join(',')
  else
    opponents=list_of_peer_reviwers[0]
  end

  #place="Seminar room Grimeton at CoS, Kistag&aring;ngen 16, East, Floor 4, Elevator B, Kista"
  place="unknown location"
  $eecs_meeting_rooms.each do |room|
    #puts("room is #{room}")
    split_room=room.split(',')
    if split_room[0] == oral_presentation_location
      if room.include?("Kistagången")
        place=room+", Kista"
      else
        place=room+", Stockhom"
      end
    end
  end

  puts("place is #{place}")

  user_id=session['target_user_id']
  authors=session['authors']
  authors_str=authors.join(" and ")
  
  list_of_existing_columns=list_custom_columns(session['course_id'])
  #puts("list_of_existing_columns is #{list_of_existing_columns}")

  examiner=get_custom_column_entries(session['course_id'], 'Examiner', user_id, list_of_existing_columns)
  #puts("examiner is #{examiner}")

  academicSupervisor=get_custom_column_entries(session['course_id'], 'Supervisor', user_id, list_of_existing_columns)
  #puts("academicSupervisor is #{academicSupervisor}")

  industrySupervisor=[]
  contact=get_custom_column_entries(session['course_id'], 'Contact', user_id, list_of_existing_columns)
  #puts("contact is #{contact}")
  eMailStartsAt=contact.index("<")
  if eMailStartsAt && eMailStartsAt > 0
    industrySupervisor=contact[0..eMailStartsAt-1].strip
  else
    industrySupervisor=contact.strip
  end
  puts("industrySupervisor is #{industrySupervisor}")
    

  if subtitle || subtitle.length > 1 		# add subtitle it one exists
    title=title+': '+subtitle
  end

  internal_prefix=%Q[<pre>
Student:           	#{authors_str}
Title:                  #{title}
Time:                   #{oral_presentation_date} at #{oral_presentation_time}
Place:                  #{place}
Examiner:               #{examiner}
Academic Supervisor: 	#{academicSupervisor}
Opponents:  		#{opponents}
Language:  		#{lang}</pre>
]

  external_prefix=%Q[<pre>
Student:           	#{authors_str}
Title:                  #{title}
Time:                   #{oral_presentation_date} at #{oral_presentation_time}
Place:                  #{place}
Examiner:               #{examiner}
Academic Supervisor: 	#{academicSupervisor}
Industrial Supervisor:  #{industrySupervisor}
Opponents:  		#{opponents}
Language:  		#{lang}</pre>
]


  if industrySupervisor
    #puts("external_prefix is #{external_prefix}")
    message="#{external_prefix}"
  else
    #puts("internal_prefix is #{internal_prefix}")
    message="#{internal_prefix}"
  end
  
  en_abtract_lines='<p lang="en">'
  english_abstract=english_abstract.gsub("\r\n", '</p><p lang="en">')
  en_abtract_lines=en_abtract_lines+english_abstract
  en_abtract_lines=en_abtract_lines+'</p>'

  #puts("en_abtract_lines is #{en_abtract_lines}")

  sv_abtract_lines='<p lang="sv">'
  swedish_abstract=swedish_abstract.gsub("\r\n", '</p><p lang="sv">')
  sv_abtract_lines=sv_abtract_lines+swedish_abstract
  sv_abtract_lines=sv_abtract_lines+'</p>'

  message_body=%Q[<div style="display: flex;">
<div>
<h2 lang="en">Abstract</h2>
#{en_abtract_lines}
<p lang="en"><strong>Keywords:</strong> <em>#{english_keywords}</em></p>
</div>
<div>
<h2 lang="sv">Sammanfattning</h2>
#{sv_abtract_lines}
<p lang="sv"><strong>Nyckelord:</strong> <em>#{swedish_keywords}</em></p>
</div>
</div>]

  message=message+message_body
  #puts("message is #{message}")

  response=create_announcement(course_id, announcementTitle, message)
  # compose calendar even for Polopoly and then insert

  <<-HTML 
  <html > 
	<head ><title ><span lang="en">Approved announcement</span> | <span lang="sv">Godkänt meddelande</span></title ></head > 
	<body >
        <p><span lang="en">Thanks for approving the announcement</span> | <span lang="sv">Tack för att du godkände meddelandet</span></p>
        <p>#{params}</p>
	</body >
   </html > 
   HTML

end


post "/approveThesisStep1" do
  puts("in route /approveThesisStep1")
  puts "params are #{params}"
  year_of_thesis=params['year_of_thesis']
  session['year_of_thesis']=year_of_thesis
  cover_language=params['cover_language']
  session['cover_language']=cover_language

  user_id=session['target_user_id']
  @url_to_use = "http://#{$canvas_host}/api/v1/users/#{user_id}/profile"
  @getResponse=HTTParty.get(@url_to_use, :headers => $header )
  author_info=@getResponse.parsed_response
  puts("author_info is #{author_info}")
  authors=[]
  authors << author_info['name']
  session['authors']=authors
  # if this was join work (in the case of a 1st cycle thesis) look up the other member of the group

  puts("author(s) is/are: #{authors}")

  @thesis_info=""
  final_thesis=session['final_thesis']
  if final_thesis
    attachments=final_thesis['attachments']
    if attachments
      attachments.each do |attachment|
        puts("process the PDF file named #{attachment['filename']}")
        @thesis_info=extract_thesis_info_pdf(authors, attachment['url'] )
        puts("@thesis_info is #{@thesis_info}")
      end
    end
  end
  
  puts("after block @thesis_info is #{@thesis_info}")
  thesis_info_title=@thesis_info['title']
  thesis_info_subtitle=@thesis_info['subtitle']

  puts("thesis_info_title is #{thesis_info_title}")

  #@thesis_info_en_abstract=@thesis_info['en_abstract']
  #@thesis_info_en_keywords=@thesis_info['en_keywords']
  #@thesis_info_sv_abstract=@thesis_info['sv_abstract']
  #@thesis_info_sv_keywords=@thesis_info['sv_keywords']

  list_of_existing_columns=list_custom_columns(session['course_id'])
  #puts("list_of_existing_columns is #{list_of_existing_columns}")

  examiner=get_custom_column_entries(session['course_id'], 'Examiner', user_id, list_of_existing_columns)
  #puts("examiner is #{examiner}")

  trita_string=get_TRITA_string($school_acronym, true, year_of_thesis, authors, thesis_info_title, examiner)
  puts("trita_string is #{trita_string}")
  ## should store the TRITA string in the gradebook - perhaps as a comment in the assignment for the final thesis
  ## it should also have the final URN stored with it

  course_code=get_custom_column_entries(session['course_id'], 'Course_code', user_id, list_of_existing_columns)
  #puts("course_code is #{course_code}")

  credits=$relevant_courses_English[course_code]['credits'].to_f

  # <select id="exam" name="exam">
  if cycle_number.to_i == 1
    exam_class='firstLevel'
  else
    exam_class='secondLevel'
  end

  if exam_class == 'firstLevel'
    if credits == 7.5
      cover_degree ='first-level-7'
    elsif credits == 10.0
      cover_degree ='first-level-10'
    elsif credits == 15.0
      cover_degree ='first-level-15'
    else
      puts("Unhandled number of credits for a First cycle degree project course - course code=#{course_code}")
    end         
  end
  if  exam_class == 'secondLevel'
    if credits == 15.0
      cover_degree = 'second-level-15'
    elsif credits == 30.0
      cover_degree ='second-level-30'
    elsif credits == 60.0
      cover_degree = 'second-level-60'
    else
      puts("Unhandled number of credits for a Second cycle degree project course - course code=#{course_code}")
    end
  end

  if (course_code == 'II122X') or (course_code == 'II142X')
    cover_exam = 2 				#  Högskoleingenjörsexamen
    cover_area = {'en': 'Computer Engineering', 'sv': 'Datateknik'}

  elsif (course_code == 'IL122X') or (course_code == 'II122X')
    cover_exam = 2 				# Högskoleingenjörsexamen
    cover_area = {'en': 'Electronics and Computer Engineering', 'sv': 'Elektronik och datorteknik'}

  elsif (course_code == 'IL122X') or (course_code == 'II122X')
    cover_exam = 1 				# kandidate exam
    cover_area = {'en': 'Information and Communication Technology', 'sv': 'Informations- och kommunikationsteknik'}

  elsif (course_code == 'II249X')
    cover_exam = 3 				# Magisterexamen
    cover_area = {'en': 'Computer Science and Engineering', 'sv': 'Datalogi och datateknik'}

  elsif (course_code == 'IL249X')
    cover_exam = 3 				# Magisterexamen
    cover_area = {'en': 'Electrical Engineering', 'sv': 'Elektroteknik'}

  elsif (course_code == 'II225X') or (course_code == 'II245X')
    cover_exam = 4 				# Civilingenjörsexamen
    cover_area = {'en': 'Information and Communication Technology', 'sv': 'Informations- och kommunikationsteknik'}

  elsif (course_code == 'IL228X') or (course_code == 'IL248X')
    cover_exam = 4 				# Civilingenjörsexamen
    cover_area = {'en': 'Information and Communication Technology', 'sv': 'Informations- och kommunikationsteknik'}

  elsif (course_code == 'II226X') or (course_code == 'II246X')
    cover_exam = 3 				# Masterexamen
    cover_area = {'en': 'Computer Science and Engineering', 'sv': 'Datalogi och datateknik'}

  elsif (course_code == 'II227X') or (course_code == 'II247X')
    cover_exam = 3 				# Masterexamen - outside of program
    cover_area = {'en': 'Computer Science and Engineering', 'sv': 'Datalogi och datateknik'}

  elsif (course_code == 'IL226X') or (course_code == 'IL246X')
    cover_exam = 3 				# Masterexamen
    cover_area = {'en': 'Electrical Engineering', 'sv': 'Elektroteknik'}

  elsif (course_code == 'IL227X') or (course_code == 'IL247X')
    cover_exam = 3 				# Masterexamen - outside of program
    cover_area = {'en': 'Electrical Engineering','sv': 'Elektroteknik'}

  elsif (course_code == 'IF226X') or (course_code == 'IF246X')
    cover_exam = 3 				# Masterexamen (not Civing.) or nanotechnology
    cover_area ={'en': 'Engineering Physics', 'sv': 'Teknisk fysik'}

  elsif (course_code == 'IF227X') or (course_code == 'IF247X')
    cover_exam = 3 				# Masterexamen - outside of program
    cover_area = {'en': 'Engineering Physics', 'sv': 'Teknisk fysik'}
  else
    puts("Unhandled exam and area - course code=#{course_code}")
  end
  
  puts("cover_exam = #{cover_exam} and cover_area = #{cover_area}")

  school= {:en => "Electrical Engineering and Computer Science",
           :sv => "Skolan för elektroteknik och datavetenskap"}
  result=make_cover(cover_language, cycle_number.to_i, year_of_thesis, cover_degree, cover_exam, cover_area,
                    school,
                    authors, thesis_info_title, thesis_info_subtitle, trita_string)
  if result.length > 0
    file = File.open("cover.pdf", "w")
    file.puts("#{result}")
    file.close
    cmd1="qpdf --split-pages cover.pdf cover_pages"
    status1=system(cmd1)

    # get thesis and same it in a file
    final_thesis=session['final_thesis']
    puts("final_thesis is #{final_thesis}")
    attachments=final_thesis['attachments']
    puts("attachments is #{attachments}")
    if attachments
      attachments.each do |attachment|
        puts("process the PDF file named #{attachment['filename']}")
        filename=attachment['filename']
        url_to_file=attachment['url']
        file_handle = open(url_to_file)
        content_of_file = file_handle.read
        file = File.open(filename, "w")
        file.puts("#{content_of_file}")
        file.close

        # apply the cover
        cmd2="qpdf  --empty --pages cover_pages-1 #{filename} cover_pages-2 -- #{filename[0..-5]}-with-cover.pdf"

        status2=system(cmd2)
        @file_results = <<-HTML 
          <html > 
	  <head ><title ><span lang="en">Thesis with cover</span> | <span lang="sv"></span></title ></head > 
	<body >
        <p><span lang="en">Thanks for approving the thesis</span> | <span lang="sv">Tack för att du godkände rapport</span></p>
        <p>The approved thesis with cover is at #{filename[0..-5]}-with-cover.pdf</p>
	</body >
   </html > 
   HTML

      end
    end
  end
  @file_results
end

get "/getUserProgram" do

  @program_options=''
  @programs=$programs_in_the_school_with_titles.sort
  puts("@programs is #{@programs}")
  # note that each "program" value is of the form ["CDATE", {"owner"=>"EECS", "title_en"=>"Degree Programme in Computer Science and Engineering", "title_sv"=>"Civilingenjörsutbildning i datateknik"}]

  @programs.each do |program|
    #puts("program is #{program}")
    if program.length > 0
      @program_name=program[0]
      puts("@program_name is #{@program_name}")
      @title=$programs_in_the_school_with_titles[@program_name]['title_en']
      @title_s=$programs_in_the_school_with_titles[@program_name]['title_sv']
      #puts("title is #{@title}")
      #puts("title is #{@title_s}")
      @program_options=@program_options+'<option value="'+@program_name+'">'+@program_name+': '+@title+' | '+@title_s+'</option>'
    end
  end

  puts("program_options is #{@program_options}")

  <<-HTML 
  <html > 
	<head ><title ><span lang="en">Which program of study are you in?</span> | <span lang="sv">Vilket studieprogram är du i?</span></title ></head > 
	<body >
          <form action="/gotUsersProgram" method="post">
          <h2>Which program of study are you in?</span> | <span lang="sv">Vilket studieprogram är du i?</span></h2>
          <select id="program_code" name="program_code">
          #{@program_options}
          </select>

           <br><input type='submit' value='Submit' />
          </form>
	</body >
   </html > 
   HTML


end

post "/gotUsersProgram" do
   program_code=params['program_code']
   if !program_code || program_code.empty?
     redirect to("/getUserProgram")
    end
   session['program_code']=program_code

   redirect to("/getGeneralData")
end

# at this point we know the user's program code
get '/getGeneralData' do

        @program_code=session['program_code']
        if cycle_number == "1"
          @cycle_number_ordinal='1<sup>st</sup>'
        else
          @cycle_number_ordinal='2<sup>nd</sup>'
        end

        puts("/getGeneralData: @program_code is #{@program_code}")
        planned_start_today=Time.new
        planned_start_min=planned_start_today
        planned_start_max=planned_start_today + (11*30*24*60*60) # 11 months into the future

        #puts("#{$programs_in_the_school_with_titles}")
        #puts("#{$programs_in_the_school_with_titles[@program_code]}")
        #puts("#{$programs_in_the_school_with_titles[@program_code]['title_en']}")

        # all TIVNM students can only take a degree project course with an A-F grade
        if %w(TIVNM ).include? @program_code 
          @graded_or_ungraded_question='<p><span lan="en">All students in ' + @program_code + ' must have A-F grading.</span>/<span lan="sv">Alla elever i ' + @program_code + ' måste ha A-F-gradering.</p>'
        else
          @graded_or_ungraded_question='<h2><span lang="en">Grading scale</span>|<span lang="sv">Betygsskala</span></h2>
        <p><span lang="en">Do you wish an A-F grade, rather than the default P/F (i.e. Pass/Fail) grade for your degree project?</span> |         <span lang="sv">Vill du ha ett betygsatt exjobb (A-F), i stället för ett vanligt med bara P/F (Pass/Fail)?</span></p>
          <span>
              <span>
                  <input type="radio" name="grading_scale"  value="grading_scale_AF"/>&nbsp;<span lan="en">Grade A-F</span> | <span lang="sv">Betygsatt exjobb (A-F)</span><br>
              </span>
              <span>
                  <input type="radio" name="grading_scale"  value="grading_scale_PF" checked="checked" autofocus required="required"/>&nbsp;<span lang="en">Pass/Fail (standard)</span> | <span lang="sv">Godkänd eller underkänd (standard)</span>
              </span>
           </span>'
        end

        
	# now render a simple form the user will submit to "take the quiz"
        <<-HTML
          <html>
          <head><title>Dynamic survey for replacing UT-EXAR form</title></head>
          <body>
          <h1>Application for a #{@cycle_number_ordinal} cycle degree project</h1>
          <form action="/assessment" method="post">
          <p><span lang="en">As a student in the #{$programs_in_the_school_with_titles[@program_code]['title_en']} (#{@program_code}) you need to complete a degree project. This survey collects some data to help admininster your project and to you register for the correct course and be assigned an appropriate examiner.</span> | <span lang="sv">Som student i #{$programs_in_the_school_with_titles[@program_code]['title_sv']} (#{@program_code}) måste du slutföra ett examensarbete. Denna undersökning samlar in några data för att hjälpa till att administrera ditt projekt och att du registrerar dig för rätt kurs och tilldelas en lämplig granskare.</span></p>

          <h2><span lang="en">Full text in DiVA</span> | <span lang="sv">Fulltext i DiVA</span></h2>
          <p><span lang="en">Do you give KTH permission to make the full text of your final report available via DiVA?</span> | <span lang="sv">Ger du KTH tillstånd att publicera hela din slutliga exjobbsrapport elektroniskt i databasen DiVA?</span></p>
          <p><strong><span lang="en">Note that in all cases the report is public and KTH must provide a copy to anyone on request.</span> | <span lang="sv">Observera att din slutliga exjobbsrapport alltid är offentlig, och att KTH alltid måste tillhandahålla en kopia om någon begär det.</span></strong></p>
          <span>
              <span>
                  <input type="radio" name="diva_permission"  value="yes_to_diva" checked="checked" autofocus required="required"/>&nbsp;<span lang="en">I accept publication via DiVA</span> | <span lang="sv">Jag godkänner publicering via DiVA</span><br>
              </span>
              <span>
                  <input type="radio" name="diva_permission"  value="no_to_diva" />&nbsp;<span lang="en">I do not accept publication via DiVA</span> | <span lang="sv">Jag godkänner inte publicering via DiVA</span>
              </span>
           </span>

           <h2><span lang="en">Tentative title</span> | <span lang="sv">Preliminär titel</span></h2>
           <input name='Tentative_title' type='text' width='1000' id='Tentative_title' />

           <h2><span lang="en">Project Description</span> | <span lang="sv">Projekt beskrivning</span></h2>
           <input name='Prelim_description' type='text' width='1000' id='Prelim_description' />

           <h2><span lang="en">At a company, indicate name</span> | <span lang="sv">På företag, ange vilket</span></h2>
           <input name='company' type='text' width='1000' id='company' />

           <h2><span lang="en">Outside Sweden, indicate Country</span> | <span lang="sv">Utomlands, ange land</span></h2>

           <select id="country_code" name="country_code">
           <option value="">--Please choose a contry code | Vänligen välj en landskod--</option>
           <option value="AF">Afghanistan</option>
           <option value="AX">Åland Islands</option>
           <option value="AL">Albania</option>
           <option value="DZ">Algeria</option>
           <option value="AS">American Samoa</option>
           <option value="AD">Andorra</option>
           <option value="AO">Angola</option>
           <option value="AI">Anguilla</option>
           <option value="AQ">Antarctica</option>
           <option value="AG">Antigua and Barbuda</option>
           <option value="AR">Argentina</option>
           <option value="AM">Armenia</option>
           <option value="AW">Aruba</option>
           <option value="AU">Australia</option>
           <option value="AT">Austria</option>
           <option value="AZ">Azerbaijan</option>
           <option value="BS">Bahamas</option>
           <option value="BH">Bahrain</option>
           <option value="BD">Bangladesh</option>
           <option value="BB">Barbados</option>
           <option value="BY">Belarus</option>
           <option value="BE">Belgium</option>
           <option value="BZ">Belize</option>
           <option value="BJ">Benin</option>
           <option value="BM">Bermuda</option>
           <option value="BT">Bhutan</option>
           <option value="BO">Bolivia, Plurinational State of</option>
           <option value="BQ">Bonaire, Sint Eustatius and Saba</option>
           <option value="BA">Bosnia and Herzegovina</option>
           <option value="BW">Botswana</option>
           <option value="BV">Bouvet Island</option>
           <option value="BR">Brazil</option>
           <option value="IO">British Indian Ocean Territory</option>
           <option value="BN">Brunei Darussalam</option>
           <option value="BG">Bulgaria</option>
           <option value="BF">Burkina Faso</option>
           <option value="BI">Burundi</option>
           <option value="KH">Cambodia</option>
           <option value="CM">Cameroon</option>
           <option value="CA">Canada</option>
           <option value="CV">Cape Verde</option>
           <option value="KY">Cayman Islands</option>
           <option value="CF">Central African Republic</option>
           <option value="TD">Chad</option>
           <option value="CL">Chile</option>
           <option value="CN">China</option>
           <option value="CX">Christmas Island</option>
           <option value="CC">Cocos (Keeling) Islands</option>
           <option value="CO">Colombia</option>
           <option value="KM">Comoros</option>
           <option value="CG">Congo</option>
           <option value="CD">Congo, the Democratic Republic of the</option>
           <option value="CK">Cook Islands</option>
           <option value="CR">Costa Rica</option>
           <option value="CI">Côte d'Ivoire</option>
           <option value="HR">Croatia</option>
           <option value="CU">Cuba</option>
           <option value="CW">Curaçao</option>
           <option value="CY">Cyprus</option>
           <option value="CZ">Czech Republic</option>
           <option value="DK">Denmark</option>
           <option value="DJ">Djibouti</option>
           <option value="DM">Dominica</option>
           <option value="DO">Dominican Republic</option>
           <option value="EC">Ecuador</option>
           <option value="EG">Egypt</option>
           <option value="SV">El Salvador</option>
           <option value="GQ">Equatorial Guinea</option>
           <option value="ER">Eritrea</option>
           <option value="EE">Estonia</option>
           <option value="ET">Ethiopia</option>
           <option value="FK">Falkland Islands (Malvinas)</option>
           <option value="FO">Faroe Islands</option>
           <option value="FJ">Fiji</option>
           <option value="FI">Finland</option>
           <option value="FR">France</option>
           <option value="GF">French Guiana</option>
           <option value="PF">French Polynesia</option>
           <option value="TF">French Southern Territories</option>
           <option value="GA">Gabon</option>
           <option value="GM">Gambia</option>
           <option value="GE">Georgia</option>
           <option value="DE">Germany</option>
           <option value="GH">Ghana</option>
           <option value="GI">Gibraltar</option>
           <option value="GR">Greece</option>
           <option value="GL">Greenland</option>
           <option value="GD">Grenada</option>
           <option value="GP">Guadeloupe</option>
           <option value="GU">Guam</option>
           <option value="GT">Guatemala</option>
           <option value="GG">Guernsey</option>
           <option value="GN">Guinea</option>
           <option value="GW">Guinea-Bissau</option>
           <option value="GY">Guyana</option>
           <option value="HT">Haiti</option>
           <option value="HM">Heard Island and McDonald Islands</option>
           <option value="VA">Holy See (Vatican City State)</option>
           <option value="HN">Honduras</option>
           <option value="HK">Hong Kong</option>
           <option value="HU">Hungary</option>
           <option value="IS">Iceland</option>
           <option value="IN">India</option>
           <option value="ID">Indonesia</option>
           <option value="IR">Iran, Islamic Republic of</option>
           <option value="IQ">Iraq</option>
           <option value="IE">Ireland</option>
           <option value="IM">Isle of Man</option>
           <option value="IL">Israel</option>
           <option value="IT">Italy</option>
           <option value="JM">Jamaica</option>
           <option value="JP">Japan</option>
           <option value="JE">Jersey</option>
           <option value="JO">Jordan</option>
           <option value="KZ">Kazakhstan</option>
           <option value="KE">Kenya</option>
           <option value="KI">Kiribati</option>
           <option value="KP">Korea, Democratic People's Republic of</option>
           <option value="KR">Korea, Republic of</option>
           <option value="KW">Kuwait</option>
           <option value="KG">Kyrgyzstan</option>
           <option value="LA">Lao People's Democratic Republic</option>
           <option value="LV">Latvia</option>
           <option value="LB">Lebanon</option>
           <option value="LS">Lesotho</option>
           <option value="LR">Liberia</option>
           <option value="LY">Libya</option>
           <option value="LI">Liechtenstein</option>
           <option value="LT">Lithuania</option>
           <option value="LU">Luxembourg</option>
           <option value="MO">Macao</option>
           <option value="MK">Macedonia, the former Yugoslav Republic of</option>
           <option value="MG">Madagascar</option>
           <option value="MW">Malawi</option>
           <option value="MY">Malaysia</option>
           <option value="MV">Maldives</option>
           <option value="ML">Mali</option>
           <option value="MT">Malta</option>
           <option value="MH">Marshall Islands</option>
           <option value="MQ">Martinique</option>
           <option value="MR">Mauritania</option>
           <option value="MU">Mauritius</option>
           <option value="YT">Mayotte</option>
           <option value="MX">Mexico</option>
           <option value="FM">Micronesia, Federated States of</option>
           <option value="MD">Moldova, Republic of</option>
           <option value="MC">Monaco</option>
           <option value="MN">Mongolia</option>
           <option value="ME">Montenegro</option>
           <option value="MS">Montserrat</option>
           <option value="MA">Morocco</option>
           <option value="MZ">Mozambique</option>
           <option value="MM">Myanmar</option>
           <option value="NA">Namibia</option>
           <option value="NR">Nauru</option>
           <option value="NP">Nepal</option>
           <option value="NL">Netherlands</option>
           <option value="NC">New Caledonia</option>
           <option value="NZ">New Zealand</option>
           <option value="NI">Nicaragua</option>
           <option value="NE">Niger</option>
           <option value="NG">Nigeria</option>
           <option value="NU">Niue</option>
           <option value="NF">Norfolk Island</option>
           <option value="MP">Northern Mariana Islands</option>
           <option value="NO">Norway</option>
           <option value="OM">Oman</option>
           <option value="PK">Pakistan</option>
           <option value="PW">Palau</option>
           <option value="PS">Palestinian Territory, Occupied</option>
           <option value="PA">Panama</option>
           <option value="PG">Papua New Guinea</option>
           <option value="PY">Paraguay</option>
           <option value="PE">Peru</option>
           <option value="PH">Philippines</option>
           <option value="PN">Pitcairn</option>
           <option value="PL">Poland</option>
           <option value="PT">Portugal</option>
           <option value="PR">Puerto Rico</option>
           <option value="QA">Qatar</option>
           <option value="RE">Réunion</option>
           <option value="RO">Romania</option>
           <option value="RU">Russian Federation</option>
           <option value="RW">Rwanda</option>
           <option value="BL">Saint Barthélemy</option>
           <option value="SH">Saint Helena, Ascension and Tristan da Cunha</option>
           <option value="KN">Saint Kitts and Nevis</option>
           <option value="LC">Saint Lucia</option>
           <option value="MF">Saint Martin (French part)</option>
           <option value="PM">Saint Pierre and Miquelon</option>
           <option value="VC">Saint Vincent and the Grenadines</option>
           <option value="WS">Samoa</option>
           <option value="SM">San Marino</option>
           <option value="ST">Sao Tome and Principe</option>
           <option value="SA">Saudi Arabia</option>
           <option value="SN">Senegal</option>
           <option value="RS">Serbia</option>
           <option value="SC">Seychelles</option>
           <option value="SL">Sierra Leone</option>
           <option value="SG">Singapore</option>
           <option value="SX">Sint Maarten (Dutch part)</option>
           <option value="SK">Slovakia</option>
           <option value="SI">Slovenia</option>
           <option value="SB">Solomon Islands</option>
           <option value="SO">Somalia</option>
           <option value="ZA">South Africa</option>
           <option value="GS">South Georgia and the South Sandwich Islands</option>
           <option value="SS">South Sudan</option>
           <option value="ES">Spain</option>
           <option value="LK">Sri Lanka</option>
           <option value="SD">Sudan</option>
           <option value="SR">Suriname</option>
           <option value="SJ">Svalbard and Jan Mayen</option>
           <option value="SZ">Swaziland</option>
           <option value="SE">Sweden</option>
           <option value="CH">Switzerland</option>
           <option value="SY">Syrian Arab Republic</option>
           <option value="TW">Taiwan, Province of China</option>
           <option value="TJ">Tajikistan</option>
           <option value="TZ">Tanzania, United Republic of</option>
           <option value="TH">Thailand</option>
           <option value="TL">Timor-Leste</option>
           <option value="TG">Togo</option>
           <option value="TK">Tokelau</option>
           <option value="TO">Tonga</option>
           <option value="TT">Trinidad and Tobago</option>
           <option value="TN">Tunisia</option>
           <option value="TR">Turkey</option>
           <option value="TM">Turkmenistan</option>
           <option value="TC">Turks and Caicos Islands</option>
           <option value="TV">Tuvalu</option>
           <option value="UG">Uganda</option>
           <option value="UA">Ukraine</option>
           <option value="AE">United Arab Emirates</option>
           <option value="GB">United Kingdom</option>
           <option value="US">United States</option>
           <option value="UM">United States Minor Outlying Islands</option>
           <option value="UY">Uruguay</option>
           <option value="UZ">Uzbekistan</option>
           <option value="VU">Vanuatu</option>
           <option value="VE">Venezuela, Bolivarian Republic of</option>
           <option value="VN">Viet Nam</option>
           <option value="VG">Virgin Islands, British</option>
           <option value="VI">Virgin Islands, U.S.</option>
           <option value="WF">Wallis and Futuna</option>
           <option value="EH">Western Sahara</option>
           <option value="YE">Yemen</option>
           <option value="ZM">Zambia</option>
           <option value="ZW">Zimbabwe</option>
           </select>

           <h2><span lang="en">At another university</span> | <span lang="sv">På annan högskola</span></h2>
           <input name='university' type='text' width='1000' id='university' />

           <h2><span lang="en">Contact</span> | <span lang="sv">Kontaktinformation</span></h2>
           <p><span lang="en">Enter the name and contact details of your contact at a company, other university, etc.</span> | <span lang="sv">Ange namn, e-postadress och annan kontaktinformation f&ouml;r din kontaktperson vid f&ouml;retaget, det andra universitetet, eller motsvarande.</span></p>
           <input name='contact' type='text' width='1000' id='contact' />

           
           <h2><span lang="en">Planned start</span>/<span lang="sv">Startdatum</span></h2>
           <label for="start">Date/Datum:</label>

           <input type="date" id="start" name=planned_start
                  value=#{planned_start_today}
                  min=#{planned_start_min}
                  max=#{planned_start_max}>

            #{@graded_or_ungraded_question}
           <br><input type='submit' value='Submit' />
          </form>
          </body>
          </html>
        HTML
end

# This is the action that the form submits to with the score that the student entered.
# In lieu of a real assessment, that score is then just submitted back to Canvas.
post "/assessment" do
  # obviously in a real tool, we're not going to let the user input their own score
  # score = params['score']
  # if !score || score.empty?
  #   redirect to("/getProgramData")
  # end

  @diva_permission = params['diva_permission']
  puts "diva_permission is #{@diva_permission}"
  session['diva_permission']=@diva_permission

  @tentative_title = params['Tentative_title']
  puts "Tentative_title is #{@tentative_title}"
  session['Tentative_title']=@tentative_title

  @prelim_description = params['Prelim_description']
  puts "prelim_description is #{@prelim_description}"
  session['prelim_description']=@prelim_description


  @company = params['company']
  puts "company is #{@company}"
  session['company']=@company

  #@country = params['country']
  #puts "country is #{@country}"

  @country_code = params['country_code']
  puts("country_code is #{@country_code}")
  session['country_code']=@country_code

  @university = params['university']
  puts "university is #{@university}"
  session['university']=@university

  @contact = params['contact']
  puts "contact is #{@contact}"
  session['contact']=@contact

  @planned_start = params['planned_start']
  puts("planned_start is #{@planned_start}")
  session['planned_start']=@planned_start

  if params.has_key?('grading_scale') 
    @grading_scale = params['grading_scale']
  else
    @grading_scale = 'grading_scale_AF'
  end
  puts("grading_scale is #{@grading_scale}")

  session['grading_scale']=@grading_scale  

  if @grading_scale == 'grading_scale_AF'
    redirect to("/grading_scale_AF")
  else
    redirect to("/grading_scale_PF")
  end
	
end

get '/grading_scale_AF' do
  puts("in the handler for grading_scale_AF")
  @courses=AF_courses.sort
  puts("courses is #{  @courses}")

  @program_code=session['program_code']
  @courses = filter_courses_for_a_program( @program_code, cycle_number, 'AF', @courses)

  @course_options=''
  @courses.each do |course|
    @title=$relevant_courses_English[course]['title']
    @title_s=$relevant_courses_Swedish[course]['title']
    @credits=$relevant_courses_English[course]['credits']
    #puts("course is #{course}")
    #puts("title is #{@title}")
    #puts("title is #{@title_s}")
    #puts("credits is #{@credits}")

    @course_options=@course_options+'<option value="'+course+'">'+course+': '+@credits+' '+@title+' | '+@title_s+'</option>'
  end

  puts("course_options is #{@course_options}")
  
  <<-HTML 
  <html > 
	<head ><title >Courses with A-F grading scales</title ></head > 
	<body >
          <form action="/Examiner" method="post">
          <h2><span lang="en">Course code graded A-F</span>|<span lang="sv">Kurskod - Betygsatt exjobb (A-F)</span></h2>
          <select id="selected_course" name="selected_course">
          #{@course_options}
          </select>

           <br><input type='submit' value='Submit' />
          </form>
	</body >
   </html > 
   HTML

end


get '/grading_scale_PF' do
  puts("in the handler for grading_scale_PF")
  @courses=PF_courses.sort
  puts("courses is #{  @courses}")

  @program_code=session['program_code']
  @courses = filter_courses_for_a_program( @program_code, cycle_number, 'PF', @courses)

  @course_options=''
  @courses.each do |course|
    @title=$relevant_courses_English[course]['title']
    @title_s=$relevant_courses_Swedish[course]['title']
    @credits=$relevant_courses_English[course]['credits']

    #puts("course is #{course}")
    #puts("title is #{@title}")
    #puts("title is #{@title_s}")
    #puts("credits is #{@credits}")

    @course_options=@course_options+'<option value="'+course+'">'+course+': '+@credits+' '+@title+' | '+@title_s+'</option>'
  end

  puts("course_options is #{@course_options}")
  
  <<-HTML 
  <html > 
	<head ><title >Courses with P/F grading scales</title ></head > 
	<body >
          <form action="/Examiner" method="post">
          <h2><span lang="en">Course code with Pass/Fail grading</span>|<span lang="sv">Kurskod med betygsatt Godkänd eller underkänd</span></h2>
          <select id="selected_course" name="selected_course">
          #{@course_options}
          </select>

           <br><input type='submit' value='Submit' />
          </form>
	</body >
   </html > 
   HTML

end

post '/Examiner' do
  if params.has_key?('selected_course') 
    @selected_course = params['selected_course']
    puts "selected_course is #{@selected_course}"
    session['selected_course']=@selected_course # store it in the session for use later
  end
  @potential_examiners=all_course_examiners[@selected_course].sort
  puts("@potential_examiners is #{@potential_examiners}")
  
  if @potential_examiners.length > 0
    @examiner_options=''
    @potential_examiners.each do |examiner|
      #puts("examiner is #{examiner}")
      @examiner_options=@examiner_options+'<option value="'+examiner+'">'+examiner+'</option>'
    end

  
    <<-HTML 
      <html > 
	<head ><title >Potential Examiner|Potentiell Examinator</title ></head > 
	<body > 
          <form action="/Outcome" method="post">
          <h2><span lang="en">Potential Examiner</span>/<span lang="sv">Potentiell Examinator</span></h2>
          <select id="selected_examiner" name="selected_examiner">
          #{@examiner_options}
          </select>

           <br><input type='submit' value='Submit' />
          </form>
	</body > 
      </html > 
    HTML

  else
    puts("There are no examiners for the course #{@selected_course}")
    <<-HTML 
      <html > 
	<head ><title >Examiner|Examinator</title ></head > 
	<body > 
          <h2><span lang="en">Examiner</span>/<span lang="sv">Examinator</span></h2>
          <p><span lang="en">There are no examiners for the course #{@selected_course}.</span> | <span lang="sv">Det finns ingen examinator för kursen #{@selected_course}.</span></p>
	</body > 
      </html > 
    HTML
    redirect to("/OutcomeNoExaminer")  
  end    

end

get '/OutcomeNoExaminer' do
  if session.has_key?('selected_course') 
    @selected_course = session['selected_course']
    puts "selected_course is #{@selected_course}"
  end

  <<-HTML 
  <html > 
	<head ><title ><span lang="en">Outcome without examiner</span> | <span lang="sv">Utfall utan examinator</span></title ></head > 
	<body > 
        <p><span lang="en">Thank you for selecting course code #{@selected_course}. Please speak with the education office to find an examiner.</span> | <span lang="sv">Tack för att du valt kurskod #{@selected_course}. Snälla tala med utbildningskontoret för att hitta en examinator.</span<p>
        <p><span lang="en">You have finished the replacement for the paper form. Best of success in your degree project.</span> | <span lang="sv">Du har slutfört ersättningen för pappersblanket. Bäst av framgång i ditt examensarbete.</span></p> 
	</body > 
   </html > 
   HTML

end


post '/Outcome' do
  if session.has_key?('selected_course') 
    @selected_course = session['selected_course']
    puts "selected_course is #{@selected_course}"
  end
  
  if params.has_key?('selected_examiner') 
    @selected_examiner = params['selected_examiner']
    # mark the examainer as tentative
    session['selected_examiner']='⚠⚠'+@selected_examiner
    #puts "potential_examiner is #{@selected_examiner}"
  else
    @selected_examiner = "No examiner selected"
  end

  puts("custom_canvas_course_id is #{session['custom_canvas_course_id']}")
  @list_of_existing_columns=list_custom_columns(session['custom_canvas_course_id'])
  #puts("custom columns are #{@list_of_existing_columns}")
  @col_number=lookup_column_number('Examiner', @list_of_existing_columns)
  #puts("@col_number is #{@col_number}")
  result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Examiner', session['custom_canvas_user_id'],
                                           session['selected_examiner'], @list_of_existing_columns)
  puts("result of the put of custom column data was #{result}")

  
  result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Course_code', session['custom_canvas_user_id'],
                                           session['selected_course'], @list_of_existing_columns)
  puts("result of the put of custom column data was #{result}")

  if session.has_key?('diva_permission') and session['diva_permission'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Student_approves_fulltext', session['custom_canvas_user_id'],
                                             session['diva_permission'], @list_of_existing_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('Tentative_title') and session['Tentative_title'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Tentative_title', session['custom_canvas_user_id'],
                                             session['Tentative_title'], @list_of_existing_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('prelim_description') and session['prelim_description'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Prelim_description', session['custom_canvas_user_id'],
                                             session['prelim_description'], @list_of_existing_columns)
    puts("result of the put of custom column data was #{result}")
  end

  place={}
  if session.has_key?('company') and session['company'].length > 0
    place['company']=session['company']
  end
  if session.has_key?('university') and session['university'].length > 0
    place['university']=session['university']
  end
  if session.has_key?('country_code') and session['country_code'].length > 0
    place['country_code']=session['country_code']
  end
  
  if place.length > 0
    place_as_string=place.collect { |k,v| "#{k} = #{v}" }.join(", ")
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Place', session['custom_canvas_user_id'],
                                             place_as_string, @list_of_existing_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('contact') and session['contact'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Contact', session['custom_canvas_user_id'],
                                             session['contact'], @list_of_existing_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('planned_start') and session['planned_start'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Planned_start_date', session['custom_canvas_user_id'],
                                             session['planned_start'], @list_of_existing_columns)
    puts("result of the put of custom column data was #{result}")
  end

  
  <<-HTML 
  <html > 
	<head ><title ><span lang="en">Outcome</span> | <span lang="sv">Utfall</span></title ></head >
	<body > 
        <p><span lang="en">Thank you for selecting course code #{@selected_course} and potential examiner #{@selected_examiner}.</span> | <span lang="sv">Tack för att du valt kurskod #{@selected_course} och potentiell examinator #{@selected_examiner}.</span<p>
        <p><span lang="en">You have finished the replacement for the paper form. Best of success in your degree project.</span> | <span lang="sv">Du har slutfört ersättningen för pappersblanket. Bäst av framgång i ditt examensarbete.</span></p> 
	</body > 
   </html > 
   HTML

end

get '/Outcome' do
  if params.has_key?('selected_course') 
    @selected_course = params['selected_course']
    puts "selected_course is #{@selected_course}"
  end
  
  <<-HTML 
  <html > 
	<head ><title >Outcome</title ></head > 
	<body > 
			<p>Success!</p> 
	</body > 
   </html > 
   HTML

end

get '/claimStudents' do
  # gqmjr
  course_id=session['custom_coursecode']
  puts("course_id is #{course_id}")
  examiner_sis_id=session['custom_user_sis_id']
  puts("examiner_sis_id is #{examiner_sis_id}")

  examiner_info=get_user_info_from_sis_id(examiner_sis_id)
  puts("examiner_info is #{examiner_info}")

  examiners_name=examiner_info['name']
  session['examiners_name']=examiners_name
  puts("examiners_name is #{examiners_name}")

  list_of_existing_columns=list_custom_columns(course_id)
  examiner_column=get_custom_column_entries_all(course_id, "Examiner", list_of_existing_columns)
  puts("examiner_column is #{examiner_column}")

  list_of_students_to_consider_for_examiner=[]
  examiner_column.each do | e |
    puts("e is #{e}")
    if e['content'][0..1] == $potential_marker and e['content'][2..-1] == examiners_name
      list_of_students_to_consider_for_examiner.append(e['user_id'])
    end
  end

  puts("list_of_students_to_consider_for_examiner is #{list_of_students_to_consider_for_examiner}")
  
  list_of_students=""
  list_of_students_to_consider_for_examiner.each do |s_id| 
    list_of_students=list_of_students+
                      '<span><input type="radio" name="'+"#{s_id}"+
                      '" value="'+"#{s_id}"+
                      '"}/>'+get_user_info_from_user_id(s_id)['name']+
                      '</span><br>'
  end
  
  # now render a simple form
  <<-HTML
  <html>
  <head><title>Claim students for #{examiners_name}</title></head>
  <body>
  	<h1>Claim students for #{examiners_name}</h1>
        <form action="/examinersClaim" method="post">

        <h2>Click the radio button to claim a student</span></h2>

        #{list_of_students}

        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html>
   HTML
 
end

post '/examinersClaim' do
  # params contain the students that have been selected
  students_to_claim_hash=params
  students_to_claim=[]
  
  students_to_claim_hash.each do |s, u|
    students_to_claim.append(s.to_i)
  end

  puts("students_to_claim is #{students_to_claim}")

  course_id=session['custom_coursecode']
  puts("course_id is #{course_id}")

  examiners_name=session['examiners_name']

  list_of_existing_columns=list_custom_columns(course_id)
  puts("list_of_existing_columns is #{list_of_existing_columns}")
  course_code_column=get_custom_column_entries_all(course_id, "Course_code", list_of_existing_columns)
  puts("course_code_column is #{course_code_column}")

  list_of_students_for_examiner=[]
  course_code_column.each do | cc |
    puts("cc is #{cc}")
    if students_to_claim.include? cc['user_id'] 
      puts("considering #{cc['user_id']}")
      if cc['content'][0..1] == $potential_marker
         students_course_code=cc['content'][2..-1]
      else
        students_course_code=cc['content']
      end

      # check if this examiner is one of the examiners for the student's selected course code
      examiners_for_course=$all_course_examiners[students_course_code]
      if examiners_for_course.include? examiners_name
        list_of_students_for_examiner.append(cc['user_id'] )
        puts("examiner is an examiner for the course #{students_course_code}")
      end
    end
  end
  puts("list_of_students_for_examiner is #{list_of_students_for_examiner}")

  existing_sections=sections_in_course(course_id)
  #puts("existing_sections are #{existing_sections}")

  examiners_section_id=section_id_with_name(examiners_name, existing_sections)
  puts("examiners_section_id is #{examiners_section_id}")
  students_in_examiners_section=list_enrollments_in_section(examiners_section_id)
  puts("students_in_examiners_section are #{students_in_examiners_section}")

  students_in_examiners_section.each do |s|
    user_id=s['user_id']
    if list_of_students_for_examiner.include? user_id
      puts("student #{ s['user_id']} is already in the examiner's section")
    else
      #add student to the examiner's section
      puts("adding student #{ s['user_id']} to the examiner's section")
      enroll_user_in_section(course_id, user_id, 'StudentEnrollment', examiners_section_id)
    end
  end

  awaiting_id=section_id_with_name("Awaiting Assignment of Examiner", existing_sections)
  puts("awaiting_id is #{awaiting_id}")

  students_in_awaiting_section=list_enrollments_in_section(awaiting_id)
  puts("students_in_awaiting_section are #{students_in_awaiting_section}")
  # 
  students_in_awaiting_section.each do |s|
    user_id=s['user_id']
    enrollment_id=s['id']
    if list_of_students_for_examiner.include? user_id
      puts("student #{user_id} is enrolled as #{enrollment_id} in the awaiting section, removing student from section")
      remove_user_from_section(course_id, enrollment_id, awaiting_id)
    end
  end

  # put the examiner's name into the examiner column for each of the students
  examiner_column_id=lookup_column_number("Examiner", list_of_existing_columns)
  puts("examiner_column_id is #{examiner_column_id}")
  list_of_students_for_examiner.each do |s|
    put_custom_column_entry(course_id, examiner_column_id, s,  examiners_name)
  end
    
  # now process the next batch based on those in the awaiting section
  redirect to("/getURL")

end

get '/Reload' do
  # get configuration data
  all_data= JSON.parse(File.read('course-data-EECS-cycle-2.json'))
  puts "cycle_number is #{all_data['cycle_number']}"
  puts "school_acronym is #{all_data['school_acronym']}"

  programs_in_the_school_with_titles=all_data['programs_in_the_school_with_titles']
  # filter out the programs that are not at the desired cucle
  $programs_in_the_school_with_titles=programs_in_cycle(cycle_number, programs_in_the_school_with_titles)
  #puts("filtered $programs_in_the_school_with_titles is #{$programs_in_the_school_with_titles}")

  dept_codes=all_data['dept_codes']
  all_course_examiners=all_data['all_course_examiners']
  AF_courses=all_data['AF_courses']
  PF_courses=all_data['PF_courses']
  $relevant_courses_English=all_data['relevant_courses_English']
  $relevant_courses_Swedish=all_data['relevant_courses_Swedish']


  <<-HTML 
  <html > 
	<head ><title >Reload configuration file</title ></head > 
	<body > 
			<p>Successfully reloaded porogram and examiner data for  #{all_data['school_acronym']} cyle #{all_data['cycle_number']}</p> 
	</body > 
   </html > 
   HTML
end
