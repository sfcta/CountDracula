#!/usr/bin/env python

"""General file containing misc. functions
"""

import os
from datetime import time,timedelta,datetime 

__author__ = "Varun Kohli, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "Jun 30, 2011" 

def movefile (src, dst, filename):	 #moves filename from src to dst directory
    
    if not os.path.isdir(dst):
        os.mkdir(dst)
     
    os.system('move \"' + src + '\\' + filename + '\" \"'+ dst+'\"')
    

def copyfile (src, dst, filename):     #moves filename from src to dst directory
    
    if not os.path.isdir(dst):
        os.mkdir(dst)
     
    os.system('copy \"' + src + '\\' + filename + '\" \"'+ dst+'\"')
    
                    
def createtimestamp (date_s,time_list_se):	#does the job of creating time in timestamp format from string
    
        start = time(int(time_list_se[0][:2]), int(time_list_se[0][2:]))  #Find start time in time format
        
        starttime = timedelta(hours = int(time_list_se[0][:2]), minutes =  int(time_list_se[0][2:])) #Find starttime and end times in timedelta format so they can be subtracted and period found !!
        endtime = timedelta(hours = int(time_list_se[1][:2]), minutes = int(time_list_se[1][2:]))
        
        starttimestamp = datetime.combine(date_s,start)               #Create timestamp
        period = '%i minute' % int((endtime - starttime).seconds/60)            #Create period
        
        return [starttimestamp,period]


    
def sourcefiles (sheetnames,book):  #extracts sourcefiles names from "book"
    sourcefile = ""
    
    if "source" in sheetnames :
        
        sheetnames.remove("source")
        #Find sources
        sourcesheet = book.sheet_by_name("source")
        for sources in range(len(sourcesheet.col(0))):
            if sourcesheet.cell_value(sources,0) != "":
                #sourcefile = sourcefile + '( ' + sourcesheet.cell_value(sources,0).replace('\\','\\\\') + ' ) '
                sourcefile = sourcefile + '( ' + sourcesheet.cell_value(sources,0) + ' ) '
                #print sourcefile
    return sourcefile


if __name__ == '__main__':
    
    sheetnames = ["asdasd","source","sources","source"]
    sources = ""
    book = "asd"
    sources = sourcefiles(sheetnames,book)
    print sheetnames