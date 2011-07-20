#!/usr/bin/env python

"""Returns appropriate list of command parameters to be used to either 
   upload to server or create csv file
"""

from datetime import date
import xlrd 
import py2psql
import us_lib   #Custom built library that has random utility functions
from types import FloatType

__author__ = "Varun Kohli, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "Jul 1 2011" 

def mainline(filename,filepath,vtype_i,host,db,user,pw):  
    """
    creates commands list for ML counts
    """
    
    #---------Variables used-----------------------------------
    commands = []
    #count = -1
    #vtype = raw_input()
    vtype = vtype_i
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
    
    book = xlrd.open_workbook(filepath + '\\' + filename)
    
    #---------Find all sheet names in book-------------------------------------- 
   
    sheetnames =  book.sheet_names()
        
      
    #---------Find if source is available and remove source sheet from list -----
    
    sourcefile = us_lib.sourcefiles(sheetnames,book) 
    
    #-------- Extract road names from filename----------------------
    streets = filename.replace(".xls","")
    splits = "_-."
    slist = ''.join([ str.upper(s) if s not in splits else ' ' for s in streets]).split()
    i=0;
    
    #----See if we need to add suffix----------------------------------- 
    
    for i in range(0,3):
        if (py2psql.street_in_streetnames(slist[i],host,db,user,pw)==1):
            #print "street"+slist[i]+"found"
            pass
        elif (py2psql.street_in_altnames(slist[i],host,db,user,pw)==1):
            alt_name = py2psql.altname(slist[i],host,db,user,pw)
            if (py2psql.street_in_streetnames(alt_name,host,db,user,pw)==1):
                slist[i] = alt_name
                #print "street"+slist[i]+"founf"
            else:
                print "street"+slist[i]+"notfounf"
                raise
        else:
            print "street"+slist[i]+"notfounf"
            raise
   
    #----------Assign ml street name, rest streets will be assigned based on column and direction------ 
    ml_onstreet = slist[0]
    
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
                vtype = vtype_i
            
            #For the column, set direction and to from streets
            ml_ondir_temp = activesheet.cell_value(0,column)
            ml_ondir = ml_ondir_temp[:2] 
            direction = ml_ondir[0]
            
            if (direction == 'S' or direction == 'E'):
                ml_fromstreet = slist[1]       #Veh is going from NtoS or WtoE
                ml_tostreet = slist[2]
            else:
                ml_fromstreet = slist[2]       #Veh is going from StoN or EtoW
                ml_tostreet = slist[1]
            #------------------------------------------------------------------------------

            row_ids = range(2,len(activesheet.col(column))) #find rows to process for column
            
            for row in row_ids:
                
                count = activesheet.cell_value(row,column) 
                if count != "" : #if we have a count, validate inputs !
                    #-------Create time in time format !!!----------------- 
                    sp = us_lib.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0).split("-"))     
                    starttime = sp[0]
                    period = sp[1]
                    
                    commands.append([count,starttime,period,vtype,ml_onstreet,ml_ondir,ml_fromstreet,ml_tostreet,ml_refpos,sourcefile,project])
                    
    return commands
       
def turns(filename,filepath, vtype_i,host,db,user,pw):  #creates commands list for turns counts
    """
    creates commands list for turn counts
    """
    #---------Variables used-----------------------------------
    commands = []
    #count = -1
    #vtype = raw_input() 
    vtype = vtype_i
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
    
    book = xlrd.open_workbook(filepath + '\\' + filename)
    
    #---------Find all sheet names in book-------------------------------------- 
   
    sheetnames =  book.sheet_names()
        
      
    #---------Find if source is available and remove source sheet from list -----
    
    sourcefile = us_lib.sourcefiles(sheetnames,book) 
    
    #-------- Extract road names from filename----------------------
    streets = filename.replace(".xls","")
    splits = "_-."
    slist = ''.join([ str.upper(s) if s not in splits else ' ' for s in streets]).split()
    
    #----See if we need to add suffix----------------------------------- 
    
    for i in range(0,2):
        if (py2psql.street_in_streetnames(slist[i],host,db,user,pw)==1):
            #print "street"+slist[i]+"found"
            pass
        elif (py2psql.street_in_altnames(slist[i],host,db,user,pw)==1):
            alt_name = py2psql.altname(slist[i],host,db,user,pw)
            if (py2psql.street_in_streetnames(alt_name,host,db,user,pw)==1):
                slist[i] = alt_name
                #print "street"+slist[i]+"founf"
            else:
                print "street"+slist[i]+"notfounf"
                raise
        else:
            print "street"+slist[i]+"notfounf"
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
                vtype = vtype_i
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
                    t_fromstreet = slist[0]
                    t_tostreet = slist[0]
                    t_intstreet = slist[1]
                else:
                    t_fromstreet = slist[1]
                    t_tostreet = slist[1]
                    t_intstreet = slist[0]
            else:   #turning movement and to and from streets are different
                if  t_fromdir == "NB" or t_fromdir == "SB":
                    t_fromstreet = slist[0]
                    t_tostreet = slist[1]
                    t_intstreet = slist[1]
                else:           #TODO added maybe by mistake !!!  (check it)
                    t_fromstreet = slist[1]
                    t_tostreet = slist[0]
                    t_intstreet = slist[0]
            #------------------------------------------------------------------------------

            row_ids = range(2,len(activesheet.col(column))) #find rows to process for column
            
            for row in row_ids:
                
                count = activesheet.cell_value(row,column) 
                if count != "" : #if we have a count, validate inputs !
                    #-------Create time in time format !!!----------------- 
                    sp = us_lib.createtimestamp(date_yyyy_mm_dd,activesheet.cell_value(row,0).split("-"))     
                    starttime = sp[0]
                    period = sp[1]
                    
                    commands.append([count,starttime,period,vtype,t_fromstreet,t_fromdir,t_tostreet,t_todir,t_intstreet,t_intid, sourcefile,project])
                    
    return commands

