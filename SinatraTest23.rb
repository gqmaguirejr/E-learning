# coding: utf-8
#
# program provided a dynamic quiz to replace teh KTH UT-EXAR form
#
#
#
require 'sinatra'
require 'json'
require 'httparty'
require 'oauth'
require 'oauth/request_proxy/rack_request'
require 'date'
require 'nitlink'

$oauth_key = "test"
$oauth_secret = "secret"

# version 18 marks the student's selection of potential examiner with ⚠⚠
$potential_marker="⚠⚠"

$with_contraints=true           # determine the course/program file to be read

$link_parser = Nitlink::Parser.new # for use with paginated replies

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

# get configuration data
if $with_contraints
  all_data=JSON.parse(File.read('course-data-EECS-cycle-2c.json'))
else
  all_data=JSON.parse(File.read('course-data-EECS-cycle-2.json'))
end

cycle_number=all_data['cycle_number']
puts "cycle_number is #{cycle_number} and it has class #{cycle_number.class}"
puts "school_acronym is #{all_data['school_acronym']}"


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
$AF_courses=all_data['AF_courses']
$PF_courses=all_data['PF_courses']
$relevant_courses_English=all_data['relevant_courses_English']
$relevant_courses_Swedish=all_data['relevant_courses_Swedish']

if $with_contraints
  $PF_course_codes_by_program=all_data['PF_course_codes_by_program']
  #puts("$PF_course_codes_by_program is #{$PF_course_codes_by_program}")
  $AF_course_codes_by_program=all_data['AF_course_codes_by_program']
  #puts("$AF_course_codes_by_program is #{$AF_course_codes_by_program}")
end

def list_custom_columns(course_id)
  # Use the Canvas API to get the list of custom column for this course
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns"
  puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header )
  #puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  return @getResponse
end

def lookup_column_number(column_name, list_of_exiting_columns)
  list_of_exiting_columns.each do |col|
    #puts("col: #{col}")
    if col['title'] == column_name
      return col['id']
    end
  end
  return -1
end

def get_custom_column_entries_by_name(course_id, column_name, user_id, list_of_existing_columns)
  data=get_all_custom_column_entries_by_name(course_id, column_name, list_of_existing_columns)
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
  
def get_all_custom_column_entries_by_name(course_id, column_name, list_of_existing_columns)
  data_found_thus_far=[]
  @column_number=lookup_column_number(column_name, list_of_existing_columns)
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #GET /api/v1/courses/:course_id/custom_gradebook_columns/:id/data
  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{@column_number}/data"
  puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header )
  puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  links = $link_parser.parse(@getResponse)
  if links.empty?                  # if not paginated, simply return the result of the request
    return @getResponse
  end

  # there was a paginated response
  @getResponse.parsed_response.each do |r|
    data_found_thus_far.append(r)
  end

  while links.by_rel('next')
    lr=links.by_rel('next').target
    #puts("links.by_rel('next').target is #{lr}")
    @getResponse= HTTParty.get(lr, :headers => $header )
    #puts("next @getResponse is #{@getResponse}")
    @getResponse.parsed_response.each do |r|
      data_found_thus_far.append(r)
    end

    links = $link_parser.parse(@getResponse)
  end

  return data_found_thus_far
end

def put_custom_column_entries(course_id, column_number, user_id, data_to_store)
  # Use the Canvas API to get the list of custom column entries for a specific column for the course
  #PUT /api/v1/courses/:course_id/custom_gradebook_columns/:id/data/:user_id

  @url = "http://#{$canvas_host}/api/v1/courses/#{course_id}/custom_gradebook_columns/#{column_number}/data/#{user_id}"
  puts "@url is #{@url}"
  @getResponse = HTTParty.get(@url, :headers => $header )
  puts("custom columns getResponse.code is  #{@getResponse.code} and getResponse is #{@getResponse}")
  return @getResponse
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
  lis_person_sourcedid custom_canvas_course_id custom_canvas_user_id
  ).each { |v| session[v] = params[v] }

  puts "params are #{params}"
  puts "session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}"
  puts "session['custom_canvas_course_id'] is #{session['custom_canvas_course_id']}"

  #redirect to("/putProgramData")
  redirect to("/getProgramData")
end

# note that the route below is not used
#put '/putProgramData' do
get '/putProgramData' do

	@payload={ns: "se.kth.canvas-app.program_of_study",
                  data: {"programs": [{"code": "TCOMK", "name": "Information and Communication Technology", "start": 2016}]}}

        puts "at start of putProgramData -payload = #{@payload} "

        @url = "http://#{$canvas_host}/api/v1/users/self/custom_data/program_of_study"
	@putResponse = HTTParty.put(@url,  
                         :body => @payload.to_json,
                         :headers => $header)
						 
	puts "putResponse.body is #{@putResponse.body}"

	redirect to("/getProgramData")
   
