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

def decide_type_n_go (file, directory,vtype,db_i,user_i): 
    """
    Decides count type (ML or turn) and uploads accordingly
    """
    db = db_i
    user = user_i
    
    streets = file.replace(".xls","")
    splits = "_."
    slist = ''.join([ s if s not in splits else ' ' for s in streets]).split()
    
    if len(slist) == 3:
        commandslist = getcommands.mainline(file,directory,vtype,db,user) #get commands from excel file
        py2psql.upload_mainline(commandslist,db,user)
    #    us_lib.movefile(directory,directory+'\\DONE',file)
        
    else :
        commandslist = getcommands.turns(file,directory,vtype,db,user) #get commands from excel file
        py2psql.upload_turns(commandslist,db,user)
    #    us_lib.movefile(directory,directory+'\\DONE',file)
        
    


if __name__ == '__main__':
    
    
    print "Input directory path to process:"
    directory = raw_input()
    
    print "Input vehicle type of files in directory:\n"
    print "'0:ALL'  |  '1:PEDESTRIAN'  |  '2:TRUCK'  |  '3:Bike'  |  '-1:UNKNOWN'"
    vtype = raw_input()
    
    print "Input database to enter counts to:\n"
    #db = raw_input()
    
    print "Input username to login as:\n"
    #user = raw_input()
    #===========================================================================
    # 
    db = "postgres"         #dbname to upload to
    user = "postgres"       #user to upload as
    # 
    #===========================================================================
    for file in os.listdir(directory):
        if file[-4:] =='.xls':
            #try:
                print "processing file : "+file
                decide_type_n_go(file, directory,vtype,db,user) #Sent filename and directory to the file that does the main work !!
                print "Done file : "+file
            #except:
            #   print "Error in file : "+file
            #   us_lib.movefile(directory,directory+'\\Failed',file)
            
            
                 
    print "DONE !!"
    