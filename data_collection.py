from asyncio import timeout
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
import json
import config
import re
import os
import numpy as np
import time
import warnings
import pickle


def raise_api_warning(function_name: str, status_code, reason):
    """
    Helper function for issuing warnings from failed API calls
    :param function_name: Name of the function that calls this function
    :param status_code: Status code returned from requests call
    :param reason: Reason retured from request call
    """

    warnings.warn(f"Failed API Call in '{function_name}'.\n"
          f"API response code: {status_code}\n"
          f"API error reason: {reason}")


def get_all_app_ids_and_names(print_endpoint: bool=False,
                              overwrite_existing_file=False):
    """
    Get a list of every app id and name. Write to file designated in config.STEAM_APP_JSON_DATA.
    :param print_endpoint: If true, print full endpoint to console. Default False.
    :param overwrite_existing_file: If True and <config.STEAM_APP_JSON_DATA> exists, overwrite that file. Default False.
    :return: A list of dictionaries containing every app id and corresponding app name. The dictionaries have two
    keys: 'appid' and 'name'.
    """
    # Create data directory if it doesn't exist
    Path(config.DATA_DIRECTORY).mkdir(exist_ok=True)

    # If data file already exists and we are not overwriting, read file and return contents
    if not overwrite_existing_file and Path(config.STEAM_APP_JSON_DATA).is_file():
        with open(config.STEAM_APP_JSON_DATA, "r") as f:
            json_data = json.load(f)
            print("Returning contents from existing file.")
            return json_data["apps"]

    # Make api
    print("Making API request.")
    response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/")
    if print_endpoint:
        print(response.url)

    # Check status
    if response.status_code != 200:
        raise_api_warning("get_all_app_ids_and_names", response.status_code, response.reason)

    # Write to file
    if overwrite_existing_file or not Path(config.STEAM_APP_JSON_DATA).is_file():
            with open(config.STEAM_APP_JSON_DATA, "w") as f:
                json.dump(response.json()["applist"], f)
                print("file written")

    # Return resulting list
    return response.json()["applist"]["apps"]


def get_app_details(appid: str or int, print_endpoint: bool=False, num_api_calls=None):
    """
    Get the details about a single app in a dictionary. Dictionary keys returned:
    ['type', 'name', 'steam_appid', 'required_age', 'is_free', 'controller_support', 'dlc', 'detailed_description',
    'about_the_game', 'short_description', 'supported_languages', 'reviews', 'header_image', 'capsule_image',
    'capsule_imagev5', 'website', 'pc_requirements', 'mac_requirements', 'linux_requirements', 'legal_notice',
    'developers', 'publishers', 'price_overview', 'packages', 'package_groups', 'platforms', 'metacritic',
    'categories', 'genres', 'screenshots', 'movies', 'recommendations', 'achievements', 'release_date',
    'support_info', 'background', 'background_raw', 'content_descriptors', 'ratings']
    See https://github.com/Revadike/InternalSteamWebAPI/wiki/Get-App-Details for more information.
    :param appid: A single Steam AppID as an integer or a string
    :param print_endpoint: if True, print the API endpoint used in the request
    :return: App details in JSON format. Returns none if no details or false if api call fails. Second return is
    num_api_calls.
    """
    # Set parameters, make api call, and optionally print the endpoing
    parameters = {"appids": appid}
    response = requests.get("https://store.steampowered.com/api/appdetails", params=parameters)
    num_api_calls += 1
    if print_endpoint:
        print(response.url)

    # Throw error if the status code is not 200
    if response.status_code == 429:
        print("TOO MANY API REQUESTS")
        print("Num API calls:", num_api_calls)
        raise_api_warning("get_app_details", response.status_code, response.reason)
        return False, num_api_calls
    elif response.status_code != 200:
        print("Num API calls:", num_api_calls)
        raise_api_warning("get_app_details", response.status_code, response.reason)
        return False, num_api_calls

    with open("jsondata.json", "w") as f:
        json.dump(response.json(), f)

    # Return the JSON information
    try:
        return response.json()[str(appid)]['data'], num_api_calls
    except KeyError:
        return None, num_api_calls


def get_app_reviews(appid: str or int, print_endpoint: bool=False, cursor="*", aggregate_app_review_data=None,
                    report_threshold=1000):
    """
    Get the reviews for a single app.
    See https://github.com/Revadike/InternalSteamWebAPI/wiki/Get-App-Reviews
    :param report_threshold: Do not use
    :param appid: A single Steam AppID as an integer or a string
    :param print_endpoint: if True, print the API endpoint used in the request
    :param cursor: Cursor returned by previous calls
    :param aggregate_app_review_data: Dictionary with the following structure: {
        query_summary: dict
        reviews: list
    }
    :return: App details in JSON format. Returns False if API call fails
    """
    # Allocate memory
    if aggregate_app_review_data is not None:
        app_review_data = aggregate_app_review_data
    else:
        app_review_data = {
            "query_summary": {},
            "reviews": []
        }

    # Get the response and optionally print the full API endpoint
    cur = quote(cursor)
    response = requests.get(f"https://store.steampowered.com/appreviews/{appid}?json=1&num_per_page=100&cursor="
                            f"{cur}&filter=recent&purchase_type=all", timeout=10)
    if print_endpoint:
        print(response.url)

    # Check status code. Raise error if status code is not 200
    if response.status_code != 200:
        raise_api_warning("get_app_reviews", response.status_code, response.reason)
        return False

    json_data = response.json()

    if cursor == "*":
        app_review_data["query_summary"] = json_data["query_summary"]

    # Get important parts of the json
    reviews = json_data["reviews"]
    cursor = json_data["cursor"]

    # save to dictionary
    app_review_data["reviews"] = app_review_data["reviews"] + reviews
    num_reviews = len(app_review_data["reviews"])
    total_reviews = app_review_data["query_summary"]["total_reviews"]

    if num_reviews < total_reviews and json_data["query_summary"]["num_reviews"] != 0:
        if num_reviews > report_threshold:
            print(f"App {appid} review progress:", f"{np.round(100 * num_reviews / total_reviews, 2)}%")
            report_threshold += 1000
        return get_app_reviews(appid, False, cursor, app_review_data, report_threshold)
    else:
        return app_review_data

