"""
Created on April 5, 2012
@author: lmz

This script reads intersection information from a San Francisco Cube Network.
Someday it would be nice to have one that reads data from some sort of API but for now, this is expedient!

"""

USAGE = r"""

 python insertSanFranciscoIntersectionsFromCube.py sf_cube_network.net
 
 e.g. python insertSanFranciscoIntersectionsFromCube.py Y:\networks\Roads2010\FREEFLOW.net

"""

import logging, os, shutil, socket, subprocess, sys, tempfile, traceback

libdir = os.path.realpath(os.path.join(os.path.split(__file__)[0], "..", "geodjango"))
sys.path.append(libdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'

from django.core.management import setup_environ
from geodjango import settings

import countdracula.models
from django.contrib.gis.geos import Point


EXPORT_SCRIPTNAME = "ExportCubeForCountDracula.s"
EXPORT_SCRIPT = r"""
RUN PGM=NETWORK

NETI[1]=%s
 NODEO=%s\nodes.csv,FORMAT=SDF, INCLUDE=N,X,Y
 LINKO=%s\links.csv ,FORMAT=SDF, INCLUDE=A,B,STREETNAME,TYPE
ENDRUN    
"""

def readCubeNetwork(cube_network, logger):
    """
    Exports the cube network and reads it in, returning the following a tuple of
    ({NodeNum -> (x,y)}, 
     {(a,b) -> (streetname, type)})
    """
    # export the cube network
    tempdir = tempfile.mkdtemp(dir=r"X:\temp")
    scriptFilename = os.path.join(tempdir, EXPORT_SCRIPTNAME)
    
    logger.info("Writing export script to %s" % scriptFilename)
    scriptFile = open(scriptFilename, "w")
    scriptFile.write(EXPORT_SCRIPT % (cube_network, tempdir, tempdir))
    scriptFile.close()
    
    # run the script file
    cmd = "runtpp " + scriptFilename
    env = dict(os.environ)
    hostname = socket.gethostname().lower()
    if hostname not in ['berry']:
        cmd = r'Y:\champ\util\bin\dispatch-one.bat %s' % cmd
        env['MACHINES'] = 'vanness'

    logger.info("Running %s" % cmd)           
    proc = subprocess.Popen( cmd, 
                             cwd = tempdir, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             env=env)
    for line in proc.stdout:
        line = line.strip('\r\n')
        logger.info("  stdout: " + line)

    for line in proc.stderr:
        line = line.strip('\r\n')
        logger.info("stderr: " + line)
    retcode  = proc.wait()
    if retcode ==2:
        raise Exception("Failed to export CubeNetwork using %s" % scriptFilename)

    logger.info("Received %d from [%s]" % (retcode, cmd))
    
    # read the nodes file
    nodes = {}
    nodesFile = open(os.path.join(tempdir, "nodes.csv"), "r")
    for line in nodesFile:
        fields = line.strip().split(",")
        nodes[int(fields[0])] = ( float(fields[1]), float(fields[2]) )
    nodesFile.close()
    
    # read the links file
    links = {}
    linksFile = open(os.path.join(tempdir, "links.csv"), "r")
    for line in linksFile:
        fields = line.strip().split(",")

        streetname = fields[2]
        if len(streetname) > 0:
            if streetname[0]=="'" and streetname[-1]=="'": streetname = streetname[1:-1]
        streetname = streetname.strip(" ")
        
        type = fields[3]
        if len(type) > 0:
            if type[0]=="'" and type[-1]=="'": type = type[1:-1]
        type = type.strip(" ")
        
        links[ (int(fields[0]),int(fields[1])) ] = ( streetname, type )
    linksFile.close()
    shutil.rmtree(tempdir)
    
    return (nodes, links) 

def coordInSanFrancisco(x,y):
    """
    The following query works well enough to create a bounding box for San Francisco
    in GIS (Create a new selection on a FREEFLOW_nodes.shp file).  The second bit is to include
    Treasure Island without the southern tip of Marin.
    
    (Y > 2085000 And Y < 2129000 And X < 6024550) Or 
    (Y > 2085000 And Y < 2140000 And X > 6019000 And X < 6024550)
    
    7/3/2012 edit: extended south to include some border nodes 
    """
    if y > 2082000 and y < 2129000 and x < 6024550:
        return True
    if y > 2082000 and y < 2140000 and x > 6019000 and x < 6024550:
        return True
    return False

if __name__ == '__main__':
    logger = logging.getLogger('countdracula')
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(consolehandler)        
    logger.setLevel(logging.DEBUG)
    
    if len(sys.argv) != 2:
        print USAGE
        sys.exit(2)
        
    CUBE_NETWORK = sys.argv[1]    
    
    (nodes,links) = readCubeNetwork(CUBE_NETWORK, logger)

    # map map nodeid -> [(streetname1,type1), (streetname2,type2) ]
    node_to_streets = {}
    
    # collect set of [(streetname1,type1), (streetname2,type2)]
    streetnames = set()
    
    for linknodes,streetnametuple in links.iteritems():
        # skip if node A isn't in SF
        if not coordInSanFrancisco(nodes[linknodes[0]][0], nodes[linknodes[0]][1]): continue

        # skip if node B isn't in SF
        if not coordInSanFrancisco(nodes[linknodes[1]][0], nodes[linknodes[1]][1]): continue
        
        # pass over unnamed links
        if len(streetnametuple[0]) == 0: continue

        # collect in the streetname_list if there's a real streetname there
        streetnames.add(streetnametuple)
        
        # make the mapping
        if linknodes[0] not in node_to_streets:
            node_to_streets[linknodes[0]] = []
        if streetnametuple not in node_to_streets[linknodes[0]]:
            node_to_streets[linknodes[0]].append(streetnametuple)
        
        if linknodes[1] not in node_to_streets:
            node_to_streets[linknodes[1]] = []
        if streetnametuple not in node_to_streets[linknodes[1]]:
            node_to_streets[linknodes[1]].append(streetnametuple)
    
    # insert the nodes first
    for nodeid in node_to_streets.iterkeys():
        try:
            node = countdracula.models.Node(id=nodeid, point=Point(nodes[nodeid][0], nodes[nodeid][1], srid=3494))
            node.save()
        except:
            print "Unexpected error:", sys.exc_info()[0]       
            traceback.print_exc()
            print node
            sys.exit(2)
    
    # then the streets {(a,b) -> (streetname, type)})
    for street_tuple in streetnames:
        combined = street_tuple[0]+((" " +street_tuple[1]) if len(street_tuple[1])>0 else "")
        streetname = countdracula.models.StreetName(street_name=combined,
                                                    nospace_name=combined.replace(" ",""),
                                                    short_name=street_tuple[0],
                                                    suffix=street_tuple[1])
        streetname.save()
        
    # insert the node/street correspondence
    # nodeid -> [(streetname1,type1), (streetname2,type2) ]
    for nodeid,streetset in node_to_streets.iteritems():
        node = countdracula.models.Node.objects.get(id=nodeid)
        for street_tuple in streetset:
            combined = street_tuple[0]+((" " +street_tuple[1]) if len(street_tuple[1])>0 else "")
            street_name = countdracula.models.StreetName.objects.get(street_name=combined)
            
            # add the association
            street_name.nodes.add(node)    
    
