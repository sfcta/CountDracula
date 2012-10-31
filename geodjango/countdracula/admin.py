import logging, os, traceback
from django.conf.urls import patterns
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.contrib.gis.maps.google import GoogleMap
from django.shortcuts import render

from countdracula.forms import TurnCountForm
from countdracula.models import Node,StreetName,TurnCountLocation,TurnCount,MainlineCountLocation,MainlineCount

# key associated with sfcta.mapping@gmail.com
GMAP = GoogleMap(key='AIzaSyDSscDrdYK3lENjefyjoBof_JjXY5LJLRo')

admin.site.register(StreetName)
admin.site.register(TurnCountLocation)

class MainlineCountLocationAdmin(admin.ModelAdmin):
    list_display = ('on_street', 'from_street', 'to_street')

admin.site.register(MainlineCountLocation, MainlineCountLocationAdmin)
    
class TurnCountAdmin(admin.ModelAdmin):
    # let users search by sourcefile
    search_fields = ['sourcefile']
    list_display = ('location', 'period_minutes', 'count_date', 'count_year', 'start_time', 'count')
    
    def get_urls(self):
        urls = super(TurnCountAdmin, self).get_urls()
        my_urls = patterns('', (r'^upload_turn_counts/$', self.admin_site.admin_view(self.upload_view)))
        return my_urls + urls

    def upload_view(self, request):
        context_dict = {}
        
        if request.method == 'POST':
            form = TurnCountForm(request.POST, request.FILES)
            if form.is_valid():
                (num_processed, string_error) = form.read_sourcefile_and_insert_counts(request, request.FILES['sourcefile'])
                if num_processed < 0:
                    context_dict['upload_errors'] = string_error
                else:
                    # success!
                    context_dict['success_msg'] = "Successfully uploaded %d counts from %s!" % (num_processed, form.cleaned_data['sourcefile'])
                    form = TurnCountForm()
        else:
            # form is not bound to data
            form = TurnCountForm()

        context_dict['form'] = form
        return render(request, 'admin/countdracula/upload.html', context_dict)
    
admin.site.register(TurnCount, TurnCountAdmin)

class MainlineCountAdmin(admin.ModelAdmin):
    # let users search by sourcefile
    search_fields = ['sourcefile']
    list_display = ('location', 'period_minutes', 'count_date', 'count_year', 'start_time', 'count')

admin.site.register(MainlineCount, MainlineCountAdmin)

class GoogleAdmin(gis_admin.OSMGeoAdmin):
    extra_js = [GMAP.api_url + GMAP.key]
    map_template = 'gis/admin/googlemap.html'
    
gis_admin.site.register(Node, GoogleAdmin)
