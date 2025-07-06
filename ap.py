import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="🌾 Panel Cuaca & Irigasi Desa Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ SECRETS ------------------
OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")

# ------------------ LOKASI ------------------
LAT, LON = -4.012579, 119.472102  # Koordinat akurat Desa Lakessi

# ------------------ HEADER ------------------
st.markdown("## 🌤 Sistem Monitoring Cuaca & Irigasi – Desa Lakessi, Sidrap")
st.markdown("""
Pantauan real-time cuaca, kelembapan, rekomendasi irigasi, dan *estimasi waktu tanam dan panen padi* berdasarkan data prakiraan.  
📍 *Koordinat:* -4.0126, 119.4721  
🧑‍💻 Dikembangkan oleh Dian Eka Putra
""")

# ------------------ DATA CUACA ------------------
with st.spinner("Mengambil data cuaca harian dari Open-Meteo..."):
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}&"
        "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
        "timezone=auto"
    )
    resp = requests.get(weather_url)
    data = resp.json()

df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"]
})

# ------------------ FILTER HARI ------------------
hari_ditampilkan = st.sidebar.slider("Berapa hari ke depan ingin ditampilkan?", 1, 7, 5)
df = df.head(hari_ditampilkan)

# ------------------ IRIGASI ------------------
threshold = st.sidebar.slider("Batas Curah Hujan untuk Irigasi (mm):", 0, 20, 5)
df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply(
    lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Tidak Perlu Irigasi"
)

# ------------------ PETA ------------------
with st.container():
    st.markdown("### 🗺 Peta Posisi Desa Lakessi & Curah Hujan")
    col1, col2 = st.columns([1.2, 2])
    with col1:
        m = folium.Map(location=[LAT, LON], zoom_start=13, height="100%", control_scale=True)
        if OWM_API_KEY:
            tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
            folium.TileLayer(
                tiles=tile_url,
                attr="OpenWeatherMap",
                name="Curah Hujan",
                overlay=True,
                control=True,
                opacity=0.6
            ).add_to(m)
        folium.Marker([LAT, LON], tooltip="Desa Lakessi").add_to(m)
        st_folium(m, height=350, width=500)
    with col2:
        st.markdown("📍 Desa Lakessi berada di Kabupaten Sidrap. Peta ini menampilkan lapisan curah hujan real-time dari OpenWeatherMap.")

# ------------------ GRAFIK PLOTLY ------------------
st.markdown("### 📊 Grafik Data Cuaca Harian")

fig1 = px.bar(
    df,
    x="Tanggal",
    y="Curah Hujan (mm)",
    title="Curah Hujan Harian",
    color_discrete_sequence=["skyblue"]
)
fig1.add_hline(y=threshold, line_dash="dash", line_color="red")
st.plotly_chart(fig1, use_container_width=True)
st.caption("🔵 Batang: Curah hujan. 🔴 Garis: Batas minimum untuk irigasi.")

fig2 = px.line(
    df,
    x="Tanggal",
    y=["Suhu Maks (°C)", "Suhu Min (°C)"],
    markers=True,
    title="Suhu Harian"
)
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.line(
    df,
    x="Tanggal",
    y="Kelembapan (%)",
    markers=True,
    color_discrete_sequence=["green"],
    title="Kelembapan Harian"
)
st.plotly_chart(fig3, use_container_width=True)

# ------------------ TIPS PERTANIAN ------------------
st.markdown("### 🌾 Rekomendasi & Tips Pertanian")
for _, row in df.iterrows():
    tanggal = row["Tanggal"].strftime("%d-%m-%Y")
    tips = []
    if row["Curah Hujan (mm)"] < threshold:
        tips.append("lakukan irigasi")
    if row["Suhu Maks (°C)"] > 33:
        tips.append("antisipasi stres panas tanaman")
    if row["Kelembapan (%)"] > 85:
        tips.append("waspada hama/jamur")
    if not tips:
        tips.append("cuaca baik untuk menanam atau memanen")
    st.markdown(f"📅 *{tanggal}*: {', '.join(tips).capitalize()}.")

# ------------------ ESTIMASI WAKTU TANAM & PANEN ------------------
st.markdown("### 🗓 Estimasi Waktu Tanam & Panen Padi")
if df["Curah Hujan (mm)"].iloc[0] > 5:
    tanam = df["Tanggal"].iloc[0]
    panen = tanam + pd.Timedelta(days=105)
    st.success(f"🌱 *Waktu cocok untuk tanam padi: {tanam.strftime('%d-%m-%Y')}*")
    st.info(f"🌾 *Perkiraan panen padi: {panen.strftime('%d-%m-%Y')}*")
else:
    st.warning("💧 Curah hujan masih kurang. Tunda penanaman padi.")

# ------------------ UNDUH DATA ------------------
st.markdown("### 📥 Unduh Data")
st.download_button("⬇ Download Data Cuaca (CSV)", df.to_csv(index=False), file_name="cuaca_lakessi.csv")

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown("🛰 Aplikasi ini dibangun untuk membantu pertanian Desa Lakessi menggunakan data prakiraan cuaca real-time.")
