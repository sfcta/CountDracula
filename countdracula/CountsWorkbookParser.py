'''
Created on Jul 25, 2011

@author: varun
'''

import xlrd
from datetime import datetime,date, time, timedelta
from types import FloatType

class CountsWorkbookParserException(Exception):
    pass

class CountsWorkbookParser():
    """
    Reads in and parses in Excel workbooks in certain standardized formats, returning tuples to be used by
    :py:class:`CountsDatabaseWriter` to insert into the Counts Database.
    """


    def __init__(self):
        '''        
        Initialize the counts workbook parser.
        '''
        pass
      
    def createtimestamp (self, date_yyyy_mm_dd, time_period_str):
        """
        Interprets date and time period string
        
        * *date_yyyy_mm_dd*: the date string in "yyyy-mm-dd" format. E.g. `2011-09-26`.
        * *time_period_str*: can be one of `AMPKHOUR`, `PMPKHOUR`, `ADT`, or a range in military time, such as `1600-1615`.

        
        Returns tuple -> (starttime, period) where startime is a datetime object and period is a string
        which postgres can interpret (e.g. `1 day`, `34 minute`)
        """    
        special_times = {'AMPKHOUR':[time( 8,00,00,100801),time( 9,00,00,100801)],
                         'PMPKHOUR':[time(17,00,00,101701),time(18,00,00,101701)],
                         'ADT'     :[time( 0,00,00,102424),time(23,30,00,102424)]}  # ???  what the deuce are the microseconds
        
        if time_period_str == 'ADT':
            return (datetime.combine(date_yyyy_mm_dd, special_times[time_period_str][0]), "1 day")
        
        elif time_period_str in special_times:            
            return (datetime.combine(date_yyyy_mm_dd, special_times[time_period_str][0]), "1 hour")

        
        (start, end) = time_period_str.split("-")    
            
        starttime = timedelta(hours=int(start[:2]), minutes=int(start[2:]))
        endtime   = timedelta(hours=int(  end[:2]), minutes=int(  end[2:]))
            
        return (datetime.combine(date_yyyy_mm_dd,time(hour=int(start[:2]),minute=int(start[2:]))), 
                '%i minute' % int((endtime - starttime).seconds/60))


    def readSourcefile(self,book):
        """
        Extracts sourcefiles names from "book"

        Our convention is to include any strings in the first column of the worksheet called "source";
        Source strings are each enclosed in parentheses.
        """
        
        sourcefile = ""
        
        if "source" not in book.sheet_names() :
            return sourcefile
        
        sourcesheet = book.sheet_by_name("source")
        for row_num in range(len(sourcesheet.col(0))):
            if sourcesheet.cell_value(row_num,0) == "": continue
            sourcefile = sourcefile + '( ' + sourcesheet.cell_value(row_num,0) + ' ) '

        return sourcefile
          
        
    def readMainlineCounts(self, file, primary_street, from_crossstreet, to_crossstreet, cdreader):  
        """
        Parses the given excel file representing mainline counts into a table of values for the countdracula database.
 
        * *file* is the Excel workbook file
        * *streetname1* is the NS-oriented street
        * *streetname2* is the EW-oriented street
        * *cdreader* is an instance of a CountsDatabaseReader, used to lookup the relevant streets and intersection.
        
        Returns a table of values for the countdracula database, for use with :py:meth:`CountsDatabaseWriter.insertMainlineCounts`
        """
        
        #---------Variables used-----------------------------------
        parametersList = []
        vtype = 0 # ??
        project = ""        #!! What to do !!
        
        #----- Street vars !! ----------------------------     
        ml_refpos = 0
        ml_onstreet = ""       #Mainline street name
        ml_ondir = ""          #Mainline direction
        ml_fromstreet = ""      #U/S street
        ml_tostreet = ""        #D/S street
                
        book = xlrd.open_workbook(file)
        sourcefile = self.readSourcefile(book) 
        sheetnames =  book.sheet_names()        
                
        mainStreetslist = cdreader.getPossibleStreetNames(primary_street)
        if mainStreetslist == []:
            raise CountsWorkbookParserException("readMainlineCounts: Street %s not found." % primary_street)
        
        fromStreetslist = cdreader.getPossibleStreetNames(from_crossstreet)
        if fromStreetslist == []:
            raise CountsWorkbookParserException("readMainlineCounts: Street %s not found." % from_crossstreet)
        
        toStreetslist = cdreader.getPossibleStreetNames(to_crossstreet)
        if toStreetslist == []:
            raise CountsWorkbookParserException("readMainlineCounts: Street %s not found." % to_crossstreet)
        
        
        final_mainstreet = None
        final_fromstreet = None
        final_tostreet = None
        intersection_id1 = None
        intersection_id2 = None
        
        for mainstreet in mainStreetslist:
            # print "mainstreet = "+ mainstreet
            
            possibleFromIntersections = 0
            for NWstreet in fromStreetslist:
                # print "NWstreet = "+ NWstreet
                
                intersection_id = cdreader.getIntersectionId(mainstreet,NWstreet)
                if not intersection_id: continue
                
                possibleFromIntersections += 1
                if possibleFromIntersections>1:
                    raise CountsWorkbookParserException("readMainlineCounts: Street %s and %s can have multiple intersections possible." % 
                                                        (primary_street, from_crossstreet))
                
                final_fromstreet = NWstreet
                intersection_id1 = intersection_id
                # print "  %s - %s int id %d" % (mainstreet, NWstreet, intersection_id1)
                
            possibleToIntersections = 0
            for SEstreet in toStreetslist:
                # print "NWstreet = "+ NWstreet
                
                intersection_id = cdreader.getIntersectionId(mainstreet,SEstreet)
                if not intersection_id: continue
                
                possibleToIntersections+=1
                if possibleToIntersections>1:
                    raise CountsWorkbookParserException("readMainlineCounts: Street %s and %s can have multiple intersections possible." % 
                                                        (primary_street, to_crossstreet))


                final_tostreet = SEstreet
                intersection_id2 = intersection_id
                # print "  %s - %s int id %d" % (mainstreet, SEstreet, intersection_id2)

            # done
            # print possibleFromIntersections, possibleToIntersections
            if possibleFromIntersections==1 and possibleToIntersections==1:
                final_mainstreet = mainstreet
                break

        if not final_mainstreet:
            raise CountsWorkbookParserException("readMainlineCounts: Couldn't find relevant intersections for %s from %s to %s." % (primary_street, from_crossstreet, to_crossstreet))
 
        #----------Assign ml street name, rest streets will be assigned based on column and direction------ 
        ml_onstreet = final_mainstreet         
        totalsheets_ids = range(len(sheetnames))  #create sheet id list
        
        for sheet_idx in totalsheets_ids :
           
            if sheetnames[sheet_idx]=="source": continue           
            activesheet = book.sheet_by_name(sheetnames[sheet_idx])
            
            #-------Create date from sheetname in date format-------------------------------- 
            tmp_date = sheetnames[sheet_idx].split('.')
            date_yyyy_mm_dd = date(int(tmp_date[0]),int(tmp_date[1]),int(tmp_date[2]) )
            
            column_ids = range(1,len(activesheet.row(0))) #find list of columns to process
            
            ref = activesheet.cell_value(1,0)
            if type(ref) is FloatType:
                ml_refpos = ref
            else:
                ml_refpos = 0
            
            
            for column in column_ids :
                
                vehicle = activesheet.cell_value(1,column)
                if type(vehicle) is FloatType and vehicle in range(-1,16):
                    vtype = vehicle
                else:
                    vtype = 0 # self._vtype
                
                #For the column, set direction and to from streets
                ml_ondir_temp = activesheet.cell_value(0,column)
                ml_ondir = ml_ondir_temp[:2] 
                direction = ml_ondir[0]
                
                if (direction == 'S' or direction == 'E'):
                    ml_fromstreet = final_fromstreet       #Veh is going from NtoS or WtoE
                    ml_tostreet = final_tostreet
                else:
                    ml_fromstreet = final_tostreet       #Veh is going from StoN or EtoW
                    ml_tostreet = final_fromstreet
                #------------------------------------------------------------------------------
    
                row_ids = range(2,len(activesheet.col(column))) #find rows to process for column
                
                for row in row_ids:
                    
                    count = activesheet.cell_value(row,column) 
                    if count == "" : continue
                    
                    (starttime, period) = self.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0))     
    
                    parametersList.append([count,starttime,period,vtype,ml_onstreet,ml_ondir,
                                           ml_fromstreet,ml_tostreet,ml_refpos,
                                           sourcefile,project])
                        
        return parametersList
    
    def readTurnCounts(self, file, streetname1, streetname2, cdreader):
        """
        Parses the given excel file representing turn counts into a table of values for the countdracula database.
        
        * *file* is the Excel workbook file
        * *streetname1* is the NS-oriented street
        * *streetname2* is the EW-oriented street
        * *cdreader* is an instance of a CountsDatabaseReader, used to lookup the relevant streets and intersection.
        
        Returns a table of values for the countdracula database, for use with :py:meth:`CountsDatabaseWriter.insertTurnCounts`
        """
        #---------Variables used-----------------------------------
        turnCountList = []
        vtype = None # ??? self._vtype
        project         = ""        #!! What to do !!
        
        #----- Street vars !! ----------------------------     
        t_fromstreet    = ""  #Turn approach street
        t_fromdir       = ""  #Turn approach direction
        t_tostreet      = ""  #Turn final street
        t_todir         = ""  #Turn final direction
        t_intstreet     = ""  #Intersecting street
        t_intid         = -1
                
        book = xlrd.open_workbook(file)       
        sourcefile = self.readSourcefile(book)
                
        NSstreetslist = cdreader.getPossibleStreetNames(streetname1)
        if NSstreetslist == []:
            raise CountsWorkbookParserException("readTurnCounts: Street %s not found." % streetname1)
        
        EWstreetslist = cdreader.getPossibleStreetNames(streetname2)
        if EWstreetslist == []:
            raise CountsWorkbookParserException("readTurnCounts: Street %s not found." % streetname2)
                
        # find the relevant intersection id
        possible_intersections = 0
        final_NSstreet = ""
        final_EWstreet = ""
        for NSstreet in NSstreetslist:
            for EWstreet in EWstreetslist:
                intersection_id = cdreader.getIntersectionId(NSstreet,EWstreet)
                # print NSstreet, EWstreet, intersection_id
                if not intersection_id: continue
                
                possible_intersections+=1
                if possible_intersections>1:
                    raise CountsWorkbookParserException("readTurnCounts: Streets %s and %s can have multiple intersections possible." % 
                                                       (streetname1, streetname2))

                final_NSstreet = NSstreet
                final_EWstreet = EWstreet
                t_intid = intersection_id
            
        if possible_intersections ==0:
            raise CountsWorkbookParserException("readTurnCounts: Streets %s and %s don't intersect." %
                                                (streetname1, streetname2)) 

        
        sheetnames =  book.sheet_names()
        totalsheets_ids = range(len(sheetnames))  #create sheet id list
        
        for sheet in totalsheets_ids :
            
            if sheetnames[sheet]=="source": continue
            activesheet = book.sheet_by_name(sheetnames[sheet])
            
            #-------Create date from sheetname in date format-------------------------------- 
            tmp_date = sheetnames[sheet].split('.')
            date_yyyy_mm_dd = date(int(tmp_date[0]),int(tmp_date[1]),int(tmp_date[2]) )  
            
            column_ids = range(1,len(activesheet.row(0))) #find list of columns to process
            
            for column in column_ids :
                vehicle = activesheet.cell_value(1,column)
                if type(vehicle) is FloatType and vehicle in range(-1,16):
                    vtype = vehicle
                else:
                    vtype = 0 #TODO: fix
                    
                #For the column, set direction and to from streets
                movement = activesheet.cell_value(0,column)
                t_fromdir = movement[:2]
                turntype = movement[2:]
                
                if t_fromdir not in ["NB", "WB", "EB", "SB"]:
                    raise CountsWorkbookParserException("readTurnCounts: Could not parse column header of %s; expect movement to start with direction.  Movement=%s" %
                                                        (file, movement))

                # First determines direction
                compass = ['N','E','S','W']                
                if turntype == "TH":    # through
                    t_todir = t_fromdir
                elif turntype in [' U-Turn','UT','U-Turn']:
                    t_todir = compass[compass.index(t_fromdir[0])-2] + 'B'
                elif turntype == 'RT':  # right turn
                    t_todir = compass[compass.index(t_fromdir[0])-1] + 'B'
                elif turntype == 'LT':  # left turn
                    t_todir = compass[compass.index(t_fromdir[0])-1] + 'B'
                elif turntype == 'PD':  # through - pedestrian?
                    t_todir = t_fromdir
                    vtype = 1
                else:
                    raise CountsWorkbookParserException("readTurnCounts: Could not parse column header of %s; turntype [%s] not understood." %
                                                        (file, turntype)) 
                
                # Determine Street names and order
                if turntype in ['TH',' U-Turn','U-Turn','UT','PD']:
                    if  t_fromdir == "NB" or t_fromdir == "SB":
                        t_fromstreet    = final_NSstreet
                        t_tostreet      = final_NSstreet
                        t_intstreet     = final_EWstreet
                    else:
                        t_fromstreet    = final_EWstreet
                        t_tostreet      = final_EWstreet
                        t_intstreet     = final_NSstreet
                else:   #turning movement and to and from streets are different
                    if  t_fromdir == "NB" or t_fromdir == "SB":
                        t_fromstreet    = final_NSstreet
                        t_tostreet      = final_EWstreet
                        t_intstreet     = final_EWstreet
                    else:           #TODO added maybe by mistake !!!  (check it)
                        t_fromstreet    = final_EWstreet
                        t_tostreet      = final_NSstreet
                        t_intstreet     = final_NSstreet
                #------------------------------------------------------------------------------
    
                row_ids = range(2,len(activesheet.col(column))) #find rows to process for column
                
                for row in row_ids:
                    
                    count = activesheet.cell_value(row,column) 
                    if count == "" : continue
                    
                    (starttime, period) = self.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0))     
                        
                    turnCountList.append([count,starttime,period,vtype,t_fromstreet,t_fromdir,t_tostreet,t_todir,
                                           t_intstreet,t_intid, sourcefile,project])
                        
        return turnCountList
    
    def readIntersectionIds(self,file):  
        """
        Reads an excel workbook with intersection information (see exampledata\intersections.xls) and returns
        the rows, for use with :py:meth:`CountsDatabaseWriter.insertIntersectionIds`
        """
    
        book = xlrd.open_workbook(file)
        sheetnames =  book.sheet_names()
        totalsheets_ids = range(len(sheetnames))
        intersection_tuples = []
        
        for sheet_id in totalsheets_ids :
           
            activesheet = book.sheet_by_name(sheetnames[sheet_id])
            row_ids = range(0,len(activesheet.col(0))) #find rows to process for column
                
            for row in row_ids:
                    
                street1 = activesheet.cell_value(row,0)
                street2 = activesheet.cell_value(row,1)
                int_id = activesheet.cell_value(row,2)
                long_x = activesheet.cell_value(row,3)
                lat_y = activesheet.cell_value(row,4)
                if (street1 != "" and street2 != "" and int_id != ""): #if all inputs exist
                    intersection_tuples.append([street1,street2,int_id,long_x,lat_y])
                    
        return intersection_tuples
    
    
    def readStreetNames(self,file):  
        """
        Reads an excel workbook with street names (see exampledata\streets.xls) and returns
        the rows, for use with :py:meth:`CountsDatabaseWriter.insertStreetNames`
        """        
        book = xlrd.open_workbook(file)       
        sheetnames =  book.sheet_names()
        totalsheets_ids = range(len(sheetnames))  #create sheet id list
        streetname_tuples = []

        for sheet_id in totalsheets_ids :
           
            activesheet = book.sheet_by_name(sheetnames[sheet_id])
            row_ids = range(0,len(activesheet.col(0))) #find rows to process for column
                
            for row in row_ids:
                if activesheet.cell_value(row,0) == "" : continue
 
                streetname_tuples.append([activesheet.cell_value(row,0),
                                          activesheet.cell_value(row,1),
                                          activesheet.cell_value(row,2),
                                          activesheet.cell_value(row,3)])
                    
        return streetname_tuples
    
    
    
    #===========================================================================
    # 
    # def read_alt_streets(self,file): 
    #    """
    #    creates commands list for street suffixes to send to py2psql
    #    """
    # 
    # 
    #    #---------Variables used-----------------------------------
    #    commands = []
    #    street = ""
    #    suffix = ""
    #    #-------------------------- open the .xls file------------------------------
    #    
    #    book = xlrd.open_workbook(file)
    #    
    #    #----------Loop through counts and Create SQL Commandslist with parameters-------------    
    #    sheetnames =  book.sheet_names() 
    #    totalsheets_ids = range(len(sheetnames))  #create sheet id list
    #    
    #    for sheet in totalsheets_ids :
    #       
    #        activesheet = book.sheet_by_name(sheetnames[sheet])
    #        row_ids = range(0,len(activesheet.col(0))) #find rows to process for column
    #            
    #        for row in row_ids:
    #                
    #            street = activesheet.cell_value(row,0)
    #            suffix = activesheet.cell_value(row,1)
    #            if (street != "" and suffix != ""): #if all inputs exist
    #                #-------Create time in time format !!!----------------- 
    #                commands.append([street,suffix])
    #                
    #    return commands
    # 
    #===========================================================================
