import requests
from bs4 import BeautifulSoup
import csv

# Step 1: Define the URL of the Epic Games Store
url = "https://store.epicgames.com/en-US/"

# Step 2: Send a request to get the webpage content
response = requests.get(url)
print(response.reason)
soup = BeautifulSoup(response.content, "html.parser")

# Step 3: Define a list to hold the game details
game_data = []

# Step 4: Find the game elements
# The actual class names or tags might vary depending on Epic's HTML structure
games = soup.find_all("div", class_="css-2mlzob")  # Adjust class name as necessary

for game in games:
    # Extract game title
    title = game.find("span", class_="css-rgqwpc").text  # Adjust class as necessary

    # Extract game price (if available)
    price_tag = game.find("span", class_="css-4jky3p")  # Adjust class as necessary
    price = price_tag.text if price_tag else "Free"

    # Add game details to the list
    game_data.append([title, price])

# Step 5: Write the scraped data to a CSV file in the current directory
output_file = "epic_games.csv"
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Title", "Price"])  # Header
    writer.writerows(game_data)

print(f"Game details saved to {output_file}")
