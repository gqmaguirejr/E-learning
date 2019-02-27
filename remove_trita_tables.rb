#!/usr/bin/ruby
# remove_trita_tables.rb
#
# remove each of the TRITA related tables
#
# G. Q. Maguire Jr.
#
# 2019.02.27
#
require 'pg'

puts 'Version of libpg: ' + PG.library_version.to_s

begin

    con = PG.connect :hostaddr => "172.18.0.4", :dbname => 'trita', :user => 'postgres'
    #puts con.server_version

    rs = con.exec "SELECT * FROM pg_catalog.pg_tables" do |result|
      result.each do |row|
        if row["schemaname"] == "public"
          puts row
          tr =  con.exec "DROP TABLE IF EXISTS  #{row['tablename']}"
        end
      end
    
    end    

rescue PG::Error => e

    puts e.message 
    
ensure

    con.close if con
    
end
