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

def decide_type_n_go (file, directory): #Decides count type (ML or turn) and uploads accordingly
    
    db = "postgres"         #dbname to upload to
    user = "postgres"       #user to upload as
    
    streets = file.replace(".xls","")
    splits = "_."
    slist = ''.join([ s if s not in splits else ' ' for s in streets]).split()
    
    if len(slist) == 3:
        commandslist = getcommands.mainline(file,directory) #get commands from excel file
        py2psql.upload_mainline(commandslist,db,user)
        us_lib.copyfile(directory,directory+'\\Donefiles',file)
        
    else :
        commandslist = getcommands.turns(file,directory) #get commands from excel file
        py2psql.upload_turns(commandslist,db,user)
        us_lib.copyfile(directory,directory+'\\Donefiles',file)
        
    


if __name__ == '__main__':
    
    print "Input directory path to process:"
    directory = raw_input()
    
    for file in os.listdir(directory):
        if file[-4:] =='.xls':
            #-------------------------------------------------------------- try:
                decide_type_n_go(file, directory) #Sent filename and directory to the file that does the main work !!
                
            #===================================================================
            # except :
            #    print file
            #    us_lib.copyfile(directory,directory+'\\FailedFiles',file)
            #===================================================================
                 
    print "DONE !!"
    