import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# ---------- CONFIG ----------
st.set_page_config(page_title="Monitoring Irigasi & Pertanian Desa Lakessi", layout="wide")

# ---------- SECRETS ----------
# Pastikan Anda sudah menyimpan OWM_API_KEY di Secrets
OWM_API_KEY = st.secrets.get("OWM_API_KEY")

# ---------- HEADER ----------
st.title("Monitoring Irigasi & Data Pertanian Desa Lakessi")
st.markdown("""
Aplikasi ini memantau cuaca, estimasi irigasi, dan menampilkan peta curah hujan real‑time di sekitar Desa Lakessi.  
Dikembangkan oleh Dian Eka Putra
""")

# ---------- KOORDINAT ----------
latitude, longitude = -4.02, 119.44

# ---------- PETA CURAH HUJAN ----------
st.subheader("📍 Peta Curah Hujan Real‑time")
# Peta dasar OSM
m = folium.Map(location=[latitude, longitude], zoom_start=12, tiles="OpenStreetMap")
if OWM_API_KEY:
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
folium.Marker([latitude, longitude], tooltip="Desa Lakessi").add_to(m)
st_folium(m, width=700, height=400)

# ---------- FETCH DATA CUACA ----------
st.subheader("📊 Data Cuaca Harian")
url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={latitude}&longitude={longitude}&"
    f"daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    f"timezone=auto"
)
data = requests.get(url).json()
df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"]
})

# ---------- THRESHOLD IRIGASI ----------
threshold = st.sidebar.slider("Batas curah hujan untuk irigasi (mm):", 0, 20, 5)

# ---------- TABEL & REKOMENDASI ----------
df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply(
    lambda x: "Irigasi Diperlukan" if x < threshold else "Tidak Perlu Irigasi"
)
st.dataframe(df[["Tanggal","Curah Hujan (mm)","Rekomendasi Irigasi"]], use_container_width=True)

# ---------- GRAFIK CURAH HUJAN ----------
st.subheader("📈 Grafik Curah Hujan Harian")
fig, ax = plt.subplots(figsize=(10,4))
ax.bar(df["Tanggal"], df["Curah Hujan (mm)"], color="skyblue", label="Curah Hujan (mm)")
ax.axhline(threshold, color="red", linestyle="--", label=f"Threshold ({threshold} mm)")
ax.set_ylabel("Curah Hujan (mm)")
ax.set_xticks(df["Tanggal"])
ax.set_xticklabels(df["Tanggal"].dt.strftime("%d-%m"), rotation=45)
ax.legend()
st.pyplot(fig)
st.markdown("""
**Keterangan Grafik:**  
- 🔴 Garis merah putus-putus = batas minimal curah hujan untuk irigasi.  
- Batang biru = curah hujan harian.
""")

# ---------- GRAFIK SUHU & KELEMBAPAN ----------
st.subheader("📈 Grafik Suhu & Kelembapan Harian")
fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,6), sharex=True)
ax1.plot(df["Tanggal"], df["Suhu Maks (°C)"], marker='o', label="Suhu Maks")
ax1.plot(df["Tanggal"], df["Suhu Min (°C)"], marker='s', label="Suhu Min")
ax1.set_ylabel("°C")
ax1.legend()
ax1.set_title("Suhu Harian")
ax2.plot(df["Tanggal"], df["Kelembapan (%)"], marker='^', color='green', label="Kelembapan")
ax2.set_ylabel("%")
ax2.legend()
ax2.set_title("Kelembapan Harian")
plt.xticks(df["Tanggal"], df["Tanggal"].dt.strftime("%d-%m"), rotation=45)
st.pyplot(fig2)

# ---------- TIPS PERTANIAN ----------
st.subheader("💡 Tips Pertanian Harian")
for _, row in df.iterrows():
    tips = []
    if row["Curah Hujan (mm)"] < threshold:
        tips.append("lakukan irigasi")
    if row["Suhu Maks (°C)"] > 33:
        tips.append("awas stres panas")
    if row["Kelembapan (%)"] > 85:
        tips.append("awas risiko jamur/hama")
    if not tips:
        tips.append("cuaca baik untuk berkebun")
    st.write(f"{row['Tanggal'].date()}: {', '.join(tips).capitalize()}.")

# ---------- FOOTER ----------
st.markdown("---")
st.markdown("© 2025 Desa Lakessi – Aplikasi KKN Mandiri by Dian Eka Putra")
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
