'''
Created on Jul 25, 2011

@author: varun
'''

import psycopg2

class WriteToCD(object):
    '''
    Class that does all the writing (uploading) to our Database
    '''


    def __init__(self, host, database, username, pw):
        '''
        self._host = host address
        
        self._database = database name
        
        self._username = username
        
        self._pw = password
        
        self._conn2db = Connector to db
        
        self._cur2db = Cursor to DB
        '''
        
        self._host = host
        self._db = database
        self._user = username
        self._pw = pw
        
        
    def upload_mainline (self,commandslist):        #uploads counts to mainline table
        """
        Uploads counts to table counts_ml
        
        commandslist = list of parameter lists for each sql insert commad Eg: [[count,starttime,period...],[...]]
        
        """
        
        UPLOAD = 0
        Duplicates = 0
        
        conn2db = psycopg2.connect("host="+self._host+" dbname="+self._db+" user="+self._user+" password="+self._pw)
        cur2db = conn2db.cursor()

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
                conn2db = psycopg2.connect("host="+self._host+" dbname="+self._db+" user="+self._user+" password="+self._pw)
                cur2db = conn2db.cursor()
                
            
        conn2db.commit()
        cur2db.close()
        conn2db.close()
        
        print UPLOAD,' count(s) uploaded'
        if Duplicates !=0:
            print Duplicates, ' duplicate or erroneous count(s) found and skipped!'


    def upload_turns (self,commandslist):    
        """
        Uploads counts to turns table
        
        commandslist = list of parameter lists for each sql insert commad Eg: [[count,starttime,period...],[...]]
        """
        
        UPLOAD = 0
        Duplicates = 0
        
        
        conn2db = psycopg2.connect("host="+self._host+" dbname="+self._db+" user="+self._user+" password="+self._pw)
        cur2db = conn2db.cursor()
        
        for command in commandslist:
            #send command to server
            try:
                cur2db.execute("INSERT INTO counts_turns (count,starttime,period,vtype,fromstreet,fromdir,tostreet,todir,intstreet,intid,sourcefile,project) Values (%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s )",
                                (command[0],command[1],command[2],command[3],command[4],command[5],command[6],command[7],command[8],command[9],command[10],command[11],))
                conn2db.commit()
                UPLOAD+=1
                #print command
            except psycopg2.IntegrityError:
                #print command
                #print "Duplicate count!!"
                Duplicates +=1
                cur2db.close()
                conn2db.close()
                conn2db = psycopg2.connect("host="+self._host+" dbname="+self._db+" user="+self._user+" password="+self._pw)
                cur2db = conn2db.cursor()

        conn2db.commit()
        cur2db.close()
        conn2db.close()
        
        print UPLOAD,' count(s) uploaded'
        if Duplicates !=0:
            print Duplicates, ' duplicate or erroneous count(s) found and skipped!'
            
    def int_ids (self, commandslist):    #uploads intersection ids table
        """
        Uploads intersection_ids to db
        
        command list is a list of list of parameters for each query
        
        Each query requires node, lat, long, street1, street2
        """
        
        conn2db = psycopg2.connect("host="+self._host+" dbname="+self._db+" user="+self._user+" password="+self._pw)
        cur2db = conn2db.cursor()
        
        #________________THIS IS ONLY FOR TESTING !!!
        #OR EMPTY EXISTING INTERSECTIONS BEFORE ENTERING NEW TABLE
        cur2db.execute("DELETE from intersection_ids;")
        cur2db.execute("DELETE from nodes;")
        cur2db.execute("ALTER TABLE intersection_ids DROP CONSTRAINT intersection_ids_int_id_fkey;")
        
        
        
        for command in commandslist:
            #ONLY done if street-pair doesn't exist already 
            cur2db.execute("Select street_name from street_names where nospace_name = %s or street_name = %s",
                           (command[0],command[0]))
            street1 = cur2db.fetchone()
            
            cur2db.execute("Select street_name from street_names where nospace_name = %s or street_name = %s",
                           (command[1],command[1]))
            street2 = cur2db.fetchone()
            
            if not (street1 == None or street2 == None):
                cur2db.execute("INSERT INTO intersection_ids (street1, street2, int_id, long_x, lat_y) SELECT %s, %s, %s,%s,%s  WHERE NOT EXISTS (SELECT street1, street2 FROM intersection_ids WHERE street1 = %s AND street2 = %s);",
                                   (street1,street2,command[2],command[3],command[4],street1,street2))
            
        cur2db.execute("INSERT INTO nodes SELECT DISTINCT int_id, long_x, lat_y from intersection_ids;")
        cur2db.execute("ALTER TABLE intersection_ids ADD FOREIGN KEY (int_id) REFERENCES nodes ON UPDATE CASCADE;")
        
        conn2db.commit()
        cur2db.close()
        conn2db.close()            
        
        
    def street_names(self, names):
            
        """
        Uploads street_names to table street_names
        
        command list is a list of list of parameters for each query
        """
        conn2db = psycopg2.connect("host="+self._host+" dbname="+self._db+" user="+self._user+" password="+self._pw)
        cur2db = conn2db.cursor()
        
        #________________THIS IS ONLY FOR TESTING !!!
        #OR Clear DB before uploading new street_names
        cur2db.execute("DELETE from counts_ml;")
        cur2db.execute("DELETE from counts_turns;")
        cur2db.execute("DELETE from intersection_ids;")
        cur2db.execute("DELETE from street_names;")
        
        for index, command in enumerate(names):
            #send command to server
            cur2db.execute("INSERT INTO street_names VALUES (%s, %s, %s, %s)",
                           (command))
 
        #--------------------------------------------- for command in alt_names:
            #-------------------------------------------- send command to server
            #------------------------------- street_name = command[0]+command[1]
            # cur2db.execute("UPDATE street_names SET short_name = %s, suffix = %s where street_name = %s",
            #--------------- (command[0],command[1],street_name))
        
        
        conn2db.commit()
        cur2db.close()
        conn2db.close()

