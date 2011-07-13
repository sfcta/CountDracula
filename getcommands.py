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

def mainline(filename,filepath,vtype_i,db,user):  
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
        if (py2psql.street_in_streetnames(slist[i],db,user)==1):
            #print "street"+slist[i]+"found"
            pass
        elif (py2psql.street_in_altnames(slist[i],db,user)==1):
            alt_name = py2psql.altname(slist[i],db,user)
            if (py2psql.street_in_streetnames(alt_name,db,user)==1):
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
            ml_ondir = activesheet.cell_value(0,column)
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
       
def turns(filename,filepath, vtype_i,db,user):  #creates commands list for turns counts
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
        if (py2psql.street_in_streetnames(slist[i],db,user)==1):
            #print "street"+slist[i]+"found"
            pass
        elif (py2psql.street_in_altnames(slist[i],db,user)==1):
            alt_name = py2psql.altname(slist[i],db,user)
            if (py2psql.street_in_streetnames(alt_name,db,user)==1):
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




if __name__ == '__main__':
    
    
    print mainline("4thAve_Irving.Parnassus.xls","C:\Documents and Settings\Varun\Desktop\Standardized")
    #===========================================================================
    # 
    # t_fromdir = "NB"
    # 
    # compass = ['N','W','S','E']
    # t_todir = compass[compass.index(t_fromdir[0])-1]
    # print t_todir
    #===========================================================================