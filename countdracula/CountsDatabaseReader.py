'''
Created on Jul 25, 2011

@author: varun
'''
import psycopg2, datetime
from datetime import date, time, timedelta, datetime
import logging
import math


class CountsDatabaseReader(object):
    '''
    Class to handle read operations to the Counts database
    '''


    def __init__(self, host='localhost', database='countdracula', username='cdreader', pw='', 
                 logger=logging.getLogger('countdracula.CountsDatabaseReader')):
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

    def mapNodeId(self, node_x, node_y, tolerance):
        """
        Function that returns id for a node in CountDracula which lies within 'tolerance' feet
        
        to the coordinates node_x,node_y
        
        Returns -1 if a match is not found
        """
        self._cur2db.execute("SELECT int_id from nodes WHERE  sqrt((long_x - %s)^2 + (lat_y - %s)^2) < %s ;",(node_x,node_y,tolerance))
        answer =  self._cur2db.fetchone()

        #------ASSUMING there is a single match !!!!------ 
        if answer:
            return int(answer[0])
            #counter = counter+1
        else:
            return -1
    
        
        
    def getTurningCounts(self, at_node, from_node, to_node, from_angle, to_angle, starttime, period, num_intervals):
        """
        Returns the counts from the database for a specific movement
        
        * *at_node* is the intersection node
        * *to_node* is the destination node
        * *from_node* is the origin node
        * *from_angle* is approach angle with East direction in radians
        * *to_angle* is the departing angle from East with radians
        * *starttime* is starting time for counts to get
        * *period* is time interval for each count
        * *num_intervals* = number of intervals to retrieve
        
        Returns a list of counts.
        
        .. todo:: document error conditions.  Also, isn't *from_angle* and *to_angle* something we can calculate here?
        """
        
           
        #counts = [-1]*num_intervals
        ## Find approach street by finding the street name that is common between the list of streets at the at_node and from_node
        
        self._cur2db.execute("SELECT street1 from (    ((SELECT DISTINCT street1 from intersection_ids where int_id = %s) UNION (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) UNION ALL ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s)UNION(SELECT DISTINCT  street2 from intersection_ids where int_id = %s))    ) Street GROUP BY street1 HAVING count(street1) > 1",
                       (at_node,at_node,from_node,from_node))
        fromstreet =   self._cur2db.fetchone()
        
        ## Find departing street by finding the street name that is common between the list of streets at the at_node and to_node
        
        self._cur2db.execute("SELECT street1 from (    ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s) UNION (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) UNION ALL ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s)UNION(SELECT DISTINCT  street2 from intersection_ids where int_id = %s))    ) Street GROUP BY street1 HAVING count(street1) > 1",
                       (at_node,at_node,to_node,to_node))
        tostreet =   self._cur2db.fetchone()
        
        if fromstreet == None or tostreet== None:
            return []
        
        #Decide direction based on angle
        if (from_angle > 0.25*math.pi) and (from_angle <= 0.75*math.pi):
            fromdir = "SB"
        elif (from_angle > 0.75*math.pi) and (from_angle <= 1.25*math.pi):
            fromdir = "WB"
        elif (from_angle > 1.25*math.pi) and (from_angle <= 1.75*math.pi):
            fromdir = "NB"
        else: 
            fromdir = "EB"
 
        if (to_angle > 0.25*math.pi) and (to_angle <= 0.75*math.pi):
            todir = "SB"
        elif (to_angle > 0.75*math.pi) and (to_angle <= 1.25*math.pi):
            todir = "WB"
        elif (to_angle > 1.25*math.pi) and (to_angle <= 1.75*math.pi):
            todir = "NB"
        else: 
            todir = "EB"
        
        
        #intstreets = []
        
        #if fromstreet != tostreet:
        #    intstreets.append(tostreet)
        #else:
            #if approach and departing street are same (i.e. for a thru movement), we find the intersection street
        #   self._cur2db.execute("SELECT street1 from ((SELECT DISTINCT street1 from intersection_ids where int_id = %s) UNION (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) STREET where street1 <> %s",
        #                (at_node,at_node,fromstreet))
        #  intstreets =   self._cur2db.fetchall()
            
        counttime = starttime
        #endtime = (datetime.combine(date(2000,1,1),counttime) + period*num_intervals).time()
        
        counts = [-1]*num_intervals
        found = 0
        for i in range(0,num_intervals):
            count = None
            
            #Get avg of counts for the given movement and timeperiod 
            self._cur2db.execute("SELECT AVG(count) from counts_turns where fromstreet = %s AND fromdir = %s AND tostreet = %s  AND todir = %s AND intid = %s AND period = %s  GROUP BY starttime HAVING  starttime::time = %s",
                           (fromstreet, fromdir, tostreet, todir, at_node, period, counttime))
            
    # !!! TODO !!!
        #=======================================================================
        #    The above command could be modified to process counts as 'flows'
        #    Eg: say we want count for period 15:00:00 to 15:15:00, we do a query on all counts, period for the movement where
        #    starttime::time is >= starttime and period <= period   
        #    then we do average of (count/count.period) * period
        #    
        #    This can be done something like:
        # Select AVG(count*%s/period) from counts_turns where starttime::time >= %s and period <=%s,
        # period, starttime, period
        # Might be tough as postgres doesn't support division of intervals as of now
        #    which means period/period may not work
        # 
        #=======================================================================
            
            count =  self._cur2db.fetchone()
            if not count == None:
                found +=1 
                counts[i]=float(count[0])
                
            
            counttime = (datetime.combine(date(2000,1,1),counttime) + period).time()
        if found>0:
            return counts
        else: 
            return []
        
    def retrieve_table (self,filepath,table):        #save a table as csv (used for testing primarily) 
        """
        Saves a table to a csv file
        """
        
        
        myfile = open(filepath + '\\' + self._db + '_' + table + '.csv', 'wb') #Create CSV filename
        
        conn2db = psycopg2.connect("host="+self._host+" dbname="+self._db+" user="+self._user+" password="+self._pw)
        cur2db = conn2db.cursor()
        
        cur2db.copy_to(myfile, table, sep="|")
        
        conn2db.commit()
        cur2db.close()
        conn2db.close()

    #===========================================================================
    # def street_in_streetname(self,name):
    #    """
    #    Checks if street name is in street_names table 
    #    """
    #    
    #    self._cur2db.execute("SELECT street_name from street_names where street_name = %s",[name]);
    #    entries = self._cur2db.fetchone()
    #    if entries == None:
    #        return 0
    #    else:
    #        return 1
    # 
    # def street_in_altnames(self, name):
    #    """
    #    Checks if street name is in alt_names table 
    #    """
    #    
    #    self._cur2db.execute("SELECT street_name from street_names where short_name = %s",[name]);
    #    entries = self._cur2db.fetchone()
    #    if entries == None:
    #        #print entries
    #        return 0
    #    else:
    #        #print entries
    #        return 1
    #    
    # def altname(self, name):
    #    """
    #    Returns street_name with suffix added 
    #    """
    #    self._cur2db.execute("SELECT street_name from street_names where short_name = %s",[name]);
    #    entries = self._cur2db.fetchone()
    #    if entries == None:
    #        #print entries
    #        return ""
    #    else:
    #        #print entries
    #        return (""+entries[0])
    #===========================================================================
        
        
    def getPossibleStreetNames(self, name):
        """
        Given a street name string, looks up the name in the various columns of the :ref:`table-street_names`
        and returns a list of the possible street_names (first column).
        """
        cur2db = self._conn2db.cursor()
        
        cur2db.execute("SELECT street_name from street_names where upper(street_name) = %s ;", (name.upper(),));
        entries = cur2db.fetchall()
        if len(entries) > 0:
            return list(i for i, in entries)
        
        cur2db.execute("SELECT street_name from street_names where upper(nospace_name) = %s ;", (name.upper(),));
        entries = cur2db.fetchall()
        if len(entries) > 0:
            return list(i for i, in entries)

        cur2db.execute("SELECT street_name from street_names where upper(short_name) = %s ;", (name.upper(),));
        entries = cur2db.fetchall()
        return list(i for i, in entries)
        
    def getIntersectionId(self,NSstreet,EWstreet):
        """
        Given a NS street and an EW street, looks for the intersection id of their intersection.
        
        Returns the intersection id or None, if none is found.
        """
        cur2db = self._conn2db.cursor()

        cur2db.execute("SELECT int_id from intersection_ids WHERE ((street1=%s AND street2=%s) OR (street1=%s AND street2=%s));",
                       (NSstreet,EWstreet,EWstreet,NSstreet))
        result = cur2db.fetchone()
        if result:
            result = result[0]

        return result
        
        