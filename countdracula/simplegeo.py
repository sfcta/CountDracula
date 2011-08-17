#!/usr/bin/env python
"""set of functions to retrieve geocoding data using simple geo API"""

from simplegeo import Client

__author__ = "Elizabeth Sall, San Francisco County Transportation Authority"
__license__= "GPL"
__email__  = "modeling@sfcta.org"
__date__   = "August 15 2011" 

client = Client('2PmE4wnWJjvrQb8maLxXH5hZgygHUc3S','htZd3AsJN2e8Ay28gEekXDuLDKHjm3w4')

def getSimplegeoIntByName(streets,city='San Francisco',state='CA',tolerance='15'):
    """returns a GeoJSON SimpleGeo object of the nearest intersection to the street intersection list,
    will return None if nothing is found within the given tolerance"""
    location = (" and ").join(streets)+" "+city+" "+state
    record=client.context.get_context_by_address(location)
    distance_away = tolerance
    closest_int = None
    for int in record['intersections']:
        if int['distance'] < distance_away: 
            closest_int = int
            distance_away = int['distance']
    return closest_int

def getStreetsFromSimplegeoInt(simpleGeoInt):
    '''returns a list of all the streets of a given simpleGeoIntersection'''
    streets=[]
    for s in simpleGeoInt['properties']['highways']:
        streets.append(s['name'])
    return streets

def getLatLongFromSimplegeoInt(simpleGeoInt):
    '''returns a lat/long tuple of a given simpleGeoIntersection'''
    lat  = simpleGeoInt['geometry']['coordinates'][1]
    long = simpleGeoInt['geometry']['coordinates'][0] 
    return (lat,long)
    
if __name__ == "__main__":
    search_streets=['van ness','market']
    rec=getSimplegeoIntByName(search_streets)
    
    print rec
    streets=getStreetsFromSimplegeoInt(rec)
    print streets
    