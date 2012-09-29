"""
Created on Jul 25, 2011

@author: lmz

This script reads PEMS counts from Excel workbooks and inserts the info into the CountDracula dataabase.
"""

import datetime, getopt, logging, os, sys, time, traceback
import pytz
import xlrd

libdir = os.path.realpath(os.path.join(os.path.split(__file__)[0], "..", "geodjango"))
sys.path.append(libdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import setup_environ
from geodjango import settings

from countdracula.models import Node, StreetName, MainlineCountLocation, MainlineCount

TIMEZONE = pytz.timezone('America/Los_Angeles')
USAGE = """

 python insertSanFranciscoPeMSCounts.py [-v pems_vds_datfile] [-c pems_census_dir] PeMS_to_NetworkNodes.xls

 e.g. python scripts\insertSanFranciscoPeMSCounts.py -v "Q:\Roadway Observed Data\PeMS\D4_Data_2010\pems_dist4_2010_fullyr.dat" -c "Q:\Roadway Observed Data\PeMS\D4_Data_2010\PeMS_Census" "Q:\Roadway Observed Data\PeMS\PeMs_to_NetworkNodes.xls"
 
 PeMS_to_NetworkNodes.xls is a workbook that tells us how to associate PeMS data with the network.
 
 The *pems_vds_datfile* is a tab-delimited file.
 
 The *census_dir* is a directory with Excel workbooks downloaded from PeMS for various Census sensors.

 Note: more than one census dir or vds file can be passed in at once, just use the option tag each time. 
"""

def readMappingWorkbook(workbook_filename):
    """
    Reads the workbook that maps PeMS station data to network node numbers.
    The workbook looks like this:
    
    .. image:: /images/PeMS_to_NetworkNodes_Workbook.png

    Returns a dictionary mapping a tuple to a tuple: 
      ( PeMSType, PeMS_IDdir) -> ( LocationType, Rte, Dir, LocDescription, Model_A_node, Model_B_node, Model_LocDescription )
      
    e.g. ``( "VDS", "402553") -> ( "SF Screenline", "Golden Gate", "US-101", "N", "GG Bridge Mainline", 8803, 8806, "N of Alex Rd exit" )``

    All fields are text except for *Model_A_node* and *Model_B_node*, which are ints.

    """
    book        = xlrd.open_workbook(workbook_filename)
    sheetnames  = book.sheet_names()
    assert(len(sheetnames)==1) # there should be only one sheet
    activesheet = book.sheet_by_name(sheetnames[0])
    return_dict = {}
    
    # row 0: source
    # row 1: header 1
    # row 2: header 2
    for row in range(3, len(activesheet.col(0))):
        pems_ID_dir = activesheet.cell_value(row, 10)
        # floats are just integer IDs but we want a string
        if isinstance(pems_ID_dir, float):
            pems_ID_dir = "%.0f" % pems_ID_dir
            
        pems_tuple = (activesheet.cell_value(row, 8),       # PeMSType
                      pems_ID_dir)                          # PeMS_IDdir
        
        result_tuple = (activesheet.cell_value(row, 0),     # LocationType
                        activesheet.cell_value(row, 2),     # Rte
                        activesheet.cell_value(row, 3),     # Dir
                        activesheet.cell_value(row, 4),     # LocDescription
                        int(activesheet.cell_value(row,12)),# Model_A_node
                        int(activesheet.cell_value(row,13)),# Model_B_node
                        activesheet.cell_value(row,15))     # Model_LocDescription
        return_dict[pems_tuple] = result_tuple
    return return_dict

def getIntersectionStreetnamesForPemsKey(mapping, pems_key):
    """
    Given *mapping*, which is the result of :py:func:`readMappingWorkbook`
    and *pems_key*, a tuple key into *mapping* (e.g. ``( "VDS", "40255")``,
    looks up the link in the *mapping* and then looks up the nodes in the Count Dracula database using
    *cd_reader* (an instance of :py:class:`CountsDatabaseReader`).
    
    Returns a tuple: ( on_street, from_street, from_node, to_street, to_node )
    
    Raises an Exception for failure.
    """
    # grab the model nodes and their streets
    loc_desc            = mapping[pems_key][3]
    model_node_A_num    = mapping[pems_key][4]
    model_node_B_num    = mapping[pems_key][5]
    
    try:
        model_node_A    = Node.objects.get(id=model_node_A_num)
    except:
        raise Exception("Couldn't find node %6d in countdracula. Skipping %s" %
                        (model_node_A_num, loc_desc))
    
    try:
        streets_A_set = set(streetname for streetname in model_node_A.streetname_set.all())
    except:
        raise Exception("Couldn't find streets for model node A %6d in countdracula.  Skipping %s." %
                        (model_node_A_num, loc_desc))
    # logger.debug("model_node_A = %s  streets_A_set = %s" % (model_node_A, streets_A_set))
    
    try:
        model_node_B    = Node.objects.get(id=model_node_B_num)
    except:
        raise Exception("Couldn't find node %6d in countdracula. Skipping %s" %
                        (model_node_B_num, loc_desc))    
    
    try:
        streets_B_set = set(streetname for streetname in model_node_B.streetname_set.all())
    except:
        raise Exception("Couldn't find streets for model node B %6d in countdracula.  Skipping %s." %
                        (model_node_B_num, loc_desc))
    # logger.debug("model_node_B = %s  streets_B_set = %s" % (model_node_B, streets_B_set))
    
    # figure out the on_street 
    on_street_set = streets_A_set & streets_B_set
    if len(on_street_set) != 1:
        raise Exception("Couldn't find a unique single street for both node A %d (%s) and node B %d (%s)" %
                        (model_node_A_num, str(streets_A_set), model_node_B_num, str(streets_B_set)))
    on_street = on_street_set.pop()
    on_street_set.add(on_street)
    
    # figure out the from_street
    from_street_set = streets_A_set
    from_street_set -= on_street_set
    from_street = "" # try blank...
    if len(from_street_set) > 0:
        # hack - this is the most descriptive
        if 'LAKE ST' in from_street_set:
            from_street = 'LAKE ST' 
        else:
            from_street = from_street_set.pop()
    if from_street == "":
        raise Exception("Couldn't find from street for node A %d (%s) to node B %d (%s)" %
                        (model_node_A_num, str(streets_A_set), model_node_B_num, str(streets_B_set)))

    # and the to_street
    to_street_set = streets_B_set
    to_street_set -= on_street_set
    to_street = ""
    if len(to_street_set) > 0: 
        # hack - this is the most descriptive
        if 'LAKE ST' in to_street_set:
            to_street = 'LAKE ST' 
        else:
            to_street = to_street_set.pop()
    if to_street == "":
        raise Exception("Couldn't find to street for node A %d (%s) to node B %d (%s)" %
                        (model_node_A_num, str(streets_A_set), model_node_B_num, str(streets_B_set)))
    
    return (on_street, from_street, model_node_A, to_street, model_node_B)

def readVDSCounts(mapping, vds_datfilename):
    """
    Read the VDS (Vehicle Detector Station) data from the given *vds_datafilename*, and insert the mainline
    counts into countdracula.
    """
    vds_datfilename_abspath = os.path.abspath(vds_datfilename)
    vds_datfile = open(vds_datfilename, mode="r")
    
    # read the header line and parse it
    line = vds_datfile.readline()
    header_fields = line.strip().split("\t")
    fieldname_to_fieldidx = {}
    for idx in range(len(header_fields)):
        fieldname_to_fieldidx[header_fields[idx]] = idx
    first_line_pos = vds_datfile.tell()
    
    # preprocess the info for the pems_id, VDS mapping lookup stuff first and cache that result
    logger.info("Processing VDS locations to CountDracula locations")
    pemsid_to_cdlocation = {}
    for line in vds_datfile:
        line = line.strip()
        fields = line.split("\t")
        
        pems_id     = fields[fieldname_to_fieldidx["loc"]]
        pems_time   = fields[fieldname_to_fieldidx["time"]]
        
        # once we've finished all the 00:00:00 we're done with the preprocessing
        if pems_time != "00:00:00": break
        
        # is the pems ID in our mapping?  if not, we don't care about it
        pems_key = ("VDS", pems_id)
        if pems_key not in mapping:
            # logger.debug("Couldn't find %s in mapping; don't care about this VDS. Skipping." % str(pems_key))
            continue
        
        # did we already do this?
        if pems_key in pemsid_to_cdlocation: continue

        try:
            pemsid_to_cdlocation[pems_key] = getIntersectionStreetnamesForPemsKey(mapping, pems_key)
            
            logger.debug("Mapped key=%s route=[%s] dir=[%s] description=[%s] to on_street=[%s] from_street=[%s] to_street=[%s]" % 
                         (str(pems_key), fields[fieldname_to_fieldidx["route"]], fields[fieldname_to_fieldidx["dir"]], 
                          mapping[pems_key][3], pemsid_to_cdlocation[pems_key][0], pemsid_to_cdlocation[pems_key][1], pemsid_to_cdlocation[pems_key][2]))
            
        except Exception, e:
            logger.error(e)
            # logger.exception('Exception received!')
             
        
    for pems_key,intersection in pemsid_to_cdlocation.iteritems():
        logger.debug("%20s -> %s" % (str(pems_key), str(intersection)))
                        
    # create the counts list for countdracula
    vds_datfile.seek(first_line_pos)
    counts_saved = 0
    for line in vds_datfile:
        line = line.strip()
        fields = line.split("\t")
        
        # read the fields
        pems_id     = fields[fieldname_to_fieldidx["loc"]]
        # pems_route  = fields[fieldname_to_fieldidx["route"]]
        pems_dir    = fields[fieldname_to_fieldidx["dir"]]
        # pems_type   = fields[fieldname_to_fieldidx["type"]]
        pems_flow   = fields[fieldname_to_fieldidx["flow"]] # number of vehicles, or count
        # pems_avgspd = fields[fieldname_to_fieldidx["avgspd"]] -- TODO
        pems_date   = fields[fieldname_to_fieldidx["date"]]
        pems_time   = fields[fieldname_to_fieldidx["time"]]
                
        # If we failed to map this pems key to count dracula then skip it.  
        # We already logged issues in preprocessing
        pems_key = ("VDS", pems_id)
        if pems_key not in pemsid_to_cdlocation: continue
        
        # this is the format in count dracula
        if   pems_dir == "S": pems_dir = "SB"
        elif pems_dir == "N": pems_dir = "NB"
        elif pems_dir == "E": pems_dir = "EB"
        elif pems_dir == "W": pems_dir = "WB"

        # look for the mainline count location
        try:
            mainline_count_location = MainlineCountLocation.objects.get(from_int    = pemsid_to_cdlocation[pems_key][2],
                                                                        to_int      = pemsid_to_cdlocation[pems_key][4],
                                                                        on_street   = pemsid_to_cdlocation[pems_key][0],
                                                                        on_dir      = pems_dir)
        except ObjectDoesNotExist:
            mainline_count_location = MainlineCountLocation(on_street           = pemsid_to_cdlocation[pems_key][0],
                                                            on_dir              = pems_dir,
                                                            from_street         = pemsid_to_cdlocation[pems_key][1],
                                                            from_int            = pemsid_to_cdlocation[pems_key][2],
                                                            to_street           = pemsid_to_cdlocation[pems_key][3],
                                                            to_int              = pemsid_to_cdlocation[pems_key][4])
            mainline_count_location.save()
                    
        # required fields for insertMainlineCounts: count, starttime, period, vtype, 
        #      onstreet, ondir, fromstreet, tostreet, refpos, sourcefile, project

        pems_date_fields = pems_date.split(r"/")
        pems_time_fields = pems_time.split(r":")
        starttime = datetime.datetime(year=int(pems_date_fields[2]), 
                                      month=int(pems_date_fields[0]), 
                                      day=int(pems_date_fields[1]),
                                      hour=int(pems_time_fields[0]),
                                      minute=int(pems_time_fields[1]),
                                      second=int(pems_time_fields[2]),
                                      tzinfo=TIMEZONE)
        project_str = "PeMS VDS %s - %s" % (pems_id, mapping[pems_key][3])


            
        mainline_count = MainlineCount(location             = mainline_count_location,
                                       count                = pems_flow,
                                       start_time           = starttime,
                                       period_minutes       = 60,
                                       vehicle_type         = 0, # ALL                                                           
                                       reference_position   = -1,
                                       sourcefile           = vds_datfilename_abspath,
                                       project              = project_str)
        mainline_count.save()
        counts_saved += 1

    logger.info("Saved %d PeMS VDS counts into countdracula" % counts_saved)
    vds_datfile.close()

def readCensusCounts(mapping, census_dirname):
    """
    Reads the census station count workbooks and inputs those counts into the Count Dracula database.
    """
    filenames = sorted(os.listdir(census_dirname))
    for filename in filenames:
        
        if filename[-4:] != ".xls":
            logger.debug("Skipping non-xls file %s" % filename)
            continue
        
        logger.info("Processing PeMS Census file %s" % filename)
        
        filename_parts = filename[:-4].split("_")
        pems_id = filename_parts[0]
        pems_dir = pems_id[-2:].upper()
                
        pems_id = pems_id.replace("nb", "N")
        pems_id = pems_id.replace("sb", "S")
        
        
        pems_key = ("Census", pems_id)
        if pems_key not in mapping:
            logger.debug("Couldn't find %s in mapping; don't care about this VDS. Skipping." % str(pems_key))
            continue        
        
        try:
            intersection = getIntersectionStreetnamesForPemsKey(mapping, pems_key)
            logger.debug("%20s -> %s" % (str(pems_key), str(intersection)))
        except Exception, e:
            logger.error(e)
            continue

        # look for the mainline count location in countdracula
        try:
            mainline_count_location = MainlineCountLocation.objects.get(from_int    = intersection[2],
                                                                        to_int      = intersection[4],
                                                                        on_street   = intersection[0],
                                                                        on_dir      = pems_dir)
        except ObjectDoesNotExist:
            mainline_count_location = MainlineCountLocation(on_street           = intersection[0],
                                                            on_dir              = pems_dir,
                                                            from_street         = intersection[1],
                                                            from_int            = intersection[2],
                                                            to_street           = intersection[3],
                                                            to_int              = intersection[4])
            mainline_count_location.save()

        workbook_filename = os.path.join(census_dirname, filename)
        book = xlrd.open_workbook(workbook_filename)
    
        # open the workbook
        assert("Report Data" in book.sheet_names()) # standard PeMS sheetnames
        datasheet = book.sheet_by_name("Report Data")
        counts_saved = 0
        
        # for each day
        for col in range(1, len(datasheet.row(0))):
            pems_date = xlrd.xldate_as_tuple(datasheet.cell_value(0, col), book.datemode)
            
            # for each time
            for row in range(1, len(datasheet.col(0))):
                pems_time = xlrd.xldate_as_tuple(datasheet.cell_value(row, 0), book.datemode)
                
                starttime = datetime.datetime(year  = int(pems_date[0]), 
                                              month = int(pems_date[1]), 
                                              day   = int(pems_date[2]),
                                              hour  = int(pems_time[3]),
                                              minute= int(pems_time[4]),
                                              second= 0,
                                              tzinfo=TIMEZONE)
                
                count = datasheet.cell_value(row,col)
                if count == "": continue  # skip blanks
                if count == 0.0: continue # skip zeros, they aren't real zero counts                
                project_str = "PeMS Census %s - %s" % (pems_id, mapping[pems_key][3])

                # read the counts                    
                mainline_count = MainlineCount(location             = mainline_count_location,
                                               count                = count,
                                               start_time           = starttime,
                                               period_minutes       = 60,
                                               vehicle_type         = 0, # ALL
                                               reference_position   = -1,
                                               sourcefile           = workbook_filename,
                                               project              = project_str)
                mainline_count.save()
                counts_saved += 1
        
        del book
        logger.info("Saved %3d census counts from %s into countdracula" % (counts_saved, workbook_filename))
            
if __name__ == '__main__':

    opts, args = getopt.getopt(sys.argv[1:], 'c:v:')
    if len(args) != 1:
        print USAGE
        sys.exit(2)
        
    if len(opts) == 0:
        print "No PeMS data specified for processing"
        print USAGE
        sys.exit(2)
    
    MAPPING_FILE = args[0]
        
    logger = logging.getLogger('countdracula')
    logger.setLevel(logging.DEBUG)
    
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(consolehandler)        
    
    debugFilename = "insertSanFranciscoPeMSCounts_%s.DEBUG.log" % time.strftime("%Y%b%d.%H%M%S")
    debugloghandler = logging.StreamHandler(open(debugFilename, 'w'))
    debugloghandler.setLevel(logging.DEBUG)
    debugloghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M'))
    logger.addHandler(debugloghandler)
        
    mapping = readMappingWorkbook(MAPPING_FILE)
    
    for (opttype, optarg) in opts:
        if opttype == "-v":
            readVDSCounts(mapping, optarg)
        if opttype == "-c":
            readCensusCounts(mapping, optarg)
