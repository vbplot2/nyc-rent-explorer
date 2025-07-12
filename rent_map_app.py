import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
import random

# 1. Load neighbourhoods CSV and GeoJSON
@st.cache_data
def load_neighbourhoods_data():
    # Adjust paths as needed
    csv_path = "neighbourhoods.csv"
    geojson_path = "neighbourhoods.geojson"
    
    df = pd.read_csv(csv_path)
    with open(geojson_path) as f:
        geojson = json.load(f)
    return df, geojson

# 2. Generate dummy rent data
@st.cache_data
def generate_dummy_rent_data(neighbourhoods):
    rents = []
    for n in neighbourhoods:
        rent = random.randint(1500, 6000)
        rents.append({"neighbourhood": n, "avg_rent": rent})
    return pd.DataFrame(rents)

# 3. Merge and enrich GeoJSON features with rent and borough info
def enrich_geojson(geojson, df_metadata, df_rent):
    for feature in geojson["features"]:
        nbhd_name = feature["properties"].get("neighbourhood")
        
        # Get borough
        borough = df_metadata.loc[df_metadata["neighbourhood"] == nbhd_name, "neighbourhood_group"]
        borough = borough.values[0] if len(borough) > 0 else "Unknown"
        
        # Get rent
        rent = df_rent.loc[df_rent["neighbourhood"] == nbhd_name, "avg_rent"]
        if len(rent) > 0:
            rent = int(rent.values[0])  # Convert numpy.int64 to int here
        else:
            rent = "N/A"

        
        # Add to properties
        feature["properties"]["borough"] = borough
        feature["properties"]["avg_rent"] = rent
    return geojson

# 4. Build and display Folium map
def create_map(geojson):
    # Center map on NYC
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)
    
    def style_function(feature):
        return {
            "fillColor": "#blue",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.5,
        }
    
    def popup_html(feature):
        props = feature["properties"]
        name = props.get("neighbourhood", "N/A")
        borough = props.get("borough", "N/A")
        rent = props.get("avg_rent", "N/A")
        html = f"<b>{name}</b><br>Borough: {borough}<br>Avg Rent: ${rent}"
        return html
    
    folium.GeoJson(
        geojson,
        name="Neighborhoods",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["neighbourhood", "borough", "avg_rent"],
            aliases=["Neighborhood", "Borough", "Avg Rent"],
            localize=True,
        ),
        popup=folium.GeoJsonPopup(fields=["neighbourhood", "borough", "avg_rent"], labels=True, localize=True),
    ).add_to(m)
    
    return m

# === Streamlit app ===
st.title("NYC Neighborhood Rent Map")

df_metadata, geojson = load_neighbourhoods_data()
# df_rent = generate_dummy_rent_data(df_metadata["neighbourhood"].unique())
if "df_rent" not in st.session_state:
    st.session_state.df_rent = generate_dummy_rent_data(df_metadata["neighbourhood"].unique())

df_rent = st.session_state.df_rent

geojson = enrich_geojson(geojson, df_metadata, df_rent)

st.write("Generated dummy rent data for neighborhoods:")
st.dataframe(df_rent.head())

rent_map = create_map(geojson)
st_folium(rent_map, width=700, height=500)
