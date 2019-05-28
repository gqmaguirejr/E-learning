# coding: utf-8
#
# program to help administrtors with a degree project
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
require 'net/http/post/multipart'
require 'open-uri'

set :port, 3598                   # an port to use
load 'sinatra_ssl.rb'
set :ssl_certificate, "/home/maguire/certificates_for_canvas_docker/server.crt"
set :ssl_key, "/home/maguire/certificates_for_canvas_docker/server.key"

$link_parser = Nitlink::Parser.new # for use with paginated replies

$oauth_key = "test"
$oauth_secret = "secret"

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

dept_codes=all_data['dept_codes']
all_course_examiners=all_data['all_course_examiners']
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

def get_custom_column_entries(course_id, column_name, user_id, list_of_existing_columns)
  @column_number=lookup_column_number(column_name, list_of_existing_columns)
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #GET /api/v1/courses/:course_id/custom_gradebook_columns/:id/data
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{@column_number}/data"
  puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header )
  puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  data=@getResponse.parsed_response
  data.each do |u|
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

def select_from_list_by_name(target_name, full_list)
  full_list.each do |elem|
    if elem['name'] == target_name
      return elem
    end
  end
end

def getProgramData(sis_id)

	@payload={"ns" => "se.kth.canvas-app.program_of_study"}

        puts "in getProgramData sis_id is #{sis_id}"
        @url_to_use = "http://#{$canvas_host}/api/v1/users/sis_user_id:#{sis_id}/custom_data/program_of_study"
        puts "url_to_use is #{@url_to_use}"
        starting = Process.clock_gettime(Process::CLOCK_MONOTONIC)
        # time consuming operation
        @getResponse = HTTParty.get(@url_to_use,:body => @payload.to_json, :headers => $header )
        ending = Process.clock_gettime(Process::CLOCK_MONOTONIC)
        elapsed = ending - starting
        puts("elapsed time to get a user's custom data is #{elapsed} seconds")

        # @getResponse = HTTParty.get(base_url,:body => @payload.to_json, :headers => $header )
        puts "getResponse is #{@getResponse}"
        @class_of_response=@getResponse.class
        puts "class of getResponse is #{@class_of_response}"
        puts "getResponse.code is #{@getResponse.code}"

        puts "getResponse.body is #{@getResponse.body}"

        if @getResponse.code > 200
          puts("The user had no program data stored for them.")
          return []
        end

        @return_data=@getResponse['data']
        return @return_data
end

def putProgramData(sis_id, program_data)
# program_data must be of the form: {"programs": [{"code": "TCOMK", "name": "Information and Communication Technology", "start": 2016}]}
	@payload={ns: "se.kth.canvas-app.program_of_study",
                  data: program_data}

        puts "at start of putProgramData, payload = #{@payload} "

        @url = "http://#{$canvas_host}/api/v1/users/self/custom_data/program_of_study"
	@putResponse = HTTParty.put(@url,  
                         :body => @payload.to_json,
                         :headers => $header)
						 
	puts "putResponse.body is #{@putResponse.body}"
end

def getStudentDataName(sis_id)
  #GET /api/v1/users/:id
  @url_to_use = "http://#{$canvas_host}/api/v1/users/sis_user_id:#{sis_id}"
  puts "url_to_use is #{@url_to_use}"
  @getResponse = HTTParty.get(@url_to_use,:body => @payload.to_json, :headers => $header )
  return @getResponse
end

def getStudentName(student_data)
  return student_data['name']
end

##### start of routes

post '/start' do
  begin
    signature = OAuth::Signature.build(request, :consumer_secret => $oauth_secret)
    puts "In start1 - signature = #{signature}"
    signature.verify() or raise OAuth::Unauthorized
  rescue OAuth::Signature::UnknownSignatureMethod,
         OAuth::Unauthorized
    return %{unauthorized attempt. make sure you used the consumer secret "#{$oauth_secret}"}
  end

  puts "In start - signature = #{signature}"

  # store the relevant parameters from the launch into the user's session, for
  # access during subsequent http requests.
  # note that the name and email might be blank, if the tool wasn't configured
  # in Canvas to provide that private information.
  %w(lis_outcome_service_url lis_result_sourcedid lis_person_name_full lis_person_contact_email_primary 
  lis_person_sourcedid custom_canvas_course_id custom_canvas_user_id
  ).each { |v| session[v] = params[v] }

  puts "params are #{params}"
  puts "session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}"
  puts "session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}"

  redirect to("/getID")
