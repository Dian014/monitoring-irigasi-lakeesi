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

LAT, LON = -4.02, 119.44
OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")

# --- SIDEBAR OPTIONS ---
jumlah_hari = st.sidebar.selectbox("📆 Tampilkan berapa hari?", [3, 5, 7], index=2)
threshold = st.sidebar.slider("💧 Threshold Curah Hujan (mm)", 0, 50, 20)
use_history = st.sidebar.checkbox("Tampilkan Data Tahun Lalu")

# --- FETCH FUNCTION ---
@st.cache_data(ttl=3600)
def fetch_weather(start_date, end_date):
    params = {
        "latitude": LAT, "longitude": LON,
        "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean",
        "start_date": start_date, "end_date": end_date, "timezone": "auto"
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params) if start_date>=date.today() else requests.get("https://archive-api.open-meteo.com/v1/archive", params=params)
    r.raise_for_status()
    d = r.json()["daily"]
    return pd.DataFrame({"Tanggal": pd.to_datetime(d["time"]),
                         "Hujan": d["precipitation_sum"],
                         "SuhuMax": d["temperature_2m_max"],
                         "SuhuMin": d["temperature_2m_min"],
                         "Kelembapan": d["relative_humidity_2m_mean"]})

# --- GET DATA ---
today = date.today()
start = today - timedelta(days=jumlah_hari - 1)
df_now = fetch_weather(start, today)

if use_history:
    start_last = start.replace(year=today.year - 1)
    end_last = today.replace(year=today.year - 1)
    df_hist = fetch_weather(start_last, end_last)

# --- DETEKSI TANAM & PANEN PADI ---
def deteksi_tanam(df):
    for i in range(len(df)-2):
        sub = df.iloc[i:i+3]
        if all(sub["Hujan"] >= threshold) and (25 <= sub["SuhuMax"].mean() <= 33) and (sub["Kelembapan"].mean() > 75):
            return sub.iloc[0]["Tanggal"].date()
    return None

tanggal_tanam = deteksi_tanam(df_now)
tanggal_panen = (tanggal_tanam + timedelta(days=110)) if tanggal_tanam else None

# --- LOGGING ---
if not os.path.exists("data_log.csv"):
    df_now.to_csv("data_log.csv", index=False)
else:
    df_now.to_csv("data_log.csv", mode="w", index=False)

# --- MAP ---
st.subheader("🗺 Peta Curah Hujan")
m = folium.Map(location=[LAT, LON], zoom_start=12, tiles="OpenStreetMap")
if OWM_API_KEY:
    folium.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}",
        attr="OpenWeatherMap", overlay=True, opacity=0.5
    ).add_to(m)
folium.Marker([LAT, LON], tooltip="Desa Lakessi").add_to(m)
st_folium(m, width="100%", height=300)

# --- DATA & DOWNLOAD ---
df_now["Rekomendasi"] = df_now["Hujan"].apply(lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Cukup Hujan")
st.markdown("### 📋 Data Cuaca & Rekomendasi")
st.dataframe(df_now, use_container_width=True)
csv = df_now.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Unduh CSV", data=csv, file_name="cuaca_lakessi.csv", mime="text/csv")

# --- GRAFIK INTERAKTIF ---
st.subheader("📈 Grafik Interaktif Cuaca")
fig1 = px.bar(df_now, x="Tanggal", y="Hujan", title="Curah Hujan Harian", color_discrete_sequence=["skyblue"])
fig1.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Threshold {threshold} mm")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.line(df_now, x="Tanggal", y=["SuhuMax", "SuhuMin", "Kelembapan"], markers=True,
               title="Suhu & Kelembapan Harian")
st.plotly_chart(fig2, use_container_width=True)

if use_history:
    st.subheader("📊 Perbandingan Tahun Lalu")
    fig_hist = px.line(df_hist, x="Tanggal", y="precipitation_sum", title="Curah Hujan – Tahun Lalu", markers=True)
    st.plotly_chart(fig_hist, use_container_width=True)

# --- MUSIM TANAM & PANEN ---
st.subheader("🌾 Musim Tanam & Panen Padi (Prediksi)")
if tanggal_tanam and tanggal_panen:
    st.success(f"📌 Diprediksi tanam: *{tanggal_tanam.strftime('%d %b %Y')}*")
    st.info(f"🌾 Diprediksi panen: *{tanggal_panen.strftime('%d %b %Y')}*")
else:
    st.warning("⚠ Belum ada pola cuaca memadai untuk tanam padi.")

# --- TIPS AUTOMATIS ---
st.subheader("📝 Tips Harian Otomatis")
for _, r in df_now.iterrows():
    tips = []
    if r["Hujan"] < threshold: tips.append("irigasi")
    if r["SuhuMax"] > 33: tips.append("panen lebih awal")
    if r["Kelembapan"] > 85: tips.append("awas jamur")
    if not tips: tips.append("bertani/nanam")
    st.write(f"{r['Tanggal'].date()}: {', '.join(tips).capitalize()}")

# --- FOOTER ---
st.markdown("---")
st.caption("© 2025 Desa Lakessi – Aplikasi KKN Mandiri by Dian Eka Putra")
