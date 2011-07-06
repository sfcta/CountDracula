#!/usr/bin/env python

"""General file containing misc. functions
"""

import os
from datetime import time,timedelta,datetime 
import us_lib
import xlrd


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

def exact_street_names (filepath):
    allowed_streets = []
    
    book = xlrd.open_workbook(filepath)
    activesheet = book.sheet_by_index(0)
    
    row_ids = range(0,len(activesheet.col(0)))
    for row in row_ids:
        allowed_streets.append(activesheet.cell_value(row,0)) 
    
    return allowed_streets
    

def alt_street_names (filepath):
    alt_streets = {}
    
    book = xlrd.open_workbook(filepath)
    activesheet = book.sheet_by_index(0)
    
    row_ids = range(0,len(activesheet.col(0)))
    for row in row_ids:
        if not (activesheet.cell_value(row,0) in alt_streets):
            alt_streets[activesheet.cell_value(row,0)] = activesheet.cell_value(row,1)
        
    return alt_streets



if __name__ == '__main__':
    
    filenamestreets = "C:\\Documents and Settings\\Varun\\Desktop\\Docs\\nodenumbering\\FINAL\\Streets.xls"
    filenamealts = "C:\\Documents and Settings\\Varun\\Desktop\\Docs\\nodenumbering\\FINAL\\ALT_Streets.xls"
    us_lib.exact_street_names(filenamestreets)
    print us_lib.allowed_streets
    us_lib.alt_street_names(filenamealts)
    print us_lib.alt_streets
    
    