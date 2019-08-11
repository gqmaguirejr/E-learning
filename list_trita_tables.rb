#!/usr/bin/ruby
# list_trita_tables.rb
#
# list each of the TRITA related tables and the entries in each table
#
# G. Q. Maguire Jr.
#
# 2019.02.27
#
require 'pg'

puts 'Version of libpg: ' + PG.library_version.to_s

begin

    con = PG.connect :hostaddr => "172.20.0.2", :dbname => 'trita', :user => 'postgres'
    #puts con.server_version

    rs = con.exec "SELECT * FROM pg_catalog.pg_tables" do |result|
      result.each do |row|
        if row["schemaname"] == "public"
          puts row
          tr =  con.exec "SELECT * FROM #{row['tablename']}" do |tresult|
            tresult.each do |trow|
              puts trow
            end
          end
        end
      end
    
    end    
rescue PG::Error => e

    puts e.message 
    
ensure

    con.close if con
    
end
