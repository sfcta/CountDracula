CountDracula Setup
==================

Requirements
------------

CountDracula runs on `Geodjango <http://geodjango.org/>`_, a GIS-based extension to 
`Django <https://www.djangoproject.com/>`_, which is a high-level python web framework.

To setup a CountDracula database, you should first install `Geodjango <http://geodjango.org/>`_
The best way to do this is to follow the Geodjango `Platform-specific instructions <https://docs.djangoproject.com/en/1.5/ref/contrib/gis/install/#platform-specific-instructions>`_.


The following were used to develop and test CountDracula:

* Windows 7 64-bit
* `postgreSQL <http://www.postgresql.org>`_, an open source object-relational database system.  
  *Tested with postgreSQL 9.0.10*
* `postGIS <http://postgis.refractions.net>`_, an open source add-on that "spatially enables" postgreSQL 
  with GIS functionality. *Tested with postGIS 1.5*
* `Apache <http://www.apache.org/>`_, the webserver.  *Tested with Apache 2.2* 
* `Python 2.7.3 32-bit <http://www.python.org/download/releases/2.7.3/>`_
* `modwsgi <http://code.google.com/p/modwsgi/>`_, a Python WSGI adaptor module for Apache.  This doesn't seem to have a version.
  The following python modules are also used:
  
  * `psycopg <http://www.initd.org/psycopg/>`_, an PostgreSQL adapter for Python.  *Tested with psycopg 2.4.5*
  * `xlrd <http://pypi.python.org/pypi/xlrd>`_, a python library for reading Microsoft Excel files.  
    *Tested with xlrd 0.7.1*
  * `python-memcached <http://pypi.python.org/pypi/python-memcached/>`_ This is a memory-based caching
    framework that can help with performance.  Optional. *Tested with python-memcached 1.48*.
  * `django <https://www.djangoproject.com/`>_  *Tested with django-1.5.1*

Installation Instructions
-------------------------
* postgreSQL has a straightforward installer; it asks you to choose a password for the "database superuser" and "service account".
* postGIS has an installer which asks you for the password (presumably from the previous step)

Depending on how your setup is, you may want to adjust the 
`client authentication settings <http://www.postgresql.org/docs/9.0/interactive/client-authentication.html>`_ 
on your database.  For example, if your database is setup on a publicly accessible machine, you might want to
restrict the hosts which can connect to the database to be only localhost, or only the machine from which you'll
run theses scripts.

Django/GeoDjango Setup for CountDracula
---------------------------------------
Download the CountDracula code from `CountDracula on GitHub <https://github.com/sfcta/CountDracula>`_.
This should be downloaded to a location that can be served by Apache, or the same local drive.
In our setup, we'll download into ``C:\CountDracula``.  From here forward, ``%COUNT_DRACULA_ROOT%`` refers
to the root directory of the code.

Update the CountDracula settings file, ``%COUNT_DRACULA_ROOT%\geodjango\geodjango\settings.py``
You should confirm/set the following:

* Admins: A name and email address.  (What's this used for?  I'm not sure...)
* The Database information: choose the name of your countdracula database, the postgres user that
  will access it, and a password for that user.  
* The ``MEDIA_ROOT`` and ``STATIC_ROOT`` directories are wher media (currently none) and static files (js, css)
  files will be put.  We put them in ``%COUNT_DRACULA_ROOT%/media`` and ``%COUNT_DRACULA_ROOT%/static``,
  respectively.
* Comment out ``CACHES`` if you don't want to deal with `Memcache or Caching <https://docs.djangoproject.com/en/dev/topics/cache/>`_ 
  (or if you want to deal with it later).
* Set the ``TIME_ZONE`` to the right time zone for you.

Then run the following setup commands - we recommend doing each on by hand to start with.

.. literalinclude:: ..\scripts\setupSanFranciscoCountDracula.bat
   :linenos:
   :language: bat
   :end-before: setup_complete

Now your CountDracula instance is setup!  One last thing - you'll need to setup Apache to serve the CountDracula web interface.

Apache Setup
------------

First, install `modwsgi <http://code.google.com/p/modwsgi/>`_, a python WSGI adapter module for Apache.  We followed
the `Windows installation instructions <http://code.google.com/p/modwsgi/wiki/InstallationOnWindows>`_.

Install the following Apache configuration file into the Apache configuration directory; the installation typically includes
an *extra* subdir in the configuration directory.

In our Windows installation, this file is saved as ``C:\Program Files (x86)\Apache Software Foundation\Apache2.2\conf\extra\httpd-countdracula.conf``.
Note you may have to act as root or the System Administrator to edit Apache configuration.

.. literalinclude:: ..\httpd-countdracula.conf

Add a line into the main Apache configuration file to make sure this file is included.  I typically do this where other configuration files are also included::

  LoadModule wsgi_module modules/mod_wsgi.so

  # CountDracula
  Include conf/extra/httpd-countdracula.conf


Restart Apache.  That's it!  Hopefully everything worked out and you can now open a browser window
and navigate to http://[your_hostname]/countdracula/admin for the admin interface, and http://[your_hostname]/countdracula/map for the
map view.

Now you can start to put counts in!  More on this later.

.. literalinclude:: ..\scripts\setupSanFranciscoCountDracula.bat
   :linenos:
   :language: bat
   :start-after: setup_complete
   
Troubleshooting
---------------
Some issues we ran into:

* When installing `OSGeo4W <http://trac.osgeo.org/osgeo4w/>`_, make sure you include the libraries GDAL18, Geos, zlib, proj, openssl, libjpeg12.
* I had some dynamic library loading errors associated with loading gdal.  I found it useful to try to load it from the command line following
  `these instructions <https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#can-t-find-gdal-library>`_ until it was successful.
  For each error I encountered, I would run the OSGeo4W installer again and choose Advanced Install, and pick the libraries that appeared to
  be relevant.  I also  had to rename ``C:\OSGeo4W\bin\proj.dll`` to ``C:\OSGeo4W\bin\proj_fw.dll``.