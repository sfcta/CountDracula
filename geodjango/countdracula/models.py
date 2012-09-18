from django.contrib.gis.db import models as gis_models
from django.db import models

# Master list of (intersection) nodes and their coordinates
class Node(gis_models.Model):
    
    point   = gis_models.PointField()  # default srid 4326=WGS84 long/lat
    # In order to conduct geographic queries, each geographic model requires a GeoManager model manager. 
    objects = gis_models.GeoManager()

    def long_x(self):
        return self.point[0]
        
    def lat_y(self):
        return self.point[1]
        
    # Returns the string representation of the model.
    def __unicode__(self):
        return "ID:%d long_x:%f lat_y:%f" % (self.id, self.long_x(), self.lat_y())

# http://www.fhwa.dot.gov/policy/ohpi/vehclass.htm
VehicleTypes = \
( (-1,  'Unknown'),         # Unknown
  ('Basic', ( 
    (0,   'All'),           # Motorized Vehicles
    (1,   'Pedestrian'),    # Wheelchairs?  Razr scooters? Skateboarders? Unicycles?
    (2,   'Bike'),          # Two-wheeled bicycles
    (3,   'Truck'),         # Generic truck classification
    (4,   'Bus'),           # Buses -- All vehicles manufactured as traditional passenger-carrying buses with two axles and six tires or three or more axles. This category includes only traditional buses (including school buses) functioning as passenger-carrying vehicles. Modified buses should be considered to be a truck and should be appropriately classified.
    (5,   'Cars'),          # All sedans, coupes, and station wagons manufactured primarily for the purpose of carrying passengers and including those passenger cars pulling recreational or other light trailers.
    )
  ),
  ('Truck Detail', (  
   (6,   '2 Axle Long'),    # Other Two-Axle, Four-Tire Single Unit Vehicles -- All two-axle, four-tire, vehicles, other than passenger cars. Included in this classification are pickups, panels, vans, and other vehicles such as campers, motor homes, ambulances, hearses, carryalls, and minibuses. Other two-axle, four-tire single-unit vehicles pulling recreational or other light trailers are included in this classification. Because automatic vehicle classifiers have difficulty distinguishing class 3 from class 2, these two classes may be combined into class 2.
   (7,   '2 Axle 6 Tire'),  # Two-Axle, Six-Tire, Single-Unit Trucks -- All vehicles on a single frame including trucks, camping and recreational vehicles, motor homes, etc., with two axles and dual rear wheels.
   (8,   '3 Axle Single'),  # Three-Axle Single-Unit Trucks -- All vehicles on a single frame including trucks, camping and recreational vehicles, motor homes, etc., with three axles.
   (9,   '4 Axle Single'),  # Four or More Axle Single-Unit Trucks -- All trucks on a single frame with four or more axles.
   (10,  '<5 Axle Double'), # Four or Fewer Axle Single-Trailer Trucks -- All vehicles with four or fewer axles consisting of two units, one of which is a tractor or straight truck power unit.
   (11,  '5 Axle Double'),  # Five-Axle Single-Trailer Trucks -- All five-axle vehicles consisting of two units, one of which is a tractor or straight truck power unit.
   (12,  '>6 Axle Double'), # Six or More Axle Single-Trailer Trucks -- All vehicles with six or more axles consisting of two units, one of which is a tractor or straight truck power unit.
   (13,  '<6 Axle Multi'),  # Five or fewer Axle Multi-Trailer Trucks -- All vehicles with five or fewer axles consisting of three or more units, one of which is a tractor or straight truck power unit.
   (14,  '6 Axle Multi'),   # Six-Axle Multi-Trailer Trucks -- All six-axle vehicles consisting of three or more units, one of which is a tractor or straight truck power unit.
   (15,  '>6 Axle Multi'),  # Seven or More Axle Multi-Trailer Trucks -- All vehicles with seven or more axles consisting of three or more units, one of which is a tractor or straight truck power unit.')
                    )
  )
)

Directions = \
( ('NB',    'Northbound'),
  ('SB',    'Southbound'),
  ('EB',    'Eastbound'),
  ('WB',    'Westbound')
)
    
# All streetnames in the network
class StreetName(models.Model):
    street_name     = models.CharField(max_length=100, primary_key=True,    help_text="e.g. CESAR CHAVEZ ST")
    nospace_name    = models.CharField(max_length=100,                      help_text="e.g. CESARCHAVEZST")
    short_name      = models.CharField(max_length=100,                      help_text="e.g. CESAR CHAVEZ")
    suffix          = models.CharField(max_length=20,                       help_text="e.g. ST")
    
    # many to many relationship with the node
    nodes           = models.ManyToManyField(Node)
    
    def __unicode__(self):
        return self.street_name

# Turn counts for an intersection
class TurnCount(models.Model):
    count               = models.IntegerField()
    start_time          = models.TimeField(help_text="Start time for the count")
    period_minutes      = models.IntegerField("Period the count was taken (minutes)")
    vehicle_type        = models.IntegerField(choices=VehicleTypes)
    from_street         = models.ForeignKey(StreetName, help_text="Street from which turn originates")
    from_dir            = models.CharField(max_length=5, choices=Directions, help_text="Direction going into turn")
    to_street           = models.ForeignKey(StreetName, help_text="Street to which the turn is destined", related_name="tc_to_street+")
    to_dir              = models.CharField(max_length=5, choices=Directions, help_text="Direction coming out of turn")
    intersection_street = models.ForeignKey(StreetName, help_text="Cross street to identify the intersection", related_name="tc_int_street+")
    int                 = models.ForeignKey(Node, help_text="Intersection", related_name="tc_int_id+")
    sourcefile          = models.CharField(max_length=500, help_text="For tracking where this count came from")
    project             = models.CharField(max_length=100, help_text="For tracking if this count was collected for a specific project")
    
# Mainline counts for an intersection
class MainlineCount(models.Model):
    count               = models.IntegerField()
    start_time          = models.TimeField(help_text="Start time for the count")
    period_minutes      = models.IntegerField("Period the count was taken (minutes)")
    vehicle_type        = models.IntegerField(choices=VehicleTypes)
    on_street           = models.ForeignKey(StreetName, help_text="The street with the count", related_name="mc_on_street+")
    on_dir              = models.CharField(max_length=5, choices=Directions, help_text="Direction of count")
    from_street         = models.ForeignKey(StreetName, help_text="Cross street before count", related_name="mc_from_street+")
    from_int            = models.ForeignKey(Node, help_text="Intersection ID for that Cross street before count", related_name="mc_from_intid+")
    to_street           = models.ForeignKey(StreetName, help_text="Cross street after count", related_name="mc_to_street+")
    to_int              = models.ForeignKey(Node, help_text="Intersection for that Cross street after count", related_name="mc_to_intid+")
    reference_position  = models.FloatField(help_text="How far along the link the count was actually taken; use -1 for unknown.  Units?")
    sourcefile          = models.CharField(max_length=500, help_text="For tracking where this count came from")
    project             = models.CharField(max_length=100, help_text="For tracking if this count was collected for a specific project")

    def __unicode__(self):
        return "%3d-minute Mailine count on %s (from %s to %s)" % \
                (self.period_minutes, self.on_street, self.from_street, self.to_street)