#!/usr/bin/ruby
# generate_cover.rb
#
# A simple test program to create a thesis cover using the KTH cover generator. The resulting PDF file is stored in test.pdf.
#
# G. Q. Maguire Jr.
#
# 2019.02.27
#
require 'json'
require 'httparty'
require 'date'
require 'net/http'
require 'net/http/post/multipart'

uri_for_cover = URI("https://intra.kth.se/kth-cover/kth-cover.pdf")
n = Net::HTTP.new(uri_for_cover.host, uri_for_cover.port)
n.use_ssl =  (uri_for_cover.scheme == 'https')
#n.set_debug_output($stdout)
parm={:degree=>"second-level-30",
      :exam=>4,
      :area=>"Information and Communication Technology",
      :school => "School of Hard Knocks",
      :title=>"A fake title for a fake thesis",
      :secondaryTitle=>"A short subtitle",
      :author=>["James FakeStudent"],
      :trita=>"TRITA-EECS-EX-2019:28",
      :model=>"1337-brynjan!"}  #  this model is important otherwise the generator will not make the page
puts("parm is #{parm}")
req = Net::HTTP::Post::Multipart.new(uri_for_cover, parm)
req['Referer']="https://intra.kth.se/kth-cover?l=en"
req['Accept-Encoding']="gzip, deflate, br"
req['Accept-Language']="en-US,en;q=0.9"
req['Accept']="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"


res = n.start do |http|
  result = http.request(req) # Net::HTTPResponse object
  puts("post to create course cover returned #{result}")
  puts("result.code is #{result.code}")
  puts("Content-Disposition is #{result['Content-Disposition']}")
  puts("result.body.length is #{result.body.length}")
  file = File.open("test1.pdf", "w")
  file.puts("#{result.body}")
  file.close

end
