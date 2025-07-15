from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests
from bs4 import BeautifulSoup

# --------------------------- Configuration ----------------------------------
LISTINGS_TARGET = 500  # default number of listings to collect
CSV_PATH = Path("data/streeteasy_listings.csv")
REQUEST_DELAY = 2  # seconds between page requests
BASE_URL = "https://streeteasy.com/for-rent/manhattan/beds:1?page={page}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
    )
}

# Fields we plan to capture
FIELDS = [
    "title",
    "price",
    "beds",
    "baths",
    "sqft",
    "neighborhood",
    "address",
    "url",
]

# --------------------------- Helper functions -------------------------------

def fetch_page(page_num: int) -> BeautifulSoup:
    """GET a search results page and return its BeautifulSoup object."""
    url = BASE_URL.format(page=page_num)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_listing(card: BeautifulSoup) -> Dict[str, Any]:
    """Extract data from a result card → dict matching `FIELDS`."""
    try:
        title = card.select_one('p[class*="ListingDescription-module__title"]')
        address_tag = card.select_one('a[class*="addressTextAction"]')
        price = card.select_one('span[class*="PriceInfo-module__price"]')

        bed = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(1) span')
        bath = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(2) span')
        sqft = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(3) span')

        return {
            "title": title.get_text(strip=True) if title else None,
            "price": price.get_text(strip=True) if price else None,
            "beds": bed.get_text(strip=True) if bed else None,
            "baths": bath.get_text(strip=True) if bath else None,
            "sqft": sqft.get_text(strip=True) if sqft else None,
            "neighborhood": title.get_text(strip=True).replace("Rental Unit in ", "") if title else None,
            "address": address_tag.get_text(strip=True) if address_tag else None,
            "url": address_tag["href"] if address_tag else None,
        }
    except Exception as e:
        print(f"Error parsing listing: {e}")
        return {}


def scrape_listings(target: int = LISTINGS_TARGET) -> List[Dict[str, Any]]:
    """Walk paginated search results until we hit `target` rows."""
    listings: List[Dict[str, Any]] = []
    page = 1

    while len(listings) < target:
        soup = fetch_page(page)
        cards = soup.select('li.sc-541ed69f-1, article[data-testid="search-result"]')
        if not cards:
            print(f"No cards found on page {page}. Stopping scrape.")
            break

        for card in cards:
            if len(listings) >= target:
                break
            parsed = parse_listing(card)
            if parsed:
                listings.append(parsed)

        print(f"Page {page}: collected {len(listings)} listings total …")
        page += 1
        time.sleep(REQUEST_DELAY)

    return listings


def save_to_csv(records: List[Dict[str, Any]], path: Path = CSV_PATH) -> None:
    """Write scraped records to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records, columns=FIELDS)
    df.to_csv(path, index=False)

    # Use absolute path first, then display relative form if possible
    abs_path = path.resolve()
    try:
        rel_path = abs_path.relative_to(Path.cwd().resolve())
        display_path = rel_path
    except ValueError:
        display_path = abs_path

    print(f"Saved {len(records)} listings → {display_path}")


# --------------------------- Entry point ------------------------------------
if __name__ == "__main__":
    try:
        target = int(sys.argv[1]) if len(sys.argv) > 1 else LISTINGS_TARGET
    except ValueError:
        print("Usage: python streeteasy_scraper.py [num_listings]")
        sys.exit(1)

    print(f"Starting scrape for {target} listings …")
    rows = scrape_listings(target)
    save_to_csv(rows)
    print("Done.  ✔︎")