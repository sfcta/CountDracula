from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

from countdracula.models import Node

def gmapview(request):
    # get all the node objects
    nodes = Node.objects.all()
    return render_to_response('countdracula/gmap.html', 
                              {'nodes':nodes}, 
                              context_instance=RequestContext(request))