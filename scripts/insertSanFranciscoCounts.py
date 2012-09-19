"""
Created on Jul 25, 2011
@author: lmz

This script reads counts data from input Excel workbooks and inserts the info into the CountDracula dataabase.

"""

import logging, os, sys, time, traceback

libdir = os.path.realpath(os.path.join(os.path.split(__file__)[0], "..", "geodjango"))
print libdir
sys.path.append(libdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'

from django.core.management import setup_environ
from geodjango import settings

import countdracula.models
from countdracula.parsers.CountsWorkbookParser import CountsWorkbookParser

USAGE = """

 python insertSanFranciscoCounts.py countsWorkbookFile.xls|countsWorkbookDirectory [startFile]

 If a workbook file is passed, reads that workbook into the CountDracula database.
 If a directory is passed, reads all the workbook files in the given directory into the CountDracula database.
   If optional startFile is passed along with directory, starts at the startFile (the filenames are sorted)
 
 example: python insertSanFranciscoCounts.py "Q:\Roadway Observed Data\Counts\_Standardized_chs"
 
"""


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print USAGE
        sys.exit(2)
    
    counts_input = sys.argv[1]
    startfile = None
    if len(sys.argv) > 2:
        startfile = sys.argv[2]
    
    logger = logging.getLogger('countdracula')
    logger.setLevel(logging.DEBUG)
    
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(consolehandler)        
    
    debugFilename = "insertSanFranciscoCounts_%s.DEBUG.log" % time.strftime("%Y%b%d.%H%M%S")
    debugloghandler = logging.StreamHandler(open(debugFilename, 'w'))
    debugloghandler.setLevel(logging.DEBUG)
    debugloghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M'))
    logger.addHandler(debugloghandler)

    logger.info("Processing %s%s" % (counts_input, " starting with %s" % startfile if startfile else ""))
    
    xl_parser = CountsWorkbookParser()
   
    # Read the counts.  These reference the above streets and intersections.
    mainline_processed_files  = 0
    mainline_processed_counts = 0
    mainline_attempted_files  = 0
    turns_processed_files     = 0
    turns_processed_counts    = 0
    turns_attempted_files     = 0
    
    if os.path.isdir(counts_input):
        dir = counts_input
        files_to_process = sorted(os.listdir(counts_input))
    else:
        (dir,file) = os.path.split(counts_input)
        files_to_process = [ file ]
        
    if startfile: started = False
    for file in files_to_process:
        if file[-4:] !='.xls':
            print "File suffix is not .xls: %s -- skipping" % file[-4:]
            continue
        
        # given a startfile -- look for it
        if startfile and not started:
            if file.upper() == startfile.upper():
                started = True
            else:
                continue
        
        logger.info("")
        logger.info("Processing file %s" % file)
        # commandsgenerator.setFileName(file)
        # parse the streets from the filename
        streets = file.replace(".xls","")
        delimiters = "_-."
            
        for delim in delimiters: streets = streets.replace(delim, " ")
        streetlist = streets.split()
                    
        if len(streetlist) == 3:           
            mainline_attempted_files += 1
            
            (processed,failed) = xl_parser.readAndInsertMainlineCounts(os.path.join(dir, file), streetlist[0], streetlist[1], streetlist[2], logger)

            mainline_processed_counts += processed
            mainline_processed_files += (1 if processed > 0 else 0)
                                       
        elif len(streetlist) == 2:
            turns_attempted_files += 1

            (processed,failed) = xl_parser.readAndInsertTurnCounts(os.path.join(dir, file), streetlist[0], streetlist[1], logger)
            
            turns_processed_counts += processed
            turns_processed_files += (1 if processed > 0 else 0)


    
    logger.info("Mainline counts: %4d processed files out of %4d attempts" % (mainline_processed_files, mainline_attempted_files))
    logger.info("Turn     counts: %4d processed files out of %4d attempts" % (   turns_processed_files,    turns_attempted_files))
