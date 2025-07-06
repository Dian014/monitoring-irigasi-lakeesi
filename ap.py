import streamlit as st
import requests, pandas as pd, plotly.express as px, folium, os
from streamlit_folium import st_folium
from datetime import date, timedelta

st.set_page_config(page_title="🌾 Panel Predictive Cuaca & Irigasi – Desa Lakessi", layout="wide")
st.markdown("## Sistem Prediksi Cuaca & Irigasi – Desa Lakessi, Sidrap")

LAT, LON = -4.012579, 119.472102
OWM = st.secrets.get("OWM_API_KEY", "")

# Sidebar
hari = st.sidebar.slider("Forecast untuk hari ke:", 1, 7, 5)
threshold = st.sidebar.slider("Threshold Hujan (mm)", 0, 50, 20)

@st.cache_data(ttl=300)
def get_forecast(days):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": LAT, "longitude": LON,
              "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean",
              "forecast_days": days, "timezone": "auto"}
    r = requests.get(url, params=params); r.raise_for_status()
    d = r.json()["daily"]
    df = pd.DataFrame({
        "Tanggal": pd.to_datetime(d["time"]),
        "Hujan": d["precipitation_sum"],
        "SuhuMax": d["temperature_2m_max"],
        "SuhuMin": d["temperature_2m_min"],
        "Kelembapan": d["relative_humidity_2m_mean"]
    })
    return df

df = get_forecast(hari)

# PETA
st.subheader("🗺 Peta Curah Hujan – Desa Lakessi")
m = folium.Map(location=[LAT, LON], zoom_start=13)
if OWM:
    folium.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM}",
        attr="OpenWeatherMap", overlay=True, opacity=0.6).add_to(m)
folium.CircleMarker([LAT, LON], radius=6, color="blue", fill=True).add_to(m)
st_folium(m, width="100%", height=260, returned_objects=[])

# Rekomendasi & data
df["Irigasi"] = df["Hujan"].apply(lambda x: "🚿 Irigasi" if x < threshold else "✅ No Irigasi")
st.markdown("### 📋 Data Ramalan & Rekomendasi")
st.dataframe(df, use_container_width=True)
st.download_button("⬇ Unduh CSV", df.to_csv(index=False).encode(), "forecast_lakessi.csv", "text/csv")

# Grafik
st.subheader("📊 Grafik Interaktif Cuaca")
fig_h = px.bar(df, x="Tanggal", y="Hujan", title="Prakiraan Curah Hujan", color_discrete_sequence=["skyblue"])
fig_h.add_hline(y=threshold, line_dash="dash", line_color="red")
fig_s = px.line(df, x="Tanggal", y=["SuhuMax", "SuhuMin", "Kelembapan"], markers=True, title="Suhu & Kelembapan")
st.plotly_chart(fig_h, use_container_width=True)
st.caption("🔵 Batang = Hujan; 🔴 Batas threshold")
st.plotly_chart(fig_s, use_container_width=True)

# Deteksi tanam & panen
def deteksi_tanam(df):
    for i in range(len(df) - 2):
        s = df.iloc[i:i+3]
        if all(s["Hujan"] >= threshold) and 25 <= s["SuhuMax"].mean() <= 33 and s["Kelembapan"].mean() > 75:
            return s.iloc[0]["Tanggal"].date()
    return None

tanam = deteksi_tanam(df)
panen = tanam + timedelta(days=110) if tanam else None
st.subheader("🌱 Estimasi Tanam & Panen Padi")
if tanam:
    st.success(f"📌 Tanam: {tanam.strftime('%d %b %Y')}")
    st.info(f"🌾 Panen: {panen.strftime('%d %b %Y')}")
else:
    st.warning("💡 Data prakiraan belum memenuhi kondisi tanam optimal.")

# Tips harian
st.subheader("📝 Tips Harian Otomatis")
for _, r in df.iterrows():
    tips = []
    if r["Hujan"] < threshold: tips.append("irigasi")
    if r["SuhuMax"] > 33: tips.append("panen awal")
    if r["Kelembapan"] > 85: tips.append("awas jamur")
    if not tips: tips.append("bertani")
    st.markdown(f"- {r['Tanggal'].strftime('%d-%m-%Y')}: {', '.join(tips).capitalize()}")

st.markdown("---")
st.caption("🛰 Desain & Data otomatis – Dian Eka Putra")
