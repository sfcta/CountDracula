'''
Created on Jul 25, 2011

@author: varun
'''

import logging, psycopg2, sys

class CountsDatabaseWriter(object):
    '''
    Class to handle write operations to the Counts database
    '''


    def __init__(self, host='localhost', database='countdracula', username='cdadmin', pw='', 
                 logger=logging.getLogger('countdracula.CountsDatabaseWriter')):
        '''
        Constructor; connects to the counts database with the given credentials.
         
         * *host* is the host where the counts database resides; e.g. 'localhost' or an ip address, like '172.0.0.1'
         * *database* is the database name; `countdracula` is the standard
         * *username* is a database user with write permissions; `cdadmin` is the standard.
         * *password* is the password for that the user.
         * *logger* is a logging.Logger instance for errors and informational messages.
         
        TODO: optional port?
        '''
        
        self._host      = host
        self._db        = database
        self._user      = username
        self._pw        = pw
        self._logger    = logger
        
        self._conn2db = psycopg2.connect("host="     +self._host+
                                         " dbname="  +self._db+
                                         " user="    +self._user+
                                         " password="+self._pw)

    def __del__(self):
        """
        Disconnects from the database.
        """
        self._conn2db.close()
        
    def insertMainlineCounts(self, countsList):
        """
        Inserts *countsList* into the :ref:`table-counts_ml`; see that documentation for more on
        what these variables actually represent.
        
        countsList is a list of tuples, each tuple containing the following values; 
        
         * *count*
         * *starttime*
         * *period*
         * *vtype*
         * *onstreet*
         * *ondir*
         * *fromstreet*
         * *tostreet*
         * *refpos*
         * *sourcefile*
         * *project*
        
        Database errors will be ignored.
        
        """
        
        upload_count = 0
        duplicate_count = 0
        
        cur2db = self._conn2db.cursor()

        for count_tuple in countsList:
            #send command to server
            try:
                cur2db.execute("INSERT INTO counts_ml (count,starttime,period,vtype,onstreet,ondir," + 
                               "fromstreet,tostreet,refpos,sourcefile,project) VALUES " +
                               "(%s, %s, %s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s )", count_tuple)
                self._conn2db.commit()
                upload_count+=1
            except psycopg2.IntegrityError as e:
                # print str(e)
                #print command
                #print "Error inserting in DB"
                duplicate_count += 1

                #TODO: is this reasonable error handling?
                cur2db.close()
                self._conn2db.close()
                self._conn2db = psycopg2.connect("host="     +self._host+
                                                 " dbname="  +self._db+
                                                 " user="    +self._user+
                                                 " password="+self._pw)
                cur2db = self._conn2db.cursor()
            
        self._conn2db.commit()
        cur2db.close()

        self._logger.info("insertMainlineCounts: %4d counts inserted." % upload_count)
        if duplicate_count !=0:
            self._logger.info("insertMainlineCounts: %4d duplicate or erroneous count(s) found and skipped." % duplicate_count)
                  

    def insertTurnCounts (self,turnCountList):    
        """
        Inserts the given list of turn counts into the :ref:`table-counts_turns`.

        The *turnList* is a list of tuples with the following values:
        
        * *count*
        * *starttime*
        * *period* 
        * *vtype*
        * *fromstreet*
        * *fromdir*
        * *tostreet*
        * *todir*
        * *intstreet*
        * *intid*
        * *sourcefile*
        * *project*
        
        See :ref:`table-counts_turns` for the descriptions of the fields.
        """    
        cur2db = self._conn2db.cursor()
        
        upload_count = 0
        duplicate_count = 0
        
        for turncount_tuple in turnCountList:
            try:
                cur2db.execute("INSERT INTO counts_turns (count,starttime,period,vtype,fromstreet,fromdir,tostreet,todir,intstreet,intid,sourcefile,project) Values (%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s )",
                                (turncount_tuple[0],turncount_tuple[1],turncount_tuple[2],turncount_tuple[3],turncount_tuple[4],
                                 turncount_tuple[5],turncount_tuple[6],turncount_tuple[7],turncount_tuple[8],turncount_tuple[9],
                                 turncount_tuple[10],turncount_tuple[11]))
                self._conn2db.commit()
                upload_count+=1
                #print command
            except psycopg2.IntegrityError:
                #print command
                #print "Duplicate count!!"
                duplicate_count +=1
                cur2db.close()
                self._conn2db.close()
                self._conn2db = psycopg2.connect("host="     +self._host+
                                                 " dbname="  +self._db+
                                                 " user="    +self._user+
                                                 " password="+self._pw)
                cur2db = self._conn2db.cursor()

        cur2db.close()
        
        self._logger.info("insertTurnCounts: %4d counts inserted." % upload_count)
        if duplicate_count !=0:
            self._logger.info("insertTurnCounts: %4d duplicate or erroneous count(s) found and skipped." % duplicate_count)
            

    def insertNodes(self, nodeList):
        """
        Inserts the given list of intersection nodes into the :ref:`table-nodes`.

        The *nodeList* is a list of tuples with the following values:
        
        * *intersection_id* - an integer id.
        * *x* - the x coordinate, such as the latitude
        * *y* - the y coordinate, such as the longitude
        
        """
        cur2db = self._conn2db.cursor()
        
        insert_count = 0
        for intersection_tuple in nodeList:
            
            try:
                cur2db.execute("INSERT INTO nodes (int_id, long_x, lat_y) values (%s, %s, %s)",
                               (intersection_tuple[0],intersection_tuple[1], intersection_tuple[2]))
                insert_count += 1
            except Exception, e: 
                # self._logger.warn(e.pgerror)
                pass
                        
        self._conn2db.commit()
        cur2db.close()
        
        self._logger.info("insertNodes: %4d intersection ids inserted out of %4d" % (insert_count, len(nodeList)))
                
    def insertNodeStreets(self, nodeStreetList):
        """
        Inserts the given list of intersections into the :ref:`table-node_streets`.
        
        The *nodeStreetList* is a list of tuples with the following values:

        * *intersection_id* - an integer id, should correspond with an int_id from :ref:`table-nodes`.
        * *streetname* - should correspond with a street_name or nospace_name from :ref:`table-street_names`.
        
        Can be used with :py:meth:`CountsWorkbookParser.readIntersectionIds`
        """
        
        cur2db = self._conn2db.cursor()
        
        insert_count = 0
        for intersection_tuple in nodeStreetList:
            try:
                cur2db.execute("Select street_name from street_names where nospace_name = %s or street_name = %s",
                           (intersection_tuple[1],intersection_tuple[1]))
                street = cur2db.fetchone()
            except Exception, e:
                # self._logger.warn(e.pgerror)
                continue
            
            if street==None:
                self._logger.warn("insertNodeStreets: street %s not found in street_names table -- skipping" %
                                  intersection_tuple[1])
                continue
            
            # update nodes
            cur2db.execute("SELECT int_id FROM nodes WHERE int_id=%d;" % intersection_tuple[0])
            nodes_id= cur2db.fetchone()
            if nodes_id == None:
                self._logger.warn("insertNodeStreets: node %d not found in nodes table -- skipping" % intersection_tuple[0])
                continue
            
            try:          
                cur2db.execute("INSERT INTO node_streets (int_id, street_name) values (%s, %s)",
                               (intersection_tuple[0],street))
                insert_count += 1
            except Exception, e: 
                # self._logger.warn(e.pgerror)
                pass
            
        self._conn2db.commit()
        cur2db.close()
        
        self._logger.info("insertIntersectionIds: %4d intersection ids inserted out of %4d" % (insert_count, len(nodeStreetList)))
        
        
    def insertStreetNames(self, streetnameList):
            
        """
        Inserts the given list of streetnames into the :ref:`table-street_names`.
        
        The *streetnameList* is a list of tuples with the following values:
        
        * *street_name* 
        * *nospace_name*
        * *short_name*
        * *suffix*
        
        Can be used with :py:meth:`CountsWorkbookParser.readStreetNames`
        """
        cur2db = self._conn2db.cursor()

        insert_count = 0
        for streetname_tuple in streetnameList:
            
            # if the streetname is already in there *with a suffix* and we have no suffix, then skip
            if streetname_tuple[3]=="":
                cur2db.execute("SELECT street_name, nospace_name, short_name, suffix from street_names where short_name = %s ;", (streetname_tuple[2],))
                result = cur2db.fetchall()
                if len(result) > 0: 
                    self._logger.warn("Assuming that existing street_names entry %s is the same as given entry %s, skipping" % (result, streetname_tuple))
                    continue
                                
            try:                    
                cur2db.execute("INSERT INTO street_names VALUES (%s, %s, %s, %s)",
                               streetname_tuple)
                insert_count += 1
            except Exception, e: 
                # self._logger.warn(e.pgerror)
                pass
 
        #--------------------------------------------- for command in alt_names:
            #-------------------------------------------- send command to server
            #------------------------------- street_name = command[0]+command[1]
            # cur2db.execute("UPDATE street_names SET short_name = %s, suffix = %s where street_name = %s",
            #--------------- (command[0],command[1],street_name))
        
        
        self._conn2db.commit()
        cur2db.close()
        
        self._logger.info("insertStreetNames: %4d streets inserted out of %4d" % (insert_count, len(streetnameList)))

