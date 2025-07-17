# NYC Rent Explorer

NYC Rent Explorer is a project that scrapes rental listings from StreetEasy and provides a Streamlit dashboard to explore Manhattan rental market data interactively.

---

## Features

- Scrapes detailed rental data including price, beds, baths, square footage, neighborhood, and URL.
- Cleans and parses the raw data for analysis.
- Interactive Streamlit dashboard for filtering and visualizing rental trends.
- Easy to run locally or deploy for quick insights.

---

## Installation

1. Clone the repo:
```bash
git clone https://github.com/vbplot2/nyc-rent-explorer.git
cd nyc-rent-explorer
```

2. Create and activate a virtual environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

3. Install dependencies
```bash 
pip install -r requirements.txt
```

---

## Usage

This project includes both a data scraper and a Streamlit dashboard for visualization.

### Running the Scraper Locally

If you want to fetch fresh data yourself, you can run the scraper script independently:

```bash
python streeteasy_scraper.py [num_listings]
```

Replace [num_listings] with how many listings you want to scrape (default is 500).

### Streamlit Dashboard

To launch the dashboard for exploring the scraped data, run:

```bash
streamlit run app.py
```

> **Note:** The scraper and dashboard can be used separately or together depending on your needs.

---

## Project Stucture

```bash
nyc-rent-explorer/
├── data/                     # Scraped CSV files
├── app.py                    # Streamlit dashboard app
├── streeteasy_scraper.py     # Web scraper script
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── ...
```

---

## License
This project is licensed under the [MIT License](LICENSE).
