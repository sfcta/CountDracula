#!/usr/bin/env python

""""THIS FILE DOES ALL THE INTERACTION WITH PSQL !!
"""

import psycopg2 #Imported library(external) to interact with psql

__author__ = "Varun Kohli, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "Jul 1 2011" 

def upload_mainline (commandslist,db,user):	    #uploads counts to mainline table
    
    conn2db = psycopg2.connect("dbname="+db+" user="+user)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    
    #cur2db.execute("DELETE from counts_ml;")
    
    for command in commandslist:
        #send command to server
        cur2db.execute("INSERT INTO counts_ml (count,starttime,period,vtype, onstreet,ondir,fromstreet,tostreet,refpos,sourcefile,project) Values (%s, %s, %s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s )",
                       tuple(command))
        
    conn2db.commit()
    cur2db.close()
    conn2db.close()

def upload_turns (commandslist,db,user):	#uploads counts to turns table
    
    conn2db = psycopg2.connect("dbname="+db+" user="+user)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    
    #cur2db.execute("DELETE from counts_turns;")
    
    for command in commandslist:
        #-----Check if intersection exists in DB-------------- 
        cur2db.execute("SELECT int_id from intersection_ids WHERE ((street1=%s AND street2=%s) OR (street1=%s AND street2=%s));",(command[4],command[8],command[8],command[4]))
        intid = -1 
        intid = cur2db.fetchone()
        if intid == None:   #i.e. intersection not found !!
            print ('INTERSECTION with streets 1) '+command[4]+' 2) '+command[8]+' NOT IN DB')
            raise   #raise exception
        else:
            #send command to server
            cur2db.execute("INSERT INTO counts_turns (count,starttime,period,vtype,fromstreet,fromdir,tostreet,todir,intstreet,intid,sourcefile,project) Values (%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s )",
                            (command[0],command[1],command[2],command[3],command[4],command[5],command[6],command[7],command[8],intid,command[10],command[11],))
    conn2db.commit()
    cur2db.close()
    conn2db.close()

def street_names (commandslist,db,user):    #uploads street names to  DB
    
    conn2db = psycopg2.connect("dbname="+db+" user="+user)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    #OR Clear DB before uploading new street_names
    cur2db.execute("DELETE from counts_ml;")
    cur2db.execute("DELETE from counts_turns;")
    cur2db.execute("DELETE from intersection_ids;")
    cur2db.execute("DELETE from street_names;")
    
    for command in commandslist:
        #send command to server
        cur2db.execute("INSERT INTO street_names VALUES (%s)",
                       [command])
    conn2db.commit()
    cur2db.close()
    conn2db.close()

def int_ids (commandslist,db,user):    #uploads intersection ids table
    
    conn2db = psycopg2.connect("dbname="+db+" user="+user)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    #OR EMPTY EXISTING INTERSECTIONS BEFORE ENTERING NEW TABLE
    cur2db.execute("DELETE from intersection_ids;")
    
    
    for command in commandslist:
        #ONLY done if street-pair doesn't exist already 
        cur2db.execute("INSERT INTO intersection_ids (street1, street2, int_id, long_x, lat_y) SELECT %s, %s, %s,%s,%s  WHERE NOT EXISTS (SELECT street1, street2 FROM intersection_ids WHERE street1 = %s AND street2 = %s);",
                           (command[0],command[1],command[2],command[3],command[4],command[0],command[1]))
    
    cur2db.execute("INSERT INTO nodes SELECT DISTINCT int_id, long_x, lat_y from intersection_ids;")
    cur2db.execute("ALTER TABLE intersection_ids ADD FOREIGN KEY (int_id) REFERENCES nodes ON UPDATE CASCADE;")
    
    conn2db.commit()
    cur2db.close()
    conn2db.close()


           
def retrieve_table (filepath,table,db,user):        #save a table as csv (used for testing primarily) 
    
    myfile = open(filepath + '\\' + db + '_' + table + '.csv', 'wb') #Create CSV filename
    
    conn2db = psycopg2.connect("dbname="+db+" user="+user)
    cur2db = conn2db.cursor()
    
    cur2db.copy_to(myfile, table, sep="|")
    
    conn2db.commit()
    cur2db.close()
    conn2db.close()

if __name__ == '__main__':
    
    print 'Enter DB to login to:'
    db = raw_input()
    
    print 'Enter username to login as:'
    user = raw_input()
    
    print 'Enter Table to download:'
    table = raw_input()
    
    print 'Enter filepath to save:'
    filepath = raw_input()
    
    retrieve_table(filepath,table,db,user)
    
    print 'DONE'
    
    