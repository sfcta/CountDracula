"""
Created on Jul 25, 2011
@author: lmz

This script reads counts data from input Excel workbooks and inserts the info into the CountDracula dataabase.

"""

import getopt, logging, os, re, shutil, sys, time, traceback, xlrd, xlwt

libdir = os.path.realpath(os.path.join(os.path.split(__file__)[0], "..", "geodjango"))
sys.path.append(libdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'

from django.core.management import setup_environ
from geodjango import settings
from django.contrib.auth.models import User

import countdracula.models
from countdracula.parsers.CountsWorkbookParser import CountsWorkbookParser

USAGE = """

 python updateCountsWorkbooks.py v1.0_toprocess_dir v1.0_outdated_dir v1.1_new_dir
 
"""

DATE_REGEX = re.compile(r"(\d\d\d\d)\.(\d{1,2})\.(\d{1,2})")
MAINLINE_NODES = re.compile(r"(\d{5,6}) (\d{5,6})")

CALIBRI_10PT = xlwt.easyxf('font: name Calibri, height 200;')

CALIBRI_10PT_RED = xlwt.easyxf('font: name Calibri, height 200, color-index red;')
CALIBRI_10PT_ORANGE_CENTER = xlwt.easyxf('font: name Calibri, height 200; pattern: pattern solid, fore_color 0x33; alignment: horz center;')
CALIBRI_10PT_LIME_CENTER = xlwt.easyxf('font: name Calibri, height 200; pattern: pattern solid, fore_color 0x32; alignment: horz center;')

def copysheet(rb, r_sheet, wb):
    w_sheet = wb.add_sheet(r_sheet.name)
    for rownum in range(r_sheet.nrows):
        for colnum in range(r_sheet.ncols):
            w_sheet.write(rownum, colnum, r_sheet.cell_value(rownum,colnum), CALIBRI_10PT_RED)


def isRowEmpty(r_sheet, r_rownum):
    """
    Is the row empty? (aside for the first column)
    """
    for colnum in range(1,r_sheet.ncols):
        # logger.debug("cell_type=%d cell_value=[%s]" % (r_sheet.cell_type(r_rownum,colnum), str(r_sheet.cell_value(r_rownum,colnum))))
        
        if r_sheet.cell_type(r_rownum,colnum) in [xlrd.XL_CELL_BLANK,xlrd.XL_CELL_EMPTY]: 
            continue
        
        if r_sheet.cell_value(r_rownum,colnum) != "": 
            # found something!
            return False
    
    return True # didn't find anything

def isColumnZeros(r_sheet, colnum):
    """
    Starts at row 2.  Breaks on empty row.
    """
    for r_rownum in range(2,r_sheet.nrows):
        
        if r_sheet.cell_type(r_rownum,colnum) in [xlrd.XL_CELL_BLANK,xlrd.XL_CELL_EMPTY]: break
        
        elif r_sheet.cell_type(r_rownum,colnum) in [xlrd.XL_CELL_NUMBER]:
            if float(r_sheet.cell_value(r_rownum,colnum)) > 0.0: return False

        else:
            raise Exception("Didn't understand cell value at (%d,%d)" % (r_rownum, colnum))
    
    return True
        
         
                        
def updateWorkbook(logger, DIR_TOPROCESS, DIR_OLDV10, DIR_NEWV11, file, mainline_or_turns):
    """
    Converts a v1.0 workbook to a v1.1 workbook.  For anything unexpected, logs and error and returns.
    
    For success only, the new workbook will be placed in *DIR_NEWV11* and the old one will be placed in *DIR_OLDV10*.
    """
    assert(mainline_or_turns in ["MAINLINE","TURNS"])
    rb = xlrd.open_workbook(os.path.join(DIR_TOPROCESS, file), formatting_info=True)
    wb = xlwt.Workbook(encoding='utf-8')
    
    # go through the sheets
    for sheet_idx in range(rb.nsheets):
        r_sheet = rb.sheet_by_index(sheet_idx)
        
        sheet_name = r_sheet.name
        logger.info("  Reading sheet [%s]" % sheet_name)\

        # just copy the source sheet
        if sheet_name == "source":
            copysheet(rb, r_sheet, wb)
            continue
                    
        match_obj = re.match(DATE_REGEX, sheet_name)
        if match_obj.group(0) != sheet_name:
            logger.error("Sheetname [%s] is not the standard date format!  Skipping this workbook." % sheet_name)
            return
    
        w_sheet = wb.add_sheet(sheet_name)

        # check what we're copying over
        for colnum in range(r_sheet.ncols):
            if mainline_or_turns == "MAINLINE":
                # nodes ok
                if r_sheet.cell_type(1,colnum) == xlrd.XL_CELL_TEXT and re.match(MAINLINE_NODES, str(r_sheet.cell_value(1,colnum))) != None:
                    continue
                
                if r_sheet.cell_value(1,colnum) not in [1.0, 2.0, ""]:
                    logger.warn("Unexpected MAINLINE row 1 cell value = [%s]!  Skipping this workbook." %  r_sheet.cell_value(1,colnum))
                    return
            if mainline_or_turns == "TURNS" and colnum==0 and r_sheet.cell_value(1,colnum) not in [3.0, 4.0, ""]:
                logger.warn("Unexpected TURNS row 1 cell value = [%s]!  Skipping this workbook." %  r_sheet.cell_value(1,colnum))
                return               
        
        # copy first line down; make sure its MAINLINE|TURNS, [dir1], [dir2], ...
        for colnum in range(r_sheet.ncols):
            if colnum == 0 and r_sheet.cell_value(0, colnum) != mainline_or_turns:
                logger.warn("Unexpected row 0 cell value = [%s]!  Skipping this workbook." % r_sheet.cell_value(0,colnum))
                return
            if mainline_or_turns == "MAINLINE" and colnum > 0 and r_sheet.cell_value(0,colnum) not in ["NB","SB","EB","WB", ""]:
                logger.warn("Unexpected mainline row 0 cell value = [%s]!  Skipping this workbook." % r_sheet.cell_value(0,colnum))
                return
            if mainline_or_turns == "TURNS" and colnum > 0 and r_sheet.cell_value(0,colnum) not in ["NBLT", "NBRT", "NBTH",
                                                                                                    "SBLT", "SBRT", "SBTH",
                                                                                                    "EBLT", "EBRT", "EBTH",
                                                                                                    "WBLT", "WBRT", "WBTH"]:
                logger.warn("Unexpected turns row 0 cell value = [%s]!  Skipping this workbook." % r_sheet.cell_value(0,colnum))
                return
            
            w_sheet.write(1, colnum, r_sheet.cell_value(0,colnum), CALIBRI_10PT_ORANGE_CENTER)
            if colnum != 0: w_sheet.write(0, colnum, "")

        w_sheet.write(0,0, "All", CALIBRI_10PT_LIME_CENTER)
        
        # mainline - copy over non-empty rows
        if mainline_or_turns == "MAINLINE":
            w_rownum = 2
            for r_rownum in range(2,r_sheet.nrows):
                # don't copy the empty rows
                if isRowEmpty(r_sheet, r_rownum): continue
                
                # copy this row
                for colnum in range(r_sheet.ncols):
                    w_sheet.write(w_rownum, colnum, r_sheet.cell_value(r_rownum,colnum), CALIBRI_10PT)
                w_rownum += 1
        # turns - error non-zero columns
        else:
            # look for zero columns and abort if found
            for colnum in range(1,r_sheet.ncols):
                if isColumnZeros(r_sheet, colnum):
                    logger.warn("Zero column found!  Skipping this workbook.")
                    return
            
            # copy over everything
            for r_rownum in range(2,r_sheet.nrows):
                for colnum in range(r_sheet.ncols):
                    w_sheet.write(r_rownum, colnum, r_sheet.cell_value(r_rownum,colnum), CALIBRI_10PT)
    
    if os.path.exists(os.path.join(DIR_NEWV11, file)):
        logger.warn("File %s already exists!  Skipping." % os.path.join(DIR_NEWV11, file))
        return
    
    wb.default_style.font.height = 20*10
    wb.save(os.path.join(DIR_NEWV11, file))
    
    # move the old one to the deprecated dir
    shutil.move(os.path.join(DIR_TOPROCESS,file),
                os.path.join(DIR_OLDV10,file))
            
if __name__ == '__main__':
    optlist, args = getopt.getopt(sys.argv[1:], '')
    if len(args) < 2:
        print USAGE
        sys.exit(2)
        
    if len(args) != 3:
        print USAGE
        sys.exit(2)
            
    DIR_TOPROCESS   = args[0]
    DIR_OLDV10      = args[1]
    DIR_NEWV11      = args[2]
    
    logger = logging.getLogger('countdracula')
    logger.setLevel(logging.DEBUG)
    
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(consolehandler)        
    
    debugFilename = "updateCountsWorkbooks.DEBUG.log"
    debugloghandler = logging.StreamHandler(open(debugFilename, 'w'))
    debugloghandler.setLevel(logging.DEBUG)
    debugloghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M'))
    logger.addHandler(debugloghandler)

    files_to_process = sorted(os.listdir(DIR_TOPROCESS))
    
    for file in files_to_process:
        if file[-4:] !='.xls':
            print "File suffix is not .xls: %s -- skipping" % file[-4:]
            continue
        
        logger.info("")
        logger.info("Processing file %s" % file)

        streetlist = CountsWorkbookParser.parseFilename(file)
        
        # mainline
        if len(streetlist) in [2,3]:
            updateWorkbook(logger, DIR_TOPROCESS, DIR_OLDV10, DIR_NEWV11, file, "MAINLINE" if len(streetlist)==3 else "TURNS")
        else:
            logger.info("  Invalid workbook name %s" % file)
            
