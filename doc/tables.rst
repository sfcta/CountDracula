CountDracula Tables
===================

.. _table-vtype:

vtype Table
-----------
Vehicle type table, mapping vehicle type codes to descriptions.

============== ========= =======================================================
column name    data type notes
============== ========= =======================================================
vtype          integer   
vehicle        text      descriptor
============== ========= =======================================================

Initial values are:

======= =================
vtype   vehicles
======= =================
-1      `Unknown`
0       `All (Total)`
1       `Pedestrian`
2       `Truck`
3       `Bike`
4       `Bus`
5       `Cars Only`
6       `2 Axle Long`
7       `2 Axle 6 Tire`
8       `3 Axle Single`
9       `4 Axle Single`
10      `<5 Axle Double`
11      `5 Axle Double`
12      `>6 Axle Double`
13      `<6 Axle Multi`
14      `6 Axle Multi`
15      `>6 Axle Multi`
======= =================

.. _table-directions:

directions Table
----------------
Directions disambiguate which direction a count is referring to.

============== ========= =======================================================
column name    data type notes
============== ========= =======================================================
direction      text      Initial values are `NB`, `SB`, `EB`, and `WB`
============== ========= =======================================================

.. _table-street_names:

street_names Table
------------------
.. todo:: This table of streetnames is for ...?
.. todo:: is nospace_name = short_name + suffix with spaces removed?
.. todo:: is street_name = short_name + " " + suffix?
.. todo:: what about alternative names?

Can be updated with :py:meth:`countdracula.CountsDatabaseWriter.insertStreetNames`

============== ========= =======================================================
column name    data type notes
============== ========= =======================================================
street_name    text      primary key.  e.g. *CESAR CHAVEZ ST*
nospace_name   text      name without spaces. e.g. *CESARCHAVEZST*
short_name     text      name without suffix. e.g. *CESAR CHAVEZ*
suffix         text      *BLVD*, *AVE*, etc
============== ========= =======================================================

.. _table-nodes:

nodes Table
-----------

Master list of (intersection) nodes and their coordinates.

============== ========= =======================================================
column name    data type notes
============== ========= =======================================================
int_id         integer   primary key
long_x         double    x-coordinate (could be longitude but not necessary)
lat_y          double    y-coordinate (could be latitutde but not necessary)
============== ========= =======================================================

.. _table-node_streets:

node_streets Table
------------------

This table corresonds intersections with their named streets. The table has no
primary key but it does have the constraint that (int_id, street) is unique.
Can be updated with :py:meth:`countdracula.CountsDatabaseWriter.insertNodeStreets`

============== ========= =======================================================
column name    data type notes
============== ========= =======================================================
int_id         integer   corresponds to *int_id* in :ref:`table-nodes`
street         text      corresponds to *street_name* in 
                         :ref:`table-street_names`
============== ========= =======================================================

.. _table-counts_turns:

counts_turns Table
------------------

This table stores turn counts for intersections.  Can be updated with
:py:meth:`countdracula.CountsDatabaseWriter.insertTurnCounts`

============== ========= =======================================================
column name    data type notes
============== ========= =======================================================
count          integer   turn count
starttime      timestamp start time for the count (e.g. 2007-06-19 16:30:00)
period         interval  interval for the count (e.g. 00:15:00)
vtype          integer   vehicle type code, corresponds to *vtype* in
                         :ref:`table-vtype`
fromstreet     text      turn origin, corresponds to *street_name* in
			 :ref:`table-street_names`
fromdir        text      direction going into turn, corresponds to *direction*
		         in :ref:`table-directions`
tostreet       text      turn destination, corresponds to *street_name* in
                         :ref:`table-street_names`
todir          text      direction coming out of turn, corresponds to
                         *direction* in :ref:`table-directions`
intstreet      text      for through or u-turn counts, this is the cross street.
                         for turns, this is the same as *tostreet*
intid          integer   corresponds to *int_id* in 
                         :ref:`table-intersection_ids`
sourcefile     text      labeling string to keep track of where this came from
project        text      another labeling string for tracking, meant to be used
                         when the counts were gathered for a specific project
============== ========= =======================================================

.. _table-counts_ml:

counts_ml Table
---------------

This table stores mainline counts for a given primary street between two cross streets.
Can be updated with :py:meth:`countdracula.CountsDatabaseWriter.insertMainlineCounts`

============== ========= =======================================================
column name    data type notes
============== ========= =======================================================
count          integer   mainline count
starttime      timestamp start time for the count (e.g. 2007-06-19 16:30:00)
period         interval  interval for the count (e.g. 00:15:00)
vtype          integer   vehicle type code, corresponds to *vtype* in
                         :ref:`table-vtype`
onstreet       text      the street with the count, corresponds to *street_name*
                         in :ref:`table-street_names`
ondir          text      direction of count, corresponds to
                         *direction* in :ref:`table-directions`
fromstreet     text      cross street before count, corresponds to *street_name*
                         in :ref:`table-street_names`
tostreet       text      cross street before count, corresponds to *street_name*
                         in :ref:`table-street_names`
refpos         float     reference position for how far along the link the count
                         was actually taken; use -1 for uknown
sourcefile     text      labeling string to keep track of where this came from
project        text      another labeling string for tracking, meant to be used
                         when the counts were gathered for a specific project
============== ========= =======================================================
