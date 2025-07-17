from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import re
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
FIELDS = ["address", "unit_type", "neighborhood", "price", "beds", "baths", "sqft", "url"]

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
    
def parse_title(title_text):
    """Extracts unit type and neighborhood from a title string."""
    if not title_text:
        return None, None

    # Normalize all whitespace
    cleaned = re.sub(r'\s+', ' ', title_text).strip()

    # Fix jammed 'in' (e.g., "unitin Chelsea" → "unit in Chelsea")
    cleaned = re.sub(r'(\w)in ', r'\1 in ', cleaned, count=1)

    # Now split on the first ' in '
    if " in " in cleaned:
        unit_type, neighborhood = cleaned.split(" in ", 1)
        return unit_type.strip(), neighborhood.strip()
    else:
        return cleaned, None
    
def parse_sqft(sqft_text):
    """Parses a square footage string like '574 ft²' into an integer."""
    # Gets the digits, but ignores the superscript 2 for ft^2.
    if sqft_text and sqft_text.strip() != "-ft²":
        match = re.search(r'\d[\d,]*', sqft_text)  # Match numbers like 1,200 or 574
        if match:
            return int(match.group(0).replace(",", ""))
    return None

def parse_number(text):
    match = re.search(r'-?\d+\.?\d*', text)
    return float(match.group()) if match else None

def parse_listing(card: BeautifulSoup) -> Dict[str, Any]:

    # --- Initialize all fields as None ---
    address = unit_type = neighborhood = price = beds = baths = sqft = url = None

    try:
        title_tag = card.select_one('p[class*="ListingDescription-module__title"]')
        if title_tag:
            full_title = title_tag.get_text(strip=True)
            unit_type, neighborhood = parse_title(full_title)

        address_tag = card.select_one('a[class*="addressTextAction"]')
        if address_tag:
            address = address_tag.get_text(strip=True)
            url = address_tag.get("href")

        price_tag = card.select_one('span[class*="PriceInfo-module__price"]')
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            price = int(price_text.replace('$', '').replace(',', ''))

        bed_tag = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(1) span')
        if bed_tag:
            beds_text = bed_tag.get_text(strip=True)
            beds = parse_number(beds_text)

        bath_tag = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(2) span')
        if bath_tag:
            baths_text = bath_tag.get_text(strip=True)
            baths = parse_number(baths_text)

        sqft_tag = card.select_one('ul[class*="BedsBathsSqft"] li:nth-of-type(3) span')
        sqft_text = sqft_tag.get_text(strip=True) if sqft_tag else ""
        if sqft_text:
            sqft = parse_sqft(sqft_text)

        return {
            "address": address,
            "unit_type": unit_type,
            "neighborhood": neighborhood,
            "price": price,
            "beds": beds,
            "baths": baths,
            "sqft": sqft,
            "url": url,
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