import arcpy
import pandas as pd
from arcgis.gis import GIS
from arcgis.geocoding import geocode
import os

def main(excel_file_path, output_gdb_path, feature_class_name="store_locations"):
    """
    Geocodes store locations from an Excel file and saves them as a point feature class in a geodatabase.

    Args:
        excel_file_path (str): Path to the Excel file containing store data.
        output_gdb_path (str): Path to the output geodatabase.
        feature_class_name (str): Name of the feature class to be created.
    """
    # Read Excel data into a Pandas DataFrame
    df = pd.read_excel(excel_file_path)

    # Log in to GIS (Anonymous for Esri World Geocoding Service)
    gis = GIS("https://www.arcgis.com", anonymous=True)

    # Set up arcpy environment
    arcpy.env.workspace = output_gdb_path
    arcpy.env.overwriteOutput = True

    # Create a new point feature class in the geodatabase
    spatial_reference = arcpy.SpatialReference(4326)  # WGS 1984
    output_fc = arcpy.CreateFeatureclass_management(
        output_gdb_path, feature_class_name, "POINT", spatial_reference=spatial_reference
    )

    # Add attribute fields
    arcpy.AddField_management(output_fc, "store", "TEXT")
    arcpy.AddField_management(output_fc, "address", "TEXT")
    arcpy.AddField_management(output_fc, "url", "TEXT")

    # Loop through each row in the dataframe and geocode the address
    with arcpy.da.InsertCursor(output_fc, ["SHAPE@XY", "store", "address", "url"]) as cursor:
        for index, row in df.iterrows():
            store_name = row['store']
            address = row['address']
            url = row['url']

            # Geocode the address to get coordinates
            geocode_result = geocode(address)
            if geocode_result:
                location = geocode_result[0]['location']
                point = (location['x'], location['y'])

                # Insert the row into the feature class
                cursor.insertRow([point, store_name, address, url])
            else:
                print(f"Could not geocode address: {address}")

    print("Feature class creation and population complete.")

if __name__ == "__main__":
    # Example usage with environment variables
    excel_file_path = os.getenv('EXCEL_FILE_PATH', r'C:\path\to\acrnm_stores.xlsx')
    output_gdb_path = os.getenv('OUTPUT_GDB_PATH', r'C:\path\to\output.gdb')
    feature_class_name = "store_locations"

    main(excel_file_path, output_gdb_path, feature_class_name)
