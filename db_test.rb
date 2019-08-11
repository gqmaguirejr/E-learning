#!/usr/bin/ruby

require 'pg'

puts 'Version of libpg: ' + PG.library_version.to_s

begin

    con = PG.connect :hostaddr => "172.20.0.2", :dbname => 'trita', :user => 'postgres'
    puts con.server_version

    #con.exec "DROP TABLE IF EXISTS eecs_trita_for_thesis_2018"
    # create the table if it does not exist
    rs = con.exec "CREATE TABLE IF NOT EXISTS eecs_trita_for_thesis_2019 (
    -- make the 'id' column a primary key; this also creates
    -- a UNIQUE constraint and a b+-tree index on the column
    id    SERIAL PRIMARY KEY,
    authors  TEXT,
    title    TEXT,
    examiner TEXT)"
    rs=con.exec "INSERT INTO eecs_trita_for_thesis_2019(authors, title, examiner) VALUES ('James FakeStudent', 'Another fake title', 'Gerald Q. Maguire Jr.') RETURNING id"
    puts(rs[0])
    id=rs[0]['id']
    puts(id)
    
    
rescue PG::Error => e

    puts e.message 
    
ensure

    con.close if con
    
end
