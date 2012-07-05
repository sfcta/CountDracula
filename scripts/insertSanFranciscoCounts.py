'''
Created on Jul 25, 2011

@author: lmz
'''


"""
This script reads counts data from input Excel workbooks and inserts the info into the CountDracula dataabase.

"""

import countdracula
import logging, os, sys, time, traceback

USAGE = """

 python insertSanFranciscoCounts.py countsWorkbookFile.xls|countsWorkbookDirectory

 If a workbook file is passed, reads that workbook into the CountDracula database.
 If a directory is passed, reads all the workbook files in the given directory into the CountDracula database.
 
 example: python insertSanFranciscoCounts.py "Q:\Roadway Observed Data\Counts\_Standardized_chs"
 
"""


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print USAGE
        sys.exit(2)
    
    counts_input = sys.argv[1]
    
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
        
    
    cd_writer = countdracula.CountsDatabaseWriter(pw="CDadmin", logger=logger)
    cd_reader = countdracula.CountsDatabaseReader(pw="ReadOnly", logger=logger)
    xl_parser = countdracula.CountsWorkbookParser()
   
    # Read the counts.  These reference the above streets and intersections.
    mainline_processed  = 0
    mainline_attempted  = 0
    turns_processed     = 0
    turns_attempted     = 0
    
    if os.path.isdir(counts_input):
        dir = counts_input
        files_to_process = os.listdir(counts_input)
    else:
        (dir,file) = os.path.split(counts_input)
        files_to_process = [ file ]
        
    for file in files_to_process:
        if file[-4:] !='.xls':
            print "File suffix is not .xls: %s -- skipping" % file[-4:]
            continue
        
        logger.info("")
        logger.info("Processing file %s" % file)
        # commandsgenerator.setFileName(file)
        # parse the streets from the filename
        streets = file.replace(".xls","")
        delimiters = "_-."
            
        for delim in delimiters: streets = streets.replace(delim, " ")
        streetlist = streets.split()
        
        try:
            
            if len(streetlist) == 3:
                mainline_attempted += 1
                mainlineCountList = xl_parser.readMainlineCounts(os.path.join(dir, file), streetlist[0], streetlist[1], streetlist[2], cd_reader)
                cd_writer.insertMainlineCounts(mainlineCountList)
                mainline_processed += 1
                                           
            elif len(streetlist) == 2:
                turns_attempted += 1
                turnCountList = xl_parser.readTurnCounts(os.path.join(dir, file), streetlist[0], streetlist[1], cd_reader)
                cd_writer.insertTurnCounts(turnCountList)
                turns_processed += 1

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    
    logger.info("Mainline counts: %4d processed out of %4d attempts" % (mainline_processed, mainline_attempted))
    logger.info("Turn     counts: %4d processed out of %4d attempts" % (   turns_processed,    turns_attempted))
