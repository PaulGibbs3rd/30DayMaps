# point_to_polyline.py
# This script creates polylines from consecutive points in a given feature class.
# The resulting polylines are stored in a new feature class with additional fields for type change and arrival time.

import arcpy

# Input feature class
input_fc = "LocationHistoryLayer"

# Output polyline feature class
output_fc = "LocationHistoryPolylines"

# Define spatial reference based on input feature class
spatial_reference = arcpy.Describe(input_fc).spatialReference

# Create a new feature class to store the polylines
out_path = arcpy.mp.ArcGISProject("CURRENT").defaultGeodatabase
arcpy.management.CreateFeatureclass(out_path, output_fc, "POLYLINE", spatial_reference=spatial_reference)
arcpy.management.AddField(f"{out_path}\{output_fc}", "type_change", "TEXT", field_length=255)
arcpy.management.AddField(f"{out_path}\{output_fc}", "time_arrived", "DATE")

# Initialize the cursor to insert polylines
with arcpy.da.SearchCursor(input_fc, ['SHAPE@XY', 'timestamp', 'type']) as search_cursor:
    with arcpy.da.InsertCursor(f"{out_path}\{output_fc}", ['SHAPE@', 'type_change', 'time_arrived']) as insert_cursor:
        reader = iter(search_cursor)
        for current_row in reader:
            # Extract current point and timestamp
            current_point = arcpy.Point(current_row[0][0], current_row[0][1])
            current_timestamp = current_row[1]
            current_type = current_row[2]
            
            # Get the next row to form a line
            next_row = next(reader, None)
            if next_row:
                next_point = arcpy.Point(next_row[0][0], next_row[0][1])
                next_timestamp = next_row[1]
                next_type = next_row[2]
                
                # Create a polyline from the current point to the next point
                polyline = arcpy.Polyline(arcpy.Array([current_point, next_point]), spatial_reference)
                
                # Write the polyline, type change, and arrival time information to the output feature class
                type_change = f"{current_type} to {next_type}"
                time_arrived = next_timestamp
                insert_cursor.insertRow([polyline, type_change, time_arrived])

print(f"Polylines have been created successfully in {output_fc}")


