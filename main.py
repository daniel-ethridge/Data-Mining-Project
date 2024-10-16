import data_collection
import data_processing
import pandas as pd
import json
import numpy as np
import time


# Get all Steam apps, print the first 20, then find Hollow Knight's ID
steam_apps = data_collection.get_all_app_ids_and_names()
print("\n")

# Create a CSV file from the JSON data
# data_processing.create_csv_of_apps()

app_ids = pd.read_csv("data/steam_apps.csv")["appid"]
num_detail_api_calls = 0

try:
    with open("data/steam_game_data.json", "r") as f:
        app_reviews = json.load(f)

    with open("data/steam_apps_queried.json, r") as f:
        queried_apps = json.load(f)

except FileNotFoundError:
    app_reviews = []
    queried_apps = []

num_checked = len(queried_apps)

for app_id in app_ids:
    # Skip games we already have checked
    if app_id in queried_apps:
        continue

    num_checked += 1
    # Get Hollow Knight's details and reviews. Print them to the console.
    num_detail_api_calls += 1
    time.sleep(0.1)
    details, num_detail_api_calls = data_collection.get_app_details(app_id, print_endpoint=False,
                                                                    num_api_calls=num_detail_api_calls)
    queried_apps.append(app_id)
    with open("data/queried_steam_apps.json", "w") as f:
        json.dump(queried_apps, f)

    if details is not None:
        app_review_data = data_collection.get_app_reviews(app_id, print_endpoint=False)
        if len(app_review_data["reviews"]) > 0:
            app_reviews = app_reviews + [{
                "appid": app_id,
                "app_details": details,
                "review_summary": app_review_data["query_summary"],
                "reviews": app_review_data["reviews"]
            }]
            print(f"{len(app_reviews)} apps written. {len(app_ids) - num_checked} to go...")

            with open("data/steam_game_data.json", "w") as f:
                json.dump(app_reviews, f)

#
# print("\n")
# data_collection.extract_and_save_image_links(data_collection.get_app_details(hk, print_endpoint=True),
#                                              'data/TEST_HOLLOWKNIGHT_vvideo_urls.json')
