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


# get configuration data'
specializations=JSON.parse(File.read('specialization-eecs.json'))

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
  $PF_courses_by_program=all_data['PF_courses_by_program']
  #puts("$PF_courses_by_program is #{$PF_courses_by_program}")
  $AF_courses_by_program=all_data['AF_courses_by_program']
  #puts("$AF_courses_by_program is #{$AF_courses_by_program}")
  $AF_course_codes_by_program=all_data['AF_course_codes_by_program']
  puts("$AF_course_codes_by_program is #{$AF_course_codes_by_program}")
  $PF_course_codes_by_program=all_data['PF_course_codes_by_program']
  puts("$PF_course_codes_by_program is #{$PF_course_codes_by_program}")

end

def list_students_in_course(course_id)
  students_found=[]
  # Use the Canvas API to get the list of teachers for this course
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/enrollments"
  @payload={:role => ['StudentEnrollment']}
  puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header, :body => @payload.to_json,)
  #puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  links = $link_parser.parse(@getResponse)
  if links.empty?                  # if not paginated, simply return the result of the request
    return @getResponse
  end

  # there was a paginated response
  @getResponse.parsed_response.each do |r|
    students_found.append(r)
  end

  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      students_found.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  return students_found
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

def get_custom_column_entries_by_name(course_id, column_name, user_id, list_of_existing_columns)
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
  puts("@column_number is #{@column_number}")
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #PUT /api/v1/courses/:course_id/custom_gradebook_columns/:id/data/:user_id

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{@column_number}/data/#{user_id}"
  puts "@url is #{@url}"
  #puts("data_to_store is #{data_to_store} and of class #{data_to_store.class}")

  @payload={'column_data': {'content': data_to_store}}
  puts("@payload is #{@payload}")
  @putResponse = HTTParty.put(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  puts("custom columns putResponse.code is  #{@putResponse.code} and putResponse is #{@putResponse}")
  return @putResponse
end

def filter_courses_for_a_program_and_specialization(program_code, major_subject, specialization, cycle_number, grading_scale, courses)
  cycle_code='cycle'+cycle_number
  puts("cycle_code is #{cycle_code}")

  relevant_courses=[]
  if $with_contraints
    if grading_scale == 'AF'
      in_cycle=$AF_courses_by_program[cycle_code] #gqm
      if in_cycle.has_key?(program_code)
        for_major=in_cycle[program_code]
        default_course_code=for_major['default']
        if for_major.has_key?(specialization)
          specialization_course_code=for_major[specialization]
          if specialization_course_code.length > 0
            potentially_relevant_course_codes=specialization_course_code
          else
            potentially_relevant_course_codes=default_course_code
          end
        else
          potentially_relevant_course_codes=default_course_code
        end
      end
    else
      in_cycle=$PF_courses_by_program[cycle_code]
      if in_cycle.has_key?(program_code)
        for_major=in_cycle[program_code]
        default_course_code=for_major['default']
        if for_major.has_key?(specialization)
          specialization_course_code=for_major[specialization]
          if specialization_course_code.length > 0
            potentially_relevant_course_codes=specialization_course_code
          else
            potentially_relevant_course_codes=default_course_code
          end
        else
          potentially_relevant_course_codes=default_course_code
        end
      end
    end

    if not potentially_relevant_course_codes
      puts("no relevant course codes found for #{program_code} in cycle #{cycle_number}")
      return courses            # if there are no course codes, then do not filter
    end

    puts("potentially_relevant_course_codes for #{program_code} in cycle #{cycle_number} are #{potentially_relevant_course_codes}")

    courses.each do |course_code| # you have to iterate this way as programs is a hash
      puts("course_code is #{course_code}")
      if potentially_relevant_course_codes.include?(course_code)
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

        @url = "http://#{$canvas_host}/api/v1/users/sis_user_id:#{sis_id}/custom_data/program_of_study"
	@putResponse = HTTParty.put(@url,  
                         :body => @payload.to_json,
                         :headers => $header)
						 
	puts "putResponse.body is #{@putResponse.body}"
end

def getStudentDataNameByUserID(user_id)
  #GET /api/v1/users/:id
  @url_to_use = "http://#{$canvas_host}/api/v1/users/#{user_id}"
  puts "url_to_use is #{@url_to_use}"
  @getResponse = HTTParty.get(@url_to_use,:body => @payload.to_json, :headers => $header )
  if @getResponse.code > 200
    puts("The user does not exist.")
    return nil
  end

  return @getResponse
end

def getStudentDataName(sis_id)
  #GET /api/v1/users/:id
  @url_to_use = "http://#{$canvas_host}/api/v1/users/sis_user_id:#{sis_id}"
  puts "url_to_use is #{@url_to_use}"
  @getResponse = HTTParty.get(@url_to_use,:body => @payload.to_json, :headers => $header )
  if @getResponse.code > 200
    puts("The user does not exist.")
    return nil
  end

  return @getResponse
end

def getStudentName(student_data)
  return student_data['name']
end

def removeProgramCodeFromPrograms(prog_code,students_programs)
  new_programs=[]
  students_programs.each do |p|
    if p['code'] != prog_code
      new_programs.append(p)
    end
  end
  return new_programs
end

# Enroll a user 
# return the user's Canvas user_id
# currently: ignores section ID
def enroll_user_with_sis_id(course_id, sis_id, role, section_id)
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
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/enrollments"

  @payload={'enrollment': {'user_id': 'sis_user_id:'+sis_id,
                           'type': role,
                           'enrollment_state': 'active' # make the person automatically active in the course
                          }
           }
  puts("@payload is #{@payload}")
  @postResponse = HTTParty.post(@url, 
                              :body => @payload.to_json,
                              :headers => $header )
  #  if section_id              # if there is a section_id then add the users to section
  #    payload['enrollment[course_section_id]']=section_id

  if @postResponse.code == 404 # "404 Not Found"
    puts("student #{sis_id} not in Canvas - status code is #{@postResponse.code}")
    return NIL
  end
  if @postResponse.code > 200
    puts("unable to enroll student #{sis_id} in Canvas course #{course_id}, status code  #{@postResponse.code}")
    return NIL
  else
    puts("inserted person into course")
  end
  return @postResponse['user_id']
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

  # params are {"oauth_consumer_key"=>"test",
  #             "oauth_signature_method"=>"HMAC-SHA1",
  #             "oauth_timestamp"=>"1559242938",
  #             "oauth_nonce"=>"i0bJSnF8uvrP58lZiJj4N0GiPEbdQRqks0lc7cP4",
  #             "oauth_version"=>"1.0",
  #             "context_id"=>"35b23d7061f6864f4d5ee67bf552c73079d30577",
  #             "context_label"=>"J5",
  #             "context_title"=>"Test course 5",
  #             "custom_canvas_api_domain"=>"canvas.docker",
  #             "custom_canvas_course_id"=>"5",
  #             "custom_canvas_enrollment_state"=>"active",
  #             "custom_canvas_user_id"=>"1",
  #             "custom_canvas_user_login_id"=>"chip.maguire@gmail.com",
  #             "custom_canvas_workflow_state"=>"available",
  #             "ext_roles"=>"urn:lti:instrole:ims/lis/Administrator,urn:lti:instrole:ims/lis/Instructor,urn:lti:role:ims/lis/Instructor,urn:lti:sysrole:ims/lis/SysAdmin,urn:lti:sysrole:ims/lis/User",
  #             "launch_presentation_document_target"=>"iframe",
  #             "launch_presentation_height"=>"400",
  #             "launch_presentation_locale"=>"en",
  #             "launch_presentation_return_url"=>"http://canvas.docker/courses/5/external_content/success/external_tool_redirect",
  #             "launch_presentation_width"=>"800",
  #             "lis_person_contact_email_primary"=>"chip.maguire@gmail.com",
  #             "lis_person_name_family"=>"",
  #             "lis_person_name_full"=>"chip.maguire@gmail.com",
  #             "lis_person_name_given"=>"chip.maguire@gmail.com",
  #             "lis_person_sourcedid"=>"z0",
  #             "lti_message_type"=>"basic-lti-launch-request",
  #             "lti_version"=>"LTI-1p0",
  #             "oauth_callback"=>"about:blank",
  #             "resource_link_id"=>"35b23d7061f6864f4d5ee67bf552c73079d30577",
  #             "resource_link_title"=>"AdminIt",
  #             "roles"=>"Instructor,urn:lti:instrole:ims/lis/Administrator",
  #             "tool_consumer_info_product_family_code"=>"canvas",
  #             "tool_consumer_info_version"=>"cloud",
  #             "tool_consumer_instance_contact_email"=>"canvas@canvas.docker",
  #             "tool_consumer_instance_guid"=>"Mx0emRDTpd0ZRMuIdpipqIgmGDUsjrosDsiOeJ17:canvas-lms",
  #             "tool_consumer_instance_name"=>"chiptest",
  #             "user_id"=>"535fa085f22b4655f48cd5a36a9215f64c062838",
  #             "user_image"=>"http://canvas.instructure.com/images/messages/avatar-50.png",
  #             "oauth_signature"=>"dp9fixE0UAw7IpWDuRBJ9cVpRd8="}
  #

  # store the relevant parameters from the launch into the user's session, for
  # access during subsequent http requests.
  # note that the name and email might be blank, if the tool wasn't configured
  # in Canvas to provide that private information.
  %w(lis_outcome_service_url lis_result_sourcedid lis_person_name_full lis_person_contact_email_primary 
  lis_person_sourcedid custom_canvas_course_id custom_canvas_user_id custom_sis_id
  custom_user_sis_id ext_roles
  ).each { |v| session[v] = params[v] }

  puts "session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}"
  puts "session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}"
  puts "session['custom_sis_id'] is #{session['custom_sis_id']}"
  puts "session['custom_user_sis_id'] is #{session['custom_user_sis_id']}"

  puts "session['ext_roles'] is #{session['ext_roles']}"
  ## Only allows this functionality for Instructor,  Administrator, or SysAdmin
  
  allowed_roles = ["urn:lti:instrole:ims/lis/Administrator",
                   "urn:lti:instrole:ims/lis/Instructor",
                   "urn:lti:role:ims/lis/Instructor",
                   "urn:lti:sysrole:ims/lis/SysAdmin"]

  if !params['ext_roles'].match(Regexp.union(allowed_roles))
    return %{This LTI tool can only be used by persons with one of the roles: Instructor,  Administrator, or SysAdmin}
  end

  <<-HTML 
          <form action="/gotStudentsID" method="post">
          <h2>Enter student's KTH-id or user page URL</span> | <span lang="sv">Ange studentens KTH:ID eller user sidor URL?</span></h2>
          <input name='s_ID' type='text' style="width: 600px;" id='s_ID' />
          <input type='submit' value='Submit' />

          </form>
          <script type='text/javascript'>
            document.getElementById('s_ID').value = document.referrer.substring(document.referrer.search('url=') + 4);
            </script>

   HTML

end

get '/getID' do
  puts("in GET route for /getID")
  <<-HTML 
          <form action="/gotStudentsID" method="post">
          <h2>Enter student's KTH-id or user page URL</span> | <span lang="sv">Ange studentens KTH:ID eller user sidor URL?</span></h2>
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
## gqmjr
   puts("s_ID is #{s_ID}")

   # check if this is a number, in which case it is a Canvas user_id
   # a URL for the user, then user_id is the last number
   # if it has a "@", then a primary e-mail address
   # or it must be a sis_id

   session['s_ID']=false

   if s_ID.start_with?('http')
     puts("processing URL to get student identifier")
     elements=s_ID.split('/')
     puts("elements is #{elements}")
     # produces ["http:", "", "canvas.docker", "courses", "2", "users", "8"]
     if (elements[3] == "courses") and  (elements[5] == "users") 
       # check for this student's information
       puts("check for students information #{elements[6]}")
       student_data=getStudentDataNameByUserID(elements[6])
       puts("student_data is  #{student_data}")
       if student_data
         session['s_ID']=student_data['sis_user_id']
       end
     end
   elsif s_ID.include?('@')
     # find matching students's user ID
     list_students_in_course(session['custom_canvas_course_id']).each do |s|
       puts("s is #{s}")
       @url_to_use = "http://#{$canvas_host}/api/v1/users/#{s['user_id']}/profile"
       puts("url_to_use is #{@url_to_use}")
       getResponse = HTTParty.get(@url_to_use, :headers => $header )
       puts("Student is: #{getResponse}") 
       primary_email=getResponse['primary_email']
       if primary_email == s_ID
         session['s_ID']=s['sis_user_id']
         break
       end
     end
   elsif s_ID.match(/\A+?0*[1-9]\d*\Z/)
     student_data=getStudentDataNameByUserID(s_ID)
     if student_data
       session['s_ID']=student_data['sis_user_id']
     end
   else # assume it is a sis_id
     student_data=getStudentDataName(s_ID)
     if student_data
       session['s_ID']=student_data['sis_user_id']
     end
   end

   if !session['s_ID']
     redirect to("/getID")
     puts("no such student - try again")
   end

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
 #  {"programs"=>[{"code"=>"CINTE", "name"=>"Degree Programme in Information and Communication Technology", "major"=>"Elektroteknik", "start"=>2016}]}

  puts "program_data is #{program_data}"
  if program_data.length == 0
    puts("Student is not in any existing program.")
    @existing_programs='<p>Student is not in any existing program.</p>'
    #redirect to("/addProgramForStudent")
  else
    if program_data.has_key?('programs')
      students_programs=program_data['programs']
      puts "students_programs is #{students_programs}"
      if students_programs.length == 0
        puts("Student is not in any existing program.")
        @existing_programs='<p>Student is not in any existing program.</p>'
        #redirect to("/addProgramForStudent")
      else
        prog_entry=0
        if students_programs.length > 1 
          @existing_programs='<p><span lang="en">Existing programs</span></p>'
        else
          @existing_programs='<p><span lang="en">Existing program</span></p>'
        end

        students_programs.each do |prog|
          prog_index="program_#{prog_entry}"
          #puts("prog_index is #{prog_index}")
          prog_code="#{prog['code']}"
          #puts("prog_code is #{prog_code}")
          prog_name="#{prog['name']}"
          prog_major="#{prog['major']}"
          prog_track_code="#{prog['track']}"
          prog_start="#{prog['start']}"
          prog_end="#{prog['end']}"

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
                             "&nbsp;<span lan='en'>#{prog_track_code}</span> | "+
                             "#{prog_start}"
          if prog_end
            @existing_programs=@existing_programs+" | #{prog_end}"
          end
          @existing_programs=@existing_programs+'<br>'
          prog_entry=prog_entry+1
        end
      end
    end
  puts("@existing_programs is #{@existing_programs}")
  end

  # now render a simple form

  <<-HTML
    <html>
    <head ><title>Program data for #{students_name}</title></head>
      <body>
  	<h1>Program data for #{students_name}</h1>
        <form action="/alterProgramData" method="post">
        #{@existing_programs}
        <p>If you check one or more radio boxes in the above list (if it exists), then you can Delete the student from these programs or Enroll the student in the course. Otherwise you can Add the student to a program or enter Next student.</p>
        <br><input type='submit' name='action' value='Delete' />&nbsp;&nbsp;&nbsp;&nbsp;<input type='submit' name='action' value='Add program' />&nbsp;&nbsp;&nbsp;&nbsp;<input type='submit' name='action' value='Enroll' />&nbsp;&nbsp;&nbsp;&nbsp;<input type='submit' name='action' value='Next student' />
        </form>
      </body>
    </html>
   HTML
  
end

post '/alterProgramData' do
  puts("params is #{params}")

  sis_id=session['s_ID']
  # selecting a radio button and pushing Delete will yield as params = {"program_0"=>"TIVNM", "action"=>"Delete"}

  if params.has_key?('action') 
    action=params['action']
    if action == 'Delete'
      student_program_data=getProgramData(session['s_ID'])
      puts("student_program_data is #{student_program_data}")

      if student_program_data
        students_programs=student_program_data['programs']
        puts("students_programs is #{students_programs}")
        
        (0..10).each do |m|
          key="program_#{m}"
          if params.has_key?(key) 
            # remove this program from user's programs
            puts("removing program #{key}")
            students_programs=removeProgramCodeFromPrograms(params[key],students_programs)
          end
        end
        puts("students_programs is now #{students_programs}")

        # update the student's program data
        putProgramData(sis_id, {'programs': students_programs})
        
        remaining_programs=getProgramData(sis_id)
        puts("remaining_programs is/are #{remaining_programs}")

        redirect to("/processDataForStudent")
      end
    elsif action == 'Add program'
      puts("time to add a program")
      redirect to("/addProgramForStudent")
    elsif action == 'Enroll'
      puts("Enroll the student in the degree project course")

      student_program_data=getProgramData(session['s_ID'])
      puts("student_program_data is #{student_program_data}")

      if student_program_data
        students_programs=student_program_data['programs']
        puts("students_programs is #{students_programs}")
        
        (0..10).each do |m|
          key="program_#{m}"
          if params.has_key?(key) 
            # set this as the active program to enroll the student
            puts("enrolling for program #{key}")
            session['program_code']=params[key]
          end
        end
        if !session['program_code']
          session['program_code']=students_programs[0]['code']
          puts("no program was checked using  #{session['program_code']}")
        end
        puts("students_programs is now #{session['program_code']}")


        redirect to("/enrollStudentInCourse")
      else
        puts("Student must be in a program to be enrolled")
        redirect to("/getID")
      end
    elsif action == 'Next student'
      puts("Enter data for the next student")
      redirect to("/getID")
    else
      puts("Unknown action - try again")
      redirect to("/processDataForStudent")
    end
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

  @year_options=''
  current_year=Time.now.year
  (0..10).each do |m|
    n=current_year-m
    @year_options=@year_options+'<option value="'+"#{n}"+'">'+"#{n}"+'</option>'     
  end

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

        <h3>Which year did the student start the program?</span> | <span lang="sv">Vilket år började studenten programmet?</span></h2>
        <select if="program_start_year" name="program_start_year">
        #{@year_options}
        </select>

        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html>
   HTML

end

get '/enrollStudentInCourse' do
  puts("Now it is time to enroll the student in the degree project course")

  sis_id=session['s_ID']
  student_data=getStudentDataName(sis_id)
  puts("student_data is #{student_data}")
  students_name=getStudentName(student_data)
  puts("students_name is #{students_name}")
  session['students_name']=students_name

  course_id=session['custom_canvas_course_id']
  user_id=enroll_user_with_sis_id(course_id, sis_id, 'StudentEnrollment', 0)
  session['user_id']=user_id
  puts("user_id is #{user_id}")

  # Limit student's choice of courses
  cycle_code='cycle'+cycle_number
  puts("cycle_code is #{cycle_code}")

  program_code=session['program_code']
  puts("program_code is #{program_code}")

  prog_name=""
  prog_major=""
  prog_track_code=""
  prog_start=""
  prog_end=""


  students_existing_programs=getProgramData(sis_id)
  if students_existing_programs.length == 0
    puts("Error: Student is not in any existing program.")
    redirect to("/addProgramForStudent")
  else
    if students_existing_programs.has_key?('programs')
      students_programs=students_existing_programs['programs']
      puts "students_programs is #{students_programs}"
      if students_programs.length == 0
        puts("Student is not in any existing program.")
      else
        students_programs.each do |prog|
          if program_code == prog['code']
            prog_name="#{prog['name']}"
            prog_major="#{prog['major']}"
            prog_track_code="#{prog['track']}"
            prog_start="#{prog['start']}"
            prog_end="#{prog['end']}"

            puts("Student is in program #{prog_name} (#{program_code}),  major #{prog_major}, track #{prog_track_code}")
          end
        end
      end
    end
  end

  puts("** Student is in program #{prog_name} (#{program_code}),  major #{prog_major}, track #{prog_track_code}")
  _AF_course_options=''
  _PF_course_options=''
  
  relevant_AF_course_codes=$AF_course_codes_by_program[cycle_code][program_code]
  puts("relevant_AF_course_codes is #{relevant_AF_course_codes}")
  if relevant_AF_course_codes
    courses=relevant_AF_course_codes.sort
  else
    courses=AF_courses
  end
  puts("AF courses is #{courses}")

  course_codes_for_major=[]
  courses.each do |major, options|
    if major == prog_major
      course_codes_for_major=options
    end
  end
  puts("course_codes_for_major is #{course_codes_for_major}")

  if course_codes_for_major.length > 0    # if there are no courses for this major then skip this
       if course_codes_for_major.has_key?(prog_track_code)
         course_codes_for_track=course_codes_for_major[prog_track_code]
       else
         course_codes_for_track=course_codes_for_major["default"]
       end
    course_codes_for_track.each do |course_code|
      title=$relevant_courses_English[course_code]['title']
      title_s=$relevant_courses_Swedish[course_code]['title']
      credits=$relevant_courses_English[course_code]['credits']
      #puts("course is #{course}")
      #puts("title is #{title}")
      #puts("title is #{title_s}")
      #puts("credits is #{credits}")

      _AF_course_options=_AF_course_options+
                         '<span><input type="radio" name="'+course_code+
                         '" value="'+course_code+
                         '"}/>'+course_code+': <span lan="en">' + title +
                         '</span> | <span lang="sv">'+ title_s +
                         '</span><br>'
    end
  end

  puts("_AF_course_options #{_AF_course_options}")

  relevant_PF_course_codes=$PF_course_codes_by_program[cycle_code][program_code]
  puts("relevant_PF_course_codes is #{relevant_PF_course_codes}")
  if relevant_PF_course_codes
    courses=relevant_PF_course_codes.sort
  else
    courses=PF_courses
  end
  puts("PF courses is #{courses}")

  course_codes_for_major=[]
  courses.each do |major, options|
    if major == prog_major
      course_codes_for_major=options
    end
  end
  puts("course_codes_for_major is #{course_codes_for_major}")

  if course_codes_for_major.length > 0   # if there are no courses for this major then skip this
       if course_codes_for_major.has_key?(prog_track_code)
         course_codes_for_track=course_codes_for_major[prog_track_code]
       else
         course_codes_for_track=course_codes_for_major["default"]
       end
    course_codes_for_track.each do |course_code|
      title=$relevant_courses_English[course_code]['title']
      title_s=$relevant_courses_Swedish[course_code]['title']
      credits=$relevant_courses_English[course_code]['credits']
      #puts("course is #{course}")
      #puts("title is #{title}")
      #puts("title is #{title_s}")
      #puts("credits is #{credits}")

      _PF_course_options=_PF_course_options+
                         '<span><input type="radio" name="'+course_code+
                         '" value="'+course_code+
                         '"}/>'+course_code+': <span lan="en">' + title +
                         '</span> | <span lang="sv">'+ title_s +
                         '</span><br>'
    end
  end
  
  # now render a simple form
  <<-HTML
  <html>
  <head><title>Limit choices of course codes for #{students_name}</title></head>
  <body>
  	<h1>Limit choices of course codes for #{students_name}</h1>
        <form action="/limitedCourseCodes" method="post">

        <h3>Which course codes should the student be able to choose?</span> | <span lang="sv">Vilka kurskoder ska studenten kunna välja mellan?</span></h2>

        <h2><span lang="en">Course code graded A-F</span>|<span lang="sv">Kurskod - Betygsatt exjobb (A-F)</span></h2>
          #{_AF_course_options}
          </select>

       <h2><span lang="en">Course code with Pass/Fail grading</span>|<span lang="sv">Kurskod med betygsatt Godkänd eller underkänd</span></h2>

        #{_PF_course_options}
        </select>

        <br><input type='submit' value='Submit' />
        </form>
        </body>
        </html>
   HTML

end

post '/updateProgramDataOLD' do
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

post '/updateProgramData' do
  program_code=params['program_code']
  session['program_code']=program_code

  program_start_year=params['program_start_year']
  session['program_start_year']=program_start_year

  student_data=getStudentDataName(session['s_ID'])
  puts("student_data is #{student_data}")
  students_name=getStudentName(student_data)
  puts("students_name is #{students_name}")
  session['students_name']=students_name

  @major_options=''
  # not that in cycle 1 the major subject is "Teknik"
  @majors=['Datalogi och datateknik', 'Elektroteknik', "Teknisk Fysik"]
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
  session['major_code']=major_code
  puts("major_code is #{major_code}")

  student_data=getStudentDataName(session['s_ID'])
  puts("student_data is #{student_data}")
  students_name=getStudentName(student_data)
  puts("students_name is #{students_name}")
  session['students_name']=students_name


  program_code=session['program_code']
  #track_options=''
  # add a default entry
  track_options='<option value="'+
                     "default"+
                     '">'+
                     "default | <span lang='en'>Default</span> | <span lang='sv'>Standard</span> "+
                    '</option>'

  if specializations.has_key?(program_code)
    tracks_in_program=specializations[program_code]
    puts("tracks_in_program is #{tracks_in_program}")

    tracks_in_program.each do |track_code, track_value|
      puts("track_code is #{track_code}")
      track_options=track_options+
                    '<option value="'+
                     "#{track_code}"+
                     '">'+
                     "#{track_code} | <span lang='en'>#{track_value['en']}</span> | <span lang='sv'>#{track_value['sv']}</span> "+
                    '</option>'
    end

    puts("track_options is #{track_options}")

    # now render a simple form
    <<-HTML
      <html>
        <head><title>Track for #{students_name}</title></head>
        <body>
  	    <h1>Track for #{students_name}</h1>
            <form action="/updateProgramData3" method="post">

            <h3>Which track should the student be in?</span> | <span lang="sv">Vilket spår?</span></h2>
            <select if="track_code" name="track_code">
            #{track_options}
            </select>

            <br><input type='submit' value='Submit' />
            </form>
            </body>
            </html>
    HTML
  else
    # there is not track or tracks for this program
    redirect to("/storeProgramDataNoTrack")
  end
end


get '/storeProgramDataNoTrack' do
  puts("in /storeProgramDataNoTrack")
  sis_id=session['s_ID']
  program_code=session['program_code']
  students_name=session['students_name']
  major_code=session['major_code']

  program_start_year=session['program_start_year']


  program_data=[{"code": "#{program_code}",
                              "name": "#{$programs_in_the_school_with_titles[program_code]['title_en']}",
                              "major": "#{major_code}",
                              "start": "#{program_start_year}"}]
  # program_data must be of the form: {"programs": [{"code": "TCOMK", "name": "Information and Communication Technology", "start": 2016}]}

  puts("program_data is #{program_data}")
  #putProgramData(sis_id, program_data)

  students_existing_programs=getProgramData(sis_id)
  puts("students_existing_programs is #{students_existing_programs}")
  if students_existing_programs.length == 0
    puts("case where there is no existing program")
    putProgramData(sis_id, {'programs': program_data})
  else
    puts("case where there is an existing program or programs")
    putProgramData(sis_id, {'programs': students_existing_programs['programs']+program_data})
  end
  redirect to("/processDataForStudent")
end

post '/updateProgramData3' do
  track_code=params['track_code']
  session['track_code']=track_code
  
  sis_id=session['s_ID']
  program_code=session['program_code']
  students_name=session['students_name']
  major_code=session['major_code']

  program_start_year=session['program_start_year']


  program_data=[{"code": "#{program_code}",
                              "name": "#{$programs_in_the_school_with_titles[program_code]['title_en']}",
                              "major": "#{major_code}",
                              "track": "#{track_code}",
                              "start": "#{program_start_year}"}]
  # program_data must be of the form: {"programs": [{"code": "TCOMK", "name": "Information and Communication Technology", "start": 2016}]}

  puts("program_data is #{program_data}")
  #putProgramData(sis_id, program_data)

  students_existing_programs=getProgramData(sis_id)
  puts("students_existing_programs is #{students_existing_programs}")
  if students_existing_programs.length == 0
    puts("case where there is no existing program")
    putProgramData(sis_id, {'programs': program_data})
  else
    puts("case where there is an existing program or programs")
    putProgramData(sis_id, {'programs': students_existing_programs['programs']+program_data})
  end

  redirect to("/processDataForStudent")
end

post '/limitedCourseCodes' do
  puts("In post /limitedCourseCodes")
  if params.length > 0
    # only limit choices if some limited choices were indicated
    puts("params is #{params}")
    potential_course_code_choices=''
    params.each do |course_code, course_value|
      puts("course_code is #{course_code}")
      potential_course_code_choices=potential_course_code_choices+'|'+course_code
    end
    puts("potential_course_code_choices is #{potential_course_code_choices}")

    sis_id=session['s_ID']

    @list_of_exiting_columns=list_custom_columns(session['custom_canvas_course_id'])
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Course_code', session['user_id'],
                                             $limited_choices_maker+potential_course_code_choices, @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")

    # update the course code column to have the limited list of course codes
  end
  redirect to("/getID")
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
