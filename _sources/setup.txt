CountDracula Setup
==================

Requirements
------------

To setup a CountDracula database, you'll need to install the following:

* `postgreSQL <http://www.postgresql.org>`_, an open source object-relational database system.
  *Tested with postgreSQL 9.0.3 on windows and ? on Linux*
* `postGIS <http://postgis.refractions.net>`_, an open source add-on that "spatially enables" postgreSQL 
  with GIS functionality.  *Tested with postGIS 9.0.3 on windows*
* `python <http://www.python.org/>`_, the programming language in which CountDracula is implemented. 
  *Tested with python 2.6*  The following python modules are also used:
  
  * `psycopg <http://www.initd.org/psycopg/>`_, an PostgreSQL adapter for Python.  *Tested with psycopg 2.4.2*
  * `xlrd <http://pypi.python.org/pypi/xlrd>`_, a python library for reading Microsoft Excel files.  
    *Tested with xlrd 0.7.1*

Installation Instructions
-------------------------
* postgreSQL has a straightforward installer; it asks you to choose a password for the "database superuser" and "service account".
* postGIS has an installer which asks you for the password (presumably from the previous step)

Depending on how your setup is, you may want to adjust the 
`client authentication settings <http://www.postgresql.org/docs/9.0/interactive/client-authentication.html>`_ 
on your database.  For example, if your database is setup on a publicly accessible machine, you might want to
restrict the hosts which can connect to the database to be only localhost, or only the machine from which you'll
run theses scripts.

Database Setup
--------------
During the postgreSQL installation, a user was likely created for you called `postgres`. 
You can now create the CountDracula postgreSQL database, its users, and initialize its tables 
(noting that the location of the postgres executables should be in your path)::

  X:\lmz\util\CountDracula>psql --username postgres --file=countdracula\initializeCountDraculaDatabase.sql

You'll get prompted for your postgreSQL password again, and you should see a bunch of output like the following::

  CREATE DATABASE
  CREATE ROLE
  GRANT
  CREATE ROLE
  GRANT
  WARNING: Console code page (437) differs from Windows code page (1252)
           8-bit characters might not work correctly. See psql reference
           page "Notes for Windows users" for details.
  You are now connected to database "countdracula".
  psql:countdracula/initializeCountDraculaDatabase.sql:22: NOTICE:  CREATE TABLE / PRIMARY KEY will create implicit index "vtype_pkey" for table "vtype"

  CREATE TABLE
  INSERT 0 17
  psql:countdracula/initializeCountDraculaDatabase.sql:50: NOTICE:  CREATE TABLE / PRIMARY KEY will create implicit index "directions_pkey" for table "directions"
  CREATE TABLE
  INSERT 0 4
  psql:countdracula/initializeCountDraculaDatabase.sql:62: NOTICE:  CREATE TABLE / PRIMARY KEY will create implicit index "street_names_pkey" for table "street_names"
  CREATE TABLE
  CREATE TABLE
  psql:countdracula/initializeCountDraculaDatabase.sql:74: NOTICE:  ALTER TABLE / ADD UNIQUE will create implicit index "intersection_ids_street1_street2_key" for table "intersection_ids"
  ALTER TABLE
  psql:countdracula/initializeCountDraculaDatabase.sql:80: NOTICE:  CREATE TABLE / PRIMARY KEY will create implicit index "nodes_pkey" for table "nodes"

  CREATE TABLE
  ALTER TABLE
  CREATE TABLE
  psql:countdracula/initializeCountDraculaDatabase.sql:100: NOTICE:  ALTER TABLE / ADD UNIQUE will create implicit index "counts_ml_count_starttime_vtype_period_onstreet_ondir_froms_key" for table "counts_ml"
  ALTER TABLE
  CREATE TABLE
  psql:countdracula/initializeCountDraculaDatabase.sql:120: NOTICE:  ALTER TABLE / ADD UNIQUE will create implicit index "counts_turns_count_starttime_vtype_period_fromstreet_fromdi_key" for table "counts_turns"
  ALTER TABLE
  GRANT
  GRANT
  GRANT
  GRANT
  GRANT
  GRANT
  GRANT

