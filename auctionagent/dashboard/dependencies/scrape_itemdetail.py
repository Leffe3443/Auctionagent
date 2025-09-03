# app/scrape.py
import json, requests, datetime as dt
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}

def _abs(u):
    if not u: return u
    if u.startswith("http"): return u
    if u.startswith("//"): return "https:" + u
    if u.startswith("/"):  return "https://auctionet.com" + u
    return u

def scrape_item_detail(item_id: str) -> dict:
    url = f"https://auctionet.com/en/{item_id}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_el = soup.select_one("h1.sr-only") or soup.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else f"Item {item_id}"

    # Description paragraphs
    info_text = ""
    desc_div = soup.find("div", {"data-controller": "expandable-content"})
    if desc_div:
        ps = [p.get_text(" ", strip=True) for p in desc_div.find_all("p")]
        info_text = "\n".join([p for p in ps if p])

    # Current bid (span inside primary-value)
    bid_span = soup.select_one("div.item-page__bid-info_primary-value span")
    current_bid = bid_span.get_text(strip=True) if bid_span else None

    # Images: og:image + gallery imgs
    imgs = []
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        imgs.append(_abs(og["content"]))
    gallery = [img.get("src") for img in soup.select('img[src*="images.auctionet.com"]')]
    imgs.extend(_abs(u) for u in gallery if u)
    # dedupe preserve order
    seen=set(); images=[u for u in imgs if not (u in seen or seen.add(u))]

    # Location (best-effort—adjust if you have better selector)
    loc_el = soup.find(attrs={"class": lambda c: c and "location" in c})  # heuristic
    location = loc_el.get_text(strip=True) if loc_el else ""

    return {
        "id": int(item_id),
        "url": url,
        "title": title,
        "info_text": info_text,
        "current_bid": current_bid,  # string as scraped; normalize if you want a number
        "currency": "SEK" if "SEK" in (current_bid or "") else "",
        "ends_at": None,             # add if you parse it
        "location": location,
        "images": images[:8],        # cap
    }

def search_similar_baseline(reference: dict, max_pages=1) -> list:
    """
    Super simple fallback: reuse keywords from title to search listing pages and return candidates.
    """
    title = (reference.get("title") or "").lower()
    # crude keywords
    tokens = [t for t in title.replace(",", " ").split() if len(t) > 2][:4]

    results=[]
    for page in range(1, max_pages+1):
        url = f"https://auctionet.com/en/search/31-clocks-watches?page={page}#results"
        r = requests.get(url, headers=HEADERS, timeout=20); r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        boot = soup.find("div", {"data-react-class": "ErrorBoundary"})
        if not boot or "data-react-props" not in boot.attrs:
            continue
        data = json.loads(boot["data-react-props"])
        items = data.get("items", [])
        for it in items:
            title2 = it.get("shortTitle") or it.get("title") or ""
            hay = title2.lower()
            if tokens and not all(t in hay for t in tokens[:2]):  # minimal overlap
                continue
            # images
            imgs=[]
            if it.get("mainImageUrl"): imgs.append(_abs(it["mainImageUrl"]))
            for u in (it.get("imageUrls") or []): imgs.append(_abs(u))
            seen=set(); imgs=[u for u in imgs if not (u in seen or seen.add(u))]

            results.append({
                "id": int(it.get("id")),
                "title": title2,
                "url": f"https://auctionet.com/en/{it.get('id')}",
                "images": imgs[:6],
                "currency": it.get("currency") or "",
                "current_bid": it.get("currentBid") or (it.get("currentBidCents",0)/100.0 if it.get("currentBidCents") else None),
                "ends_at": it.get("auctionEndsAt") or None,
                "location": it.get("locationName") or "",
                "info_text": "",
            })
    return results[:24]
