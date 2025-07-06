import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import date, timedelta

st.set_page_config(page_title="🌾 Panel Prakiraan Irigasi Desa Lakessi", layout="wide")
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/2/2a/Sawah_di_Sulawesi_Selatan.jpg",
    caption="Persawahan di Sulawesi Selatan (Wikimedia Commons)",
    use_container_width=True
)

st.title("Sistem Monitoring Cuaca & Irigasi – Desa Lakessi")
st.markdown("Aplikasi ini menyajikan data prakiraan cuaca dan rekomendasi pertanian otomatis, berlaku untuk Desa Lakessi di Kabupaten Sidrap.")

LAT, LON = -4.012579, 119.472102
OWM_KEY = st.secrets.get("OWM_API_KEY", "")

hari = st.sidebar.slider("Prakiraan cuaca ke depan (hari):", 1, 7, 5)
threshold = st.sidebar.slider("Ideal curah hujan minimal (mm):", 10, 50, 20)

@st.cache_data(ttl=300)
def fetch(days):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT, "longitude": LON,
        "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean",
        "forecast_days": days, "timezone": "auto"
    }
    resp = requests.get(url, params=params); resp.raise_for_status()
    d = resp.json()["daily"]
    return pd.DataFrame({
        "Tanggal": pd.to_datetime(d["time"]),
        "Hujan": d["precipitation_sum"],
        "SuhuMax": d["temperature_2m_max"],
        "SuhuMin": d["temperature_2m_min"],
        "Kelembapan": d["relative_humidity_2m_mean"]
    })

df = fetch(hari)
df["Irigasi"] = df["Hujan"].apply(lambda x: "🚿 Irigasi diperlukan" if x < threshold else "✅ Optimal")

st.subheader("Forecast Cuaca & Rekomendasi Irigasi")
st.dataframe(df, use_container_width=True)
st.download_button("Unduh Data CSV", df.to_csv(index=False).encode(), "forecast_lakessi.csv", "text/csv")

st.subheader("Peta Curah Hujan Prakiraan")
m = folium.Map(location=[LAT, LON], zoom_start=13)
if OWM_KEY:
    folium.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_KEY}",
        attr="OpenWeatherMap", overlay=True, opacity=0.6
    ).add_to(m)
folium.CircleMarker([LAT, LON], radius=6, color="blue", fill=True).add_to(m)
st_folium(m, width="100%", height=260, returned_objects=[])

st.subheader("Grafik Interaktif")
fig_h = px.bar(df, x="Tanggal", y="Hujan", title="Curah Hujan Prakiraan", color_discrete_sequence=["skyblue"])
fig_h.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Threshold {threshold} mm")
st.plotly_chart(fig_h, use_container_width=True)
st.caption("Batang = hujan, Garis merah = threshold irigasi")

fig_s = px.line(df, x="Tanggal", y=["SuhuMax", "SuhuMin", "Kelembapan"], markers=True, title="Suhu & Kelembapan Harian")
st.plotly_chart(fig_s, use_container_width=True)

def detect_start(df):
    for i in range(len(df)-2):
        s = df.iloc[i:i+3]
        if all(s["Hujan"] >= threshold) and 25 <= s["SuhuMax"].mean() <= 33 and s["Kelembapan"].mean() > 75:
            return s.iloc[0]["Tanggal"].date()
    return None

tanam = detect_start(df)

st.subheader("Estimasi Musim Tanam & Panen Padi")
if tanam:
    est_panen = tanam + timedelta(days=150)  # +5 bulan ≈ 150 hari
    st.success(f"Perkiraan tanam musim saat ini: {tanam:%d %b %Y}")
    st.info(f"Perkiraan panen: sekitar {est_panen:%b %Y}")  # cukup bulan
else:
    st.warning("Data prakiraan belum cukup untuk mendeteksi musim tanam padi.")

st.subheader("Tips Harian Otomatis")
for _, r in df.iterrows():
    tips = []
    if r.Hujan < threshold: tips.append("irigasi")
    if r.SuhuMax > 33: tips.append("panen lebih awal")
    if r.Kelembapan > 85: tips.append("awas jamur/hama")
    if not tips: tips.append("bertani/praktek pertanian")
    st.markdown(f"- {r.Tanggal:%d-%m-%Y}: {', '.join(tips).capitalize()}")

st.markdown("---")
st.caption("Data real-time sesuai koordinat Desa Lakessi, Sidrap.")
