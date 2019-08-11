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
    con = PG.connect :hostaddr => "172.20.0.2", :dbname => 'postgres', :user => 'postgres'
    #puts con.server_version
    trita_db_exists=false
    rs = con.exec "SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower('trita')" do |result|
      result.each do |row|
        if row["datname"] == "trita"
          trita_db_exists=true
        end
      end
    end

    if not trita_db_exists
      rs = con.exec "CREATE DATABASE trita" do |result|
        result.each do |row|
          puts row
        end
      end
    end
    
rescue PG::Error => e

    puts e.message 
    
ensure

    con.close if con
    
end