end

post '/getID' do
  puts("in POST route for /getID")
  puts "params are #{params}"
  puts("request is #{request}")
  puts("$oauth_secret is #{$oauth_secret}")
  begin
    signature = OAuth::Signature.build(request, :consumer_secret => $oauth_secret)
    puts "In getID - signature = #{signature}"
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
  custom_user_sis_id
  ).each { |v| session[v] = params[v] }

  puts "session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}"
  puts "session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}"
  puts "session['custom_sis_id'] is #{session['custom_sis_id']}"
  puts "session['custom_user_sis_id'] is #{session['custom_user_sis_id']}"
  <<-HTML 
          <form action="/gotStudentsID" method="post">
          <h2>Enter student's KTH-id</span> | <span lang="sv">Ange studentens KTH:ID?</span></h2>
          <input name='s_ID' type='text' style="width: 600px;" id='s_ID' />
          <input type='submit' value='Submit' />

          </form>
   HTML


  # redirect to("/getURL")
end

get '/getID' do
  puts("in GET route for /getID")
  <<-HTML 
          <form action="/gotStudentsID" method="post">
          <h2>Enter student's KTH-id</span> | <span lang="sv">Ange studentens KTH:ID?</span></h2>
          <input name='s_ID' type='text' style="width: 600px;" id='s_ID' />
          <input type='submit' value='Submit' />

          </form>
   HTML
end

post '/gotStudentsID' do
  puts "params are #{params}"
   s_ID=params['s_ID']
   puts("s_ID is #{s_ID}")
   
   if !s_ID || s_ID.empty?
     redirect to("/getID")
    end
   session['s_ID']=s_ID
   puts("s_ID is #{s_ID}")

   redirect to("/processDataForStudent")
end

get '/processDataForStudent' do

  student_data=getStudentDataName(session['s_ID'])
  puts("student_data is #{student_data}")

  students_name=getStudentName(student_data)
  puts("students_name is #{students_name}")
  session['students_name']=students_name

  program_data=getProgramData(session['s_ID'])
  puts "program_data is #{program_data}"
  if program_data.length == 0
    puts("Student is not in any existing program.")
    @existing_programs='<p>Student is not in any existing program.</p>'
    redirect to("/addProgramForStudent")
  else
    #  {"programs"=>[{"code"=>"CINTE", "name"=>"Degree Programme in Information and Communication Technology", "major"=>"Elektroteknik", "start"=>2016}]}
    @prog_entry=0
    if program_data.length > 1 
      @existing_programs='<p><span lang="en">Existing programs</span></p>'
    else
      @existing_programs='<p><span lang="en">Existing program</span></p>'
    end
    students_programs=program_data['programs']
    students_programs.each do |prog|
      prog_index="program_#{@prog_entry}"
      #puts("prog_index is #{prog_index}")
      prog_code="#{prog['code']}"
      #puts("prog_code is #{prog_code}")
      prog_name="#{prog['name']}"
      prog_major="#{prog['major']}"
      prog_start="#{prog['start']}"
      prog_end="#{prog['end']}"
      if !prog_end || prog_end.empty?
        @existing_programs=@existing_programs+
                           '<span><input type="radio" name="'+
                           "#{prog_index}"+
                           '" value="'+
                           "#{prog_code}"+
                           '"}/>'+
                           "#{prog_code}"+
                           '&nbsp;<span lan="en">'+
                           "#{prog_name}"+
                           '</span> | <span lang="sv">'+
                           "#{prog_major}"+
                           '</span> | '+
                           "#{prog_start}"+
                           '<br>'
      else
        @existing_programs=@existing_programs+
                           '<span><input type="radio" name="'+
                           "#{prog_index}"+
                           '" value="'+
                           "#{prog_code}"+
                           '"}/>'+
                           "#{prog_code}"+
                           '&nbsp;<span lan="en">'+
                           "#{prog_name}"+
                           '</span> | <span lang="sv">'+
                           "#{prog_major}"+
                           '</span> | '+
                           "#{prog_start} | #{prog_end}"+
                           '<br>'
      end
    end
  end
  puts("@existing_programs is #{@existing_programs}")

  # now render a simple form

  <<-HTML
    <html>
    <head ><title>Program data for #{students_name}</title></head>
      <body>
  	<h1>Program data for #{students_name}</h1>
        <form action="/deleteProgramData" method="post">
        #{@existing_programs}

        <br><input type='submit' name='action' value='Delete' />
        </form>
      </body>
    </html>
   HTML
  
