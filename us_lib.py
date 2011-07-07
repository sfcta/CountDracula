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
    
        special_times = {'AMPKHOUR':[time(8,00,00,100801),time(9,00,00,100801)],'PMPKHOUR' : [time(17,00,00,101701),time(18,00,00,101701)],'ADT' : [time(0,00,00,102424),time(23,30,00,102424)]}
        if  time_list_se[0] not in special_times: 
            
            start = time(int(time_list_se[0][:2]), int(time_list_se[0][2:]))  #Find start time in time format
            
            starttime = timedelta(hours = int(time_list_se[0][:2]), minutes =  int(time_list_se[0][2:])) #Find starttime and end times in timedelta format so they can be subtracted and period found !!
            endtime = timedelta(hours = int(time_list_se[1][:2]), minutes = int(time_list_se[1][2:]))
            
            starttimestamp = datetime.combine(date_s,start)
            period = '%i minute' % int((endtime - starttime).seconds/60)
            
        else:
            start = special_times[time_list_se[0]][0]
            
            starttime = timedelta(hours = int(special_times[time_list_se[0]][0].hour), minutes =  int(special_times[time_list_se[0]][0].minute)) #Find starttime and end times in timedelta format so they can be subtracted and period found !!
            endtime = timedelta(hours = int(special_times[time_list_se[0]][1].hour), minutes =  (int(special_times[time_list_se[0]][1].minute)+30))
            
            if int(start.microsecond) == 102424:
                starttimestamp = datetime.combine(date_s,start)
                period = '1 day'
            else:
                starttimestamp = datetime.combine(date_s,start)
                period = '%i minute' % int((endtime - starttime).seconds/60)
        
               
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
    
    time_list_se = ['AMPKHOUR']
    
    special_times = {'AMPKHOUR':[time(8,00,00,100801),time(8,30,00,100801)],'PMPKHOUR' : [time(17,00,00,101701),time(17,30,00,101701)],'ADT' : [time(0,00,00,102424),time(23,30,00,102424)]}
    if time_list_se[0] not in special_times:
        print time_list_se
    else:
        print special_times[time_list_se[0]][1].second    
    