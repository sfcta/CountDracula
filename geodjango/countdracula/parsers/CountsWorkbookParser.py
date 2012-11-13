import xlrd, sys, traceback, types
from datetime import datetime,date, time, timedelta

from countdracula.models import Node, StreetName, MainlineCountLocation, MainlineCount, TurnCountLocation, TurnCount, VehicleTypes
from django.core.exceptions import ObjectDoesNotExist


class CountsWorkbookParserException(Exception):
    pass

class CountsWorkbookParser():
    """
    Reads in and parses in Excel workbooks in certain standardized formats, returning tuples to be used by
    :py:class:`CountsDatabaseWriter` to insert into the Counts Database.
    """

    @classmethod
    def parseFilename(cls, filename):
        """
        Parse the filename into the component streets and returns them as a list.
        
        Delimiters are `_`, `-`, `.` and ` `.
        """
        streets = filename.replace(".xls","")
        delimiters = "_-."
        
        # convert them all to spaces
        for delim in delimiters: streets = streets.replace(delim, " ")
        
        return streets.split()
                

    def __init__(self):
        '''        
        Initialize the counts workbook parser.
        '''
        pass
      
    def createtimestamp (self, time_period_str, tzinfo):
        """
        Interprets time period string
        
        * *time_period_str*: can be one of `AMPKHOUR`, `PMPKHOUR`, `ADT`, or a range in military time, such as `1600-1615`.

        
        Returns tuple -> (starttime, period_minutes) where 
         starttime is datetime.time instance,
         and period_minutes is a integer representing number of minutes
        """        
        special_times = {'AMPKHOUR':[time( 8,00,00,100801),time( 9,00,00,100801)],
                         'PMPKHOUR':[time(17,00,00,101701),time(18,00,00,101701)],
                         'ADT'     :[time( 0,00,00,102424),time(23,30,00,102424)]}  # ???  what the deuce are the microseconds
        
        if time_period_str == 'ADT':
            return (special_times[time_period_str][0],  24*60)
        
        elif time_period_str in special_times:            
            return (special_times[time_period_str][0], 60)

        
        (start, end) = time_period_str.split("-")    
            
        starttime = timedelta(hours=int(start[:2]), minutes=int(start[2:]))
        endtime   = timedelta(hours=int(  end[:2]), minutes=int(  end[2:]))
            
        return (time(hour=int(start[:2]),minute=int(start[2:]), tzinfo=tzinfo), 
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
          
    def readGeo(self, book):
        """
        Reads optional worksheet called "geo" and returns the resulting data ( {inlinks_designation_car:inlink}, {outlinks_designation_char:outlink} ) where
        each link is a list: [streetname, dir]
        """
        inlinks     = {}
        outlinks    = {}
        if "geo" not in book.sheet_names():
            return (inlinks, outlinks)
        
        geosheet = book.sheet_by_name("geo")
        for row_num in range(geosheet.nrows):
            if geosheet.cell_value(row_num,0) == "" or geosheet.cell_value(row_num,0) == 'Streetname': continue
            
            streetname  = geosheet.cell_value(row_num,0).encode('ascii')
            inout       = geosheet.cell_value(row_num,1).encode('ascii')
            dir         = geosheet.cell_value(row_num,2).encode('ascii')
            designation = geosheet.cell_value(row_num,3).encode('ascii')
            
            # checking
            if inout.upper() not in ["IN", "OUT"]:
                raise CountsWorkbookParserException("Invalid geo worksheet: In/Out is invalid: %s" % inout)
            
            if dir not in ["NB","SB","WB","EB"]:
                raise CountsWorkbookParserException("Invalid geo worksheet: Invalid link dir: %s" % dir)
            
            if len(designation) != 1:
                    raise CountsWorkbookParserException("Invalid geo worksheet: Invalid designation (len != 1): %s" % designation)

            notallowed = "NSEWTHRLU2 -"
            if notallowed.find(designation) != -1:
                raise CountsWorkbookParserException("Invalid geo worksheet: Invalid designation (char not allowed): %s" % designation)
                
            if inout.upper() == "IN":
                inlinks[designation] = [streetname, dir]
            else:
                outlinks[designation] = [streetname, dir]
            
        return (inlinks, outlinks)
                
        
    
    def findSectionStarts(self, worksheet):
        """
        Simple method to iterate through the rows in the workbook and find sections, where a section is defined as a
        set of contiguous non-blank rows.
        
        Returns a list of tuples: [(startrownum1,endrownum1), (startrownum2,endrownum2), ... ]
        """
        sections            = []
        current_startrow    = -1
        current_endrow      = -1
        for rownum in range(worksheet.nrows):
            blank = True
            
            # check if the row is blank
            for colnum in range(worksheet.ncols):
                if worksheet.cell_type(rownum, colnum) not in [xlrd.XL_CELL_BLANK, xlrd.XL_CELL_EMPTY]:
                    blank = False
                    break
            # blank -- end section
            if blank and current_startrow != -1:
                current_endrow = rownum-1
                sections.append( (current_startrow, current_endrow) )
                current_startrow    = -1
                current_endrow      = -1
            
            # not blank -- start section
            if not blank and current_startrow == -1:
                current_startrow = rownum
        
        # are we in a section?
        if current_startrow != -1:
            current_endrow = rownum
            sections.append( (current_startrow, current_endrow) )
            
        return sections

    def numNonBlankColumns(self, worksheet, rownum):
        """
        Counts the number of non-blank columns for the given row.
        """
        for colnum in range(worksheet.ncols):
            if worksheet.cell_type(rownum, colnum) in [xlrd.XL_CELL_BLANK, xlrd.XL_CELL_EMPTY]: return colnum
        
        return worksheet.ncols            
    
    def vehicleTypeForString(self, vehicletype_str):
        """
        Returns the vehicle type code given the vehicle type string. (e.g. 0 for "All", 1 for "Pedestrian", etc.)
        """
        if type(vehicletype_str) == types.UnicodeType:
            vehicletype_str = vehicletype_str.encode('ascii')
            
        for tuple1 in VehicleTypes:
            
            # check if the strings match
            if type(tuple1[1]) == types.StringType and tuple1[1].upper() == vehicletype_str.upper():
                return tuple1[0]
            
            # second level of tuples
            if type(tuple1[1]) == types.TupleType:
                
                for tuple2 in tuple1[1]:

                    if type(tuple2[1]) == types.StringType and tuple2[1].upper() == vehicletype_str.upper():
                        return tuple2[0]
                    
        return self.vehicleTypeForString("Unknown")
                
        
    def readAndInsertMainlineCounts(self, file, primary_street, cross_street1, cross_street2, user, logger, tzinfo=None):  
        """
        Parses the given excel file representing mainline counts and inserts those counts into the countdracula database.
 
        * *file* is the Excel workbook file name
        * *primary_street* is the street on which the counts were taken
        * *cross_street1* and *cross_street2* are the bounding cross streets
        * *user* is the django User to associate with the count
        * *logger* is a logging instance
        
        On success, returns number of successful counts inserted.
        
        On failure, removes all counts from this workbook so it can be fixed and inserted again, and returns -1.
        """
        # logger.info("primary_street=[%s], cross_street1=[%s] cross_street2=[%s]" % (primary_street, cross_street1, cross_street2))
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
                    
                    intersections1[primary_street_name][cross_street1_name] = Node.objects.filter(street_to_node__street_name=primary_street_name) \
                                                                                          .filter(street_to_node__street_name=cross_street1_name)                
                    # don't bother if it's an empty set
                    if len(intersections1[primary_street_name][cross_street1_name]) == 0:
                        del intersections1[primary_street_name][cross_street1_name]
    
                for cross_street2_name in cross_street2_list:
                    intersections2[primary_street_name][cross_street2_name] = Node.objects.filter(street_to_node__street_name=primary_street_name) \
                                                                                          .filter(street_to_node__street_name=cross_street2_name)
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

                project  = ""
                sections = self.findSectionStarts(activesheet)
                # loop through the different sections in the workbook
                for section in sections:
                
                    # project section?
                    if activesheet.cell_value(section[0],0).upper() == "PROJECT":
                        project = activesheet.cell_value(section[0]+1,0)
                        continue
                    
                    # figure out the vehicle type and row with the column labels
                    assert(activesheet.cell_value(section[0]+1,0).upper() == "MAINLINE")
                    label_row = section[0]+1
                   
                    # figure out the vehicle type code
                    vehicle = activesheet.cell_value(section[0], 0)
                    if type(vehicle) in [types.FloatType, types.IntType] and vehicle in range(16):
                        vtype = vehicle
                    elif type(vehicle) in [types.StringType, types.UnicodeType]:
                        vtype = self.vehicleTypeForString(vehicle)
                    else:
                        vtype = 0 #TODO: fix
                    logger.info("  Worksheet %20s Vehicle=%s" % (sheetnames[sheet_idx], vehicle))
                                                            

                    for column in range(1,self.numNonBlankColumns(activesheet, label_row)):
                        
                        # Read the label header
                        ml_ondir_temp   = activesheet.cell_value(label_row,column)
                        ml_ondir        = ml_ondir_temp[:2] 
                        direction       = ml_ondir[0]
                        
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
                        for row in range(section[0]+2, section[1]+1):
                            
                            count = activesheet.cell_value(row,column) 
                            if count == "" : continue
                            
                            (starttime, period) = self.createtimestamp(activesheet.cell_value(row,0), tzinfo=tzinfo)     
            
                            mainline_count = MainlineCount(location             = mainline_count_location,
                                                           count                = count,
                                                           count_date           = date_yyyy_mm_dd,
                                                           start_time           = starttime,
                                                           period_minutes       = period,
                                                           vehicle_type         = vtype,
                                                           reference_position   = -1, # reference position unknown, it's not in the workbook
                                                           sourcefile           = file,
                                                           project              = project,
                                                           upload_user          = user)
                            mainline_count.clean()
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
    
    def readAndInsertTurnCounts(self, file, street1, street2, user, logger, tzinfo=None):
        """
        Parses the given excel file representing turn counts and inserts them into the countdracula database.
        
        * *file* is the Excel workbook file
        * *street1* is the name of the NS-oriented street
        * *street2* is the name of the EW-oriented street
        * *user* is the django User to associate with the count
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
                    intersection_ids = Node.objects.filter(street_to_node__street_name=NSstreet) \
                                                   .filter(street_to_node__street_name=EWstreet)
                    
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
            logger.info("intersection id = %d" % final_intid.id)
            # logger.debug("final_NSstreet=[%s], final_EWstreet=[%s]" % (final_NSstreet, final_EWstreet))
            
            # go through the sheets and read the data        
            book                = xlrd.open_workbook(file)       
            sheetnames          = book.sheet_names()
            counts_saved        = 0
            # read any other link info from geo worksheet
            (adtl_inlinks, adtl_outlinks) = self.readGeo(book)

            # add the StreetName objs to the adtl_links
            for street in StreetName.objects.filter(nodes=final_intid):
                for designation,list in adtl_inlinks.iteritems():
                    if list[0].upper() == street.street_name: adtl_inlinks[designation].append(street)
                for designation,list in adtl_outlinks.iteritems():
                    if list[0].upper() == street.street_name: adtl_outlinks[designation].append(street)
            logger.info("adtl_inlinks = %s" % str(adtl_inlinks))
            logger.info("adtl_outlinks = %s" % str(adtl_outlinks))                    

            valid_fromdirs =  ["NB", "WB", "EB", "SB"]
            for indesig in adtl_inlinks.keys(): 
                if len(adtl_inlinks[indesig]) == 3: valid_fromdirs.append(indesig+"_")

            for sheet_idx in range(len(sheetnames)) :
                
                if sheetnames[sheet_idx] in ["source","geo"]: continue
                activesheet = book.sheet_by_name(sheetnames[sheet_idx])
                
                # create date from sheetname in date format 
                tmp_date = sheetnames[sheet_idx].split('.')
                date_yyyy_mm_dd = date(int(tmp_date[0]),int(tmp_date[1]),int(tmp_date[2]) )

                project  = ""
                sections = self.findSectionStarts(activesheet)
                
                # loop through the different sections in the workbook
                for section in sections:

                    # project section?
                    if activesheet.cell_value(section[0],0).upper() == "PROJECT":
                        project = activesheet.cell_value(section[0]+1,0)
                        continue
                    
                    # figure out the vehicle type and row with the column labels
                    assert(activesheet.cell_value(section[0]+1,0).upper() == "TURNS")
                    label_row = section[0]+1
                   
                    # figure out the vehicle type code
                    vehicle = activesheet.cell_value(section[0], 0)
                    if type(vehicle) in [types.FloatType, types.IntType] and vehicle in range(16):
                        vtype = vehicle
                    elif type(vehicle) in [types.StringType, types.UnicodeType]:
                        vtype = self.vehicleTypeForString(vehicle)
                    else:
                        vtype = 0 #TODO: fix
                    logger.info("  Worksheet %20s Vehicle=%s" % (sheetnames[sheet_idx], vehicle))
                    
                    if vtype==1:
                        logger.info("Pedestrian crossings are not handled yet -- skipping")
                        continue
                        
                    # iterate through the columns
                    for column in range(1,self.numNonBlankColumns(activesheet, label_row)):
                            
                        # Read the label header
                        movement = activesheet.cell_value(label_row,column)
                        t_fromdir = movement[:2]
                        turntype = movement[2:]
                        
                        if t_fromdir not in valid_fromdirs:
                            raise CountsWorkbookParserException("readTurnCounts: Could not parse column header of %s!%s; expect movement to start with direction.  Movement=[%s] Column=%d Type=%d" %
                                                                (file, sheetnames[sheet_idx], movement, column, activesheet.cell_type(label_row,column)))
                        # todo: special inbound link
                        
                        if  t_fromdir in ["NB","SB"]:
                            t_fromstreet    = final_NSstreet
                        elif t_fromdir in ["EB", "WB"]:
                            t_fromstreet    = final_EWstreet
                        elif t_fromdir[1] == "_":
                            t_fromstreet    = adtl_inlinks[t_fromdir[0]][2]
                            t_fromdir       = adtl_inlinks[t_fromdir[0]][1]
                                    
                        # determine direction of outbound link
                        
                        # special case
                        if turntype[-2:-1]=="_" and turntype[-1:] in adtl_outlinks.keys():
                            t_todir             = adtl_outlinks[turntype[-1:]][1]
                            t_tostreet          = adtl_outlinks[turntype[-1:]][2]

                        # regular case
                        else:
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
                                if  t_fromdir in ["NB","SB"]:
                                    t_tostreet      = final_NSstreet
                                    t_intstreet     = final_EWstreet
                                else:
                                    t_tostreet      = final_EWstreet
                                    t_intstreet     = final_NSstreet
                            else:   #turning movement and to and from streets are different
                                if  t_fromdir in ["NB","SB"]:
                                    t_tostreet      = final_EWstreet
                                    t_intstreet     = final_EWstreet
                                else:           #TODO added maybe by mistake !!!  (check it)
                                    t_tostreet      = final_NSstreet
                                    t_intstreet     = final_NSstreet
                        # logger.debug("movement [%s] from %s %s to %s %s" % (movement, t_fromstreet, t_fromdir, t_tostreet, t_todir))
    
    
                        # look for the turn count location in countdracula
                        try:
                            turn_count_location = TurnCountLocation.objects.get(from_street    = t_fromstreet,
                                                                                from_dir       = t_fromdir,
                                                                                to_street      = t_tostreet,
                                                                                to_dir         = t_todir,
                                                                                intersection   = final_intid)
                        except ObjectDoesNotExist:
                            turn_count_location = TurnCountLocation(from_street    = t_fromstreet,
                                                                    from_dir       = t_fromdir,
                                                                    to_street      = t_tostreet,
                                                                    to_dir         = t_todir,
                                                                    intersection_street = t_intstreet,
                                                                    intersection   = final_intid)
                            turn_count_location.save()
                                                    
                        for row in range(section[0]+2, section[1]+1):
                            
                            count = activesheet.cell_value(row,column) 
                            if count == "" : continue
                            
                            (starttime, period) = self.createtimestamp(activesheet.cell_value(row,0), tzinfo=tzinfo)     
                            
                            turn_count = TurnCount(location         = turn_count_location,
                                                   count            = count,
                                                   count_date       = date_yyyy_mm_dd,
                                                   start_time       = starttime,
                                                   period_minutes   = period,
                                                   vehicle_type     = vtype,
                                                   sourcefile       = file,
                                                   project          = project,
                                                   upload_user      = user)
                            turn_count.clean()
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
    
