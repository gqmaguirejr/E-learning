#!/usr/bin/ruby
# list_databases.rb
#
# list each of the databases
#
# G. Q. Maguire Jr.
#
# 2019.08.11
# will output:
# Version of libpg: 100010
# {"datname"=>"template1"}
# {"datname"=>"template0"}
# {"datname"=>"postgres"}
# {"datname"=>"canvas"}
# {"datname"=>"canvas_test_rails3_"}
# {"datname"=>"trita"}
#
require 'pg'

puts 'Version of libpg: ' + PG.library_version.to_s

begin

    con = PG.connect :hostaddr => "172.20.0.2", :dbname => 'postgres', :user => 'postgres'
    #puts con.server_version

    rs = con.exec "SELECT datname FROM pg_catalog.pg_database" do |result|
      result.each do |row|
          puts row
      end
    end    

rescue PG::Error => e

    puts e.message 
    
ensure

    con.close if con
    
end
