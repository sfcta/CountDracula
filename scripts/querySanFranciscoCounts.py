"""
Created on April 3, 2012
@author: lmz

Quick script to print out a tally of the most popular time slices for counts in the database.
""" 

import countdracula
import logging, os
from operator import itemgetter

def ignoreDates(count_counts):
    """
    Assuming counts is a dictionary of (datetime.datetime, datetime.timedelta) -> counts
    
    Returns the equivalent but with the datetime.datetime objects converted to datetime.time objects (so summing across dates).
    """
    # but we're actually interested in just the times, not the dates -> aggregate
    time_counts = {}
    for (timeslice,count) in count_counts.iteritems():
        newkey = (timeslice[0].time(), timeslice[1])
        if newkey not in time_counts: time_counts[newkey] = 0
        time_counts[newkey] += count
    return time_counts

        
if __name__ == '__main__':
    logger = logging.getLogger('countdracula')
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    logger.addHandler(consolehandler)        
    logger.setLevel(logging.DEBUG)
    
    cd_reader = countdracula.CountsDatabaseReader(pw="ReadOnly", logger=logger)


    count_counts = cd_reader.countCounts(turning=True, mainline=False)
    time_counts = ignoreDates(count_counts)

    print "Most Frequent Timeslices for Turn Counts"
    print " %10s %10s %10s" % ("start", "duration(min)", "#counts")

    for (timeslice,count) in sorted(time_counts.items(), key=itemgetter(1), reverse=True):
        print " %10s %10d %10d" % (timeslice[0].isoformat(), timeslice[1].seconds/60.0, count)
    
    print
    print "Sequential Timeslices for Turn Counts"
    print " %10s %10s %10s" % ("start", "duration(min)", "#counts")

    for timeslice in sorted(time_counts.keys(), key=itemgetter(0)):
        print " %10s %10d %10d" % (timeslice[0].isoformat(), timeslice[1].seconds/60.0, time_counts[timeslice])
            
    count_counts = cd_reader.countCounts(turning=False, mainline=True)
    time_counts = ignoreDates(count_counts)

    print
    print "Most Frequent Timeslices for Mainline Counts"
    print " %10s %10s %10s" % ("start", "duration(min)", "#counts")

    for (timeslice,count) in sorted(time_counts.items(), key=itemgetter(1), reverse=True):
        print " %10s %10d %10d" % (timeslice[0].isoformat(), timeslice[1].seconds/60.0, count)    

    print
    print "Sequential Timeslices for Mainline Counts"
    print " %10s %10s %10s" % ("start", "duration(min)", "#counts")

    for timeslice in sorted(time_counts.keys(), key=itemgetter(0)):
        print " %10s %10d %10d" % (timeslice[0].isoformat(), timeslice[1].seconds/60.0, time_counts[timeslice])