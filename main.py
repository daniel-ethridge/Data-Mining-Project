import data_collection
import data_processing


# Get all Steam apps, print the first 20, then find Hollow Knight's ID
steam_apps = data_collection.get_all_app_ids_and_names()
print("Example list of the first 20 steam apps: ", steam_apps[:20])
hk = data_collection.get_steam_app_id("Hollow Knight", steam_apps)

# Create a CSV file from the JSON data
data_processing.create_csv_of_apps()

# Get Hollow Knight's details and reviews. Print them to the console.
print("App details: ", data_collection.get_app_details(hk, print_endpoint=True))
print("App user reviews: ", data_collection.get_app_reviews(hk, print_endpoint=True))
