import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from io import StringIO
import os

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="Monitoring Irigasi & Pertanian Desa Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ SECRETS ------------------
OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")

# ------------------ KOORDINAT ------------------
LAT, LON = -4.02, 119.44

# ------------------ HEADER ------------------
st.title("📡 Monitoring Irigasi & Pertanian Desa Lakessi")
st.markdown("""
Aplikasi ini memantau *cuaca harian, memberikan **rekomendasi irigasi, dan menampilkan **peta curah hujan* secara real‑time untuk wilayah *Desa Lakessi*.  
Dikembangkan oleh: *Dian Eka Putra*  
📧 ekaputradian01@gmail.com | 📱 085654073752
""")

# ------------------ PILIH JUMLAH HARI ------------------
jumlah_hari = st.sidebar.selectbox("📆 Tampilkan berapa hari ke depan:", options=[1, 3, 5, 7], index=3)

# ------------------ BATAS IRIGASI ------------------
threshold = st.sidebar.slider("💧 Batas curah hujan untuk irigasi (mm):", 0, 20, 5)

# ------------------ PETA ------------------
with st.expander("🗺 Peta Curah Hujan Real‑time", expanded=True):
    m = folium.Map(location=[LAT, LON], zoom_start=12, tiles="OpenStreetMap", height=400)
    if OWM_API_KEY:
        tile_url = (
            "https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png"
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
    folium.Marker([LAT, LON], tooltip="📍 Desa Lakessi").add_to(m)
    st_folium(m, width=None, height=400)

# ------------------ AMBIL DATA CUACA ------------------
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}&"
    f"daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    f"timezone=auto"
)
resp = requests.get(weather_url)
resp.raise_for_status()
data = resp.json()

df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"]
})

# ------------------ FILTER JUMLAH HARI ------------------
df = df.head(jumlah_hari)

# ------------------ LOGGING LOKAL ------------------
if not os.path.exists("data_log.csv"):
    df.to_csv("data_log.csv", index=False)
else:
    df.to_csv("data_log.csv", mode='w', index=False)

# ------------------ REKOMENDASI IRIGASI ------------------
df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply(
    lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Tidak Perlu Irigasi"
)

# ------------------ TAMPILKAN DATA ------------------
st.subheader("📋 Data & Rekomendasi Irigasi")
st.dataframe(df, use_container_width=True)

# ------------------ DOWNLOAD CSV ------------------
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇ Unduh Data sebagai CSV",
    data=csv,
    file_name="cuaca_desa_lakessi.csv",
    mime="text/csv"
)

# ------------------ GRAFIK CURAH HUJAN ------------------
st.subheader("📈 Curah Hujan Harian (Plotly)")
fig_hujan = px.bar(
    df,
    x="Tanggal",
    y="Curah Hujan (mm)",
    color_discrete_sequence=["skyblue"],
    title="Curah Hujan Harian",
)
fig_hujan.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Threshold: {threshold} mm")
st.plotly_chart(fig_hujan, use_container_width=True)

# ------------------ GRAFIK SUHU ------------------
st.subheader("🌡 Suhu Harian")
fig_suhu = px.line(
    df,
    x="Tanggal",
    y=["Suhu Maks (°C)", "Suhu Min (°C)"],
    markers=True,
    title="Suhu Maks & Min",
)
st.plotly_chart(fig_suhu, use_container_width=True)

# ------------------ GRAFIK KELEMBAPAN ------------------
st.subheader("💧 Kelembapan Harian")
fig_kelembapan = px.line(
    df,
    x="Tanggal",
    y="Kelembapan (%)",
    markers=True,
    title="Kelembapan Harian",
    line_shape="linear",
    color_discrete_sequence=["green"]
)
st.plotly_chart(fig_kelembapan, use_container_width=True)

# ------------------ TIPS PERTANIAN ------------------
st.subheader("🌾 Tips Pertanian Harian")
for _, row in df.iterrows():
    tips = []
    if row["Curah Hujan (mm)"] < threshold:
        tips.append("lakukan irigasi")
    if row["Suhu Maks (°C)"] > 33:
        tips.append("awas stres panas")
    if row["Kelembapan (%)"] > 85:
        tips.append("awas jamur/hama")
    if not tips:
        tips.append("cuaca baik untuk berkebun")
    st.write(f"📅 {row['Tanggal'].date()}: {', '.join(tips).capitalize()}.")

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown("© 2025 Desa Lakessi – Aplikasi KKN Mandiri by *Dian Eka Putra*")
