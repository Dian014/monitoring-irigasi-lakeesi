# ------------------ IMPORTS ------------------

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
import numpy as np

# ------------------ CONFIG ------------------

st.set_page_config(
    page_title="📡 Sistem Monitoring Irigasi & Pertanian Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ HEADER ------------------

st.title("🌾 Sistem Monitoring Irigasi & Pertanian Cerdas - Kelurahan Lakessi")
st.markdown("""
Aplikasi ini memantau cuaca harian, memberi rekomendasi irigasi, serta menampilkan estimasi waktu tanam dan panen berdasarkan data real-time di wilayah Kelurahan Lakessi, Kecamatan Maritengngae, Kabupaten Sidrap, Sulawesi Selatan.

🧑‍💻 Developer: Dian Eka Putra  
📧 ekaputradian01@gmail.com | 📱 085654073752
""")

# ------------------ KOORDINAT ------------------

LAT, LON = -3.947760, 119.810237

# ------------------ PETA ------------------

with st.expander("🗺 Peta Curah Hujan Real‑time"):
    m = folium.Map(location=[LAT, LON], zoom_start=13)
    OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")
    
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

    folium.Marker([LAT, LON], tooltip="📍 Kelurahan Lakessi").add_to(m)
    st_folium(m, width=700, height=400)

# ------------------ DATA CUACA ------------------

weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}&"
    "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    "timezone=auto"
)
resp = requests.get(weather_url)
data = resp.json()

# ------------------ DATAFRAME ------------------

df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": np.round(data["daily"]["precipitation_sum"], 1),
    "Suhu Maks (°C)": np.round(data["daily"]["temperature_2m_max"], 1),
    "Suhu Min (°C)": np.round(data["daily"]["temperature_2m_min"], 1),
    "Kelembapan (%)": np.round(data["daily"]["relative_humidity_2m_mean"], 1)
})

# ------------------ REKOMENDASI IRIGASI ------------------

threshold = st.sidebar.slider("💧 Batas curah hujan untuk irigasi (mm):", 0, 20, 5)
df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply(
    lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Tidak Perlu Irigasi"
)

# ------------------ TABEL DATA ------------------

def highlight_irigasi(row):
    color = '#ffe6e6' if row["Rekomendasi Irigasi"] == "🚿 Irigasi Diperlukan" else '#ffffff'
    return ['background-color: {}'.format(color)] * len(row)

with st.expander("📋 Tabel Data & Rekomendasi Harian"):
    st.dataframe(df.style.apply(highlight_irigasi, axis=1), use_container_width=True)
    st.download_button("⬇ Download CSV", data=df.to_csv(index=False), file_name="data_irigasi_lakessi.csv")

# ------------------ GRAFIK CURAH HUJAN ------------------

with st.expander("📊 Grafik Curah Hujan Harian"):
    fig = px.bar(df, x="Tanggal", y="Curah Hujan (mm)", color="Curah Hujan (mm)", title="Curah Hujan Harian")
    fig.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Batas Irigasi ({threshold} mm)")
    st.plotly_chart(fig, use_container_width=True)

# ------------------ GRAFIK SUHU & KELEMBAPAN ------------------

with st.expander("🌡 Grafik Suhu & Kelembapan Harian"):
    fig2 = px.line(df, x="Tanggal", y=["Suhu Maks (°C)", "Suhu Min (°C)"], markers=True, title="Suhu Harian")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(df, x="Tanggal", y="Kelembapan (%)", title="Kelembapan Harian", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

# ------------------ ESTIMASI TANAM & PANEN ------------------

with st.expander("🌱 Estimasi Waktu Tanam & Panen"):
    waktu_tanam = df["Tanggal"].min().date()
    waktu_panen = waktu_tanam + pd.Timedelta(days=100)
    st.info(f"""
🧮 Estimasi waktu tanam: {waktu_tanam}  
🌾 Estimasi waktu panen: {waktu_panen} (berdasarkan siklus padi 100 hari)
""")

# ------------------ PREDIKSI HASIL PANEN ------------------

with st.expander("🤖 Prediksi Hasil Panen Berdasarkan Cuaca"):
    historical_df = pd.DataFrame({
        "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
        "Suhu Maks (°C)": [30, 32, 29, 31, 33],
        "Kelembapan (%)": [75, 80, 78, 82, 79],
        "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
    })

    X = historical_df[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]]
    y = historical_df["Hasil Panen (kg/ha)"]
    model = LinearRegression().fit(X, y)

    X_now = df[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    prediksi = model.predict(X_now)[0]
    st.metric("📈 Prediksi Hasil Panen Saat Ini (kg/ha)", f"{prediksi:,.0f}")

# ------------------ TIPS PERTANIAN ------------------

with st.expander("🧠 Tips Pertanian Harian Otomatis"):
    for _, row in df.iterrows():
        tips = []
        if row["Curah Hujan (mm)"] < threshold:
            tips.append("Lakukan irigasi untuk menjaga kelembaban tanah")
        if row["Suhu Maks (°C)"] > 33:
            tips.append("Waspadai stres panas pada padi")
        if row["Kelembapan (%)"] > 85:
            tips.append("Tingkatkan kewaspadaan terhadap penyakit jamur")
        if not tips:
            tips.append("Kondisi ideal untuk pertumbuhan padi")
        st.markdown(f"📅 {row['Tanggal'].date()}: {'; '.join(tips)}")

# ------------------ PERHITUNGAN TAMBAHAN ------------------

with st.expander("📌 Info Tambahan Otomatis"):
    luas_sawah_ha = 100  # Asumsi luas sawah
    harga_gabah = 6000   # Asumsi harga gabah per kg
    total_produksi = (prediksi * luas_sawah_ha)
    pendapatan = total_produksi * harga_gabah
    st.success(f"💰 Estimasi Pendapatan per Musim (100 ha): Rp {pendapatan:,.0f}")

# ------------------ FOOTER ------------------

st.markdown("---")
st.markdown("© 2025 Kelurahan Lakessi – Aplikasi KKN Mandiri oleh Dian Eka Putra")
