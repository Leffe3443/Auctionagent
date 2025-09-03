import requests
import json
from bs4 import BeautifulSoup


# Enter the item id here:
item_id_user_input = ""


item_id = int(item_id_user_input)

item_search = requests.get(f"https://auctionet.com/en/{item_id}")

soup_item = BeautifulSoup(item_search.text, "html.parser")

print("Item id: ", item_id)
item_title = soup_item.find("h1", class_="sr-only")

item_info = soup_item.find("div", {"data-controller": "expandable-content"})


print("Item title:", item_title.text)

# get all p tags inside it
if item_info:
    paragraphs = item_info.find_all("p")
    for p in paragraphs:
        print("Item information:",p.get_text(strip=True))

print("Item information:", item_info)

print(item_info.prettify())


