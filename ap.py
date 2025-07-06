import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import date, timedelta
import os

# -------- CONFIG --------
st.set_page_config(page_title="Irigasi Lakessi", layout="wide")
st.title("📡 Monitoring Irigasi & Pertanian - Desa Lakessi")

# -------- KOORDINAT --------
LAT, LON = -4.02, 119.44

# -------- PILIH DURASI --------
durasi = st.sidebar.selectbox("Pilih Periode Data", ["Harian (7 hari)", "Mingguan (4 minggu)", "Bulanan (6 bulan)"])
use_history = st.sidebar.checkbox("Tampilkan data tahun lalu")

# -------- API KEY --------
OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")

# -------- PETA --------
with st.expander("🗺 Peta Curah Hujan"):
    m = folium.Map(location=[LAT, LON], zoom_start=12)
    if OWM_API_KEY:
        tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
        folium.TileLayer(tiles=tile_url, name="Curah Hujan", attr="OpenWeatherMap", opacity=0.6).add_to(m)
    folium.Marker([LAT, LON], tooltip="Desa Lakessi").add_to(m)
    st_folium(m, height=400)

# -------- GET RANGE --------
today = date.today()
if durasi == "Harian (7 hari)":
    start = today
    end = today + timedelta(days=6)
elif durasi == "Mingguan (4 minggu)":
    start = today
    end = today + timedelta(days=28)
else:
    start = today
    end = today + timedelta(days=180)

# -------- FETCH DATA --------
def fetch_weather(start_date, end_date):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
        f"&daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean"
        f"&start_date={start_date}&end_date={end_date}&timezone=auto"
    )
    r = requests.get(url)
    r.raise_for_status()
    d = r.json()
    df = pd.DataFrame({
        "Tanggal": pd.to_datetime(d["daily"]["time"]),
        "Curah Hujan (mm)": d["daily"]["precipitation_sum"],
        "Suhu Maks (°C)": d["daily"]["temperature_2m_max"],
        "Suhu Min (°C)": d["daily"]["temperature_2m_min"],
        "Kelembapan (%)": d["daily"]["relative_humidity_2m_mean"]
    })
    return df

df_now = fetch_weather(start, end)

# -------- TAHUN LALU --------
if use_history:
    tahun_lalu = today.replace(year=today.year - 1)
    df_last = fetch_weather(tahun_lalu, tahun_lalu + (end - start))
    st.markdown("### 📅 Perbandingan Data Tahun Lalu")
    st.dataframe(df_last)

# -------- GRAFIK PLOTLY --------
st.markdown("### 📈 Grafik Curah Hujan")
fig = px.bar(df_now, x="Tanggal", y="Curah Hujan (mm)", color="Curah Hujan (mm)", title="Curah Hujan Harian")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🌡 Suhu & Kelembapan")
fig2 = px.line(df_now, x="Tanggal", y=["Suhu Maks (°C)", "Suhu Min (°C)", "Kelembapan (%)"],
               markers=True, title="Suhu & Kelembapan")
st.plotly_chart(fig2, use_container_width=True)

# -------- TIPS --------
st.markdown("### 🌾 Tips Harian")
threshold = st.sidebar.slider("Ambang Curah Hujan (mm)", 0, 20, 5)
for _, row in df_now.iterrows():
    tips = []
    if row["Curah Hujan (mm)"] < threshold:
        tips.append("🚿 Perlu irigasi")
    if row["Suhu Maks (°C)"] > 33:
        tips.append("🔥 Potensi stres panas")
    if row["Kelembapan (%)"] > 85:
        tips.append("🐛 Waspadai jamur")
    if not tips:
        tips.append("✅ Cuaca baik")
    st.write(f"{row['Tanggal'].date()}: {', '.join(tips)}")

# -------- DOWNLOAD CSV --------
st.markdown("### 📥 Unduh Data")
csv = df_now.to_csv(index=False).encode('utf-8')
st.download_button("📄 Download CSV", csv, file_name="cuaca_lakessi.csv", mime="text/csv")

# -------- LOG KE FILE --------
log_path = "data_log.csv"
if not os.path.exists(log_path):
    df_now.to_csv(log_path, index=False)
else:
    df_log = pd.read_csv(log_path)
    combined = pd.concat([df_log, df_now]).drop_duplicates(subset="Tanggal")
    combined.to_csv(log_path, index=False)
