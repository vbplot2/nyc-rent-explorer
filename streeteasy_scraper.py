from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

# --------------------------- Configuration ----------------------------------
LISTINGS_TARGET = 500
CSV_PATH = Path("data/streeteasy_listings.csv")
REQUEST_DELAY = 2
BASE_URL = "https://streeteasy.com/for-rent/manhattan/beds:1?page={page}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
    )
}
FIELDS = ["title", "price", "beds", "baths", "sqft", "neighborhood", "address", "url"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --------------------------- Helper functions -------------------------------

def fetch_page(page_num: int) -> BeautifulSoup:
    """GET a search results page and return its BeautifulSoup object."""
    url = BASE_URL.format(page=page_num)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def to_float(text: Optional[str]) -> Optional[float]:
    """Convert bed/bath text to float, return None on failure or 'Studio'."""
    if not text:
        return None
    text = text.strip().lower()
    if "studio" in text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return None


def parse_listing(card: BeautifulSoup) -> Dict[str, Any]:
    try:
        title_tag = card.select_one('p[class*="ListingDescription-module__title"]')
        title_raw = title_tag.get_text(strip=True) if title_tag else ""
        title = title_raw.replace("Rental unitin", "Rental unit in").strip()

        address_tag = card.select_one('a[class*="addressTextAction"]')
        price_raw = card.select_one('span[class*="PriceInfo-module__price"]')
        price_text = price_raw.get_text(strip=True) if price_raw else ""

        bed = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(1) span')
        bath = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(2) span')
        sqft_raw = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(3) span')
        sqft_text = sqft_raw.get_text(strip=True) if sqft_raw else ""

        price_clean = None
        if price_text:
            price_clean = int(price_text.replace("$", "").replace(",", "").strip())

        sqft_clean = None
        if sqft_text and sqft_text != "-ft²":
            sqft_clean = int("".join(filter(str.isdigit, sqft_text)))

        bed_text = bed.get_text(strip=True) if bed else None
        bath_text = bath.get_text(strip=True) if bath else None

        beds = to_float(bed_text)
        baths = to_float(bath_text)

        neighborhood = None
        if " in " in title:
            neighborhood = title.split(" in ", 1)[1].strip()
        elif title:
            neighborhood = title.replace("Rental unit in ", "").strip()

        return {
            "title": title,
            "price": price_clean,
            "beds": beds,
            "baths": baths,
            "sqft": sqft_clean,
            "neighborhood": neighborhood,
            "address": address_tag.get_text(strip=True) if address_tag else None,
            "url": address_tag["href"] if address_tag else None,
        }
    except Exception as e:
        logging.warning(f"Error parsing listing: {e}")
        return {}


def scrape_listings(target: int = LISTINGS_TARGET) -> List[Dict[str, Any]]:
    listings: List[Dict[str, Any]] = []
    page = 1

    while len(listings) < target:
        try:
            soup = fetch_page(page)
        except Exception as e:
            logging.error(f"Failed to fetch page {page}: {e}")
            break

        cards = soup.select('li.sc-541ed69f-1, article[data-testid="search-result"]')
        if not cards:
            logging.warning(f"No listings found on page {page}. Ending scrape.")
            break

        for card in cards:
            if len(listings) >= target:
                break
            parsed = parse_listing(card)
            if parsed:
                listings.append(parsed)

        logging.info(f"Page {page}: collected {len(listings)} listings total …")
        page += 1
        time.sleep(REQUEST_DELAY)

    return listings


def save_to_csv(records: List[Dict[str, Any]], path: Path = CSV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records, columns=FIELDS)
    df.to_csv(path, index=False)

    abs_path = path.resolve()
    try:
        rel_path = abs_path.relative_to(Path.cwd().resolve())
        display_path = rel_path
    except ValueError:
        display_path = abs_path

    logging.info(f"Saved {len(records)} listings → {display_path}")


# --------------------------- Entry point ------------------------------------
if __name__ == "__main__":
    try:
        target = int(sys.argv[1]) if len(sys.argv) > 1 else LISTINGS_TARGET
    except ValueError:
        print("Usage: python streeteasy_scraper.py [num_listings]")
        sys.exit(1)

    logging.info(f"Starting scrape for {target} listings …")
    rows = scrape_listings(target)
    save_to_csv(rows)
    logging.info("Scraping complete. ✔︎")


# from __future__ import annotations

# import csv
# import sys
# import time
# from pathlib import Path
# from typing import Any, Dict, List

# import pandas as pd
# import requests
# from bs4 import BeautifulSoup

# # --------------------------- Configuration ----------------------------------
# LISTINGS_TARGET = 500  # default number of listings to collect
# CSV_PATH = Path("data/streeteasy_listings.csv")
# REQUEST_DELAY = 2  # seconds between page requests
# BASE_URL = "https://streeteasy.com/for-rent/manhattan/beds:1?page={page}"
# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
#     )
# }

# # Fields we plan to capture
# FIELDS = [
#     "title",
#     "price",
#     "beds",
#     "baths",
#     "sqft",
#     "neighborhood",
#     "address",
#     "url",
# ]

# # --------------------------- Helper functions -------------------------------

# def fetch_page(page_num: int) -> BeautifulSoup:
#     """GET a search results page and return its BeautifulSoup object."""
#     url = BASE_URL.format(page=page_num)
#     resp = requests.get(url, headers=HEADERS, timeout=15)
#     resp.raise_for_status()
#     return BeautifulSoup(resp.text, "html.parser")


# def parse_listing(card: BeautifulSoup) -> Dict[str, Any]:
#     """Extract data from a result card → dict matching `FIELDS`."""
#     try:
#         title = card.select_one('p[class*="ListingDescription-module__title"]')
#         address_tag = card.select_one('a[class*="addressTextAction"]')
#         price = card.select_one('span[class*="PriceInfo-module__price"]')

#         bed = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(1) span')
#         bath = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(2) span')
#         sqft = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(3) span')

#         return {
#             "title": title.get_text(strip=True) if title else None,
#             "price": price.get_text(strip=True) if price else None,
#             "beds": bed.get_text(strip=True) if bed else None,
#             "baths": bath.get_text(strip=True) if bath else None,
#             "sqft": sqft.get_text(strip=True) if sqft else None,
#             "neighborhood": title.get_text(strip=True).replace("Rental Unit in ", "") if title else None,
#             "address": address_tag.get_text(strip=True) if address_tag else None,
#             "url": address_tag["href"] if address_tag else None,
#         }
#     except Exception as e:
#         print(f"Error parsing listing: {e}")
#         return {}


# def scrape_listings(target: int = LISTINGS_TARGET) -> List[Dict[str, Any]]:
#     """Walk paginated search results until we hit `target` rows."""
#     listings: List[Dict[str, Any]] = []
#     page = 1

#     while len(listings) < target:
#         soup = fetch_page(page)
#         cards = soup.select('li.sc-541ed69f-1, article[data-testid="search-result"]')
#         if not cards:
#             print(f"No cards found on page {page}. Stopping scrape.")
#             break

#         for card in cards:
#             if len(listings) >= target:
#                 break
#             parsed = parse_listing(card)
#             if parsed:
#                 listings.append(parsed)

#         print(f"Page {page}: collected {len(listings)} listings total …")
#         page += 1
#         time.sleep(REQUEST_DELAY)

#     return listings


# def save_to_csv(records: List[Dict[str, Any]], path: Path = CSV_PATH) -> None:
#     """Write scraped records to a CSV file."""
#     path.parent.mkdir(parents=True, exist_ok=True)
#     df = pd.DataFrame(records, columns=FIELDS)
#     df.to_csv(path, index=False)

#     # Use absolute path first, then display relative form if possible
#     abs_path = path.resolve()
#     try:
#         rel_path = abs_path.relative_to(Path.cwd().resolve())
#         display_path = rel_path
#     except ValueError:
#         display_path = abs_path

#     print(f"Saved {len(records)} listings → {display_path}")


# # --------------------------- Entry point ------------------------------------
# if __name__ == "__main__":
#     try:
#         target = int(sys.argv[1]) if len(sys.argv) > 1 else LISTINGS_TARGET
#     except ValueError:
#         print("Usage: python streeteasy_scraper.py [num_listings]")
#         sys.exit(1)

#     print(f"Starting scrape for {target} listings …")
#     rows = scrape_listings(target)
#     save_to_csv(rows)
#     print("Done.  ✔︎")