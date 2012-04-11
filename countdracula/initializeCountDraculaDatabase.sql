CREATE DATABASE countdracula;

CREATE USER cdadmin  WITH PASSWORD 'CDadmin';

GRANT ALL PRIVILEGES ON DATABASE countdracula to cdadmin;

CREATE USER cdreader WITH PASSWORD 'ReadOnly';  --> R and O capitalized

GRANT CONNECT ON DATABASE countdracula to cdreader;

-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO cdreader;

-- This is the MySQL way: 
-- USE countdracula;
\connect countdracula;

----------------------------------------------------

CREATE TABLE vtype (
vtype int PRIMARY KEY,
vehicle text
);

---------------------------------------------------

INSERT INTO vtype (
vtype, vehicle) VALUES 
(-1, 'Unknown'), 
(0, 'All (Total)'), 
(1, 'Pedestrian'),
(2, 'Truck'),
(3, 'Bike'),
(4, 'Bus'),
(5,'Cars Only'),
(6,'2 Axle Long'),
(7,'2 Axle 6 Tire'),
(8,'3 Axle Single'),
(9,'4 Axle Single'),
(10,'<5 Axle Double'),
(11,'5 Axle Double'),
(12,'>6 Axle Double'),
(13,'<6 Axle Multi'),
(14,'6 Axle Multi'),
(15,'>6 Axle Multi');

---------------------------------------------------

CREATE TABLE directions (
direction text PRIMARY KEY
);

INSERT INTO directions VALUES ('NB'), ('SB'), ('EB'), ('WB');

------------------------------------------------------------

CREATE TABLE street_names (
street_name text PRIMARY KEY,
nospace_name text,
short_name text,
suffix text

);

------------------------------------------------------------

CREATE TABLE nodes (
int_id int PRIMARY KEY,
long_x float,
lat_y float
);

------------------------------------------------------------

CREATE TABLE node_streets (
int_id int REFERENCES nodes ON UPDATE CASCADE,
street_name text REFERENCES street_names ON UPDATE CASCADE
);

ALTER TABLE node_streets ADD UNIQUE (int_id,street_name);

------------------------------------------------------------

CREATE TABLE counts_ml (
count int NOT NULL,
starttime timestamp,
period interval,
vtype int REFERENCES vtype ON UPDATE CASCADE,
onstreet text REFERENCES street_names ON UPDATE CASCADE,
ondir text REFERENCES directions ON UPDATE CASCADE,
fromstreet text REFERENCES street_names ON UPDATE CASCADE,
tostreet text REFERENCES street_names ON UPDATE CASCADE,
refpos float,
sourcefile text,
project text
);

ALTER TABLE counts_ml ADD UNIQUE (count,starttime,vtype,period,onstreet,ondir,fromstreet,tostreet,refpos);

----------------------------------------------------------------

CREATE TABLE counts_turns (
count int NOT NULL,
starttime timestamp,
period interval,
vtype int REFERENCES vtype ON UPDATE CASCADE,
fromstreet text REFERENCES street_names ON UPDATE CASCADE,
fromdir text REFERENCES directions ON UPDATE CASCADE,
tostreet text REFERENCES street_names ON UPDATE CASCADE,
todir text REFERENCES directions ON UPDATE CASCADE,
intstreet text REFERENCES street_names ON UPDATE CASCADE,
intid int,
sourcefile text,
project text
);


ALTER TABLE counts_turns ADD UNIQUE (count,starttime,vtype,period,fromstreet,fromdir,tostreet,todir,intstreet,intid);

-----------------------------------------------------------

GRANT SELECT ON counts_ml        TO cdreader;
GRANT SELECT ON counts_turns     TO cdreader;
GRANT SELECT ON directions       TO cdreader;
GRANT SELECT ON node_streets     TO cdreader;
GRANT SELECT ON nodes            TO cdreader;
GRANT SELECT ON street_names     TO cdreader;
GRANT SELECT ON vtype            TO cdreader;

GRANT SELECT,INSERT,UPDATE,DELETE ON counts_ml        TO cdadmin;
GRANT SELECT,INSERT,UPDATE,DELETE ON counts_turns     TO cdadmin;
GRANT SELECT,INSERT,UPDATE,DELETE ON directions       TO cdadmin;
GRANT SELECT,INSERT,UPDATE,DELETE ON node_streets     TO cdadmin;
GRANT SELECT,INSERT,UPDATE,DELETE ON nodes            TO cdadmin;
GRANT SELECT,INSERT,UPDATE,DELETE ON street_names     TO cdadmin;
GRANT SELECT,INSERT,UPDATE,DELETE ON vtype            TO cdadmin;