'''
Created on Jul 25, 2011

@author: varun
'''

import xlrd, sys, traceback
from datetime import datetime,date, time, timedelta
from types import FloatType

from countdracula.models import Node, StreetName, MainlineCountLocation, MainlineCount, TurnCountLocation, TurnCount
from django.core.exceptions import ObjectDoesNotExist


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
      
    def createtimestamp (self, date_yyyy_mm_dd, time_period_str, tzinfo):
        """
        Interprets date and time period string
        
        * *date_yyyy_mm_dd*: the date string in "yyyy-mm-dd" format. E.g. `2011-09-26`.
        * *time_period_str*: can be one of `AMPKHOUR`, `PMPKHOUR`, `ADT`, or a range in military time, such as `1600-1615`.

        
        Returns tuple -> (starttime, period_minutes) where startime is a datetime object and period_minutes is a integer representing number of minutes
        """    
        special_times = {'AMPKHOUR':[time( 8,00,00,100801),time( 9,00,00,100801)],
                         'PMPKHOUR':[time(17,00,00,101701),time(18,00,00,101701)],
                         'ADT'     :[time( 0,00,00,102424),time(23,30,00,102424)]}  # ???  what the deuce are the microseconds
        
        if time_period_str == 'ADT':
            return (datetime.combine(date_yyyy_mm_dd, special_times[time_period_str][0]),  24*60)
        
        elif time_period_str in special_times:            
            return (datetime.combine(date_yyyy_mm_dd, special_times[time_period_str][0]), 60)

        
        (start, end) = time_period_str.split("-")    
            
        starttime = timedelta(hours=int(start[:2]), minutes=int(start[2:]))
        endtime   = timedelta(hours=int(  end[:2]), minutes=int(  end[2:]))
            
        return (datetime.combine(date_yyyy_mm_dd, time(hour=int(start[:2]),minute=int(start[2:]), tzinfo=tzinfo) ), 
                int((endtime - starttime).seconds/60))


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
          
        
    def readAndInsertMainlineCounts(self, file, primary_street, cross_street1, cross_street2, logger, tzinfo=None):  
        """
        Parses the given excel file representing mainline counts and inserts those counts into the countdracula database.
 
        * *file* is the Excel workbook file name
        * *primary_street* is the street on which the counts were taken
        * *cross_street1* and *cross_street2* are the bounding cross streets
        * *logger* is a logging instance
        
        On success, returns number of successful counts inserted.
        
        On failure, removes all counts from this workbook so it can be fixed and inserted again, and returns -1.
        """
        
        mainline_counts = MainlineCount.objects.filter(sourcefile=file)
        if len(mainline_counts) > 0:
            logger.error("  readAndInsertMainlineCounts() called on %s, but %d mainline counts already "\
                        "exist with that sourcefile.  Skipping." % (file, len(mainline_counts)))
            return -1
        
        try:                      
                        
            primary_street_list = StreetName.getPossibleStreetNames(primary_street)
            if len(primary_street_list) == 0:
                raise CountsWorkbookParserException("readMainlineCounts: primary street %s not found." % primary_street)
                    
            cross_street1_list = StreetName.getPossibleStreetNames(cross_street1)
            if len(cross_street1_list) == 0:
                raise CountsWorkbookParserException("readMainlineCounts: cross street 1 %s not found." % cross_street1)
    
            cross_street2_list = StreetName.getPossibleStreetNames(cross_street2)
            if len(cross_street2_list) == 0:
                raise CountsWorkbookParserException("readMainlineCounts: cross street 2 %s not found." % cross_street2)
    
            # looking for a primary street that intersects with both one of cross_street1 cross_Street2
            # collect this info in two dictionaries: 
            #  { primary_street_name (StreetName instance) -> { cross_street1_name (StreetName instance) -> QuerySet of Node instances }}
            #  { primary_street_name (StreetName instance) -> { cross_street2_name (StreetName instance) -> QuerySet of Node instances }}
            intersections1 = {}
            intersections2 = {}
            
            for primary_street_name in primary_street_list:
                intersections1[primary_street_name] = {}
                intersections2[primary_street_name] = {}
                
                for cross_street1_name in cross_street1_list:
                    
                    intersections1[primary_street_name][cross_street1_name] = Node.objects.filter(streetname__street_name=primary_street_name.street_name) \
                                                                                          .filter(streetname__street_name=cross_street1_name.street_name)                
                    # don't bother if it's an empty set
                    if len(intersections1[primary_street_name][cross_street1_name]) == 0:
                        del intersections1[primary_street_name][cross_street1_name]
    
                for cross_street2_name in cross_street2_list:
                    intersections2[primary_street_name][cross_street2_name] = Node.objects.filter(streetname__street_name=primary_street_name) \
                                                                                          .filter(streetname__street_name=cross_street2_name)
                    # don't bother if it's an empty set
                    if len(intersections2[primary_street_name][cross_street2_name]) == 0:
                        del intersections2[primary_street_name][cross_street2_name]
                        
            # ideally, there will be exactly one primary street with a cross street 1 candidate and a cross street 2 candidate
            primary_street_name_final = None
            for primary_street_name in primary_street_list:
                if len(intersections1[primary_street_name]) == 0: continue
                if len(intersections2[primary_street_name]) == 0: continue
    
                if len(intersections1[primary_street_name]) > 1:
                    raise CountsWorkbookParserException("readMainlineCounts: Street %s and cross street 1 %s have multiple intersections: %s" % 
                                                        (primary_street_name, cross_street1, str(intersections1[primary_street_name])))
                if len(intersections2[primary_street_name]) > 1:
                    raise CountsWorkbookParserException("readMainlineCounts: Street %s and cross street 2 %s have multiple intersections: %s" % 
                                                        (primary_street_name, cross_street2, str(intersections2[primary_street_name])))
                # already found one?
                if primary_street_name_final:
                    raise CountsWorkbookParserException("readMainlineCounts: Multiple primary streets (%s,%s) intersect with %s/%s" % 
                                                        (primary_street_name,  primary_street_name_final,
                                                         cross_street1, cross_street2))
                primary_street_name_final = primary_street_name
            
            if not primary_street_name_final:
                    raise CountsWorkbookParserException("readMainlineCounts: Street %s and cross streets %s,%s have no intersections: %s %s" % 
                                                        (primary_street, str(cross_street1_list), str(cross_street2_list), 
                                                         str(intersections1), str(intersections2)))
    
            # finalize the cross street names and intersection ids        
            cross_street1_name_final = intersections1[primary_street_name_final].keys()[0]
            cross_street2_name_final = intersections2[primary_street_name_final].keys()[0]
            
            # go through the sheets and read the data
            book                = xlrd.open_workbook(file)
            sheetnames          = book.sheet_names()     
            counts_saved        = 0
            for sheet_idx in range(len(sheetnames)) :
               
                if sheetnames[sheet_idx]=="source": continue
                activesheet = book.sheet_by_name(sheetnames[sheet_idx])
                
                # Create date from sheetname in date format 
                tmp_date = sheetnames[sheet_idx].split('.')
                date_yyyy_mm_dd = date(int(tmp_date[0]),int(tmp_date[1]),int(tmp_date[2]) )
                if len(tmp_date) > 3 and (tmp_date[3].upper()=="TRUCK" or tmp_date[3].upper()=="PEDESTRIAN"):
                    continue
                
                for column in range(1,len(activesheet.row(0))):
                    
                    vehicle = activesheet.cell_value(1,column)
                    if type(vehicle) is FloatType and vehicle in range(-1,16):
                        vtype = vehicle
                    else:
                        vtype = 0 # self._vtype
                    
                    #For the column, set direction and to from streets
                    ml_ondir_temp = activesheet.cell_value(0,column)
                    ml_ondir = ml_ondir_temp[:2] 
                    direction = ml_ondir[0]
                    
                    # The convention is that cross street 1 is always north or west of cross street 2
                    # so use this cue to determine the origin/destination of the movement
                    if (direction == 'S' or direction == 'E'):
                        ml_fromstreet = cross_street1_name_final
                        ml_fromint    = intersections1[primary_street_name_final][ml_fromstreet][0]
                        ml_tostreet   = cross_street2_name_final
                        ml_toint      = intersections2[primary_street_name_final][ml_tostreet][0]
                    else:
                        ml_fromstreet = cross_street2_name_final
                        ml_fromint    = intersections2[primary_street_name_final][ml_fromstreet][0]
                        ml_tostreet   = cross_street1_name_final
                        ml_toint      = intersections1[primary_street_name_final][ml_tostreet][0]
    
                    # look for the mainline count location in countdracula
                    try:
                        mainline_count_location = MainlineCountLocation.objects.get(from_int    = ml_fromint,
                                                                                    to_int      = ml_toint,
                                                                                    on_street   = primary_street_name_final,
                                                                                    on_dir      = ml_ondir)
                    except ObjectDoesNotExist:
                        mainline_count_location = MainlineCountLocation(on_street           = primary_street_name_final,
                                                                        on_dir              = ml_ondir,
                                                                        from_street         = ml_fromstreet,
                                                                        from_int            = ml_fromint,
                                                                        to_street           = ml_tostreet,
                                                                        to_int              = ml_toint)
                        mainline_count_location.save()
    
                    # process the rows                    
                    for row in range(2,len(activesheet.col(column))) :
                        
                        count = activesheet.cell_value(row,column) 
                        if count == "" : continue
                        
                        (starttime, period) = self.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0), tzinfo=tzinfo)     
        
                        mainline_count = MainlineCount(location             = mainline_count_location,
                                                       count                = count,
                                                       start_time           = starttime,
                                                       period_minutes       = period,
                                                       vehicle_type         = vtype,
                                                       reference_position   = -1, # reference position unknown, it's not in the workbook
                                                       sourcefile           = file,
                                                       project              = "")
                        mainline_count.save()
                        counts_saved += 1
                                
            logger.info("  Processed %s into countdracula" % file)
            logger.info("  Successfully saved %4d mainline counts" % counts_saved)
            return counts_saved
        
        except Exception as e:
            logger.error("  Failed to process %s" % file)
            logger.error("  " + str(e))
            logger.error("  " + traceback.format_exc())
            
            # remove the rest of the counts for this sourcefile so it can be retried
            mainline_counts = MainlineCount.objects.filter(sourcefile=file)
            if len(mainline_counts) > 0:
                logger.debug("  Removing %d counts from countdracula so sourcefile %s can be reprocessed" % 
                             (len(mainline_counts), file))
                mainline_counts.delete()
            else:
                logger.debug("  No counts to remove for sourcefile %s; sourcefile can be reprocessed" % file)
                
            return -1
    
    def readAndInsertTurnCounts(self, file, street1, street2, logger, tzinfo=None):
        """
        Parses the given excel file representing turn counts and inserts them into the countdracula database.
        
        * *file* is the Excel workbook file
        * *street1* is the name of the NS-oriented street
        * *street2* is the name of the EW-oriented street
        * *logger* is a logging instance
        
        On success, returns number of successful counts inserted.
        
        On failure, removes all counts from this workbook so it can be fixed and inserted again, and returns -1.
                
        Note that this method is a little counter-intuitive because the arguments determine the way the movements are stored in
        the database.  For example, suppose you have an intersection where the street changes names from "SouthOne Street" to 
        "SouthTwo Street" as it passes through an intersection with "EastWest Street".  This method would be called with
        street1="SouthOne Street" and street2="EastWest Street" and the through movement would be stored with
        from_street="SouthOne Street" fromdir="SB", tostreet="SouthOne Street" todir="SB" even though "SouthOne Street"
        doesn't have a southbound link from the intersection, since it's really "SouthTwo Street".  Thus, using this
        implementation, the fromstreet and tostreet define the intersection only, and not the movement.
        """
        turn_counts = TurnCount.objects.filter(sourcefile=file)
        if len(turn_counts) > 0:
            logger.error("  readAndInsertTurnCounts() called on %s, but %d turn counts already "\
                        "exist with that sourcefile.  Skipping." % (file, len(turn_counts)))
            return -1
        
        try:  
            
            NSstreetslist = StreetName.getPossibleStreetNames(street1)
            if len(NSstreetslist) == 0:
                raise CountsWorkbookParserException("readTurnCounts: Street %s not found." % street1)
            
            EWstreetslist = StreetName.getPossibleStreetNames(street2)
            if len(EWstreetslist) == 0:
                raise CountsWorkbookParserException("readTurnCounts: Street %s not found." % street2)
    
            # look for intersections of these streets; intersections maps 
            #   { (streetname1 StreetName instance, streetname2 StreetName instance) -> QuerySet of intersections }
            intersections = {}
            for NSstreet in NSstreetslist:
                for EWstreet in EWstreetslist:
                    intersection_ids = Node.objects.filter(streetname__street_name=NSstreet.street_name) \
                                                   .filter(streetname__street_name=EWstreet.street_name)
                    
                    if len(intersection_ids) > 0:
                        intersections[(NSstreet, EWstreet)] = intersection_ids
            # ideally, we'll have one intersection with one intersection id
            if len(intersections) == 0:
                raise CountsWorkbookParserException("readTurnCounts: No intersections found for %s and %s" % (street1, street2))
            
            if len(intersections) > 1:
                raise CountsWorkbookParserException("readTurnCounts: Multiple intersections found for %s and %s: %s" % (street1, street2, str(intersections)))
    
            if len(intersections.values()[0]) > 1:
                raise CountsWorkbookParserException("readTurnCounts: Multiple intersections found for %s and %s: %s" % (street1, street2, str(intersections)))
    
            # len(intersections) == 1
            final_NSstreet  = intersections.keys()[0][0]
            final_EWstreet  = intersections.keys()[0][1]
            final_intid     = intersections[(final_NSstreet,final_EWstreet)][0]
            
            # go through the sheets and read the data        
            book                = xlrd.open_workbook(file)       
            sheetnames          = book.sheet_names()
            counts_saved        = 0
                    
            for sheet_idx in range(len(sheetnames)) :
                
                if sheetnames[sheet_idx]=="source": continue
                activesheet = book.sheet_by_name(sheetnames[sheet_idx])
                
                # create date from sheetname in date format 
                tmp_date = sheetnames[sheet_idx].split('.')
                date_yyyy_mm_dd = date(int(tmp_date[0]),int(tmp_date[1]),int(tmp_date[2]) )
                if len(tmp_date) > 3 and (tmp_date[3].upper()=="TRUCK" or tmp_date[3].upper()=="PEDESTRIAN"):
                    continue
                                        
                for column in range(1,len(activesheet.row(0))):
                    
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
                        raise CountsWorkbookParserException("readTurnCounts: Could not parse column header of %s!%s; expect movement to start with direction.  Movement=[%s] Column=%d Type=%d" %
                                                            (file, sheetnames[sheet_idx], movement, column, activesheet.cell_type(0,column)))
    
                    # First determines direction
                    compass = ['N','E','S','W']                
                    if turntype == "TH":    # through
                        t_todir = t_fromdir
                    elif turntype in [' U-Turn','UT','U-Turn']:
                        t_todir = compass[compass.index(t_fromdir[0])-2] + 'B'
                    elif turntype == 'RT':  # right turn
                        t_todir = compass[compass.index(t_fromdir[0])-3] + 'B'
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

                    # look for the turn count location in countdracula
                    try:
                        turn_count_location = TurnCountLocation.objects.get(from_street    = t_fromstreet,
                                                                            from_dir       = t_todir,
                                                                            to_street      = t_tostreet,
                                                                            to_dir         = t_todir,
                                                                            intersection   = final_intid)
                    except ObjectDoesNotExist:
                        turn_count_location = TurnCountLocation(from_street    = t_fromstreet,
                                                                from_dir       = t_todir,
                                                                to_street      = t_tostreet,
                                                                to_dir         = t_todir,
                                                                intersection_street = t_intstreet,
                                                                intersection   = final_intid)
                        turn_count_location.save()
                                                
                    for row in range(2,len(activesheet.col(column))):
                        
                        count = activesheet.cell_value(row,column) 
                        if count == "" : continue
                        
                        (starttime, period) = self.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0), tzinfo=tzinfo)     
                        
                        turn_count = TurnCount(location         = turn_count_location,
                                               count            = count,
                                               start_time       = starttime,
                                               period_minutes   = period,
                                               vehicle_type     = vtype,
                                               sourcefile       = file,
                                               project          = "")
                        turn_count.save()
                        counts_saved += 1
                        
            logger.info("  Processed %s into countdracula" % file)
            logger.info("  Successfully saved %4d turn counts" % counts_saved)
            return counts_saved
        
        except Exception as e:
            logger.error("  Failed to process %s" % file)
            logger.error("  "+str(e))
            logger.error("  "+traceback.format_exc())
            
            # remove the rest of the counts for this sourcefile so it can be retried
            turn_counts = TurnCount.objects.filter(sourcefile=file)
            if len(turn_counts) > 0:
                logger.debug("  Removing %d counts from countdracula so sourcefile %s can be reprocessed" % 
                             (len(turn_counts), file))
                turn_counts.delete()
            else:
                logger.debug("  No counts to remove for sourcefile %s; sourcefile can be reprocessed" % file)

            return -1
            
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
