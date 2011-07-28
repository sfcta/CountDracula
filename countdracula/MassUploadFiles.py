'''
Created on Jul 25, 2011

@author: varun
'''

import os
from ParseXlsToCDCommandsList import ParseXlsToCDCommandsList
from WriteToCD import WriteToCD

class MassUploadFiles(object):
    '''
    Reads, parses and uploads count files to database
    '''


    def __init__(self, directory,vtype, host, database, username, pw):
        '''
        directory = directory to process
        
        vtype = default vehicle type (used if vtype not found in file)
        
        host = host ip
        
        database = database name Eg: countdracula
        
        username = username to login as
        
        pw = pw for self._username
        '''
        self._directory = directory
        self._vtype = vtype     #default vehicle type
        self._host = host       
        self._database = database
        self._username = username
        self._pw = pw
        
        
        
    def UploadFiles(self):
	"""
	Uploads the files from the directory self._directory
	"""

        
        commandsgenerator = ParseXlsToCDCommandsList("",self._directory, self._vtype, self._host, self._database, self._username, self._pw) 
        commandsuploader = WriteToCD(self._host, self._database, self._username, self._pw)
        
        for file in os.listdir(self._directory):
            if file[-4:] =='.xls':
                try:
                    print "processing file : "+file
                    commandsgenerator.setFileName(file)
                    streets = file.replace(".xls","")
                    splits = "_-."
                    slist = ''.join([ s if s not in splits else ' ' for s in streets]).split()
    
                    if len(slist) == 3:
                        commandslist = commandsgenerator.mainline() #get commands from excel file
                        commandsuploader.upload_mainline(commandslist)
                    #    us_lib.movefile(directory,directory+'\\DONE',file)
                        
                    else :
                        commandslist = commandsgenerator.turns() #get commands from excel file
                        commandsuploader.upload_turns(commandslist)
                    #    us_lib.movefile(directory,directory+'\\DONE',file)
                except:
                    print "\n*************Error in file : "+file+"*************\n"
                    #us_lib.movefile(directory,directory+'\\Error',file)
                    
                    
        print '================================'
        print '       Processing Finished'
        print '================================'