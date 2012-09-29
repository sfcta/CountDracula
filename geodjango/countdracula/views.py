from collections import defaultdict
import datetime
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson

from countdracula.models import Node, MainlineCountLocation, TurnCountLocation, MainlineCount, TurnCount

def mapview(request):
    # get all the TurnCountLocation objects
    turn_count_locs   = TurnCountLocation.objects.all()

    # get all the MainlineCountLocation objects
    mainline_count_locs   = MainlineCountLocation.objects.all()        
    
    return render_to_response('countdracula/gmap.html', 
                              {'turn_count_locs':turn_count_locs,
                               'mainline_count_locs':mainline_count_locs}, 
                              context_instance=RequestContext(request))
    
def counts_for_location(request):
    """
    This enables the gmapview to fetch count information for a location.
    """
    results = {
      'success':False,
      'period_minutes':defaultdict(int),  # period_minutes -> number of counts
      'date_min':datetime.date.max,  # earliest date for qualifying count
      'date_max':datetime.date.min   # latest date for qualifying count
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
            date = count.start_time.date()
            if results['date_min'] > date: results['date_min'] = date
            if results['date_max'] < date: results['date_max'] = date
            
            # tally counts by period_minutes
            results['period_minutes'][str(count.period_minutes)] += 1

        results['count_type']   = count_type
        results['loc_id']       = loc_id            
        results['success']      = True
        
    except Exception as inst:
        results['error'] = inst

    # convert dates into strings
    if 'date_min' in results: results['date_min'] = str(results['date_min'])
    if 'date_max' in results: results['date_max'] = str(results['date_max'])
    return HttpResponse(simplejson.dumps(results), mimetype='application/json')
            