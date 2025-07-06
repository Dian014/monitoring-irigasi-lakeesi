import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="Monitoring Irigasi & Pertanian Desa Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ SECRETS ------------------
OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")

# ------------------ HEADER ------------------
st.title("📡 Monitoring Irigasi & Data Pertanian Desa Lakessi")
st.markdown(
    """
    Aplikasi ini memantau *cuaca harian, memberikan **rekomendasi irigasi, dan menampilkan **peta curah hujan* secara real‑time untuk wilayah *Desa Lakessi*.  
    Dikembangkan oleh: *Dian Eka Putra*  
    📧 ekaputradian01@gmail.com | 📱 085654073752
    """
)

# ------------------ KOORDINAT ------------------
LAT, LON = -4.02, 119.44

# ------------------ PETA ------------------
with st.expander("🗺 Lihat Peta Curah Hujan Real‑time", expanded=True):
    m = folium.Map(location=[LAT, LON], zoom_start=12, tiles="OpenStreetMap")
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
    st_folium(m, width=700, height=400)

# ------------------ AMBIL DATA CUACA ------------------
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}&"
    "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    "timezone=auto"
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

# ------------------ THRESHOLD IRIGASI ------------------
threshold = st.sidebar.slider("💧 Batas curah hujan untuk irigasi (mm):", 0, 20, 5)

# ------------------ REKOMENDASI IRIGASI ------------------
df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply(
    lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Tidak Perlu Irigasi"
)

# ------------------ DATAFRAME ------------------
with st.expander("📋 Tabel Data & Rekomendasi", expanded=True):
    st.dataframe(df[["Tanggal", "Curah Hujan (mm)", "Rekomendasi Irigasi"]], use_container_width=True)

# ------------------ GRAFIK CURAH HUJAN ------------------
with st.expander("📈 Grafik Curah Hujan Harian", expanded=True):
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.bar(df["Tanggal"], df["Curah Hujan (mm)"], color="skyblue", label="Curah Hujan")
    ax1.axhline(threshold, color="red", linestyle="--", label=f"Batas Irigasi ({threshold} mm)")
    ax1.set_ylabel("Curah Hujan (mm)")
    ax1.set_xticks(df["Tanggal"])
    ax1.set_xticklabels(df["Tanggal"].dt.strftime("%d-%m"), rotation=45)
    ax1.legend()
    ax1.set_title("Curah Hujan Harian")
    st.pyplot(fig1)

    st.markdown("""
    *Keterangan Grafik:*  
    - 🔵 Batang biru: curah hujan harian.  
    - 🔴 Garis merah putus-putus: batas minimal curah hujan (threshold) untuk irigasi.
    """)

# ------------------ GRAFIK SUHU & KELEMBAPAN ------------------
with st.expander("🌡 Grafik Suhu & Kelembapan Harian", expanded=True):
    fig2, (ax2, ax3) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    ax2.plot(df["Tanggal"], df["Suhu Maks (°C)"], marker='o', label="Suhu Maks")
    ax2.plot(df["Tanggal"], df["Suhu Min (°C)"], marker='s', label="Suhu Min")
    ax2.set_ylabel("Suhu (°C)")
    ax2.legend()
    ax2.set_title("Suhu Harian")

    ax3.plot(df["Tanggal"], df["Kelembapan (%)"], marker='^', color='green', label="Kelembapan")
    ax3.set_ylabel("Kelembapan (%)")
    ax3.legend()
    ax3.set_title("Kelembapan Harian")

    plt.xticks(df["Tanggal"], df["Tanggal"].dt.strftime("%d-%m"), rotation=45)
    st.pyplot(fig2)

    st.markdown("""
    *Keterangan Grafik:*  
    - 🌡 Garis suhu menunjukkan suhu maksimum dan minimum setiap hari.  
    - 💧 Garis hijau menunjukkan kelembapan rata-rata harian.
    """)

# ------------------ TIPS PERTANIAN ------------------
with st.expander("🌾 Tips Pertanian Harian", expanded=True):
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
