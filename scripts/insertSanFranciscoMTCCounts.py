"""
Created on Jul 25, 2011

@author: lmz

This script reads PEMS counts from Excel workbooks and inserts the info into the CountDracula dataabase.
"""

import decimal, datetime, getopt, logging, os, sys, time, traceback
import pytz
import xlrd

libdir = os.path.realpath(os.path.join(os.path.split(__file__)[0], "..", "geodjango"))
sys.path.append(libdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import setup_environ
from geodjango import settings
from django.contrib.gis.gdal import SpatialReference, CoordTransform

from countdracula.models import Node, StreetName, MainlineCountLocation, MainlineCount

USAGE = """

 python insertSanFranciscoMTCCounts.py mtc_counts.xls

 e.g. python insertSanFranciscoMTCCounts.py "Q:\Roadway Observed Data\MTC\all_MTC_Counts.xls"
 
 The worksheets in the workbook are assumed to have the following columns: A, B, EA_OBS, AM_OBS, MD_OBS, PM_OBS, EV_OBS, TOT_OBS
 
 Excludes workbook counts2005 because counts2005_hovdummy is duplicative.  (?)
"""

OBS_COL_TO_MINUTES = {
 'EA_OBS':60*3,
 'AM_OBS':60*3,
 'MD_OBS':60*6.5,
 'PM_OBS':60*3,
 'EV_OBS':60*8.5,
 'TOT_OBS':60*24
}
OBS_COL_TO_STARTTIME = {
  'EA_OBS':datetime.time(hour=3),
  'AM_OBS':datetime.time(hour=6),
  'MD_OBS':datetime.time(hour=9),
  'PM_OBS':datetime.time(hour=15,minute=30),
  'EV_OBS':datetime.time(hour=18,minute=30),
  'TOT_OBS':datetime.time(hour=0)
}


if __name__ == '__main__':

    opts, args = getopt.getopt(sys.argv[1:], '')
    if len(args) != 1:
        print USAGE
        sys.exit(2)
    
    MTC_COUNTS_FILE = args[0]
    MTC_COUNTS_FILE_FULLNAME = os.path.abspath(MTC_COUNTS_FILE)
        
    logger = logging.getLogger('countdracula')
    logger.setLevel(logging.DEBUG)
    
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(consolehandler)        
    
    debugFilename = "insertSanFranciscoMTCCounts_%s.DEBUG.log" % time.strftime("%Y%b%d.%H%M%S")
    debugloghandler = logging.StreamHandler(open(debugFilename, 'w'))
    debugloghandler.setLevel(logging.DEBUG)
    debugloghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M'))
    logger.addHandler(debugloghandler)
        
    book = xlrd.open_workbook(MTC_COUNTS_FILE)
    
    # open the workbook
    for sheetname in sorted(book.sheet_names()):
        # duplicative with counts2005_hovdummy
        if sheetname == "counts2005": continue
        
        # countsXXXX
        count_year = int(sheetname[6:10])
        
        logger.info("Processing worksheet %s" % sheetname)
        datasheet = book.sheet_by_name(sheetname)

        # figure out the columns        
        colname_to_colnum = {}
        colnames = ['A', 'B', 'EA_OBS', 'AM_OBS', 'MD_OBS', 'PM_OBS', 'EV_OBS', 'TOT_OBS']
        for colnum in range(len(datasheet.row(0))):
            if datasheet.cell_value(0,colnum) in colnames:
                colname_to_colnum[datasheet.cell_value(0,colnum)] = colnum
        if len(colname_to_colnum) != len(colnames):
            logger.fatal("Couldn't find all column headings %s: %s" % (str(colnames), str(colname_to_colnum)))
            sys.exit(2)
        
        # read the data
        total_rows = 0
        saved_rows = 0
        for row in range(1, len(datasheet.col(0))):
            
            total_rows += 1
            A = int(datasheet.cell_value(row, colname_to_colnum['A']))
            B = int(datasheet.cell_value(row, colname_to_colnum['B']))
            
            try:
                A_node = Node.objects.get(id=A)
            except:
                # logger.error("Couldn't find node %d in CountDracula -- skipping" % A)
                continue
            
            try:
                B_node = Node.objects.get(id=B)
            except:
                # logger.error("Couldn't find node %d in CountDracula -- skipping" % B)
                continue
                
            streetnames_A = StreetName.objects.filter(nodes=A_node)
            streetnames_B = StreetName.objects.filter(nodes=B_node)
                        
            on_street_set = set(streetnames_A).intersection(set(streetnames_B))
            if len(on_street_set) != 1:
                logger.error("On street not found for %d (%s) - %d (%s)" %
                             (A, str(streetnames_A), B, str(streetnames_B)))
                continue
            
            # ok, we have on_street
            on_street = on_street_set.pop()
            
            streetnames_A_list = list(streetnames_A)
            streetnames_B_list = list(streetnames_B)
            streetnames_A_list.remove(on_street)
            streetnames_B_list.remove(on_street)
            
            # and from_street
            if len(streetnames_A_list) == 0:
                logger.error("From street not found for %d (%s) - %d (%s)" %
                             (A, str(streetnames_A), B, str(streetnames_B)))
                # use it anyway...
                from_street = on_street
            else:
                from_street = streetnames_A_list[0]

            # and to_street            
            if len(streetnames_B_list) == 0:
                logger.error("To street not found for %d (%s) - %d (%s)" %
                             (A, str(streetnames_A), B, str(streetnames_B)))
                # use it anyway...
                to_street = on_street
            else:
                to_street = streetnames_B_list[0]

            # we just need direction - tranform the two points to feet
            long_lat                = SpatialReference('WGS84')
            nad83stateplane_feet    = SpatialReference(3494)
            ct                      = CoordTransform(long_lat, nad83stateplane_feet)
            A_point_feet            = A_node.point.transform(ct, clone=True) 
            B_point_feet            = B_node.point.transform(ct, clone=True) 
            
            diff_x                  = B_point_feet.x - A_point_feet.x
            diff_y                  = B_point_feet.y - A_point_feet.y
            if abs(diff_y) > abs(diff_x):
                if diff_y > 0:
                    on_dir = "NB"
                else:
                    on_dir = "SB"
            else:
                if diff_x > 0:
                    on_dir = "EB"
                else:
                    on_dir = "WB"

            logger.info("Mainline count on_street=%s on_dir=%s from_street=%s to_street=%s" %
                        (on_street, on_dir, from_street, to_street))
            
            try:
                mainline_count_location = MainlineCountLocation.objects.get(on_street      = on_street,
                                                                            on_dir         = on_dir,
                                                                            from_int       = A_node,
                                                                            to_int         = B_node)
            except ObjectDoesNotExist:
                mainline_count_location = MainlineCountLocation(on_street       = on_street,
                                                                on_dir          = on_dir,
                                                                from_street     = from_street,
                                                                from_int        = A_node,
                                                                to_street       = to_street,
                                                                to_int          = B_node)
                mainline_count_location.save()
                
            for colname in ['EA_OBS', 'AM_OBS', 'MD_OBS', 'PM_OBS', 'EV_OBS', 'TOT_OBS']:
                count = decimal.Decimal(datasheet.cell_value(row, colname_to_colnum[colname]))
                
                if count == 0: continue # zeros are not real
                
                mainline_count = MainlineCount(location         = mainline_count_location,
                                               count            = count,
                                               count_year       = count_year,
                                               start_time       = OBS_COL_TO_STARTTIME[colname],
                                               period_minutes   = OBS_COL_TO_MINUTES[colname],
                                               vehicle_type     = 0,
                                               sourcefile       = MTC_COUNTS_FILE_FULLNAME,
                                               project          = "mtc",
                                               reference_position = -1)
                mainline_count.save()
            saved_rows += 1
        
        logger.info("Processed %d out of %d rows" % (saved_rows, total_rows))
