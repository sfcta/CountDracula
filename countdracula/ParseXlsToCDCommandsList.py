'''
Created on Jul 25, 2011

@author: varun
'''

import xlrd, datetime
from datetime import datetime,date, time, timedelta
from types import FloatType

from ReadFromCD import ReadFromCD

class ParseXlsToCDCommandsList():
    '''
    Takes in xls files and returns sql command parameters to be used by 'WriteToCD' to upload to DB
    '''


    def __init__(self, filename, filepath, vtype, host, db, username, pw):
        '''
        filename = filename (Eg: 3RDST_4THAVE.5THBLVD.xls)
        filepath = Eg: "C:\path\to\file
        vtype = vehicle type
        countDraculaReader = countDracula reader to read street_names etc.
        '''
        
        self._filename = filename
        self._filepath = filepath
        self._vtype = vtype
        self._countDraculaReader = ReadFromCD(host, db, username, pw)
      
    def setFileName(self, filename):
        self._filename = filename
      
    def createtimestamp (self, date_s,time_list_se):    #does the job of creating time in timestamp format from string
        """
        Creates timestamp from string
        date_s = date from sheet name in date format
        time_list_se as a list of start and end times from cell value Eg: cel l600-1700 is passed as time_list_se = [[1600],[1700]] 
        
        Returns list -> [starttimestamp, period] which can be fed to postgres to input in starttime and period column
        """
    
        special_times = {'AMPKHOUR':[time(8,00,00,100801),time(9,00,00,100801)],'PMPKHOUR' : [time(17,00,00,101701),time(18,00,00,101701)],'ADT' : [time(0,00,00,102424),time(23,30,00,102424)]}
        if  time_list_se[0] not in special_times: 
            
            start = time(int(time_list_se[0][:2]), int(time_list_se[0][2:]))  #Find start time in time format
            
            starttime = timedelta(hours = int(time_list_se[0][:2]), minutes =  int(time_list_se[0][2:])) #Find starttime and end times in timedelta format so they can be subtracted and period found !!
            endtime = timedelta(hours = int(time_list_se[1][:2]), minutes = int(time_list_se[1][2:]))
            
            starttimestamp = datetime.combine(date_s,start)
            period = '%i minute' % int((endtime - starttime).seconds/60)
            
        else:
            start = special_times[time_list_se[0]][0]
            
            starttime = timedelta(hours = int(special_times[time_list_se[0]][0].hour), minutes =  int(special_times[time_list_se[0]][0].minute)) #Find starttime and end times in timedelta format so they can be subtracted and period found !!
            endtime = timedelta(hours = int(special_times[time_list_se[0]][1].hour), minutes =  (int(special_times[time_list_se[0]][1].minute)))
            
            if int(start.microsecond) == 102424:
                starttimestamp = datetime.combine(date_s,start)
                period = '1 day'
            else:
                starttimestamp = datetime.combine(date_s,start)
                period = '%i minute' % int((endtime - starttime).seconds/60)
        
               
        return [starttimestamp,period]  
    
    def sourcefiles (self, sheetnames,book):
        """
        extracts sourcefiles names from "book"
        takes book object and list of sheetnames as input and returns sourcefile as a string
        """
        
        sourcefile = ""
        
        if "source" in sheetnames :
            
            sheetnames.remove("source")
            #Find sources
            sourcesheet = book.sheet_by_name("source")
            for sources in range(len(sourcesheet.col(0))):
                if sourcesheet.cell_value(sources,0) != "":
                    #sourcefile = sourcefile + '( ' + sourcesheet.cell_value(sources,0).replace('\\','\\\\') + ' ) '
                    sourcefile = sourcefile + '( ' + sourcesheet.cell_value(sources,0) + ' ) '
                    #print sourcefile
        return sourcefile
    
    
      
        
    def mainline(self ):  
        """
        creates commands list for ML counts
        retunrs a list of list of sql insert command parameters
        
        """
        
        #---------Variables used-----------------------------------
        parametersList = []
        #count = -1
        #vtype = raw_input()
        vtype = self._vtype
        #starttime       timestamp format
        #period            string "x minute" -> used by psql as an interval format
        sourcefile = ""     #Will be changed later if found
        project = ""        #!! What to do !!
        
        #----- Street vars !! ----------------------------     
        ml_refpos = 0
        ml_onstreet = ""       #Mainline street name
        ml_ondir = ""          #Mainline direction
        ml_fromstreet = ""      #U/S street
        ml_tostreet = ""        #D/S street
        
        #-------------------------- open the .xls file------------------------------
        
        book = xlrd.open_workbook(self._filepath + '\\' + self._filename)
        
        #---------Find all sheet names in book-------------------------------------- 
       
        sheetnames =  book.sheet_names()
            
          
        #---------Find if source is available and remove source sheet from list -----
        
        sourcefile = self.sourcefiles(sheetnames,book) 
        
        #-------- Extract road names from filename----------------------
        streets = self._filename.replace(".xls","")
        splits = "_-."
        slist = ''.join([ str.upper(s) if s not in splits else ' ' for s in streets]).split()
        i=0;
        
        #----See if we need to add suffix----------------------------------- 
        
        #----See if we need to add suffix----------------------------------- 
        
        ONstreetslist = self._countDraculaReader.getPossibleStreetNames(slist[0])
        if ONstreetslist == []:
            print "Street "+slist[0]+" not found. Please check and rename file !"
            raise
        
        NWstreetslist = self._countDraculaReader.getPossibleStreetNames(slist[1])
        if NWstreetslist == []:
            print "Street "+slist[1]+" not found. Please check and rename file !"
            raise
        
        SEstreetslist = self._countDraculaReader.getPossibleStreetNames(slist[2])
        if SEstreetslist == []:
            print "Street "+slist[2]+" not found. Please check and rename file !"
            raise
        
        
        possibleNWintersections = 0
        possibleSEintersections = 0
        final_ONstreet = ""
        final_NWstreet = ""
        final_SEstreet = ""
        
        for ONstreet in ONstreetslist:
            for NWstreet in NWstreetslist:
                temp_intid = self._countDraculaReader.getIntersectionId(ONstreet,NWstreet)
                if not temp_intid[0] == -1:
                    possibleNWintersections+=1
                    if possibleNWintersections>1:
                        print "Street "+slist[0]+" and Street "+slist[1]+" can have multiple intersections possible. Please check and rename file !"
                        raise
                    else:
                        for SEstreet in SEstreetslist:
                            temp_intid2 = self._countDraculaReader.getIntersectionId(ONstreet,SEstreet)
                            if not temp_intid2[0] == -1:
                                possibleSEintersections+=1
                                if possibleSEintersections>1:
                                    print "Street "+slist[0]+" and Street "+slist[2]+" can have multiple intersections possible. Please check and rename file !"
                                    raise
                                else:
                                    final_ONstreet = ONstreet
                                    final_NWstreet = NWstreet
                                    final_SEstreet = SEstreet
                        
            
        if possibleNWintersections ==0 or possibleSEintersections ==0:
            print "Street "+slist[0]+", Street "+slist[1]+" and Street "+slist[2]+" don't have a possible mainline spot for count. Please check and rename file !" 
            raise
 
        #----------Assign ml street name, rest streets will be assigned based on column and direction------ 
        ml_onstreet = final_ONstreet
        
        #----------Loop through counts and Create SQL Commandslist with parameters-------------    
         
        totalsheets_ids = range(len(sheetnames))  #create sheet id list
        
        for sheet in totalsheets_ids :
           
            activesheet = book.sheet_by_name(sheetnames[sheet])
            #-------Create date from sheetname in date format-------------------------------- 
            tmp_date = sheetnames[sheet].split('.')
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
                    vtype = self._vtype
                
                #For the column, set direction and to from streets
                ml_ondir_temp = activesheet.cell_value(0,column)
                ml_ondir = ml_ondir_temp[:2] 
                direction = ml_ondir[0]
                
                if (direction == 'S' or direction == 'E'):
                    ml_fromstreet = final_NWstreet       #Veh is going from NtoS or WtoE
                    ml_tostreet = final_SEstreet
                else:
                    ml_fromstreet = final_SEstreet       #Veh is going from StoN or EtoW
                    ml_tostreet = final_NWstreet
                #------------------------------------------------------------------------------
    
                row_ids = range(2,len(activesheet.col(column))) #find rows to process for column
                
                for row in row_ids:
                    
                    count = activesheet.cell_value(row,column) 
                    if count != "" : #if we have a count, validate inputs !
                        #-------Create time in time format !!!----------------- 
                        sp = self.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0).split("-"))     
                        starttime = sp[0]
                        period = sp[1]
                        
                        parametersList.append([count,starttime,period,vtype,ml_onstreet,ml_ondir,ml_fromstreet,ml_tostreet,ml_refpos,sourcefile,project])
                        
        return parametersList
    
    def turns(self):  #creates commands list for turns counts
        """
        creates commands list for turn counts
        retunrs a list of list of sql insert command parameters
        """
        #---------Variables used-----------------------------------
        parametersList = []
        #count = -1
        #vtype = raw_input() 
        vtype = self._vtype
        #starttime       timestamp format
        #period            string "x minute" -> used by psql as an interval format
        sourcefile = ""     #Will be changed later if found
        project = ""        #!! What to do !!
        
        #----- Street vars !! ----------------------------     
        t_fromstreet = ""      #Turn approach street
        t_fromdir = ""       #Turn approach direction
        t_tostreet = ""        #Turn final street
        t_todir = ""        #Turn final direction
        t_intstreet = ""       #Intersecting street
        t_intid = -1
        
        #-------------------------- open the .xls file------------------------------
        
        book = xlrd.open_workbook(self._filepath + '\\' + self._filename)
        
        #---------Find all sheet names in book-------------------------------------- 
       
        sheetnames =  book.sheet_names()
            
          
        #---------Find if source is available and remove source sheet from list -----
        
        sourcefile = self.sourcefiles(sheetnames,book) 
        
        #-------- Extract road names from filename----------------------
        streets = self._filename.replace(".xls","")
        splits = "_-."
        slist = ''.join([ str.upper(s) if s not in splits else ' ' for s in streets]).split()
        
        #----See if we need to add suffix----------------------------------- 
        
        NSstreetslist = self._countDraculaReader.getPossibleStreetNames(slist[0])
        if NSstreetslist == []:
            print "Street "+slist[0]+" not found. Please check and rename file !"
            raise
        
        EWstreetslist = self._countDraculaReader.getPossibleStreetNames(slist[1])
        if EWstreetslist == []:
            print "Street "+slist[1]+" not found. Please check and rename file !"
            raise
        
        possibleintersections = 0
        final_NSstreet = ""
        final_EWstreet = ""
        for NSstreet in NSstreetslist:
            for EWstreet in EWstreetslist:
                temp_intid = self._countDraculaReader.getIntersectionId(NSstreet,EWstreet)
                if not temp_intid[0] == -1:
                    possibleintersections+=1
                    if possibleintersections>1:
                        print "Street "+slist[0]+" and Street "+slist[1]+" can have multiple intersections possible. Please check and rename file !"
                        raise
                    else:
                        final_NSstreet = NSstreet
                        final_EWstreet = EWstreet
                        t_intid = temp_intid[0]
            
        if possibleintersections ==0:
            print "Street "+slist[0]+" and Street "+slist[1]+" don't intersect. Please check and rename file !" 
            raise
        
        #----------Loop through counts and Create SQL Commandslist with parameters-------------    
         
        totalsheets_ids = range(len(sheetnames))  #create sheet id list
        
        for sheet in totalsheets_ids :
           
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
                    vtype = self._vtype
                #For the column, set direction and to from streets
                movement = activesheet.cell_value(0,column)
                
                t_fromdir = movement[:2]
                turntype = movement[2:]
                #Determines directions
                if turntype == "TH":
                    t_todir = t_fromdir
                elif (turntype == ' U-Turn') or (turntype == 'UT') or (turntype == 'U-Turn'):
                    compass = ['N','W','S','E']
                    t_todir = compass[compass.index(t_fromdir[0])-2] + 'B'
                elif turntype == 'RT':
                    compass = ['N','W','S','E']
                    t_todir = compass[compass.index(t_fromdir[0])-1] + 'B'
                elif turntype == 'LT':
                    compass = ['N','E','S','W']
                    t_todir = compass[compass.index(t_fromdir[0])-1] + 'B'
                elif turntype == 'PD':
                    t_todir = t_fromdir
                    vtype = 1
                else:
                    print turntype
                    print 'Invalid Movement'
                    raise
                
                #Determines Street names and order
                if (turntype == 'TH' or turntype == ' U-Turn' or turntype == 'U-Turn' or turntype == 'PD' or turntype == 'UT') :
                    if  t_fromdir == "NB" or t_fromdir == "SB":
                        t_fromstreet = final_NSstreet
                        t_tostreet = final_NSstreet
                        t_intstreet = final_EWstreet
                    else:
                        t_fromstreet = final_EWstreet
                        t_tostreet = final_EWstreet
                        t_intstreet = final_NSstreet
                else:   #turning movement and to and from streets are different
                    if  t_fromdir == "NB" or t_fromdir == "SB":
                        t_fromstreet = final_NSstreet
                        t_tostreet = final_EWstreet
                        t_intstreet = final_EWstreet
                    else:           #TODO added maybe by mistake !!!  (check it)
                        t_fromstreet = final_EWstreet
                        t_tostreet = final_NSstreet
                        t_intstreet = final_NSstreet
                #------------------------------------------------------------------------------
    
                row_ids = range(2,len(activesheet.col(column))) #find rows to process for column
                
                for row in row_ids:
                    
                    count = activesheet.cell_value(row,column) 
                    if count != "" : #if we have a count, validate inputs !
                        #-------Create time in time format !!!----------------- 
                        sp = self.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0).split("-"))     
                        starttime = sp[0]
                        period = sp[1]
                        
                        parametersList.append([count,starttime,period,vtype,t_fromstreet,t_fromdir,t_tostreet,t_todir,t_intstreet,t_intid, sourcefile,project])
                        
        return parametersList
    
    def read_int_ids(self,file):  
        """
        creates commands list for intersection idsto send to py2psql
        """
    
        #---------Variables used-----------------------------------
        commands = []
        street1 = ""
        street2 = ""
        #ind_id = -1
        #long_x = -1.0
        #lat_y = -1.0
        #-------------------------- open the .xls file------------------------------
        
        book = xlrd.open_workbook(file)
        
        #---------Find all sheet names in book-------------------------------------- 
       
        sheetnames =  book.sheet_names()
        
        #----------Loop through counts and Create SQL Commandslist with parameters-------------    
         
        totalsheets_ids = range(len(sheetnames))  #create sheet id list
        
        for sheet in totalsheets_ids :
           
            activesheet = book.sheet_by_name(sheetnames[sheet])
            row_ids = range(0,len(activesheet.col(0))) #find rows to process for column
                
            for row in row_ids:
                    
                street1 = activesheet.cell_value(row,0)
                street2 = activesheet.cell_value(row,1)
                int_id = activesheet.cell_value(row,2)
                long_x = activesheet.cell_value(row,3)
                lat_y = activesheet.cell_value(row,4)
                if (street1 != "" and street2 != "" and int_id != ""): #if all inputs exist
                    #-------Create time in time format !!!----------------- 
                    commands.append([street1,street2,int_id,long_x,lat_y])
                    
        return commands
    
    
    
    
    def read_street_names(self,file):  
        """
        creates sql commands parameter list for inserting street names to send to py2psql
        """
    
        #---------Variables used-----------------------------------
        commands = []
        name = ""
        #-------------------------- open the .xls file------------------------------
        
        book = xlrd.open_workbook(file)
        
        #---------Find all sheet names in book-------------------------------------- 
       
        sheetnames =  book.sheet_names()
        
        #----------Loop through counts and Create SQL Commandslist with parameters-------------    
         
        totalsheets_ids = range(len(sheetnames))  #create sheet id list
        
        for sheet in totalsheets_ids :
           
            activesheet = book.sheet_by_name(sheetnames[sheet])
            row_ids = range(0,len(activesheet.col(0))) #find rows to process for column
                
            for row in row_ids:
                namesrow = [""]*4    
                name = activesheet.cell_value(row,0) 
                if name != "" : #If name exists!
                    #-------Create time in time format !!!-----------------
                    namesrow[0] = name
                    namesrow[1] =  activesheet.cell_value(row,1)
                    namesrow[2] = activesheet.cell_value(row,2)
                    namesrow[3] = activesheet.cell_value(row,3)   
                    commands.append(namesrow)
                    
        return commands
    
    
    
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
