
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("Map Rendering Test")

m = folium.Map(
    location=[28.6139, 77.2090],
    zoom_start=11,
    tiles="OpenStreetMap"
)

folium.Marker(
    [28.6139, 77.2090],
    tooltip="New Delhi",
    popup="Delhi"
).add_to(m)

st_folium(m, width=1000, height=650)
