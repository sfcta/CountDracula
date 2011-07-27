'''
Created on Jul 25, 2011

@author: varun
'''
import psycopg2, datetime
from datetime import date, time, timedelta, datetime



class ReadFromCD(object):
    '''
    Class that does all the retrieval from our Database
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
        self._database = database
        self._username = username
        self._pw = pw
        self._conn2db = psycopg2.connect("host = "+self._host + " dbname="+self._database+ " user="+self._username + " password = "+self._pw )
        self._cur2db = self._conn2db.cursor()
        

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
    
        
        
    def getTurningCounts(self, atNode, fromNode, toNode,fromangle, toangle, starttime, period, number):
        """
        Returns the counts from the database for a specific movement
        atNode = intersection node in CD
        toNode = Destination node in CD
        fromNode = Origin nodein CD
        fromangle = approach angle with East direction in radians
        toangle = departing angle from East with radians
        starttime = starting time for counts to get
        period = time interval for each count
        number = number of intervals to retrieve
        
        Returns a list of counts
        """
        
           
        counts = [-1]*number
        ## Find approach street by finding the street name that is common between the list of streets at the atNode and fromNode
        
        self._cur2db.execute("SELECT street1 from (    ((SELECT DISTINCT street1 from intersection_ids where int_id = %s) UNION (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) UNION ALL ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s)UNION(SELECT DISTINCT  street2 from intersection_ids where int_id = %s))    ) Street GROUP BY street1 HAVING count(street1) > 1",
                       (atNode,atNode,fromNode,fromNode))
        fromstreet =   self._cur2db.fetchone()
        
        ## Find departing street by finding the street name that is common between the list of streets at the atNode and toNode
        
        self._cur2db.execute("SELECT street1 from (    ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s) UNION (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) UNION ALL ((SELECT DISTINCT  street1 from intersection_ids where int_id = %s)UNION(SELECT DISTINCT  street2 from intersection_ids where int_id = %s))    ) Street GROUP BY street1 HAVING count(street1) > 1",
                       (atNode,atNode,toNode,toNode))
        tostreet =   self._cur2db.fetchone()
        
        if fromstreet == None or tostreet== None:
            return []
        
        #Decide direction based on angle
        if (fromangle > 0.785398163) and (fromangle <= 2.35619449):       #fromangle is between pi/4 and 3pi/4 -> SB
            fromdir = "SB"
        elif (fromangle > 2.35619449) and (fromangle <= 3.92699082):        #fromangle is between 3pi/4 and 5pi/4 -> WB
            fromdir = "WB"
        elif (fromangle > 3.92699082) and (fromangle <= 5.49778714):        #fromangle is between 5pi/4 and 7pi/4 -> NB
            fromdir = "NB"
        else: 
            fromdir = "EB"
 
        if (toangle > 0.785398163) and (toangle <= 2.35619449):       #toangle is between pi/4 and 3pi/4 -> SB
            todir = "SB"
        elif (toangle > 2.35619449) and (toangle <= 3.92699082):        #toangle is between 3pi/4 and 5pi/4 -> WB
            todir = "WB"
        elif (toangle > 3.92699082) and (toangle <= 5.49778714):        #toangle is between 5pi/4 and 7pi/4 -> NB
            todir = "NB"
        else: 
            todir = "EB"
        
        
        intstreets = []
        
        if fromstreet != tostreet:
            intstreets.append(tostreet)
        else:
            #if approach and departing street are same (i.e. for a thru movement), we find the intersection street
            self._cur2db.execute("SELECT street1 from ((SELECT DISTINCT street1 from intersection_ids where int_id = %s) UNION (SELECT DISTINCT  street2 from intersection_ids where int_id = %s)) STREET where street1 <> %s",
                           (atNode,atNode,fromstreet))
            intstreets =   self._cur2db.fetchall()
            
        counttime = starttime
        for i in range(0,number):
            count = None
            intstreetid = 0
            
            #Decide what to do if multiple names with multiple streets ?!!
            while count == None and intstreetid < len(intstreets):
                self._cur2db.execute("SELECT AVG(count) from counts_turns where fromstreet = %s AND fromdir = %s AND tostreet = %s  AND todir = %s AND intstreet = %s AND period = %s  GROUP BY starttime HAVING  starttime::time = %s",
                           (fromstreet, fromdir, tostreet, todir, intstreets[intstreetid], period, counttime))
            
                count =  self._cur2db.fetchone()
                if not count == None: 
                    counts[i]=count
                else: 
                    intstreetid+=1
            
            counttime = (datetime.combine(date(2000,1,1),starttime) + period).time()
        
        return counts
        
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
        
        self._cur2db.execute("SELECT street_name from street_names where street_name = %s",[name]);
        entries = self._cur2db.fetchall()
        if not entries == []:
            return entries
        else:
            self._cur2db.execute("SELECT street_name from street_names where nospace_name = %s",[name]);
            entries = self._cur2db.fetchall()
            if not entries == []:
                return entries
            else:
                self._cur2db.execute("SELECT street_name from street_names where short_name = %s",[name]);
                entries = self._cur2db.fetchall()
                return entries
        
    def getIntersectionId(self,NSstreet,EWstreet):
         
        self._cur2db.execute("SELECT int_id from intersection_ids WHERE ((street1=%s AND street2=%s) OR (street1=%s AND street2=%s));",(NSstreet,EWstreet,EWstreet,NSstreet))
        intid = self._cur2db.fetchone()
        if intid == None:   #i.e. intersection not found !!
            return (-1,)
        else:
            return intid
        
        