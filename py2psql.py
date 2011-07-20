#!/usr/bin/env python

"""THIS FILE DOES ALL THE INTERACTION WITH PSQL !!
"""

import psycopg2 #Imported library(external) to interact with psql

__author__ = "Varun Kohli, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "Jul 1 2011" 

def upload_mainline (commandslist,host,db,user,pw):	    #uploads counts to mainline table
    """
    Uploads counts to table counts_ml
    """
    
    UPLOAD = 0
    Duplicates = 0
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    
    #cur2db.execute("DELETE from counts_ml;")
    
    for command in commandslist:
        #send command to server
        try:
            cur2db.execute("INSERT INTO counts_ml (count,starttime,period,vtype, onstreet,ondir,fromstreet,tostreet,refpos,sourcefile,project) Values (%s, %s, %s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s )",
                       tuple(command))
            conn2db.commit()
            UPLOAD+=1
        except psycopg2.IntegrityError:
            #print command
            #print "Error inserting in DB"
            Duplicates+=1
            cur2db.close()
            conn2db.close()
            conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
            cur2db = conn2db.cursor()
            
        
    conn2db.commit()
    cur2db.close()
    conn2db.close()
    
    print UPLOAD,' count(s) uploaded'
    if Duplicates !=0:
        print Duplicates, ' duplicate or erroneous count(s) found and skipped!'
    


def upload_turns (commandslist,host, db,user,pw ):	
    """
    Uploads counts to turns table
    """
    
    UPLOAD = 0
    Duplicates = 0
    
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    
    #cur2db.execute("DELETE from counts_turns;")
    
    for command in commandslist:
        #-----Check if intersection exists in DB-------------- 
        intid = -1
        cur2db.execute("SELECT int_id from intersection_ids WHERE ((street1=%s AND street2=%s) OR (street1=%s AND street2=%s));",(command[4],command[8],command[8],command[4]))
        intid = cur2db.fetchone()
        if intid == None:   #i.e. intersection not found !!
            print ('INTERSECTION with streets 1) '+command[4]+' 2) '+command[8]+' NOT IN DB')
            raise   #raise exception
        else:
            #send command to server
            try:
                cur2db.execute("INSERT INTO counts_turns (count,starttime,period,vtype,fromstreet,fromdir,tostreet,todir,intstreet,intid,sourcefile,project) Values (%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s )",
                                (command[0],command[1],command[2],command[3],command[4],command[5],command[6],command[7],command[8],intid,command[10],command[11],))
                conn2db.commit()
                UPLOAD+=1
                #print command
            except psycopg2.IntegrityError:
                #print command
                #print "Duplicate count!!"
                Duplicates +=1
                cur2db.close()
                conn2db.close()
                conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
                cur2db = conn2db.cursor()
                
                
                
    conn2db.commit()
    cur2db.close()
    conn2db.close()
    
    print UPLOAD,' count(s) uploaded'
    if Duplicates !=0:
        print Duplicates, ' duplicate or erroneous count(s) found and skipped!'
    

def street_names (commandslist,host,db,user,pw):    #uploads street names to  DB
    """
    Uploads street_names to table street_names
    """
    
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
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

def int_ids (commandslist,host,db,user,pw):    #uploads intersection ids table
    """
    Uploads intersection_ids to db
    """
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    #OR EMPTY EXISTING INTERSECTIONS BEFORE ENTERING NEW TABLE
    cur2db.execute("DELETE from intersection_ids;")
    cur2db.execute("DELETE from nodes;")
    cur2db.execute("ALTER TABLE intersection_ids DROP CONSTRAINT intersection_ids_int_id_fkey;")
    
    
    
    for command in commandslist:
        #ONLY done if street-pair doesn't exist already 
        cur2db.execute("INSERT INTO intersection_ids (street1, street2, int_id, long_x, lat_y) SELECT %s, %s, %s,%s,%s  WHERE NOT EXISTS (SELECT street1, street2 FROM intersection_ids WHERE street1 = %s AND street2 = %s);",
                           (command[0],command[1],command[2],command[3],command[4],command[0],command[1]))
    
    cur2db.execute("INSERT INTO nodes SELECT DISTINCT int_id, long_x, lat_y from intersection_ids;")
    cur2db.execute("ALTER TABLE intersection_ids ADD FOREIGN KEY (int_id) REFERENCES nodes ON UPDATE CASCADE;")
    
    conn2db.commit()
    cur2db.close()
    conn2db.close()

def alt_names (commandslist,host,db,user,pw):    #uploads alt_names to  DB
    """
    Uploads street suffixes to DB
    """
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    
    #________________THIS IS ONLY FOR TESTING !!!
    #OR Clear DB before uploading new street_names
    #===========================================================================
    # cur2db.execute("DELETE from counts_ml;")
    # cur2db.execute("DELETE from counts_turns;")
    # cur2db.execute("DELETE from intersection_ids;")
    cur2db.execute("DELETE from alt_names;")
    #===========================================================================
    
    for command in commandslist:
        #send command to server
        cur2db.execute("INSERT INTO alt_names VALUES (%s,%s)",
                       (command[0],command[1]))
    conn2db.commit()
    cur2db.close()
    conn2db.close()

def street_in_streetnames(name,host,db,user,pw):
    """
    Checks if street name is in street_names table 
    """
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    cur2db.execute("SELECT * from street_names where street_name = %s",[name]);
    entries = cur2db.fetchone()
    if entries == None:
        return 0
    else:
        return 1
    
    cur2db.close()
    conn2db.close()
    
def street_in_altnames(name,host,db,user,pw):
    """
    Checks if street name is in alt_names table 
    """
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    cur2db.execute("SELECT * from alt_names where street_name = %s",[name]);
    entries = cur2db.fetchone()
    if entries == None:
        #print entries
        return 0
        
    else:
        #print entries
        return 1
    
    cur2db.close()
    conn2db.close()
    
def altname(name,host,db,user,pw):
    """
    Returns street_name with suffix added 
    """
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    cur2db.execute("SELECT * from alt_names where street_name = %s",[name]);
    entries = cur2db.fetchone()
    if entries == None:
        #print entries
        return ""
    else:
        #print entries
        return (""+entries[0]+entries[1])
    
    cur2db.close()
    conn2db.close()

           
def retrieve_table (filepath,table,host,db,user,pw):        #save a table as csv (used for testing primarily) 
    """
    Saves a table to a csv file
    """
    
    
    myfile = open(filepath + '\\' + db + '_' + table + '.csv', 'wb') #Create CSV filename
    
    conn2db = psycopg2.connect("host="+host+" dbname="+db+" user="+user+" password="+pw)
    cur2db = conn2db.cursor()
    
    cur2db.copy_to(myfile, table, sep="|")
    
    conn2db.commit()
    cur2db.close()
    conn2db.close()

if __name__ == '__main__':
    
    #===========================================================================
    print 'Enter DB to login to:'
    #db = raw_input()
    db = "postgres"
    # 
    print 'Enter username to login as:'
    #user = raw_input()
    user = "postgres"
    # 
    print 'Enter Table to download:'
    #table = raw_input()
    table = "counts_turns"
    # 
    print 'Enter filepath to save:'
    filepath = raw_input()
    # 
    retrieve_table(filepath,table,db,user)
    #===========================================================================
    #street_in_altnames("GEARY","postgres","postgres")
    
    
    print 'DONE'
    
    