def get_steam_app_id(app_name, steam_apps):
    """
    Get a Steam app ID from a Steam app name
    :param app_name: The name of the app
    :param steam_apps: A list of steam apps. Most likely this was generated by the function 'get_all_app_ids_and_names'.
    :return: The corresponding Steam app ID as an integer.
    """
    app_id = None
    for app in steam_apps:
        if app["name"].lower() != app_name.lower():
            continue
        else:
            app_id = app["appid"]
            break

    if app_id is not None:
        return app_id

    raise RuntimeError("No corresponding app id could be found. Please check the spelling of the Steam App name and "
                       "try again.")



def extract_image_links(text_data):
    """
    Extract image links from the provided text data and save return them in list format.
    Parameters:
    - detail_data (str): Data from the get_app_details function
    """
    if not isinstance(text_data, dict):
        return None

    try:
        header_image = [["header", text_data["header_image"]]]
    except KeyError:
        header_image = []

    try:
        capsule_image = [["capsule", text_data["capsule_image"]]]
    except KeyError:
        capsule_image = []

    try:
        description_text = text_data["detailed_description"]
        # Regex pattern for matching image URLs
        image_pattern = r'https?://[^\s]+(?:\.jpg|\.jpeg|\.png|\.gif|\.bmp|\.tiff|\.webp|\.svg)'
        image_links = re.findall(image_pattern, description_text, re.IGNORECASE)
        description_images = [["description", image] for image in list(set(image_links))]
    except KeyError:
        description_images = []

    # Get screenshots
    try:
        screenshots = [["screenshot", screenshot["path_full"]] for screenshot in text_data["screenshots"]]
    except KeyError:
        screenshots = []

    # Combine and return all images
    all_images = header_image + capsule_image + description_images + screenshots
    return all_images


def extract_video_links(text_data):
    """
    Extract video links from the provided text data and save return them in list format.
    Parameters:
    - text_data (str): The data containing potential video links.
    """
    if not isinstance(text_data, dict):
        return None

    try:
        videos = [movie["mp4"]["max"] for movie in text_data["movies"]]
        return videos

    except KeyError:
        return []


def save_progress(games_list, reviews_list, images_list, publishers_list, developers_list, trailers_list, queried_apps):
    games_list_columns = [
        "steam_app_id",
        "steam_app_name",
        "app_type",
        "description",
        "total_reviews",
        "total_positive_reviews",
        "total_negative_reviews",
        "price_currency",
        "price",
        "genres",
        "categores",
        "platforms",
        "developer_id",
        "publisher_id"
    ]

    review_columns = [
        "review_id",
        "steam_app_id",
        "playtime_at_review",
        "review"
    ]

    image_columns = [
        "image_id",
        "steam_app_id",
        "image_type",
        "image_url"
    ]

    publisher_columns = [
        "publisher_id",
        "publisher_name"
    ]

    developer_columns = [
        "developer_id",
        "developer_name"
    ]

    trailer_columns = [
        "trailer_id",
        "steam_app_id",
        "trailer_url"
    ]

    pd.DataFrame(games_list, columns=games_list_columns).set_index("steam_app_id").to_csv("data/steam_apps_info.csv")
    pd.DataFrame(reviews_list, columns=review_columns).set_index("review_id").to_csv("data/steam_apps_reviews.csv")
    pd.DataFrame(images_list, columns=image_columns).set_index("image_id").to_csv("data/steam_apps_images.csv")
    pd.DataFrame(publishers_list, columns=publisher_columns).set_index("publisher_id").to_csv(
        "data/steam_apps_publishers.csv")
    pd.DataFrame(developers_list, columns=developer_columns).set_index("developer_id").to_csv(
        "data/steam_apps_developers.csv")
    pd.DataFrame(trailers_list, columns=trailer_columns).set_index("trailer_id").to_csv("data/steam_apps_trailers.csv")

    with open("data/queried_apps.pkl", "wb") as f:
        pickle.dump(queried_apps, f)

    print("Data collection progress saved!")

    with open("./progress.txt", "w") as f:
        f.write(f"Last saved: {str(datetime.now())}. {len(games_list)} apps written.")
