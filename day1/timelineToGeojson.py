import json
import geojson

# Load the Google location history JSON file
input_file = 'location-history.json'  # Replace with your file path
output_file = 'location-history.geojson'

# Read the Google Timeline JSON data
with open(input_file, 'r') as f:
    location_data = json.load(f)

# Prepare a list of GeoJSON features
features = []

# Iterate over each location entry
for location in location_data:
    try:
        if location.get('activity') and location.get('activity').get('start'):
            # Extract coordinates from the start location
            start_coords = location['activity']['start'].split(':')[1].split(',')
            latitude = float(start_coords[0])
            longitude = float(start_coords[1])

            # Extract additional information such as timestamp and type
            timestamp = location.get('startTime')
            activity_type = location['activity'].get('topCandidate', {}).get('type', 'unknown')

            # Create a GeoJSON feature for each entry
            feature = geojson.Feature(
                geometry=geojson.Point((longitude, latitude)),
                properties={
                    "timestamp": timestamp,
                    "type": activity_type
                }
            )
            features.append(feature)
    except Exception as e:
        print(f"Error processing location entry: {e}")

# Create the GeoJSON FeatureCollection
feature_collection = geojson.FeatureCollection(features)

# Write the GeoJSON data to a file
with open(output_file, 'w') as f:
    geojson.dump(feature_collection, f, indent=2)

print(f"GeoJSON data has been successfully written to {output_file}")
