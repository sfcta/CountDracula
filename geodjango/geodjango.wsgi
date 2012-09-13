import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'
print sys.path

project_path=r"C:\Users\lisa\CountDracula\geodjango"
if project_path not in sys.path:
	sys.path.append(project_path)
geo_path=r"C:\OSGeo4W\bin"
if geo_path not in sys.path:
	sys.path.append(geo_path)
# print sys.path
# print os.environ['PATH']
os.environ['PATH']=r"C:\Python27;C:\OSGeo4W\bin;C:\Windows\SysWoW64;C:\Windows\System32"

from django.contrib.gis import gdal
# print gdal.HAS_GDAL
# print os.environ

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()