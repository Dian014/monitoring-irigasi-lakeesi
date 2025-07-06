import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="Sistem Monitoring Irigasi Lakessi", layout="wide")

# Gambar header dari Google Drive
image_url = "https://drive.google.com/uc?id=1KlGKNH6CmDe8rVK0GIe1q-SuCdSaiux0"
st.image(image_url, caption="📍 Kelurahan Lakessi", use_container_width=True)

st.title("🌾 Sistem Monitoring Irigasi & Pertanian – Kelurahan Lakessi")
st.markdown("""
Aplikasi ini memantau cuaca harian, memberi rekomendasi irigasi, serta menampilkan estimasi waktu tanam dan panen berdasarkan data real-time di *Kelurahan Lakessi, Kecamatan Maritengngae, Kabupaten Sidrap, Sulawesi Selatan*.
""")

# Lokasi
LAT, LON = -3.947760, 119.810237

# Peta
with st.expander("🗺 Peta Curah Hujan"):
    m = folium.Map(location=[LAT, LON], zoom_start=13)
    folium.Marker([LAT, LON], tooltip="📍 Kelurahan Lakessi").add_to(m)
    st_folium(m, width=700, height=400)

# Data cuaca dari Open-Meteo
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}&"
    "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    "timezone=auto"
)
resp = requests.get(weather_url)
data = resp.json()

# DataFrame
df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"]
})

# Pembulatan
df["Curah Hujan (mm)"] = df["Curah Hujan (mm)"].round(1)
df["Suhu Maks (°C)"] = df["Suhu Maks (°C)"].round(1)
df["Suhu Min (°C)"] = df["Suhu Min (°C)"].round(1)
df["Kelembapan (%)"] = df["Kelembapan (%)"].round(1)

# Rekomendasi irigasi
threshold = st.sidebar.slider("💧 Ambang curah hujan (mm)", 0, 20, 5)
df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply(
    lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Tidak Perlu Irigasi"
)

# Tabel data
def highlight(row):
    color = "#ffe6e6" if row["Rekomendasi Irigasi"] == "🚿 Irigasi Diperlukan" else "#ffffff"
    return ["background-color: {}".format(color)] * len(row)

with st.expander("📋 Tabel Data"):
    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)
    st.download_button("⬇ Unduh CSV", df.to_csv(index=False), file_name="data_lakessi.csv")

# Grafik curah hujan
with st.expander("📊 Curah Hujan Harian"):
    fig = px.bar(df, x="Tanggal", y="Curah Hujan (mm)", color="Curah Hujan (mm)")
    fig.add_hline(y=threshold, line_dash="dot", line_color="red")
    st.plotly_chart(fig, use_container_width=True)

# Grafik suhu dan kelembapan
with st.expander("🌡 Suhu dan Kelembapan"):
    st.plotly_chart(px.line(df, x="Tanggal", y=["Suhu Maks (°C)", "Suhu Min (°C)"],
                            title="Suhu Harian"), use_container_width=True)
    st.plotly_chart(px.line(df, x="Tanggal", y="Kelembapan (%)",
                            title="Kelembapan Harian"), use_container_width=True)

# Estimasi tanam & panen
with st.expander("🌱 Estimasi Waktu Tanam & Panen"):
    tanam = df["Tanggal"].min().date()
    panen = tanam + pd.Timedelta(days=100)
    st.info(f"📅 Tanam: {tanam}\n🌾 Panen: {panen}")

# Prediksi hasil panen
with st.expander("📈 Prediksi Hasil Panen"):
    df_latih = pd.DataFrame({
        "Curah Hujan (mm)": [3.2, 5.5, 1.0, 0.0],
        "Suhu Maks (°C)": [30, 29, 32, 31],
        "Kelembapan (%)": [75, 78, 80, 82],
        "Hasil Panen (kg/ha)": [5100, 5300, 4800, 4500]
    })

    X = df_latih[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]]
    y = df_latih["Hasil Panen (kg/ha)"]
    model = LinearRegression().fit(X, y)

    X_pred = df[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    hasil = model.predict(X_pred)[0]
    st.metric("Hasil Panen (perkiraan)", f"{hasil:,.0f} kg/ha")

# Tips pertanian
with st.expander("🧠 Tips Harian"):
    for _, row in df.iterrows():
        tips = []
        if row["Curah Hujan (mm)"] < threshold:
            tips.append("Lakukan irigasi")
        if row["Suhu Maks (°C)"] > 33:
            tips.append("Waspadai panas ekstrem")
        if row["Kelembapan (%)"] > 85:
            tips.append("Potensi penyakit tanaman")
        if not tips:
            tips.append("Cuaca ideal untuk bercocok tanam")
        st.markdown(f"📅 {row['Tanggal'].date()}: {'; '.join(tips)}")

st.markdown("---")
st.caption("© 2025 Kelurahan Lakessi – Aplikasi KKN Mandiri oleh Dian Eka Putra")
