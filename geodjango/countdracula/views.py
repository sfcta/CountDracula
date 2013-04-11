from collections import defaultdict
import csv, datetime
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

from countdracula.models import Node, MainlineCountLocation, TurnCountLocation, MainlineCount, TurnCount


def mapview(request):
    """
    The mapview shows all the counts on one map.
    """
    print "mapview starting: " + str(datetime.datetime.now())

    # get all the TurnCountLocation objects
    turn_count_locs = TurnCountLocation.objects.all()
    print len(turn_count_locs)

    # get all the MainlineCountLocation objects
    mainline_count_locs = MainlineCountLocation.objects.all()
    print len(mainline_count_locs)
    
    # and the nodes
    nodes = {}
    for node in Node.objects.all():
        nodes[node.id] = (node.point.x, node.point.y)
    
    # get all the count years
    ml_years = MainlineCount.objects.values_list('count_year',flat=True).distinct();
    turn_years = TurnCount.objects.values_list('count_year',flat=True).distinct();
    count_years = sorted(set(ml_years).union(set(turn_years)))
    
    # get a mapping of loc_id -> { year:vehtype }
    turnlocs_to_years = {}
    tcqs = TurnCountLocation.objects.values('id','turncount__count_year', 'turncount__vehicle_type').distinct()
    for row in tcqs:
        # init for id
        if row['id'] not in turnlocs_to_years: turnlocs_to_years[row['id']] = {}
        # init for id, year
        if row['turncount__count_year'] not in turnlocs_to_years[row['id']]:
            turnlocs_to_years[row['id']][row['turncount__count_year']] = 0
        # bitwise or
        if row['turncount__vehicle_type'] >= 6:
            turnlocs_to_years[row['id']][row['turncount__count_year']] |= (1 << 3)  # truck
        elif row['turncount__vehicle_type'] >= 0:
            turnlocs_to_years[row['id']][row['turncount__count_year']] |= (1 << row['turncount__vehicle_type'])
        else:
            print row
    del tcqs
    
    mainlinelocs_to_years = {}
    mlqs = MainlineCountLocation.objects.values('id','mainlinecount__count_year','mainlinecount__vehicle_type').distinct()
    for row in mlqs:
        # init for id
        if row['id'] not in mainlinelocs_to_years: mainlinelocs_to_years[row['id']] = {}
        # init for id, year
        if row['mainlinecount__count_year'] not in mainlinelocs_to_years[row['id']]:
            mainlinelocs_to_years[row['id']][row['mainlinecount__count_year']] = 0
        # bitwise or
        if row['mainlinecount__vehicle_type'] >= 6:
            mainlinelocs_to_years[row['id']][row['mainlinecount__count_year']] |= (1 << 3)  # truck
        elif row['mainlinecount__vehicle_type'] >= 0:
            mainlinelocs_to_years[row['id']][row['mainlinecount__count_year']] |= (1 << row['mainlinecount__vehicle_type'])
        else:
            print row
    del mlqs
    
    print "mapview queries done: " + str(datetime.datetime.now())
    
    x= render_to_response('countdracula/gmap.html', 
                              {'turn_count_locs'        :turn_count_locs,
                               'mainline_count_locs'    :mainline_count_locs,
                               'nodes'                  :nodes,
                               'count_years'            :count_years,
                               'turnlocs_to_years'      :turnlocs_to_years,
                               'mainlinelocs_to_years'  :mainlinelocs_to_years}, 
                              context_instance=RequestContext(request))
    print "mapview render done: " + str(datetime.datetime.now())
    return x
    
def counts_for_location(request):
    """
    This enables the mapview to fetch count information for a location.
    """
    results = {
      'success':False,
      'period_minutes':defaultdict(int),  # period_minutes -> number of counts
      'date_min':3000,  # earliest date for qualifying count
      'date_max':0      # latest date for qualifying count
    } 
    try:
        count_type  = request.GET[u'count_type']
        loc_id      = int(request.GET[u'loc_id'])
        
        if count_type == 'mainline':
            count_loc  = MainlineCountLocation.objects.get(id=loc_id)
            counts     = MainlineCount.objects.filter(location=count_loc)

        elif count_type == 'turn':
            count_loc      = TurnCountLocation.objects.get(id=loc_id)
            counts         = TurnCount.objects.filter(location=count_loc)

        else:
            raise Exception("Don't understand count_type=[%s]" % count_type)
     
        for count in counts:
            # find earliest and last dates
            if results['date_min'] > count.count_year: results['date_min'] = count.count_year
            if results['date_max'] < count.count_year: results['date_max'] = count.count_year
            
            # tally counts by period_minutes
            results['period_minutes'][str(count.period_minutes)] += 1

        results['count_type']   = count_type
        results['loc_id']       = loc_id
        results['where_str']    = str(count_loc)
        results['success']      = True
        
    except Exception as inst:
        results['error'] = inst

    # convert dates into strings
    if 'date_min' in results: results['date_min'] = str(results['date_min'])
    if 'date_max' in results: results['date_max'] = str(results['date_max'])
    return HttpResponse(simplejson.dumps(results), mimetype='application/json')

