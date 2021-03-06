from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib.gis import admin
from countdracula.admin import countdracula_admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'geodjango.views.home', name='home'),
    # url(r'^geodjango/', include('geodjango.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin_auth/', include(admin.site.urls)),

    # Count Dracula admin - edit count dracula models
    url(r'^admin/', include(countdracula_admin.urls)),
    
    # map view
    url(r'^map/', 'countdracula.views.mapview'),
    
    # for the map view to fetch count information for a location
    url(r'^counts_for_location/$', 'countdracula.views.counts_for_location'),
    
    # for the map view to fetch locations near a point
    url(r'^countlocs_for_point/$', 'countdracula.views.countlocs_for_point'),
    
    # download button from map
    url(r'^download/', 'countdracula.views.download')

)