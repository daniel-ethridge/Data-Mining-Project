import data_collection
import data_processing
import pandas as pd
import json
import numpy as np


# Get all Steam apps, print the first 20, then find Hollow Knight's ID
steam_apps = data_collection.get_all_app_ids_and_names()
print("\n")
print("Example list of the first 20 steam apps: ", steam_apps[:20])
print("\n")
hk = data_collection.get_steam_app_id("Hollow Knight", steam_apps)
print("\n")

# Create a CSV file from the JSON data
data_processing.create_csv_of_apps()

app_ids = pd.read_csv("data/steam_apps.csv")["appid"]

try:
    with open("data/steam_game_data.json", "r") as f:
        app_reviews = json.load(f)
except FileNotFoundError:
    app_reviews = []

# Generate a list of already parsed game ids:
current_app_ids = []
for app in app_reviews:
    current_app_ids.append(app["appid"])

current_app_ids.sort()
list_a = current_app_ids.copy()
list(set(current_app_ids)).sort()
assert list_a == current_app_ids, "oh jeez"

for app_id in app_ids:
    # Skip games we already have
    if app_id in current_app_ids:
        continue

    # Get Hollow Knight's details and reviews. Print them to the console.
    details = data_collection.get_app_details(app_id, print_endpoint=False)
    if details is not None:
        app_review_data = data_collection.get_app_reviews(app_id, print_endpoint=False)
        app_reviews = app_reviews + [{
            "appid": app_id,
            "app_details": details,
            "review_summary": app_review_data["query_summary"],
            "reviews": app_review_data["reviews"]
        }]

        if len(app_reviews) % 100 == 0:
            print(f"Progress: approximately {np.round(100 * len(app_reviews) / len(app_ids), 2)}%")

        with open("data/steam_game_data.json", "w") as f:
            json.dump(app_reviews, f)


print("\n")
data_collection.extract_and_save_image_links(data_collection.get_app_details(hk, print_endpoint=True),
                                             'data/TEST_HOLLOWKNIGHT_vvideo_urls.json')
