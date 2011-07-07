#!/usr/bin/env python

"""MAIN FILE THAT STARTS EVERYTHING
"""

import os   #library to move files in system
import py2psql #custom built library to interact with postgres 
import getcommands  #Custom built library functions that parse the excel file and create commands list
import us_lib   #Custom built library that has random utility functions

__author__ = "Varun Kohli, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "Jul 5 2011" 

def decide_type_n_go (file, directory,vtype,db_i,user_i): #Decides count type (ML or turn) and uploads accordingly
    

    db = db_i
    user = db_i
    
    filenamestreets = "C:\\Documents and Settings\\Varun\\Desktop\\Docs\\CountDracula_FINALS\\_EXCEL_CUBE_INPUTS\\Streets.xls"
    filenamealts = "C:\\Documents and Settings\\Varun\\Desktop\\Docs\\CountDracula_FINALS\\_EXCEL_CUBE_INPUTS\\ALT_Streets.xls"
    allowed_streets = us_lib.exact_street_names(filenamestreets)
    alt_streets = us_lib.alt_street_names(filenamealts)
    
    streets = file.replace(".xls","")
    splits = "_."
    slist = ''.join([ s if s not in splits else ' ' for s in streets]).split()
    
    if len(slist) == 3:
        commandslist = getcommands.mainline(file,directory,allowed_streets, alt_streets, vtype) #get commands from excel file
        py2psql.upload_mainline(commandslist,db,user)
        us_lib.movefile(directory,'C:\Documents and Settings\Varun\Desktop\Collections\Uploadable\_vtype',file)
        
    else :
        commandslist = getcommands.turns(file,directory,allowed_streets, alt_streets, vtype) #get commands from excel file
        py2psql.upload_turns(commandslist,db,user)
        us_lib.movefile(directory,'C:\Documents and Settings\Varun\Desktop\Collections\Uploadable\_vtype',file)
        
    


if __name__ == '__main__':
    
    
    print "Input directory path to process:"
    directory = raw_input()

    print "Input vehicle type of files in directory:\n"
    print "'0:ALL'  |  '1:PEDESTRIAN'  |  '2:TRUCK'  |  '-1:UNKNOWN'"
    vtype = raw_input()
    
    #===========================================================================
    # 
    # print "Input database to enter counts to:\n"
    # db = raw_input()
    # 
    # print "Input username to login as:\n"
    # user = raw_input()
    # 
    #===========================================================================
    
    db = "postgres"         #dbname to upload to
    user = "postgres"       #user to upload as
    
    for file in os.listdir(directory):
        if file[-4:] =='.xls':
         #   try:
                print "processing file : "+file
                decide_type_n_go(file, directory,vtype,db,user) #Sent filename and directory to the file that does the main work !!
                print "Done file : "+file
       #     except:
        #       print "Error in file : "+file
        #       us_lib.movefile(directory,'C:\Documents and Settings\Varun\Desktop\Collections\Failed',file)
            
            
                 
    print "DONE !!"
    