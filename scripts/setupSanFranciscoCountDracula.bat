
:: RUN THIS IN THE CountDracula directory
::
:: set PATH to have Python, psql, runtpp, geo (for libraries), git
::
set PATH=C:\Python27;C:\Python27\Scripts;C:\OSGeo4W\bin;C:\Program Files (x86)\PostgreSQL\9.0\bin;C:\Program Files (x86)\Citilabs\CubeVoyager;C:\Program Files (x86)\Git\bin

:: the following assumes "postgres" is the name of your postgres superuser
::
:: clear out what's in there already
::
psql -U postgres -c "drop database countdracula_geodjango"

::
:: create the countdracula user (if you haven't already)
::
createuser -SDR --username postgres -P countdracula

::
:: create the postgis database
::
createdb --username postgres --owner=countdracula -T template_postgis countdracula_geodjango

::
:: change the user for the two tables to countdracula
::
psql -U postgres -d countdracula_geodjango -c "ALTER TABLE spatial_ref_sys OWNER to countdracula;"
psql -U postgres -d countdracula_geodjango -c "ALTER TABLE geometry_columns OWNER to countdracula;"

::
:: This is just a historical note for how the project was created
:: django-admin.py startproject geodjango
cd geodjango

:: This is just a historical note for how the app was created
::python manage.py startapp countdracula

::
:: Verify the countdracula model is AOK
::
python manage.py sqlall countdracula

::
:: Setup the database -- you'll need to setup the django superuser
::
python manage.py syncdb

::
:: set up the static files into STATIC_ROOT
::
python manage.py collectstatic

::
:: get in place to run scripts
::
cd ..\scripts

::
:: read nodes and intersection streetnames from Cube static network
::
python insertSanFranciscoIntersectionsFromCube.py Y:\networks\Roads2010\FREEFLOW.net

::
:: insert PeMS counts
::
python insertSanFranciscoPeMSCounts.py -v "Q:\Roadway Observed Data\PeMS\D4_Data_2010\pems_dist4_2010_fullyr.dat" -c "Q:\Roadway Observed Data\PeMS\D4_Data_2010\PeMS_Census" "Q:\Roadway Observed Data\PeMS\PeMs_to_NetworkNodes.xls"

::
:: insert other counts
::
python scripts\insertSanFranciscoCounts.py "Q:\Roadway Observed Data\Counts\_Standardized_chs"

:done