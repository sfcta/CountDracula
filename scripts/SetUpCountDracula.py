'''
Created on Jul 25, 2011

@author: varun
'''


"""
This Script is used to Initialize the database and 
upload counts to it.

Make sure countdracula package is accessible by python and run it.

Give the inputs when asked

Some directory/host inputs are hard coded


"""

import countdracula

def initializeDB():
    print "Give full path for Street Names file:"
    #filenamestreets = raw_input()
    print "\nGive full path for Intersection_Ids file:"
    #filenameids = raw_input()
    print "Give full path for Alt Street Names file:"
    #filenamealtstreets = raw_input()
    
    print "Enter host ip:"
    host = raw_input()
    
    print "\nDB to login?"
    db = raw_input()
    print "\nUser to login as?"
    user = raw_input()
    
    print "Enter password:"
    pw = raw_input()
    
    
    
    #======Static Input======================================
    filenamestreets = "Q:\\Model Development\\CountDracula\\1_CountDracula_Creation\\_EXCEL_CUBE_INPUTS\\Streets.xls"
    filenameids = "Q:\\Model Development\\CountDracula\\1_CountDracula_Creation\\_EXCEL_CUBE_INPUTS\\Intersections.xls"
    #filenamealtstreets = "Q:\\Model Development\\CountDracula\\1_CountDracula_Creation\\_EXCEL_CUBE_INPUTS\\Alt_Streets.xls"
    #db = "postgres"
    #user = "postgres"
    #===========================================================================
    
    
    #===========================================================================
    parser = countdracula.CountsWorkbookParser("", "", 0, host, db, user, pw)
    uploader = countdracula.CountsDatabaseWriter(host, db, user, pw)
    
    street_names = parser.readStreetNames(filenamestreets)
    #alt_names = parser.read_alt_streets(filenamealtstreets)
    
    uploader.street_names(street_names)
     
    int_ids = parser.readIntersectionIds(filenameids)
    uploader.insertIntersectionIds(int_ids)
    #===========================================================================
    
    print "UPLOAD COMPLETED !"
    
    
    



if __name__ == '__main__':
    
    print "Do you want to initialize the Database (input street names etc.)  [0 - No | 1 - Yes] ?"
    init = raw_input()
    if init == 1:
        initializeDB()
        exit(0)
    
    
    print "\nHost to connect to"
    host = raw_input()
    #host = "localhost"
    #print host
    
    print "\nInput database to enter counts to:"
    db = raw_input()
    #db = "postgres"         #dbname to upload to
    #print db
    
    
    print "\nInput username to login as:"
    user = raw_input()
    #user = "postgres"       #user to upload as
    #print user
    
    print "\nPassword ?"
    pw = raw_input()
    #pw = "Pine2Front"
    #print pw
    
    print "\nInput directory path to process:"
    directory = raw_input()
    
    print "\nInput vehicle type of files in directory:"
    print "'0:ALL'  |  '1:PEDESTRIAN'  |  '2:TRUCK'  |  '3:Bike'  |  '-1:UNKNOWN'"
    vtype = raw_input()
    
    
    
    
    massuploader= countdracula.MassUploadFiles(directory,vtype, host, db, user, pw)
    
    massuploader.UploadFiles()
    
    
    
