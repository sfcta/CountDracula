"""
Created on Jul 25, 2011
@author: lmz

This script reads counts data from input Excel workbooks and inserts the info into the CountDracula dataabase.

"""

import getopt, logging, os, shutil, sys, time, traceback

libdir = os.path.realpath(os.path.join(os.path.split(__file__)[0], "..", "geodjango"))
sys.path.append(libdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'

from django.core.management import setup_environ
from geodjango import settings
from django.contrib.auth.models import User

import countdracula.models
from countdracula.parsers.CountsWorkbookParser import CountsWorkbookParser

USAGE = """

 python insertSanFranciscoCounts.py [-f failDir] [-s successDir] user countsWorkbookFile.xls|countsWorkbookDirectory [STARTFILE]

 The user should be the django user to attribute as the uploader.
 
 If a workbook file is passed, reads that workbook into the CountDracula database.
 If a directory is passed, reads all the workbook files in the given directory into the CountDracula database.
   If optional STARTFILE is passed along with directory, starts at the STARTFILE (the filenames are sorted)
 
 Pass optional failDir as a location to move failed files, and 
      optional successDir as a location to move successfully parse files.
 
 example: python insertSanFranciscoCounts.py -f "Q:\Roadway Observed Data\Counts\Standard\v1.0 CountDraculaFailed" 
                                             -s "Q:\Roadway Observed Data\Counts\Standard\v1.0 CountDraculaSuccess" 
                                             lisa "Q:\Roadway Observed Data\Counts\Standard\v1.0 CountDraculaToProcess"

 
"""


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print USAGE
        sys.exit(2)

    optlist, args = getopt.getopt(sys.argv[1:], 'f:s:')
    if len(args) < 2:
        print USAGE
        sys.exit(2)
    
    USERNAME        = args[0]
    COUNTS_INPUT    = args[1]
    STARTFILE       = None
    if len(args) > 2:
        STARTFILE   = args[2]
        
    FAIL_DIR = None
    SUCCESS_DIR = None
    for (opt,arg) in optlist:
        if opt=="-f": 
            FAIL_DIR = arg
            if not os.path.isdir(FAIL_DIR): raise ValueError("FAIL_DIR must be a directory.  [%s] is not a directory" % FAIL_DIR)
        elif opt=="-s": 
            SUCCESS_DIR = arg
            if not os.path.isdir(SUCCESS_DIR): raise ValueError("SUCCESS_DIR must be a directory.  [%s] is not a directory" % SUCCESS_DIR)
    
    user = User.objects.get(username__exact=USERNAME)
    
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

    logger.info("Processing %s%s" % (COUNTS_INPUT, " starting with %s" % STARTFILE if STARTFILE else ""))
    if FAIL_DIR:
        logger.info("Putting files that CountDracula failed to process into %s" % FAIL_DIR)
    if SUCCESS_DIR:
        logger.info("Putting files that CountDracula successfully processed into %s" % SUCCESS_DIR)
    
    xl_parser = CountsWorkbookParser()
   
    # Read the counts.  These reference the above streets and intersections.
    mainline_processed_files  = 0
    mainline_processed_counts = 0
    mainline_attempted_files  = 0
    turns_processed_files     = 0
    turns_processed_counts    = 0
    turns_attempted_files     = 0
    
    if os.path.isdir(COUNTS_INPUT):
        dir = COUNTS_INPUT
        files_to_process = sorted(os.listdir(COUNTS_INPUT))
    else:
        (dir,file) = os.path.split(COUNTS_INPUT)
        files_to_process = [ file ]
        
    if STARTFILE: started = False
    for file in files_to_process:
        if file[-4:] !='.xls' and file[-5:] != '.xlsx':
            print "File suffix is not .xls or .xlsx: %s -- skipping" % file
            continue
        
        # given a STARTFILE -- look for it
        if STARTFILE and not started:
            if file.upper() == STARTFILE.upper():
                started = True
            else:
                continue
        
        logger.info("")
        logger.info("Processing file %s" % file)

        full_file_path = os.path.join(dir, file)
        # optimism: assume success! (ok but also it'll be easier to find)
        if SUCCESS_DIR:
            full_file_path = os.path.join(SUCCESS_DIR, file) 
            shutil.move(os.path.join(dir,file), full_file_path)
        
        streetlist = CountsWorkbookParser.parseFilename(file)
                
        if len(streetlist) == 3:           
            mainline_attempted_files += 1
            
            processed = xl_parser.readAndInsertMainlineCounts(full_file_path, streetlist[0], streetlist[1], streetlist[2], user, logger)

            mainline_processed_counts += processed
            mainline_processed_files += (1 if processed >= 0 else 0)
            
            if processed < 0 and FAIL_DIR: shutil.move(full_file_path, os.path.join(FAIL_DIR, file))
                                       
        elif len(streetlist) == 2:
            turns_attempted_files += 1

            processed = xl_parser.readAndInsertTurnCounts(full_file_path, streetlist[0], streetlist[1], user, logger)
            
            turns_processed_counts += processed
            turns_processed_files += (1 if processed >= 0 else 0)

            if processed < 0 and FAIL_DIR: shutil.move(full_file_path, os.path.join(FAIL_DIR, file))
            
        else:
            logger.info("Didn't understand filename %s" % file)
            
            if FAIL_DIR: shutil.move(full_file_path, os.path.join(FAIL_DIR, file))

    logger.info("Mainline counts: %4d processed files out of %4d attempts" % (mainline_processed_files, mainline_attempted_files))
    logger.info("Turn     counts: %4d processed files out of %4d attempts" % (   turns_processed_files,    turns_attempted_files))
