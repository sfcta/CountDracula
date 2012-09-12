from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from countdracula.models import Node,StreetName,TurnCount,MainlineCount

gis_admin.site.register(Node, gis_admin.GeoModelAdmin)
admin.site.register(StreetName)
admin.site.register(TurnCount)
admin.site.register(MainlineCount)