end

# an alterntive to the pull down of country codes is:
#      <input name='country' type='text' pattern="[A-Za-z]{2}" width='20' id='country' />

get '/getProgramData' do

        @url = "http://#{$canvas_host}/api/v1/users/self/profile"
        @getResponse = HTTParty.get(@url, :headers => $header )
        puts "user associated with the TOKEN: is #{@getResponse}"

        @url_to_use = "http://#{$canvas_host}/api/v1/users/sis_user_id:#{session['lis_person_sourcedid']}/profile"
        puts "url_to_use is #{@url_to_use}"
        @getResponse = HTTParty.get(@url_to_use, :headers => $header )
        puts "Calling user: #{@getResponse}"


	@payload={"ns" => "se.kth.canvas-app.program_of_study"}

        puts "in getProgramData session['lis_person_sourcedid'] is #{session['lis_person_sourcedid']}"
        unless session['lis_person_sourcedid'].length > 0
          puts "session['lis_person_sourcedid']=#{session['lis_person_sourcedid']}"
          return %{It looks like there is no usr_sis_id for this user.}
        end
        @url_to_use = "http://#{$canvas_host}/api/v1/users/sis_user_id:#{session['lis_person_sourcedid']}/custom_data/program_of_study"
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
          puts("The user had no program data stored for them. They will have to selected their program.")
          redirect to("/getUserProgram")
        end

        @return_data=@getResponse['data']
        #puts "getResponse['data'] is #{@return_data}"
        @class_of_return_data=@return_data.class
        #puts "class of return_data is #{@class_of_return_data}"

        @return_data=@getResponse['data']['programs']
        #puts "getResponse['data']['programs'] is #{@return_data}"

        @class_of_return_data=@return_data.class
        #puts "class of return_data is #{@class_of_return_data}"

        @program_codes=Array.new
        @return_data.each do |program|
          @program_code=program['code']
          #@class_of_program_code=program['code'].class
          #puts "program is #{program}"
          #puts "program['code'] is #{program['code']}"
          #puts "class of program['code'] is #{@class_of_program_code}"
          #puts "program_code is #{@program_code}"
          @program_codes << @program_code
        end
        if @program_codes.length == 1
          session['program_code']=@program_codes[0]
          puts("There is a single program code: #{session['program_code']}")
        else
          # there is little support for students in multiple programs (yet1)
          session['program_codes']=@program_codes
          puts("There are multple program codes: #{session['program_codes']}")
        end
        redirect to("/getGeneralData")
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
          <select if="program_code" name="program_code">
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
  @program_code=session['program_code']

  @list_of_exiting_columns=list_custom_columns(session['custom_canvas_course_id'])

  result=get_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Course_code', session['custom_canvas_user_id'],
                                            @list_of_exiting_columns)
  puts("result of the getting custom column data was #{result}")
  # for a limited use this might be "⚄⚄|II225X|II245X"
  if result[0..2] == "⚄⚄|"
    limited_choices=result[3..-1].split('|')
    puts("limited_choices is #{limited_choices}")
    @courses=[]
    $AF_courses.each do |c|
      limited_choices.each do |d|
        if c == d
          puts("adding course #{d}")
          @courses=@courses.append(c)
          puts("courses in loop is #{  @courses}")
        end
      end
    end
  else
    @courses=$AF_courses
    @courses = filter_courses_for_a_program( @program_code, cycle_number, 'AF', @courses)
  end
  puts("courses is #{  @courses}")

  @courses = @courses.sort
  puts("courses after filtering is #{  @courses}")

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
          <select if="selected_course" name="selected_course">
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
  @program_code=session['program_code']

  @list_of_exiting_columns=list_custom_columns(session['custom_canvas_course_id'])

  result=get_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Course_code', session['custom_canvas_user_id'],
                                            @list_of_exiting_columns)
  puts("result of the getting custom column data was #{result}")
  # for a limited use this might be "⚄⚄|II225X|II245X"
  if result[0..2] == "⚄⚄|"
    limited_choices=result[3..-1].split('|')
    puts("limited_choices is #{limited_choices}")
    @courses=[]
    $PF_courses.each do |c|
      limited_choices.each do |d|
        if c == d
          puts("adding course #{d}")
          @courses=@courses.append(c)
          puts("courses in loop is #{  @courses}")
        end
      end
    end
  else
    @courses=$PF_courses
    @courses = filter_courses_for_a_program( @program_code, cycle_number, 'PF', @courses)
  end
  puts("courses is #{  @courses}")

  @courses = @courses.sort
  puts("courses after filtering is #{  @courses}")

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
          <select if="selected_course" name="selected_course">
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
  @potential_examiners=$all_course_examiners[@selected_course].sort
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
          <select if="selected_examiner" name="selected_examiner">
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

  session['selected_examiner'] = "No examiner selected"

  puts("custom_canvas_course_id is #{session['custom_canvas_course_id']}")
  @list_of_exiting_columns=list_custom_columns(session['custom_canvas_course_id'])
  #puts("custom columns are #{@list_of_exiting_columns}")
  @col_number=lookup_column_number('Examiner', @list_of_exiting_columns)
  #puts("@col_number is #{@col_number}")
  result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Examiner', session['custom_canvas_user_id'],
                                           $potential_marker+session['selected_examiner'], @list_of_exiting_columns)
  puts("result of the put of custom column data was #{result}")

  
  result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Course_code', session['custom_canvas_user_id'],
                                           $potential_marker+session['selected_course'], @list_of_exiting_columns)
  puts("result of the put of custom column data was #{result}")

  if session.has_key?('diva_permission') and session['diva_permission'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Student_approves_fulltext', session['custom_canvas_user_id'],
                                             session['diva_permission'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('Tentative_title') and session['Tentative_title'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Tentative_title', session['custom_canvas_user_id'],
                                             session['Tentative_title'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('prelim_description') and session['prelim_description'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Prelim_description', session['custom_canvas_user_id'],
                                             session['prelim_description'], @list_of_exiting_columns)
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
                                             place_as_string, @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('contact') and session['contact'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Contact', session['custom_canvas_user_id'],
                                             session['contact'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('planned_start') and session['planned_start'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Planned_start_date', session['custom_canvas_user_id'],
                                             session['planned_start'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  # add student to "Awaiting Assignment of Examiner" section
  add_student_to_sections(session['custom_canvas_course_id'], session['custom_canvas_user_id'], ["Awaiting Assignment of Examiner"])

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
    session['selected_examiner']=@selected_examiner
    #puts "potential_examiner is #{@selected_examiner}"
  else
    @selected_examiner = "No examiner selected"
  end

  puts("custom_canvas_course_id is #{session['custom_canvas_course_id']}")
  @list_of_exiting_columns=list_custom_columns(session['custom_canvas_course_id'])
  #puts("custom columns are #{@list_of_exiting_columns}")
  @col_number=lookup_column_number('Examiner', @list_of_exiting_columns)
  #puts("@col_number is #{@col_number}")
  result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Examiner', session['custom_canvas_user_id'],
                                           $potential_marker+session['selected_examiner'], @list_of_exiting_columns)
  puts("result of the put of custom column data was #{result}")

  
  result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                           'Course_code', session['custom_canvas_user_id'],
                                           $potential_marker+session['selected_course'], @list_of_exiting_columns)
  puts("result of the put of custom column data was #{result}")

  if session.has_key?('diva_permission') and session['diva_permission'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Student_approves_fulltext', session['custom_canvas_user_id'],
                                             session['diva_permission'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('Tentative_title') and session['Tentative_title'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Tentative_title', session['custom_canvas_user_id'],
                                             session['Tentative_title'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('prelim_description') and session['prelim_description'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Prelim_description', session['custom_canvas_user_id'],
                                             session['prelim_description'], @list_of_exiting_columns)
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
                                             place_as_string, @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('contact') and session['contact'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Contact', session['custom_canvas_user_id'],
                                             session['contact'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  if session.has_key?('planned_start') and session['planned_start'].length > 0
    result=put_custom_column_entries_by_name(session['custom_canvas_course_id'],
                                             'Planned_start_date', session['custom_canvas_user_id'],
                                             session['planned_start'], @list_of_exiting_columns)
    puts("result of the put of custom column data was #{result}")
  end

  # add student to "Awaiting Assignment of Examiner" section
  # add student to potential examiner's section
  add_student_to_sections(session['custom_canvas_course_id'], session['custom_canvas_user_id'], ["Awaiting Assignment of Examiner", session['selected_examiner']])
  
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

get '/Reload' do
  # get configuraiton data
  all_data= JSON.parse(File.read('course-data-EECS-cycle-2.json'))
  puts "cycle_number is #{all_data['cycle_number']}"
  puts "school_acronym is #{all_data['school_acronym']}"

  programs_in_the_school_with_titles=all_data['programs_in_the_school_with_titles']
  # filter out the programs that are not at the desired cucle
  $programs_in_the_school_with_titles=programs_in_cycle(cycle_number, programs_in_the_school_with_titles)
  #puts("filtered $programs_in_the_school_with_titles is #{$programs_in_the_school_with_titles}")

  $dept_codes=all_data['dept_codes']
  $all_course_examiners=all_data['all_course_examiners']
  $AF_courses=all_data['AF_courses']
  $PF_courses=all_data['PF_courses']
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

