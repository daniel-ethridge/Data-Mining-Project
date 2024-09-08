import api_calls


# Get all Steam apps, print the first 20, then find Hollow Knight's ID
steam_apps = api_calls.get_all_app_ids_and_names()
print("Example list of the first 20 steam apps: ", steam_apps[:20])
hk = api_calls.get_steam_app_id("Hollow Knight", steam_apps)

# Get Hollow Knight's details and reviews. Print them to the console.
print(api_calls.get_app_details(hk, print_endpoint=True))
print(api_calls.get_app_reviews(hk, print_endpoint=True))
