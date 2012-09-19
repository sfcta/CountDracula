from django import forms
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.contrib.gis.maps.google import GoogleMap

from countdracula.models import Node,StreetName,TurnCount,MainlineCount

# key associated with sfcta.mapping@gmail.com
GMAP = GoogleMap(key='AIzaSyDSscDrdYK3lENjefyjoBof_JjXY5LJLRo')

admin.site.register(StreetName)

class TurnCountAdmin(admin.ModelAdmin):
    # let users search by sourcefile
    search_fields = ['sourcefile']
        
admin.site.register(TurnCount, TurnCountAdmin)

class MainlineCountAdmin(admin.ModelAdmin):
    # let users search by sourcefile
    search_fields = ['sourcefile']

admin.site.register(MainlineCount, MainlineCountAdmin)

class GoogleAdmin(gis_admin.OSMGeoAdmin):
    extra_js = [GMAP.api_url + GMAP.key]
    map_template = 'gis/admin/googlemap.html'
    
gis_admin.site.register(Node, GoogleAdmin)
