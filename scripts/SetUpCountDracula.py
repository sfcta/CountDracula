'''
Created on Jul 25, 2011

@author: varun
'''

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
    filenamealtstreets = "Q:\\Model Development\\CountDracula\\1_CountDracula_Creation\\_EXCEL_CUBE_INPUTS\\Alt_Streets.xls"
    #db = "postgres"
    #user = "postgres"
    #===========================================================================
    
    
    #===========================================================================
    parser = countdracula.ParseXlsToCDCommandsList("", "", 0, host, db, user, pw)
    uploader = countdracula.WriteToCD(host, db, user, pw)
    
    street_names = parser.read_street_names(filenamestreets)
    alt_names = parser.read_alt_streets(filenamealtstreets)
    
    uploader.street_names(street_names, alt_names)
     
    int_ids = parser.read_int_ids(filenameids)
    uploader.int_ids(int_ids)
    #===========================================================================
    
    print "UPLOAD COMPLETED !"
    
    
    



if __name__ == '__main__':
    
    
#    initializeDB()
#    exit(0)
    
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

    print "Input directory path to process:"
    directory = raw_input()
    
    print "Input vehicle type of files in directory:\n"
    print "'0:ALL'  |  '1:PEDESTRIAN'  |  '2:TRUCK'  |  '3:Bike'  |  '-1:UNKNOWN'"
    vtype = raw_input()
    
    
    
    
    massuploader= countdracula.MassUploadFiles(directory,vtype, host, db, user, pw)
    
    massuploader.UploadFiles()
    
    
    
