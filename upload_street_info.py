#!/usr/bin/env python

"""This is the file that initializes DB by uploading 
street names, intersection ids, street suffixes
"""

import py2psql
import xlrd




__author__ = "Varun Kohli, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "Jul 5 2011" 

def read_street_names(file):  
    """
    creates commands list for street names to send to py2psql
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
                
            name = activesheet.cell_value(row,0) 
            if name != "" : #If name exists!
                #-------Create time in time format !!!----------------- 
                commands.append(name)
                
    return commands

def read_int_ids(file):  
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

def read_alt_streets(file): 
    """
    creates commands list for street suffixes to send to py2psql
    """


    #---------Variables used-----------------------------------
    commands = []
    street = ""
    suffix = ""
    #-------------------------- open the .xls file------------------------------
    
    book = xlrd.open_workbook(file)
    
    #----------Loop through counts and Create SQL Commandslist with parameters-------------    
    sheetnames =  book.sheet_names() 
    totalsheets_ids = range(len(sheetnames))  #create sheet id list
    
    for sheet in totalsheets_ids :
       
        activesheet = book.sheet_by_name(sheetnames[sheet])
        row_ids = range(0,len(activesheet.col(0))) #find rows to process for column
            
        for row in row_ids:
                
            street = activesheet.cell_value(row,0)
            suffix = activesheet.cell_value(row,1)
            if (street != "" and suffix != ""): #if all inputs exist
                #-------Create time in time format !!!----------------- 
                commands.append([street,suffix])
                
    return commands




if __name__ == '__main__':
    
    
    print "Give full path for Street Names file:"
    #filenamestreets = raw_input()
    print "\nGive full path for Intersection_Ids file:"
    #filenameids = raw_input()
    print "Give full path for Alt Street Names file:"
    #filenamealtstreets = raw_input()
    print "\nDB to login?"
    db = raw_input()
    print "\nUser to login as?"
    user = raw_input()
    
    
    
    #======Static Input======================================
    filenamestreets = "Q:\\Model Development\\CountDracula\\1_CountDracula_Creation\\_EXCEL_CUBE_INPUTS\\Streets.xls"
    filenameids = "Q:\\Model Development\\CountDracula\\1_CountDracula_Creation\\_EXCEL_CUBE_INPUTS\\Intersections.xls"
    filenamealtstreets = "Q:\\Model Development\\CountDracula\\1_CountDracula_Creation\\_EXCEL_CUBE_INPUTS\\Alt_Streets.xls"
    #db = "postgres"
    #user = "postgres"
    #===========================================================================
    
    
    #===========================================================================
    street_names = read_street_names(filenamestreets)
    py2psql.street_names(street_names,db,user)
    # 
    int_ids = read_int_ids(filenameids)
    py2psql.int_ids(int_ids,db,user)
    #===========================================================================
    
    alt_names = read_alt_streets(filenamealtstreets)
    py2psql.alt_names(alt_names,db,user)
    
    
    
    
    print "UPLOAD COMPLETED !"
    