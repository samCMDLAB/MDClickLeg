import requests
from bs4 import BeautifulSoup
import json

# URL of the Maryland House Members page
url = "https://mgaleg.maryland.gov/mgawebsite/Members/Index/house/name"

# Send a GET request to the webpage
response = requests.get(url)
response.raise_for_status()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all member entries (adjust selector as needed)
members = soup.find_all('div', class_='member-index-cell')

# Initialize a list to store member details
members_data = []

# Loop through each member entry to extract the hyperlink
for member in members:
    details = member.find('div', class_='col-7 text-left')
    if details:
        dd = details.find('dd')
        if dd:
            link = dd.find('a')
            if not link:  # Skip if there's no hyperlink (vacant seat)
                continue

            name = link.text.strip()
            hyperlink = f"https://mgaleg.maryland.gov{link['href']}"

            # Scrape the member's details page
            try:
                member_response = requests.get(hyperlink)
                member_response.raise_for_status()
                member_soup = BeautifulSoup(member_response.text, 'html.parser')

                # Extract data from the details page
                dl_table = member_soup.find('dl', class_='row')
                member_data = {}
                if dl_table:
                    for dt, dd in zip(dl_table.find_all('dt', class_='col-sm-3'), dl_table.find_all('dd', class_='col-sm-9')):
                        key = dt.get_text(strip=True)
                        value = dd.get_text(strip=True)
                        member_data[key] = value

                # Append the member's data to the list
                members_data.append({
                    'name': name,
                    'data': member_data
                })

            except requests.RequestException as e:
                print(f"Failed to retrieve details for {name}: {e}")

# Save the data to a JSON file
with open('maryland_house_members.json', 'w') as json_file:
    json.dump(members_data, json_file, indent=4)

print("Data saved to maryland_house_members.json")


