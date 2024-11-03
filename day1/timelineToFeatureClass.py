import json
import arcpy
from datetime import datetime
from dateutil import parser

# Load the Google location history JSON file
input_file = r'C:\Users\slack\Downloads\location-history.json'

# Read the Google Timeline JSON data
with open(input_file, 'r') as f:
    location_data = json.load(f)

# Define parameters for ArcGIS feature class output
arcpy.env.workspace = arcpy.mp.ArcGISProject('CURRENT').defaultGeodatabase
output_feature_class = 'LocationHistory'

# Create feature class
if arcpy.Exists(output_feature_class):
    arcpy.Delete_management(output_feature_class)

arcpy.CreateFeatureclass_management(arcpy.env.workspace, output_feature_class, 'POINT', spatial_reference=4326)

# Add fields for timestamp and type
arcpy.AddField_management(output_feature_class, 'timestamp', 'DATE')
arcpy.AddField_management(output_feature_class, 'type', 'TEXT', field_length=50)

# Insert data into the feature class
with arcpy.da.InsertCursor(output_feature_class, ['SHAPE@XY', 'timestamp', 'type']) as cursor:
    for location in location_data:
        try:
            if location.get('activity') and location.get('activity').get('start'):
                # Extract coordinates from the start location
                start_coords = location['activity']['start'].split(':')[1].split(',')
                latitude = float(start_coords[0])
                longitude = float(start_coords[1])

                # Extract additional information such as timestamp and type
                timestamp_str = location.get('startTime')
                timestamp = parser.isoparse(timestamp_str)  # Use dateutil.parser to parse ISO 8601 format
                activity_type = location['activity'].get('topCandidate', {}).get('type', 'unknown')

                # Insert row into the feature class
                cursor.insertRow(((longitude, latitude), timestamp, activity_type))
        except Exception as e:
            print(f"Error processing location entry: {e}")

print(f"Feature class '{output_feature_class}' has been successfully created in the geodatabase and is time-enabled.")

# Create a feature layer from the feature class
feature_layer = 'LocationHistoryLayer'
if arcpy.Exists(feature_layer):
    arcpy.Delete_management(feature_layer)

arcpy.MakeFeatureLayer_management(output_feature_class, feature_layer)

# Add the layer to the current map
aprx = arcpy.mp.ArcGISProject('CURRENT')
map_obj = aprx.listMaps()[0]
layer = map_obj.addDataFromPath(output_feature_class)

# Enable time on the feature class in the map
layer.enableTime = True
layer.time.startTimeField = 'timestamp'
layer.time.endTimeField = None
layer.time.trackIDField = None

# Set the symbology of the feature layer based on the 'type' field
sym = layer.symbology
if hasattr(sym, 'renderer'):  # Ensure the symbology has a renderer attribute
    unique_value_renderer = arcpy.mp.UniqueValueRenderer()
    unique_value_renderer.fieldNames = ['type']
    # Define default symbol and add unique values based on activity type
    default_symbol = unique_value_renderer.defaultSymbol
    default_symbol.color = {'RGB': [150, 150, 150, 100]}
    unique_value_renderer.addValue('walking', {'RGB': [0, 255, 0, 100]})
    unique_value_renderer.addValue('in passenger vehicle', {'RGB': [0, 0, 255, 100]})
    unique_value_renderer.addValue('unknown', {'RGB': [255, 0, 0, 100]})
    sym.renderer = unique_value_renderer
    layer.symbology = sym

print(f"Feature layer '{feature_layer}' has been successfully created, time-enabled, and added to the map with symbology set based on the 'type' field.")
