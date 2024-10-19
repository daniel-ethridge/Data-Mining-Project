import data_collection
import data_processing
import pandas as pd
import numpy as np
import time
import pickle
from datetime import datetime
import sys
from data_collection import save_progress


sys.setrecursionlimit(10**6)


# Get all Steam apps, print the first 20, then find Hollow Knight's ID
steam_apps = data_collection.get_all_app_ids_and_names()

come_back_later_list = [
    1281930,
    1118200,  # Might be ok
]

# Create a CSV file from the JSON data
# data_processing.create_csv_of_apps()

app_ids = pd.read_csv("data/steam_apps.csv")["appid"]
num_detail_api_calls = 0

try:
    df_games = pd.read_csv("data/steam_apps_info.csv")
    df_reviews = pd.read_csv("data/steam_apps_reviews.csv")
    df_images = pd.read_csv("data/steam_apps_images.csv")
    df_publishers = pd.read_csv("data/steam_apps_publishers.csv")
    df_developers = pd.read_csv("data/steam_apps_developers.csv")
    df_trailers = pd.read_csv("data/steam_apps_trailers.csv")
    # df_soundtracks = pd.read_csv("steam_app_reviews.csv").set_index("soundtrack_id")

    games_list = df_games.values.tolist()
    reviews_list = df_reviews.values.tolist()
    images_list = df_images.values.tolist()
    publishers_list = df_publishers.values.tolist()
    developers_list = df_developers.values.tolist()
    trailers_list = df_trailers.values.tolist()
    # soundtracks_list = df_soundtracks.to_list()

    with open("data/queried_apps.pkl", "rb") as f:
        queried_apps = pickle.load(f)

except FileNotFoundError:
    games_list = []
    reviews_list = []
    images_list = []
    publishers_list = []
    developers_list = []
    trailers_list = []
    # soundtracks_list = []

    queried_apps = []

num_checked = len(queried_apps)
start_num_checked = len(queried_apps)
start_games_len = len(games_list)

# Create dataframes
start_time = datetime.now()
start = time.time()

