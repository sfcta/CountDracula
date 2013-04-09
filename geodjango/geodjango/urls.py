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
    url(r'^admin/', include(countdracula_admin.urls)),
    
    # map view
    url(r'^map/', 'countdracula.views.mapview'),
    
    # for the map view to fetch count information for a location
    url(r'^counts_for_location/$', 'countdracula.views.counts_for_location'),
    
    # download button from map
    url(r'^download/', 'countdracula.views.download')

)