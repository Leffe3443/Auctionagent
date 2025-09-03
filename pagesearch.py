import requests
import json
from bs4 import BeautifulSoup


# Scraping the

# The url to search for watches on autctionet.com


# Defining the functin
# def scrape_auction(category, order, )
def scrape_auction():
    # The page number
    page_num = 1

    # Total amount of items scraped
    total_amount_items = 0

    # We scrape 5 pages
    while page_num < 5:
        print("Scraping page number: ", page_num)
        page_to_scrape = f"https://auctionet.com/en/search/31-clocks-watches?order=bid_asc&page={page_num}#results"
        
        resp = requests.get(page_to_scrape)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find the ErrorBoundary div
        div = soup.find("div", {"data-react-class": "ErrorBoundary"})
        props = div["data-react-props"]  # string
        
        # Load JSON
        data = json.loads(props)
        
        # Now you have the items
        items = data["items"]
        
        # Ids of some of the items
        item_ids = []
        
        
        for item in items:    
            item_ids.append(int(item["id"]))
            
        
        # Item search for all ids
        for id in item_ids:
            item_search = requests.get(f"https://auctionet.com/en/{id}")
            soup_item = BeautifulSoup(item_search.text, "html.parser")
            print("ITEM INFO:")
            print("Item id:", id)
            item_title = soup_item.find("h1", class_="sr-only")
            print("Item title:", item_title.text)
            item_info = soup_item.find("div", {"data-controller": "expandable-content"})
            if item_info:
                paragraphs = item_info.find_all("p")
                for p in paragraphs:
                    print("Item information:",p.get_text(strip=True))
                # print("Item info: ", item_info)
            print("---")
            print("_____________________")
    
        page_num += 1
        
    
    


# Caling the function

scrape_auction()


# Future plan, choose category and other search queries
# def scrape_auction(category, order, )
