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

def file_upload (file, directory,vtype,host_i,db_i,user_i,pw_i): 
    """
    Decides count type (ML or turn) and uploads accordingly
    """
    host = host_i
    db = db_i
    user = user_i
    pw = pw_i
    
    
    streets = file.replace(".xls","")
    splits = "_-."
    slist = ''.join([ s if s not in splits else ' ' for s in streets]).split()
    
    if len(slist) == 3:
        commandslist = getcommands.mainline(file,directory,vtype,host,db,user,pw) #get commands from excel file
        py2psql.upload_mainline(commandslist,host,db,user,pw)
    #    us_lib.movefile(directory,directory+'\\DONE',file)
        
    else :
        commandslist = getcommands.turns(file,directory,vtype,host,db,user,pw) #get commands from excel file
        py2psql.upload_turns(commandslist,host,db,user,pw)
    #    us_lib.movefile(directory,directory+'\\DONE',file)
        
    


if __name__ == '__main__':
    
    print "Enter type of upload:"
    print "1: Mass files upload    |    2: Single count upload"
    upload_type = int(raw_input())
    
    print "Host to connect to"
    host = raw_input()
    #host = "172.30.1.120"
    
    print "Input database to enter counts to:\n"
    db = raw_input()
    #db = "postgres"         #dbname to upload to
    #print db
    
    
    print "Input username to login as:\n"
    user = raw_input()
    #user = "postgres"       #user to upload as
    #print user
    
    print "Password?"
    pw = raw_input()
    

    
    if upload_type == 1:
        print "Input directory path to process:"
        directory = raw_input()
        
        print "Input vehicle type of files in directory:\n"
        print "'0:ALL'  |  '1:PEDESTRIAN'  |  '2:TRUCK'  |  '3:Bike'  |  '-1:UNKNOWN'"
        vtype = raw_input()
        
    
        for file in os.listdir(directory):
            if file[-4:] =='.xls':
                try:
                    print "processing file : "+file
                    file_upload(file, directory,vtype,host,db,user,pw) #Sent filename and directory to the file that does the main work !!
                    #print "Done file : "+file
                except:
                    print "\n*************Error in file : "+file+"*************"
                    #us_lib.movefile(directory,directory+'\\Error',file)
        
        print '================================'
        print '       Processing Finished'
        print '================================'
                   
                   
                   
                    
    elif upload_type == 2:
        print "Count Type to upload:"
        print "1: Mainline    |    2: Turning"
        count_type = int(raw_input())
        if count_type == 1:
            more_counts = 1
            
            while more_counts == 1:
                getcommands.command_upload_mainline(host,db,user,pw)
                print "Want to enter more MAINLINE counts ? (1 = yes, 0 = no)"
                more_counts = int(raw_input())
            
            print 'Done!'
            
        elif count_type == 2:
            more_counts = 1
            while more_counts == 1:
                getcommands.command_upload_turning(host,db,user,pw)
                print "Want to enter more TURNING counts ? (1 = yes, 0 = no)"
                more_counts = int(raw_input())
            
            print 'Done!'
            
            
        else:
            print "Invalid Count Type !"
                
                 
    
    