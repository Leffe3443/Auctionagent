import json, time, datetime as dt, requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

def _parse_iso(ts):
    try:
        # auctionet typically gives UTC-ish timestamps; be defensive
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def scrape_auction(category, sortingmethod, pages=1):
    """
    pages: int
    search_url_template: optional format string with {page}
      default: watches listing (as in your script)
    filter_fn: callable(item_dict)->bool to filter results (used by AI prompt)
    Returns: (results_list, elapsed_ms)
    """
    print("Starting auctionscrape......")

    # if search_url_template is None:
    #     print("No url provided from User!")

    t0 = time.time()
    results = []

    search_url_template = "https://auctionet.com/en/search/{category}?order={sortingmethod}&page={page}#results"

    for page in range(1, int(pages) + 1):
        url = search_url_template.format(category=category, sortingmethod=sortingmethod, page=page)
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()

        if resp.status_code != 200:
            print("Status code not 200!")
            print("Status code: ", resp.status_code)
            return 

        soup = BeautifulSoup(resp.text, "html.parser")
        bootstrap = soup.find("div", {"data-react-class": "ErrorBoundary"})
        if not bootstrap or "data-react-props" not in bootstrap.attrs:
            continue

        data = json.loads(bootstrap["data-react-props"])
        items = data.get("items", [])

        print("ITEMS:", items)

        # try to capture useful fields from listing json directly
        for it in items:
            item_id = it.get("id")
            if not item_id: 
                continue
            detail_url = f"https://auctionet.com/en/{item_id}"

            # Some fields exist directly in listing json:
            title = it.get("shortTitle") or it.get("title") or f"Item {item_id}"
            currency = it.get("currency") or ""

            current_bid = None

            # Current bid (span inside the primary-value box)
            bid_span = soup.find("div" ,"tem-page__bid-info_primary-value span")
            current_bid = bid_span.get_text(strip=True) if bid_span else None

            print("Current bid: ", current_bid)
                            
            
            # 1) "7 days" (countdown)
            # countdown_el = soup.select_one(
            #     'div.item-page__bid-info__primary-value span.item-page__bid-info__countdown'
            # )
            # countdown = countdown_el.get_text(strip=True) if countdown_el else None
            countdown = it.get("auctionEndsAtTitle")

            print("Days left: ", countdown)


            # ends_at     = _parse_iso(it.get("auctionEndsAt") or it.get("endsAt") or "")
            # print("Image url", )

            # ✅ image urls from listing JSON
            # ✅ collect all images for this item
            image_urls = []
            main_image_url = it["mainImageUrl"]

            # main image
            if it.get("mainImageUrl"):
                image_urls.append(it["mainImageUrl"])

            # additional images
            if it.get("imageUrls"):
                image_urls.extend(it["imageUrls"])

            # de-duplicate (preserve order)
            seen = set()
            image_urls = [u for u in image_urls if not (u in seen or seen.add(u))]

            
            # print("image_urls", image_urls)
            
            if it.get("estimate"):
                estimate = it.get("estimate")
            

            # Fallback scrape if none found

            # Fallback scrape for richer description
            info_text = ""
            try:
                r = requests.get(detail_url, headers=HEADERS, timeout=20)
                r.raise_for_status()
                item_soup = BeautifulSoup(r.text, "html.parser")
                title_el = item_soup.select_one("h1.sr-only") or item_soup.select_one("h1")
                if title_el:
                    title = title_el.get_text(strip=True)
                desc_div = item_soup.find("div", {"data-controller": "expandable-content"})
                if desc_div:
                    paragraphs = [p.get_text(" ", strip=True) for p in desc_div.find_all("p")]
                    info_text = "\n".join([p for p in paragraphs if p])
            except Exception:
                pass

            rec = {
                "id": int(item_id),
                "title": title,
                "url": detail_url,
                "info_text": info_text,
                "currency": currency,
                "current_bid": float(current_bid) if current_bid is not None else None,
                # "ends_at": ends_at.isoformat() if isinstance(ends_at, dt.datetime) else None,
                "estimate": estimate,
                "ends_at": countdown,
                "location": it.get("locationName") or it.get("location") or "",
                "raw": it,  # keep raw for future use
                "images": image_urls,              # ✅ add this
                "main_image_url": main_image_url, # For display later on
            }

            # if filter_fn and not filter_fn(rec):
            #     continue

            results.append(rec)

    elapsed_ms = int((time.time() - t0) * 1000)
    return results, elapsed_ms
