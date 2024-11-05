"""
Hexagonal Binning for Spatial Data in ArcGIS Pro

This script performs hexagonal binning of point data using a hexagon grid. It assigns point features (e.g., Google Timeline locations) to hexagons, calculates the count of points per hexagon, and outputs a new hexagon feature class with point counts attached.

Special thanks to John Nelson for providing the hexagon layer used in this workflow.

Steps:
1. Perform a Spatial Join to assign point features to hexagon features.
2. Summarize the number of points within each hexagon.
3. Join the summarized point counts back to the hexagon grid to create a new output layer.

To use this script, update the `points_layer` and `hexagons_layer` variables with your actual layer names.

Filename: hexagonal_binning_arcgis_pro.py
"""

import arcpy

# Set the environment and input variables
arcpy.env.overwriteOutput = True

# Input feature layers (update these with your actual layer names)
points_layer = "LocationHistoryLayer"  # Google Timeline points
hexagons_layer = "USA_Hex_150kMI"  # Hexagon grid

# Use in_memory workspace only if it exists properly
temp_workspace = arcpy.env.scratchGDB

# Define output feature class and table paths
temp_spatial_join = f"{temp_workspace}/spatial_join_result"
summarized_table = f"{temp_workspace}/summary_statistics"
output_hexagons = f"{temp_workspace}/hexagons_with_counts"

# Step 1: Spatial Join - Assign points to hexagons
try:
    if arcpy.Exists(points_layer) and arcpy.Exists(hexagons_layer):
        arcpy.analysis.SpatialJoin(
            target_features=points_layer,
            join_features=hexagons_layer,
            out_feature_class=temp_spatial_join,
            join_type="KEEP_ALL",  # Keep all hexagons even if no points intersect
            match_option="INTERSECT"
        )
        print("Spatial Join complete: Points assigned to hexagons.")
    else:
        raise RuntimeError("Input layers do not exist. Please check layer names and ensure they are correctly loaded.")
except arcpy.ExecuteError as e:
    arcpy.AddError(e)
    raise RuntimeError("Failed to complete Spatial Join. Please check input data and parameters.")

# Validate if spatial join result is created properly
if not arcpy.Exists(temp_spatial_join):
    raise RuntimeError("Spatial join result does not exist after attempted creation. Please check data integrity and input parameters.")

# Step 2: Summary Statistics - Count points per hexagon
arcpy.analysis.Statistics(
    in_table=temp_spatial_join,
    out_table=summarized_table,
    statistics_fields=[("OBJECTID", "COUNT")],
    case_field="GRID_ID"  # Use the hexagon identifier for grouping
)
print("Summary Statistics complete: Point counts per hexagon calculated.")

# Step 3: Add summarized counts back to the hexagons
# Create a table view from summarized statistics
summarized_table_view = "summarized_table_view"
arcpy.management.MakeTableView(summarized_table, summarized_table_view)

# Use FeatureClassToFeatureClass to create a new output hexagon layer with joined counts
arcpy.conversion.FeatureClassToFeatureClass(
    in_features=hexagons_layer,
    out_path=temp_workspace,
    out_name="hexagons_with_counts",
    where_clause=None,
    field_mapping=None,
    config_keyword=None
)

# Add the "PointCnt" field to the output hexagons layer
count_field = "PointCnt"
if not any(field.name == count_field for field in arcpy.ListFields(output_hexagons)):
    arcpy.management.AddField(output_hexagons, count_field, "LONG")

# Join the point count information from the summary table to the hexagons output
arcpy.management.JoinField(
    in_data=output_hexagons,
    in_field="GRID_ID",
    join_table=summarized_table_view,
    join_field="GRID_ID",
    fields=["COUNT_OBJECTID"]
)

# Update the "PointCnt" field with the joined count value
with arcpy.da.UpdateCursor(output_hexagons, ["COUNT_OBJECTID", count_field]) as cursor:
    for row in cursor:
        row[1] = row[0] if row[0] is not None else 0
        cursor.updateRow(row)

# Remove the temporary join field after updating
arcpy.management.DeleteField(output_hexagons, ["COUNT_OBJECTID"])

print("Join complete: Summary statistics joined back to hexagon grid.")

# Clean up temporary layers
if arcpy.Exists(temp_spatial_join):
    arcpy.management.Delete(temp_spatial_join)
if arcpy.Exists(summarized_table):
    arcpy.management.Delete(summarized_table)
if arcpy.Exists(summarized_table_view):
    arcpy.management.Delete(summarized_table_view)
print("Temporary spatial join and summary statistics layers deleted.")

print("Script completed successfully!")
