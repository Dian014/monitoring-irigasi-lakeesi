import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

------------------ CONFIG ------------------

st.set_page_config( page_title="📡 Sistem Monitoring Irigasi & Pertanian Lakessi", layout="wide", initial_sidebar_state="expanded" )

------------------ HEADER GAMBAR ------------------

st.image( "https://upload.wikimedia.org/wikipedia/commons/2/2a/Sawah_di_Sulawesi_Selatan.jpg", caption="📍 Persawahan di Sulawesi Selatan (Sumber: Wikimedia Commons)", use_container_width=True )

------------------ HEADER ------------------

st.title("🌾 Sistem Monitoring Irigasi & Pertanian Cerdas - Desa Lakessi") st.markdown(""" Aplikasi ini memantau cuaca harian, memberi rekomendasi irigasi, serta menampilkan estimasi waktu tanam dan panen berdasarkan data real-time di wilayah Desa Lakessi, Sidrap.

🧑‍💻 Developer: Dian Eka Putra
📧 ekaputradian01@gmail.com | 📱 085654073752 """)

------------------ KOORDINAT DESA ------------------

LAT, LON = -3.947760, 119.810237  # Koordinat Desa Lakessi

------------------ PETA ------------------

with st.expander("🗺 Peta Curah Hujan Real‑time"): map_height = 380 m = folium.Map(location=[LAT, LON], zoom_start=13, height=map_height) OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")

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
st_folium(m, width=700, height=map_height)

------------------ DATA CUACA ------------------

weather_url = ( f"https://api.open-meteo.com/v1/forecast?" f"latitude={LAT}&longitude={LON}&" "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&" "timezone=auto" ) resp = requests.get(weather_url) data = resp.json()

DataFrame

df = pd.DataFrame({ "Tanggal": pd.to_datetime(data["daily"]["time"]), "Curah Hujan (mm)": data["daily"]["precipitation_sum"], "Suhu Maks (°C)": data["daily"]["temperature_2m_max"], "Suhu Min (°C)": data["daily"]["temperature_2m_min"], "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"] })

------------------ PENGATURAN & REKOMENDASI ------------------

threshold = st.sidebar.slider("💧 Batas curah hujan untuk irigasi (mm):", 0, 20, 5) df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply( lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Tidak Perlu Irigasi" )

------------------ TABEL DATA ------------------

with st.expander("📋 Tabel Data & Rekomendasi Harian"): st.dataframe(df, use_container_width=True) st.download_button("⬇ Download CSV", data=df.to_csv(index=False), file_name="data_irigasi_lakessi.csv")

------------------ GRAFIK CURAH HUJAN ------------------

with st.expander("📊 Grafik Curah Hujan Harian"): fig = px.bar(df, x="Tanggal", y="Curah Hujan (mm)", color="Curah Hujan (mm)", title="Curah Hujan Harian") fig.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Batas Irigasi ({threshold} mm)") st.plotly_chart(fig, use_container_width=True) st.markdown("🔴 Garis batas menunjukkan ambang kebutuhan irigasi.")

------------------ GRAFIK SUHU & KELEMBAPAN ------------------

with st.expander("🌡 Grafik Suhu & Kelembapan Harian"): fig2 = px.line(df, x="Tanggal", y=["Suhu Maks (°C)", "Suhu Min (°C)"], markers=True, title="Suhu Harian") st.plotly_chart(fig2, use_container_width=True)

fig3 = px.line(df, x="Tanggal", y="Kelembapan (%)", title="Kelembapan Harian", markers=True)
st.plotly_chart(fig3, use_container_width=True)
st.markdown("📈 Kelembapan & suhu berpengaruh terhadap kondisi ideal tanaman.")

------------------ ESTIMASI TANAM & PANEN ------------------

with st.expander("🌱 Estimasi Waktu Tanam & Panen"): waktu_tanam = pd.Timestamp("2025-04-01").date() waktu_panen = pd.Timestamp("2025-06-30").date() st.info(f""" 🧮 Estimasi waktu tanam musim ini: {waktu_tanam}
🌾 Estimasi waktu panen: {waktu_panen} """)

------------------ TIPS PERTANIAN ------------------

with st.expander("🧠 Tips Pertanian Harian Otomatis"): for _, row in df.iterrows(): tips = [] if row["Curah Hujan (mm)"] < threshold: tips.append("💧 Lakukan irigasi") if row["Suhu Maks (°C)"] > 33: tips.append("🌞 Waspadai stres panas") if row["Kelembapan (%)"] > 85: tips.append("🦠 Potensi jamur/hama tinggi") if not tips: tips.append("✅ Cuaca baik untuk menanam atau memanen")

st.markdown(f"<div style='padding:5px;border-radius:8px;background-color:#f0f2f6;margin-bottom:5px'>
    📅 <b>{row['Tanggal'].date()}</b>: {'; '.join(tips)}</div>", unsafe_allow_html=True)

------------------ FOOTER ------------------

st.markdown("---") st.markdown("© 2025 Desa Lakessi – Aplikasi KKN Mandiri oleh Dian Eka Putra")
