'''
Created on Jul 25, 2011

@author: lmz
'''


"""
This script reads streetnames, intersection nodes and finally counts from input Excel workbooks and inserts the info into the CountDracula dataabase.

"""

import countdracula
import logging, os


if __name__ == '__main__':
    logger = logging.getLogger('countdracula')
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(consolehandler)        
    logger.setLevel(logging.DEBUG)
    
    cd_writer = countdracula.CountsDatabaseWriter(pw="CDadmin", logger=logger)
    cd_reader = countdracula.CountsDatabaseReader(pw="ReadOnly", logger=logger)
    xl_parser = countdracula.CountsWorkbookParser()

    # Read the streets
    street_names = xl_parser.readStreetNames(r"Q:\Model Development\CountDracula\1_CountDracula_Creation\_EXCEL_CUBE_INPUTS\Streets.xls")
    cd_writer.insertStreetNames(street_names)
    
    # And the intersections
    intersection_ids = xl_parser.readIntersectionIds( r"Q:\Model Development\CountDracula\1_CountDracula_Creation\_EXCEL_CUBE_INPUTS\Intersections.xls")
    cd_writer.insertIntersectionIds(intersection_ids)
    
    # Finally, read the counts.  These reference the above streets and intersections.
    dir = r"Q:\Model Development\CountDracula\2_Files_UPLOADABLE_standardized\Standardized\0 ALL"
    for file in os.listdir(dir):
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
                mainlineCountList = xl_parser.readMainlineCounts(os.path.join(dir, file), streetlist[0], streetlist[1], streetlist[2], cd_reader)
                cd_writer.insertMainlineCounts(mainlineCountList)
                            
            elif len(streetlist) == 2:
                turnCountList = xl_parser.readTurnCounts(os.path.join(dir, file), streetlist[0], streetlist[1], cd_reader)
                cd_writer.insertTurnCounts(turnCountList)

        except Exception as e:
            logger.error(e)    
    