def download(request):
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="CountDracula_%s.csv"' % \
        ("Mainline" if request.POST[u'download-type'] in [u'mainlinelocs', u'mainlinefilt'] else "Movement")
    writer = csv.writer(response)

    count_years = None
    vehicle_types = None
    if request.POST[u'download-type'] in [u'mainlinefilt', u'movementfilt']:
        # transform the count-year to a list
        count_years = []
        for arg in request.POST.getlist(u'count-year'):
            count_years.append(int(arg[4:]))
        
        # transform the vehicle types into a list
        vehicle_types = []
        for arg in request.POST.getlist(u'vtype'):
            vehicle_types.append(int(arg))
            # truck detail
            if int(arg)==3:
                vehicle_types.extend([6,7,8,9,10,11,12,13,14,15])
        
    location_ids = []
    if request.POST[u'download-type'] in [u'mainlinelocs', u'mainlinefilt']:

        for arg in request.POST[u'mainline_loc_ids'].split(','): location_ids.append(int(arg))
        # fetch mainline data        
        mlqs = MainlineCount.objects.select_related().filter(location_id__in=location_ids).order_by('location')
                    
    else:
        for arg in request.POST[u'movement_loc_ids'].split(','): location_ids.append(int(arg))
        # fetch turn data
        mlqs = TurnCount.objects.select_related().filter(location_id__in=location_ids).order_by('location')
        

    # log it
    writer.writerow(["LocationID in %s" % str(location_ids)])

    # further filter it    
    if request.POST[u'download-type'] in [u'mainlinefilt', u'movementfilt']:
        mlqs = mlqs.filter(count_year__in=count_years).filter(vehicle_type__in=vehicle_types)
        # log it
        writer.writerow(["Count Year in %s" % str(count_years)])
        writer.writerow(["Vehicle Type in %s" % str(vehicle_types)])
    
    
    # header row
    if request.POST[u'download-type'] in [u'mainlinelocs', u'mainlinefilt']:
        
        writer.writerow(["LocationID", "Location OnStreet", "Location OnDir", "Location FromStreet", "Location FromNode", 
                         "Location ToStreet", "Location ToNode",
                         "Count", "Count Date", "Count Year", "Start Time", "Period Minutes", "Vehicle Type",
                         "Source File", "Project", "Reference Position", "Upload User"])
    else:
        writer.writerow(["LocationID", "Location FromStreet", "Location FromDir", "Location ToStreet", "Location ToDir", 
                         "Location IntStreet", "Location IntNode",
                         "Count", "Count Date", "Count Year", "Start Time", "Period Minutes", "Vehicle Type",
                         "Source File", "Project", "Upload User"])
                
    for mcount in mlqs:
        if request.POST[u'download-type'] in [u'mainlinelocs', u'mainlinefilt']:
            writer.writerow([mcount.location.id,
                             mcount.location.on_street,
                             mcount.location.on_dir,
                             mcount.location.from_street,
                             mcount.location.from_int,
                             mcount.location.to_street,
                             mcount.location.to_int,
                             mcount.count,
                             mcount.count_date,
                             mcount.count_year,
                             mcount.start_time,
                             mcount.period_minutes,
                             mcount.vehicle_type,
                             mcount.sourcefile,
                             mcount.project,
                             mcount.reference_position,
                             mcount.upload_user])
    
        else:
            writer.writerow([mcount.location.id,
                             mcount.location.from_street,
                             mcount.location.from_dir,
                             mcount.location.to_street,
                             mcount.location.to_dir,
                             mcount.location.intersection_street,
                             mcount.location.intersection,
                             mcount.count,
                             mcount.count_date,
                             mcount.count_year,
                             mcount.start_time,
                             mcount.period_minutes,
                             mcount.vehicle_type,
                             mcount.sourcefile,
                             mcount.project,
                             mcount.upload_user])

    return response    