for app_id in app_ids:
    # Skip games we already have checked
    if app_id in queried_apps:
        continue

    if app_id in come_back_later_list:
        continue

    num_checked += 1
    # Get Hollow Knight's details and reviews. Print them to the console.
    num_detail_api_calls += 1
    details, num_detail_api_calls = data_collection.get_app_details(app_id,
                                                                    print_endpoint=True,
                                                                    num_api_calls=num_detail_api_calls)

    if details is not None and not details:  # Details is false
        break

    if details is not None:
        app_review_data = data_collection.get_app_reviews(app_id, print_endpoint=False)
        if app_review_data is not None and not app_review_data:  # app_review_data is False
            break

        queried_apps.append(app_id)
        if len(app_review_data["reviews"]) > 0:
            app_name = details["name"]
            app_type = details["type"]
            description = details["detailed_description"]
            total_reviews = app_review_data["query_summary"]["num_reviews"]
            total_positive_reviews = app_review_data["query_summary"]["total_positive"]
            total_negative_reviews = app_review_data["query_summary"]["total_negative"]

            try:
                if not details["is_free"]:
                    price_currency = details["price_overview"]["currency"]
                    price = details["price_overview"]["final_formatted"]
                else:
                    price_currency = ""
                    price = ""
            except KeyError:
                price_currency = ""
                price = ""

            try:
                genres = [genre["description"] for genre in details["genres"]]
            except KeyError:
                genres = ""

            try:
                categories = [category["description"] for category in details["categories"]]
            except KeyError:
                categories = ""

            try:
                platforms = []
                for key, value in details["platforms"].items():
                    if value:
                        platforms.append(key)
            except KeyError:
                platforms = ""

            try:
                developer = details["developers"][0]
                if len(developers_list) > 0:
                    all_developers = [dev[1] for dev in developers_list]
                    if developer in all_developers:
                        developer_idx = all_developers.index(developer)
                    else:
                        developers_list.append([len(developers_list), developer])
                        developer_idx = len(developers_list) - 1
                else:
                    developers_list.append([len(developers_list), developer])
                    developer_idx = len(developers_list) - 1
            except KeyError:
                developer_idx = -1

            try:
                publisher = details["publishers"][0]
                if len(publishers_list) > 0:
                    all_publishers = [dev[1] for dev in publishers_list]
                    if publisher in all_publishers:
                        publisher_idx = all_publishers.index(publisher)
                    else:
                        publishers_list.append([len(publishers_list), publisher])
                        publisher_idx = len(developers_list) - 1
                else:
                    publishers_list.append([len(publishers_list), publisher])
                    publisher_idx = len(publishers_list) - 1
            except KeyError:
                publisher_idx = -1

            games_list.append([
                app_id,
                app_name,
                app_type,
                description,
                total_reviews,
                total_positive_reviews,
                total_negative_reviews,
                price_currency,
                price,
                genres,
                categories,
                platforms,
                developer_idx,
                publisher_idx
            ])

            assert len(games_list) >= len(developers_list), "Problem reached"

            # Save reviews
            all_reviews = app_review_data["reviews"]
            primary_keys = np.arange(len(reviews_list), len(reviews_list) + len(all_reviews))
            try:
                test = [review["author"] for review in all_reviews]
                playtimes_at_review = [
                    review["author"]["playtime_at_review"]
                    if "playtime_at_review" in review["author"].keys() else np.nan for review in all_reviews
                ]
            except KeyError:
                playtimes_at_review = np.full(len(primary_keys), np.nan)

            review_text = [review["review"] for review in all_reviews]
            review_info = [[
                primary_key,
                app_id,
                playtime,
                review
            ] for primary_key, playtime, review in zip(primary_keys, playtimes_at_review, review_text)]

            reviews_list += review_info

            # Save images
            all_images = data_collection.extract_image_links(details)
            image_types = [image_data[0] for image_data in all_images]
            image_url = [image_data[1] for image_data in all_images]
            primary_keys = np.arange(len(images_list), len(images_list) + len(all_images))

            image_info = [[
                primary_key,
                app_id,
                image_type,
                image_link
            ] for primary_key, image_type, image_link in zip(primary_keys, image_types, image_url)]

            images_list += image_info

            # Save videos
            all_trailers = data_collection.extract_video_links(details)
            primary_keys = np.arange(len(trailers_list), len(trailers_list) + len(all_trailers))

            trailer_info = [[
                primary_key,
                app_id,
                video_url
            ] for primary_key, video_url in zip(primary_keys, all_trailers)]

            trailers_list += trailer_info

            print(f"Apps remaining: {len(app_ids) - num_checked}. App data written. Total apps: {len(games_list)}. "
                  f"Reviews for app: {len(review_info)}.")

            if len(games_list) % 10 == 0:
                save_progress(games_list, reviews_list, images_list, publishers_list, developers_list, trailers_list, queried_apps)

        else:  # if len(app_review_data["reviews"]) > 0:  (No reviews)
            print(f"Apps remaining: {len(app_ids) - num_checked}. No reviews. Skipping.")

    else:  # if details is not None:  (details is None)
        print(f"Apps remaining: {len(app_ids) - num_checked}. Details from app is None. Skipping.")
        queried_apps.append(app_id)

save_progress(games_list, reviews_list, images_list, publishers_list, developers_list, trailers_list, queried_apps)

if len(games_list) > start_games_len:
    with open("./ended.txt", "w") as f:
        f.write(f"Program ended: {str(datetime.now())}.\n"
                f"Apps written at start: {start_games_len}\n"
                f"Apps written now: {len(games_list)}\n"
                f"Apps queried at start: {start_num_checked}\n"
                f"Apps queried now: {len(queried_apps)}"
                f"{len(app_ids) - len(queried_apps)} apps left to check.")

    try:
        df = pd.read_csv("data-collection-data.csv").drop("Unnamed: 0", axis=1)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["start_time", "end_time", "run_time", "crontab_frequency", "num_apps_written",
                                   "num_apps_queried"])

    end = time.time()
    end_time = datetime.now()
    df.loc[len(df)] = [start_time, end_time, end - start, 1, len(games_list) - start_games_len, len(queried_apps) -
                       start_num_checked]
    df.to_csv("data-collection-data.csv")
