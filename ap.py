import streamlit as st
import requests, pandas as pd, plotly.express as px, folium, os
from streamlit_folium import st_folium
from datetime import date, timedelta

st.set_page_config(page_title="Irigasi Preditif Desa Lakessi", layout="wide")
st.title("📡 Monitoring Prakiraan Irigasi & Pertanian – Desa Lakessi")

LAT, LON = -3.92470, 119.77949
OWM_KEY = st.secrets.get("OWM_API_KEY", "")

# Sidebar
jumlah_hari = st.sidebar.selectbox("Forecast untuk hari ke:", [1,3,5,7], index=3)
threshold = st.sidebar.slider("Threshold Hujan (mm)", 0,50,20)

# Fetch forecast
@st.cache_data(ttl=300)
def fetch_forecast(days):
    params = {"latitude": LAT, "longitude": LON,
              "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean",
              "forecast_days": days, "timezone": "auto"}
    resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params)
    resp.raise_for_status()
    d = resp.json()["daily"]
    return pd.DataFrame({
        "Tanggal": pd.to_datetime(d["time"]),
        "Hujan": d["precipitation_sum"],
        "SuhuMax": d["temperature_2m_max"],
        "SuhuMin": d["temperature_2m_min"],
        "Kelembapan": d["relative_humidity_2m_mean"],
    })

df = fetch_forecast(jumlah_hari)

# Logging
df.to_csv("data_log.csv", index=False)

# Map
m = folium.Map(location=[LAT, LON], zoom_start=13)
if OWM_KEY:
    folium.TileLayer(tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_KEY}",
                     attr="OpenWeatherMap", overlay=True, opacity=0.6).add_to(m)
folium.CircleMarker([LAT, LON], radius=6, color="blue", fill=True).add_to(m)
st.subheader("🗺 Peta (Prakiraan)")
st_folium(m, width="100%", height=250, returned_objects=[])

# Data & Download
df["Rekomendasi"] = df["Hujan"].apply(lambda x: "🚿 Irigasi" if x < threshold else "✅ Tidak Perlu")
st.dataframe(df, use_container_width=True)
st.download_button("⬇ Unduh CSV", df.to_csv(index=False).encode(), "forecast.csv", "text/csv")

# Plotly
fig_h = px.bar(df, x="Tanggal", y="Hujan", title="Prakiraan Curah Hujan")
fig_h.add_hline(y=threshold, line_dash="dash", line_color="red")
fig_s = px.line(df, x="Tanggal", y=["SuhuMax","SuhuMin","Kelembapan"], markers=True, title="Suhu & Kelembapan")
st.plotly_chart(fig_h, use_container_width=True)
st.plotly_chart(fig_s, use_container_width=True)

# Tips
st.subheader("🌾 Tips & Estimasi")
for _, r in df.iterrows():
    t = []
    if r.Hujan < threshold:        t.append("irigasi")
    if r.SuhuMax > 33:             t.append("panen awal")
    if r.Kelembapan > 85:          t.append("awas jamur")
    if not t:                       t.append("bertani")
    st.write(f"{r.Tanggal.date()}: {', '.join(t).capitalize()}")

st.markdown("---\n© 2025 Desa Lakessi – KKN by Dian Eka Putra")
