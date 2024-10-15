from pathlib import Path
from urllib.parse import quote

import requests
import json
import config
import re
import os
import numpy as np


def raise_api_error(function_name: str, status_code, reason):
    """
    Helper function for issuing warnings from failed API calls
    :param function_name: Name of the function that calls this function
    :param status_code: Status code returned from requests call
    :param reason: Reason retured from request call
    """
    raise requests.RequestException(f"Failed API Call in '{function_name}'.\n"
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
        raise_api_error("get_all_app_ids_and_names", response.status_code, response.reason)

    # Write to file
    if overwrite_existing_file or not Path(config.STEAM_APP_JSON_DATA).is_file():
            with open(config.STEAM_APP_JSON_DATA, "w") as f:
                json.dump(response.json()["applist"], f)
                print("file written")

    # Return resulting list
    return response.json()["applist"]["apps"]


def get_app_details(appid: str or int, print_endpoint: bool=False):
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
    :return: App details in JSON format
    """
    # Set parameters, make api call, and optionally print the endpoing
    parameters = {"appids": appid}
    response = requests.get("https://store.steampowered.com/api/appdetails", params=parameters)
    if print_endpoint:
        print(response.url)

    # Throw error if the status code is not 200
    if response.status_code == 429:
        print("TOO MANY API REQUESTS")
        raise_api_error("get_app_details", response.status_code, response.reason)
    elif response.status_code != 200:
        raise_api_error("get_app_details", response.status_code, response.reason)

    # Return the JSON information
    try:
        return response.json()[str(appid)]['data']
    except KeyError:
        return None


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
    :return: App details in JSON format
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
    response = requests.get(f"https://store.steampowered.com/appreviews/{appid}?json=1&num_per_page=100&cursor={cur}")
    if print_endpoint:
        print(response.url)


    test = [
        {
            "appid": "id",
            "reviews": []
        },
    ]

    # Check status code. Raise error if status code is not 200
    if response.status_code != 200:
        raise_api_error("get_app_reviews", response.status_code, response.reason)

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

    return app_review_data

    # if num_reviews < total_reviews:
    #     if num_reviews > report_threshold:
    #         print(f"App {appid} review progress:", f"{np.round(100 * num_reviews / total_reviews, 2)}%")
    #         report_threshold += 1000
    #     return get_app_reviews(appid, False, cursor, app_review_data, report_threshold)
    # else:
    #     return app_review_data

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



def extract_and_save_image_links(text_data, output_file):
    """
    Extract image links from the provided text data and save them to a JSON file.
    Parameters:
    - text_data (str): The data containing potential image links.
    - output_file (str): The name of the output JSON file to save the image links.
    """
    if isinstance(text_data, dict):
        text_data = json.dumps(text_data)
    
    # Check if the output file already exists
    # if os.path.exists(output_file):
    #     print(f"Output file '{output_file}' already exists. Please choose a different file name.")
    #     return
    
    # Regex pattern for matching image URLs
    image_pattern = r'https?://[^\s]+(?:\.jpg|\.jpeg|\.png|\.gif|\.bmp|\.tiff|\.webp|\.svg)'
    # image_pattern = r'https?://[^\s]+(?:\.mp4)'
    image_links = re.findall(image_pattern, text_data, re.IGNORECASE)
    unique_image_links = list(set(image_links))
    images_data = {"image_links": unique_image_links}
    
    # Save the extracted image links to a new JSON file/home/daniel-ethridge/Documents/phd/machine-learning/MachineLearning/unsynced-data
    with open(output_file, 'w', encoding='utf-8') as output:
        json.dump(images_data, output, indent=4)
    print(f"Image links extracted: {len(unique_image_links)} found and saved to '{output_file}'.")
