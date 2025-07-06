import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Monitoring Irigasi & Pertanian Desa Lakessi", layout="wide")

# Baca API key dari Secrets
OWM_API_KEY = st.secrets["OWM_API_KEY"]

# Header
st.title("Monitoring Irigasi & Pertanian Desa Lakessi")
st.markdown("""
Aplikasi memantau cuaca, estimasi irigasi, dan menampilkan peta curah hujan real‑time di sekitar Desa Lakessi.  
Dikembangkan oleh Dian Eka Putra
""")

# Koordinat Desa Lakessi
lat, lon = -4.02, 119.44

# Tampilkan peta curah hujan jika API key ada
st.subheader("📍 Peta Curah Hujan Real‑time")
if OWM_API_KEY:
    m = folium.Map(location=[lat, lon], zoom_start=10)
    tile_url = (
        f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png"
        f"?appid={OWM_API_KEY}"
    )
    folium.TileLayer(
        tiles=tile_url,
        attr="© OpenWeatherMap",
        name="Curah Hujan",
        overlay=True,
        control=True,
        opacity=0.6
    ).add_to(m)
    folium.Marker([lat, lon], tooltip="Desa Lakessi").add_to(m)
    st_folium(m, width=700, height=450)
else:
    st.warning("API key curah hujan belum diset di Secrets.")

# Lanjutkan dengan fetch & display data cuaca, grafik, tabel, rekomendasi, dll...