end

post '/deleteProgramData' do
  puts("params is #{params}")

  sis_id=session['s_ID']
  student_data=getStudentDataName(session['s_ID'])

  # selecting a radio button and pushing Delete will yield as params = {"program_0"=>"TIVNM", "action"=>"Delete"}
  if params.has_key?('action') 
    action=params['action']
    if action == 'Delete'
      (0..10).each do |m|
        key="program_{m}"
        if params.has_key?(key) 
          # remove this program from user's programs
          student_data.tap { |sds| student_data.delete(key) }
        end
      end
    end
    # update the student's program data
    puts("student_data is #{student_data}")
    #putProgramData(sis_id, student_data)

    remaining_programs=getProgramData(sis_id)
    puts("remaining_programs is #{remaining_programs}")
  end
end

get '/addProgramForStudent' do
  student_data=getStudentDataName(session['s_ID'])
  puts("student_data is #{student_data}")
  students_name=getStudentName(student_data)
  puts("students_name is #{students_name}")
  session['students_name']=students_name

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

  # now render a simple form
  <<-HTML
  <html>
  <head><title>Program data for #{students_name}</title></head>
  <body>
  	<h1>Program data for #{students_name}</h1>
        <form action="/updateProgramData" method="post">

        <h2><span lang="en">Update</span> | <span lang="sv">Updatera</span></h2>
        <h3>Which program of study should the student be in?</span> | <span lang="sv">Vilket studieprogram?</span></h2>
        <select if="program_code" name="program_code">
        #{@program_options}
        </select>

        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html>
   HTML

end

post '/updateProgramData' do
   program_code=params['program_code']
   session['program_code']=program_code

   students_name=session['students_name']
   sis_id=session['s_ID']

   @year_options=''
   current_year=Time.now.year
   (0..10).each do |m|
     n=current_year-m
     @year_options=@year_options+'<option value="'+"#{n}"+'">'+"#{n}"+'</option>'     
   end

  <<-HTML
  <html>
  <head><title>Updating program data for #{students_name}</title></head>
  <body>
  	<h1>Updating Program data for #{students_name}</h1>
        <form action="/updateProgramData1" method="post">

        <h2><span lang="en">Update</span> | <span lang="sv">Updatera</span></h2>
        <h3>Which year did the student start the #{program_code} program?</span> | <span lang="sv">Vilket år började studenten programmet #{program_code}?</span></h2>
        <select if="program_start_year" name="program_start_year">
        #{@year_options}
        </select>

        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html>
   HTML

end

post '/updateProgramData1' do
  program_start_year=params['program_start_year']
  session['program_start_year']=program_start_year

  student_data=getStudentDataName(session['s_ID'])
  puts("student_data is #{student_data}")
  students_name=getStudentName(student_data)
  puts("students_name is #{students_name}")
  session['students_name']=students_name

  @major_options=''
  @majors=['Datalogi och datateknik', 'Elektroteknik']
  puts("@majors is #{@majors}")

  @majors.each do |major|
    puts("major is #{major}")
    @major_options=@major_options+
                    '<option value="'+
                    "#{major}"+
                    '">'+
                    "#{major}"+
                    '</option>'
  end

  puts("major_options is #{@major_options}")

  # now render a simple form
  <<-HTML
  <html>
  <head><title>Major data for #{students_name}</title></head>
  <body>
  	<h1>Major data for #{students_name}</h1>
        <form action="/updateProgramData2" method="post">

        <h3>Which major should the student be in?</span> | <span lang="sv">Vilket huvudsubject?</span></h2>
        <select if="major_code" name="major_code">
        #{@major_options}
        </select>

        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html>
   HTML

end


post '/updateProgramData2' do
  major_code=params['major_code']
  
  sis_id=session['s_ID']
  program_code=session['program_code']
  students_name=session['students_name']

  program_start_year=session['program_start_year']


  program_data={"programs": [{"code": "#{program_code}",
                              "name": "#{$programs_in_the_school_with_titles[program_code]['title_en']}",
                              "major": "#{major_code}",
                              "start": "#{program_start_year}"}]}
  # program_data must be of the form: {"programs": [{"code": "TCOMK", "name": "Information and Communication Technology", "start": 2016}]}

  puts("program_data is #{program_data}")
  #putProgramData(sis_id, program_data)

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
