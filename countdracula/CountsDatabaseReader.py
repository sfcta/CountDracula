'''
Created on Jul 25, 2011

@author: varun
'''
import psycopg2, datetime
from datetime import date, time, timedelta, datetime
import logging
import math

class CountsDatabaseReaderError(Exception):
    pass


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

    def getNodeNearPoint(self, node_x, node_y, tolerance):
        """
        Function that returns id for a node in CountDracula which lies within 'tolerance' feet
        
        to the coordinates node_x,node_y
        
        Raises a :py:class:`CountsDatabaseReaderError` if no nodes are found, or if multiple nodes are found.
        """
        cur2db = self._conn2db.cursor()        
        cur2db.execute("SELECT int_id from nodes WHERE (sqrt((long_x - %s)^2 + (lat_y - %s)^2) < %s);",(node_x,node_y,tolerance))
        answer = cur2db.fetchall()
                
        if len(answer) == 1:
            return answer[0][0]  # answer = [(12345,)]
            
        raise CountsDatabaseReaderError("Found %d nodes within %8.3f of (%8.3f,%8.3f)" % (len(answer), tolerance, node_x, node_y))     

    
    def countCounts(self, turning=True, mainline=True):
        """
        Returns info on what kind of turning counts we have by returning a dictionary mapping (starttime, period) -> count
        """
        
        counts = {}
        dbs = []
        if turning:
            dbs.append("counts_turns")
        if mainline:
            dbs.append("counts_ml")

        cur2db = self._conn2db.cursor()
        for db in dbs:
            cur2db.execute("SELECT starttime,period from %s" % db)
            rows = cur2db.fetchall()
            
            for row in rows:
                key = (row[0], row[1])
                if key not in counts: counts[key] = 0
                counts[key] += 1
        return counts
    
    def _getCounts(self, starttime, period, num_intervals, type, from_date, to_date, weekdays):
        """
        Internal helper to not repeat code.  *type* is one of ``turns`` or ``mainline``.
        
        See :py:meth:`CountsDatabaseReader.getMainlineCounts` and :py:meth:`CountsDatabaseReader.getTurningCounts` for
        args.
        """
        # this needs to be a datetime.datetime to get adds
        currenttime = datetime.combine(date(2000,1,1), starttime)
        cur2db      = self._conn2db.cursor()
        counts      = {} # key = (fromstreet, fromdir, tostreet, todir, intersection id)
        days        = {} # same key but counts how many days worth of counts we have
        
        for interval_num in range(num_intervals):
            
            #Get avg of counts for the given movement and timeperiod
            if type=="turns":
                cmd = "SELECT count,starttime,fromstreet,fromdir,tostreet,todir,intstreet,intid from counts_turns " + \
                      "where starttime::time=%s and period=%s"
            elif type=="mainline":
                cmd = "SELECT count,starttime,onstreet,ondir,fromstreet,tostreet from counts_ml " + \
                        "where starttime::time=%s and period=%s"
            else:
                raise CountsDatabaseReaderError("_getCounts requires type=`turns` or type=`mainline`; type=`%s`" % type)
            
            args = [currenttime.time(), period]
            if from_date:
                cmd += " and starttime::date>=%s"
                args.append(from_date)
            if to_date:
                cmd += " and starttime::date<=%s"
                args.append(to_date)
            if weekdays:
                cmd += " and ("
                for idx in range(len(weekdays)):
                    # input: Monday is 0
                    # pgsql: Sunday is 0 Monday is 1
                    cmd += "date_part('DOW', starttime)=%d" % (weekdays[idx] + 1 % 7)
                    if idx < len(weekdays)-1: cmd += " or "
                cmd += ")"

            #self._logger.debug(cmd)
            cur2db.execute(cmd, args)
            results = cur2db.fetchall()
            for row in results:
                if type=="turns":
                    key = (row[2],row[3],row[4],row[5],row[6],row[7])
                elif type=="mainline":
                    key = (row[2],row[3],row[4],row[5])

                # haven't seen this before, initialize previous counts to unknown
                if key not in counts:
                    counts[key]  = []
                    days[key]    = []
                
                # fill in non-data
                while len(counts[key]) < interval_num:
                    counts[key].append(-1)
                    days[key].append(0)
                
                # initialize for real data
                if len(counts[key]) < (interval_num+1):
                    counts[key].append(0)
                    days[key].append(0)
                
                # tally it
                counts[key][interval_num]  += row[0]
                days[key][interval_num]    += 1
                
                #self._logger.debug(row)
                
            # update the time
            currenttime += period
        
        # fill out the remainder
        for key in counts:
            while len(counts[key]) < num_intervals:
                counts[key].append(-1)
                days[key].append(0)
                        
        # divide out the days
        for key in counts.iterkeys():
            for interval_num in range(num_intervals):
                if days[key][interval_num] > 1:
                    counts[key][interval_num] = float(counts[key][interval_num])/float(days[key][interval_num])
        return counts

    def getMainlineCounts(self, starttime, period, num_intervals, from_date=None, to_date=None, weekdays=None):
        """
        Retrieve all the mainline counts available from the database for the given *starttime* (a datetime.time instance) for 
        *num_intervals* (int) of the given *period* (a datetime.timedelta instance).
        
        If *from_date* is passed (a datetime.date instance), then counts will be on or after *from_date*.
        If *to_date* is passed (a datetime.date instance), then counts will be on or before *to_date*.
        If *weekdays* is passed (a list of integers, where Monday is 0 and Sunday is 6), then counts will
        only include the given weekdays.
        
        Returns table with: (onstreet, ondir, fromstreet, tostreet, intersection id) -> [*num_intervals* counts]
        """
        return self._getCounts(starttime, period, num_intervals, type="mainline",
                               from_date=from_date, to_date=to_date, weekdays=weekdays)
    
    def getTurningCounts(self, starttime, period, num_intervals, from_date=None, to_date=None, weekdays=None):
        """
        Retrieve all the turning counts available from the database for the given *starttime* (a datetime.time instance) for 
        *num_intervals* (int) of the given *period* (a datetime.timedelta instance).
        
        If *from_date* is passed (a datetime.date instance), then counts will be on or after *from_date*.
        If *to_date* is passed (a datetime.date instance), then counts will be on or before *to_date*.
        If *weekdays* is passed (a list of integers, where Monday is 0 and Sunday is 6), then counts will
        only include the given weekdays.
        
        Returns table with: (fromstreet, fromdir, tostreet, todir, intersection id) -> [*num_intervals* counts]
        """
        return self._getCounts(starttime, period, num_intervals, type="turns",
                               from_date=from_date, to_date=to_date, weekdays=weekdays)
                               
    
    def getTurningCountsForMovement(self, at_node, from_node, to_node, from_angle, to_angle, starttime, period, num_intervals):
        """
        Returns the counts from the database for a specific movement
        
        * *at_node* is the intersection node
        * *to_node* is the destination node
        * *from_node* is the origin node
        * *from_angle* is approach angle in radians, starting from EB=0 clockwise (so SB=pi/2, WB=pi, NB=3pi/2)
        * *to_angle* is the departing angle
        * *starttime* is starting time for counts to get
        * *period* is time interval for each count
        * *num_intervals* = number of intervals to retrieve
        
        Returns a list of counts.
        
        Raises a CountsDatabaseReaderError if:
        * No incoming street is found (no common street for *from_node* and *at_node*
        * No outgoing street is found (no common street for *at_node* and *to_node*
        * No counts are found.
        
        .. todo:: Isn't *from_angle* and *to_angle* something we can calculate here?
        
        """
          
        ## Find approach street by finding the street name that is common between the list of streets at the at_node and from_node
        cur2db = self._conn2db.cursor()                
        cur2db.execute("SELECT street1 from (    ((SELECT DISTINCT street1 from intersection_ids where int_id = %s) UNION "
                                                " (SELECT DISTINCT street2 from intersection_ids where int_id = %s)) UNION ALL "
                                                "((SELECT DISTINCT street1 from intersection_ids where int_id = %s)UNION "
                                                " (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) ) "
                                                " Street GROUP BY street1 HAVING count(street1) > 1",
                       (at_node,at_node,from_node,from_node))
        fromstreet =   cur2db.fetchone()
        if fromstreet == None:
            raise CountsDatabaseReaderError("getTurningCounts: Street from %d to %d not found" % (from_node, at_node))
        
        ## Find departing street by finding the street name that is common between the list of streets at the at_node and to_node
        
        cur2db.execute("SELECT street1 from (    ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s) UNION (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) UNION ALL ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s)UNION(SELECT DISTINCT  street2 from intersection_ids where int_id = %s))    ) Street GROUP BY street1 HAVING count(street1) > 1",
                        (at_node,at_node,to_node,to_node))
        tostreet =   cur2db.fetchone()
        
        if tostreet== None:
            raise CountsDatabaseReaderError("getTurningCounts: Street from %d to %d not found" % (at_node, to_node))
        
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
        
        self._logger.debug("getTurningCounts: found CD intersection %d-%d-%d %s-%s" % (from_node,at_node,to_node,fromdir,todir))
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
            cur2db.execute("SELECT AVG(count) from counts_turns where fromstreet=%s AND fromdir=%s AND "
                                 "tostreet=%s AND todir=%s AND intid=%s AND period=%s GROUP BY starttime HAVING starttime::time = %s",
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
            
            count = cur2db.fetchone()
            if count:
                found +=1 
                counts[i]=float(count[0])
                self._logger.debug("getTurningCounts: found count for the movement at %s for %d min" % (counttime.isoformat(), period.seconds/60.0))
            
            counttime = (datetime.combine(date(2000,1,1),counttime) + period).time()
        if found>0:
            return counts
        
        raise CountsDatabaseReaderError("No turning counts were found for any of the given time periods.")
        
    def retrieve_table (self,filepath,table):        #save a table as csv (used for testing primarily) 
        """
        Saves a table to a csv file
        """
        
        
        myfile = open(filepath + '\\' + self._db + '_' + table + '.csv', 'wb') #Create CSV filename
        
        cur2db = self._conn2db.cursor()
        cur2db.copy_to(myfile, table, sep="|")

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
        
        This search is case-insensitive.
        """
        cur2db = self._conn2db.cursor()
        
        cur2db.execute("SELECT street_name from street_names where upper(street_name) = %s ;", (name.upper(),))
        entries = cur2db.fetchall()
        if len(entries) > 0:
            return list(i for i, in entries)
        
        cur2db.execute("SELECT street_name from street_names where upper(nospace_name) = %s ;", (name.upper().replace(" ",""),))
        entries = cur2db.fetchall()
        if len(entries) > 0:
            return list(i for i, in entries)

        cur2db.execute("SELECT street_name from street_names where upper(short_name) = %s ;", (name.upper(),))
        entries = cur2db.fetchall()
        if len(entries) > 0:
            return list(i for i, in entries)
        
        # see if we can match the nospace_name with a wild card for the suffix
        cur2db.execute("SELECT street_name from street_names where nospace_name LIKE '" + name.upper().replace(" ","") + "%' ;")
        entries = cur2db.fetchall()
        if len(entries) > 0:
            return list(i for i, in entries)
        
        return []
        
    def getIntersectionIdsForStreets(self,street1,street2):
        """
        Given a two streets, returns a set of the intersection ids matching both.
        
        *street1* and *street2* are matched against the *street_name* field in :ref:`table-node_streets`
        """
        cur2db = self._conn2db.cursor()

        cur2db.execute("SELECT int_id from node_streets WHERE street_name=%s ;", (street1,))
        result1 = cur2db.fetchall()
        result1 = set(i for i, in result1)

        cur2db.execute("SELECT int_id from node_streets WHERE street_name=%s ;", (street2,))
        result2 = cur2db.fetchall()
        result2 = set(i for i, in result2)        
        
        return result1 & result2
        
    def getStreetsForIntersectionId(self, node_id):
        """
        Returns a set of streetnames for the intersection with the id given by *node_id*.
        
        Raises a :py:class:`CountsDatabaseReaderError` if no nodes are found.
        """
        cur2db = self._conn2db.cursor()
        
        cur2db.execute("SELECT street_name FROM node_streets WHERE int_id=%s ;", (node_id,))
        result = cur2db.fetchall()
        
        if len(result) == 0:
            raise CountsDatabaseReaderError("No streets found for node id %d" % node_id)
        
        result = set(i for i, in result)
        return result