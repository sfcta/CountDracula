
::
:: clear out what's in there already
::
psql --username postgres --file=countdracula\deleteCountDraculaDatabase.sql

::
:: initialize an empty countdracula database
::
psql --username postgres --file=countdracula\initializeCountDraculaDatabase.sql

::
:: read nodes and intersection streetnames from Cube static network
::
python scripts\insertSanFranciscoIntersectionsFromCube.py Y:\networks\Roads2010\FREEFLOW.net

::
:: insert PeMS counts
::
python scripts\insertSanFranciscoPeMSCounts.py -v "Q:\Roadway Observed Data\PeMS\D4_Data_2010\pems_dist4_2010_fullyr.dat" -c "Q:\Roadway Observed Data\PeMS\D4_Data_2010\PeMS_Census" "Q:\Roadway Observed Data\PeMS\PeMs_to_NetworkNodes.xls"

::
:: insert other counts
::
python scripts\insertSanFranciscoCounts.py "Q:\Roadway Observed Data\Counts\_Standardized_chs"

:done