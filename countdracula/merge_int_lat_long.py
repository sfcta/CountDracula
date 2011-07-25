#!/usr/bin/env python

"""Utility file to merge intersection ids with lat/long file
"""


__author__ = "Varun Kohli, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "Jul 6 2011" 


import xlrd, csv

def merge_lat_long (int_file, lat_longfile,target_file):
    #---------Variables used-----------------------------------
    latlongs = {}
    #int_id_ll = -1
    #lat = -1
    #long = -1
    commands=[]
    #ind_id = -1
    street1 = ""
    street2 = ""
    
    
    #------Read lat/long file-------------------------- 
    book_coor = xlrd.open_workbook(lat_longfile)
    
    coor_sheet = book_coor.sheet_by_index(0)
    
    row_ids = range(0,len(coor_sheet.col(0))) #find rows to process for column
            
    for row in row_ids:
        
        int_id_ll = coor_sheet.cell_value(row,0)
        long = coor_sheet.cell_value(row,1) #X is Long
        lat = coor_sheet.cell_value(row,2)   #Y is Lattitude

        if (lat != "" and long != "" and int_id_ll != ""): #if all inputs exist
            latlongs[int_id_ll] = [long,lat]
            
    #-----READ INTERSECTIONS FILE------------------------------ 
            
    book = xlrd.open_workbook(int_file)
    
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
            if (street1 != "" and street2 != "" and int_id != ""): #if all inputs exist
                #-------Create time in time format !!!----------------- 
                commands.append([street1,street2,int_id])
                
    #-------Merge the lists---------------------------------------
    merged_ints = []
    
    for command in commands:
        if command[2] in latlongs:
            command.extend(latlongs[command[2]])
            merged_ints.append([command[0],command[1],command[2],command[3],command[4]])
     
            #Write to csv
     
    myfile = open(target_file, 'wb') #Create CSV filename
    
    wr = csv.writer(myfile, delimiter = '\n', quotechar = '|', quoting=csv.QUOTE_MINIMAL) #Write file
    wr.writerow(merged_ints)
    


if __name__ == '__main__':
    
    int_file = 'C:\Documents and Settings\Varun\Desktop\Docs\CountDracula_FINALS\_EXCEL_CUBE_INPUTS\IntIds.xls'
    lat_longfile = 'C:\Documents and Settings\Varun\Desktop\Docs\CountDracula_FINALS\_EXCEL_CUBE_INPUTS\NODES.xls'
    target_file = 'C:\Documents and Settings\Varun\Desktop\Docs\CountDracula_FINALS\_EXCEL_CUBE_INPUTS\MERGED.csv'
    
    merge_lat_long (int_file, lat_longfile,target_file)
    
    
    