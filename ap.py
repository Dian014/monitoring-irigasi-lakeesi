import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os
from datetime import date, timedelta

# --- CONFIG ---
st.set_page_config(page_title="Irigasi & Pertanian Desa Lakessi", layout="wide", initial_sidebar_state="expanded")
st.title("📡 Monitoring Irigasi & Pertanian Desa Lakessi (SIDRAP)")

# --- KOORDINAT LOKAL AKURAT ---
LAT, LON = -3.92470, 119.77949
OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")

# --- OPSI SIDEBAR ---
days = st.sidebar.selectbox("📆 Lihat data cuaca untuk berapa hari?", [3, 5, 7], index=2)
threshold = st.sidebar.slider("💧 Threshold Curah Hujan (mm)", 0, 50, 20)
use_history = st.sidebar.checkbox("Tampilkan Data Tahun Lalu")

# --- AMBIL DATA CUACA ---
@st.cache_data(ttl=3600)
def fetch(start, end):
    params = {
        "latitude": LAT, "longitude": LON,
        "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean",
        "start_date": start, "end_date": end, "timezone": "auto"
    }
    url = "https://api.open-meteo.com/v1/forecast"
    r = requests.get(url, params=params)
    r.raise_for_status()
    d = r.json()["daily"]
    return pd.DataFrame({
        "Tanggal": pd.to_datetime(d["time"]),
        "Hujan": d["precipitation_sum"],
        "SuhuMax": d["temperature_2m_max"],
        "SuhuMin": d["temperature_2m_min"],
        "Kelembapan": d["relative_humidity_2m_mean"]
    })

today = date.today()
start = today - timedelta(days=days - 1)
df = fetch(start, today)

if use_history:
    last_start = start.replace(year=today.year - 1)
    last_end = today.replace(year=today.year - 1)
    df_hist = fetch(last_start, last_end)

# --- DETEKSI TANAM/PANEN PADI ---
def detect_plant(df):
    for i in range(len(df)-2):
        s = df.iloc[i:i+3]
        if (s["Hujan"] >= threshold).all() and 25 <= s["SuhuMax"].mean() <= 33 and s["Kelembapan"].mean() > 75:
            return s.iloc[0]["Tanggal"].date()
    return None

tanam = detect_plant(df)
panen = tanam + timedelta(days=110) if tanam else None

# --- LOGGING & CSV ---
if not os.path.exists("data_log.csv"):
    df.to_csv("data_log.csv", index=False)
else:
    df.to_csv("data_log.csv", mode="w", index=False)

csv_data = df.to_csv(index=False).encode("utf-8")

# --- PETA AKURAT TANPA SPACE ---
st.subheader("🗺 Peta Curah Hujan Desa Lakessi")
m = folium.Map(location=[LAT, LON], zoom_start=13, tiles="OpenStreetMap", prefer_canvas=True)
if OWM_API_KEY:
    folium.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}",
        attr="OpenWeatherMap", overlay=True, opacity=0.5
    ).add_to(m)
folium.CircleMarker([LAT, LON], radius=8, color="blue", fill=True, fill_opacity=0.7).add_to(m)
st_folium(m, width="100%", height=280)

# --- DATA & DOWNLOAD ---
df["Rekomendasi"] = df["Hujan"].apply(lambda x: "🚿 Irigasi" if x < threshold else "✅ Cukup")
st.markdown("### 📋 Data & Rekomendasi")
st.dataframe(df, use_container_width=True)
st.download_button("⬇ Unduh CSV", csv_data, "cuaca_lakessi.csv", "text/csv")

# --- GRAFIK PLOTLY ---
st.subheader("📈 Grafik Cuaca Interaktif")
p1 = px.bar(df, x="Tanggal", y="Hujan", title="Curah Hujan", color_discrete_sequence=["skyblue"])
p1.add_hline(y=threshold, line_dash="dash", line_color="red")
p2 = px.line(df, x="Tanggal", y=["SuhuMax", "SuhuMin", "Kelembapan"], markers=True, title="Suhu & Kelembapan")
st.plotly_chart(p1, use_container_width=True)
st.plotly_chart(p2, use_container_width=True)

if use_history:
    st.subheader("📊 Perbandingan Tahun Lalu")
    ph = px.line(df_hist, x="Tanggal", y="precipitation_sum", title="Hujan Tahun Lalu", markers=True)
    st.plotly_chart(ph, use_container_width=True)

# --- TANAM/PANEN PADI ---
st.subheader("🌾 Prediksi Musim Tanam & Panen Padi")
if tanam and panen:
    st.success(f"📌 Tanam padi: *{tanam.strftime('%d %b %Y')}*")
    st.info(f"🌾 Panen padi: *{panen.strftime('%d %b %Y')}*")
else:
    st.warning("⚠ Belum terdeteksi musim tanam pada data saat ini.")

# --- TIPS OTOMATIS ---
st.subheader("📝 Tips Harian")
for _, r in df.iterrows():
    tips = []
    if r["Hujan"] < threshold: tips.append("irigasi")
    if r["SuhuMax"] > 33: tips.append("panen awal")
    if r["Kelembapan"] > 85: tips.append("awas jamur")
    if not tips: tips.append("bertani")
    st.write(f"{r['Tanggal'].date()}: {', '.join(tips).capitalize()}")

# --- FOOTER ---
st.markdown("---")
st.caption("© 2025 Desa Lakessi – KKN by Dian Eka Putra")