def command_upload_mainline (host,db, user,pw):
    """
    Gets single count info and uploads it
    """
    
    commands = []
    #get date
    print "Enter count date in YYYY.MM.DD format:"
    tmp_date = raw_input().split('.')
    date_yyyy_mm_dd = date(int(tmp_date[0]),int(tmp_date[1]),int(tmp_date[2]) )
    
    
    #get period & starttime
    print "Enter count time:"
    print "1 : AMPKHOUR    |    2 : PMPKHOUR    |    3: ADT    {Single counts are not supported as of now}"
    time_period = int(raw_input())
    time = []
    if  time_period == 1:
        time.append('AMPKHOUR')
    elif time_period == 2:
        time.append('PMPKHOUR')
    elif time_period == 3:
        time.append('ADT')
    else :
        print "Wrong time period Entered!"
        raise
        
    sp = us_lib.createtimestamp(date_yyyy_mm_dd,time)     
    starttime = sp[0]
    period = sp[1]
    
    #get vtype
    print "Enter vehicle type:"
    print "'0:ALL'  |  '1:PEDESTRIAN'  |  '2:TRUCK'  |  '3:Bike'  |  '-1:UNKNOWN'"
    vtype = int(raw_input())
    
    #get ml_onstreet
    print "Enter the street we are on:"
    ml_onstreet = raw_input().upper()
    
    #get ml_ondir
    print "Enter the direction of movement:"
    ml_ondir = raw_input().upper()
    
    #get ml_fromstreet
    print "Enter the fromstreet:"
    ml_fromstreet = raw_input().upper()
    
    #get ml_tostreet
    print "Enter the tostreet:"
    ml_tostreet = raw_input().upper()
    
    #get ml_refpos
    print "Enter count location from downstream end in feet:"
    ml_refpos = float(raw_input())
    
    #get sourcefile
    print "Do you have a sourcefile:"
    sourcefile = raw_input()
    project = ""
    
    #get count
    print "Enter count now:"
    count = int(raw_input())
    
    commands.append([count,starttime,period,vtype,ml_onstreet,ml_ondir,ml_fromstreet,ml_tostreet,ml_refpos,sourcefile,project])  

    py2psql.upload_mainline(commands,host,db,user,pw)


def command_upload_turning (host,db, user,pw): 
    """
    Gets single count info and uploads it
    """
    
    commands = []
    #get date
    print "Enter count date in YYYY.MM.DD format:"
    #tmp_date = raw_input().split('.')
    tmp_date = ['2006','06','14']
    date_yyyy_mm_dd = date(int(tmp_date[0]),int(tmp_date[1]),int(tmp_date[2]) )
    
    
    #get period & starttime
    print "Enter count time:"
    print "1 : AMPKHOUR    |    2 : PMPKHOUR    |    3: ADT    {Single counts are not supported as of now}"
    #time_period = int(raw_input())
    time_period = 3
    time = []
    if  time_period == 1:
        time.append('AMPKHOUR')
    elif time_period == 2:
        time.append('PMPKHOUR')
    elif time_period == 3:
        time.append('ADT')
    else :
        print "Wrong time period Entered!"
        raise
        
    sp = us_lib.createtimestamp(date_yyyy_mm_dd,time)     
    starttime = sp[0]
    period = sp[1]
    
    #get vtype
    print "Enter vehicle type:"
    print "'0:ALL'  |  '1:PEDESTRIAN'  |  '2:TRUCK'  |  '3:Bike'  |  '-1:UNKNOWN'"
    #vtype = int(raw_input())
    vtype = 0
    
    #get ml_onstreet
    print "Enter the street approach street:"
    t_fromstreet = raw_input().upper()
    
    #get ml_ondir
    print "Enter the direction of approach:"
    t_fromdir = raw_input().upper()

    #get t_tostreet
    print "Enter the tostreet:"
    t_tostreet = raw_input().upper()
    
    #get t_todirection
    print "Enter the to direction:"
    t_todir = raw_input().upper()
    
    #get intersecting street
    if t_fromstreet == t_tostreet:
        print "Enter intersecting street:"
        t_intstreet = raw_input().upper()
    else:
        t_intstreet = t_tostreet
    
    t_intid = -1
    #get sourcefile
    print "Do you have a sourcefile:"
    #sourcefile = raw_input()
    sourcefile = "Q:\\Roadway Observed Data\\Counts\ProjectBased\\Japantown\\1746 Post Transportation Technical Data 6-2006.pdf"
    project = ""
    
    #get count
    print "Enter count now:"
    count = int(raw_input())
    
    commands.append([count,starttime,period,vtype,t_fromstreet,t_fromdir,t_tostreet,t_todir,t_intstreet,t_intid, sourcefile,project])  

    py2psql.upload_turns(commands,host,db,user,pw)




if __name__ == '__main__':
    
    pass

    