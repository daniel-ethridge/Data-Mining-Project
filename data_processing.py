import pandas as pd
from pathlib import Path
import json
import config


def create_csv_of_apps(steam_apps: list=None, block_size=1000, overwrite_file=False):
    """
    Create a CSV file containing all Steam app IDs and names. This function creates multiple small dataframes of size
    block_size and concatenates them. This greatly speeds up computation.
    :param steam_apps: List of Steam apps. If this does not exist the file <config.STEAM_APP_JSON_DATA> must exist.
    :param block_size: The number of entries to write in a single dataframe before starting a new dataframe.
    :param overwrite_file: If true, overwrite the existing file. Default False.
    """
    # If file already exists, and overwrite_file is False, do nothing
    if Path(config.STEAM_APP_CSV_DATA).is_file() and not overwrite_file:
        print("File already exists. To overwrite, set 'overwrite_file' to 'True'.")
        return

    # Check for file or list
    elif not Path(config.STEAM_APP_JSON_DATA).is_file() and steam_apps is None:
        raise FileNotFoundError(f"{config.STEAM_APP_JSON_DATA} does not exist. Please create this file or pass a list"
                                " of Steam Apps as an argument.")

    # Read file or create data directory if necessary
    if steam_apps is None:
        with open(config.STEAM_APP_JSON_DATA, "r") as f:
            steam_apps = json.load(f)["apps"]
    else:
        Path(config.DATA_DIRECTORY).mkdir(exist_ok=True)  # Create data directory if it doesn't exist.

    # Memory allocation
    df_dict = {}
    num_apps_processed = 0
    df = pd.DataFrame(columns=["appid", "name"])

    # Create dataframes
    print("Creating Dataframes for CSV file")
    for app in steam_apps:
        num_apps_processed += 1
        if app["name"] == "":
            continue
        df.loc[len(df)] = [app["appid"], app["name"]]
        if num_apps_processed % block_size == 0:
            df_dict[num_apps_processed] = df
            df = pd.DataFrame(columns=["appid", "name"])
        if num_apps_processed % 10000 == 0:
            print(f"Progress: {round(100 * num_apps_processed / len(steam_apps), 2)}%")

    # Concatenate dataframes
    print("Progress: 100%")
    num_apps_processed += 1
    df_dict[num_apps_processed] = df
    all_dfs = df_dict.values()
    total_df = pd.concat(all_dfs).set_index("appid")
    total_df.to_csv(config.STEAM_APP_CSV_DATA)
    print(f"Total records: {len(total_df)}")
