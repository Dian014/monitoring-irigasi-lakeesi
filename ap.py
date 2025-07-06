import streamlit as st import requests import pandas as pd import plotly.express as px import folium from streamlit_folium import st_folium

st.set_page_config( page_title="📡 Sistem Monitoring Irigasi & Pertanian Lakessi", layout="wide", initial_sidebar_state="expanded" )

st.image( "https://upload.wikimedia.org/wikipedia/commons/2/2a/Sawah_di_Sulawesi_Selatan.jpg", caption="📍 Persawahan di Sulawesi Selatan (Sumber: Wikimedia Commons)", use_container_width=True )

st.title("🌾 Sistem Monitoring Irigasi & Pertanian Cerdas - Desa Lakessi") st.markdown(""" Aplikasi ini memantau cuaca harian, memberi rekomendasi irigasi, serta menampilkan estimasi waktu tanam dan panen berdasarkan data real-time di wilayah Desa Lakessi, Sidrap.

🧑‍💻 Developer: Dian Eka Putra
📧 ekaputradian01@gmail.com | 📱 085654073752 """)

LAT, LON = -3.947760, 119.810237

------------------ PETA ------------------

st.markdown("""

<div style='background-color:#d0f0c0; padding:10px 16px; border-left:6px solid green; border-radius:5px; margin-top:10px; font-size:18px; font-weight:bold; color:#1b5e20;'>🗺 Peta Curah Hujan Real‑time</div>
""", unsafe_allow_html=True)
with st.expander("Lihat peta real-time"):
    m = folium.Map(location=[LAT, LON], zoom_start=13)
    OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")
    if OWM_API_KEY:
        tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
        folium.TileLayer(
            tiles=tile_url,
            attr="© OpenWeatherMap",
            name="Curah Hujan",
            overlay=True,
            control=True,
            opacity=0.6
        ).add_to(m)
    folium.Marker([LAT, LON], tooltip="📍 Desa Lakessi").add_to(m)
    st_folium(m, width=700, height=400)------------------ CUACA ------------------

weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&timezone=auto" resp = requests.get(weather_url) data = resp.json()

df = pd.DataFrame({ "Tanggal": pd.to_datetime(data["daily"]["time"]), "Curah Hujan (mm)": data["daily"]["precipitation_sum"], "Suhu Maks (°C)": data["daily"]["temperature_2m_max"], "Suhu Min (°C)": data["daily"]["temperature_2m_min"], "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"] })

threshold = st.sidebar.slider("💧 Batas curah hujan untuk irigasi (mm):", 0, 20, 5) df["Rekomendasi Irigasi"] = df["Curah Hujan (mm)"].apply( lambda x: "🚿 Irigasi Diperlukan" if x < threshold else "✅ Tidak Perlu Irigasi" )

------------------ TABEL ------------------

st.markdown("""

<div style='background-color:#e1f5fe; padding:10px 16px; border-left:6px solid #039be5; border-radius:5px; margin-top:10px; font-size:18px; font-weight:bold; color:#01579b;'>📋 Tabel Data & Rekomendasi Harian</div>
""", unsafe_allow_html=True)
with st.expander("Lihat tabel dan unduh data"):
    st.dataframe(df, use_container_width=True)
    st.download_button("⬇ Download CSV", data=df.to_csv(index=False), file_name="data_irigasi_lakessi.csv")------------------ GRAFIK CURAH HUJAN ------------------

st.markdown("""

<div style='background-color:#fff3e0; padding:10px 16px; border-left:6px solid #fb8c00; border-radius:5px; margin-top:10px; font-size:18px; font-weight:bold; color:#e65100;'>📊 Grafik Curah Hujan Harian</div>
""", unsafe_allow_html=True)
with st.expander("Lihat grafik curah hujan"):
    fig = px.bar(df, x="Tanggal", y="Curah Hujan (mm)", color="Curah Hujan (mm)")
    fig.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Batas Irigasi ({threshold} mm)")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("🔴 Garis batas menunjukkan ambang kebutuhan irigasi.")------------------ GRAFIK SUHU ------------------

st.markdown("""

<div style='background-color:#f3e5f5; padding:10px 16px; border-left:6px solid #8e24aa; border-radius:5px; margin-top:10px; font-size:18px; font-weight:bold; color:#4a148c;'>🌡 Grafik Suhu & Kelembapan Harian</div>
""", unsafe_allow_html=True)
with st.expander("Lihat grafik suhu dan kelembapan"):
    fig2 = px.line(df, x="Tanggal", y=["Suhu Maks (°C)", "Suhu Min (°C)"], markers=True)
    st.plotly_chart(fig2, use_container_width=True)
    fig3 = px.line(df, x="Tanggal", y="Kelembapan (%)", markers=True)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("📈 Kelembapan & suhu berpengaruh terhadap kondisi ideal tanaman.")------------------ ESTIMASI TANAM PANEN ------------------

st.markdown("""

<div style='background-color:#fff9c4; padding:10px 16px; border-left:6px solid #fbc02d; border-radius:5px; margin-top:10px; font-size:18px; font-weight:bold; color:#f57f17;'>🌱 Estimasi Waktu Tanam & Panen</div>
""", unsafe_allow_html=True)
with st.expander("Estimasi waktu musim tanam"):
    waktu_tanam = pd.to_datetime("2025-04-01").date()
    waktu_panen = pd.to_datetime("2025-06-30").date()
    st.info(f"""
    🧮 *Estimasi waktu tanam musim ini:* {waktu_tanam}  
    🌾 *Estimasi waktu panen:* {waktu_panen}
    """)------------------ TIPS PERTANIAN ------------------

st.markdown("""

<div style='background-color:#e8f5e9; padding:10px 16px; border-left:6px solid #43a047; border-radius:5px; margin-top:10px; font-size:18px; font-weight:bold; color:#1b5e20;'>🧠 Tips Pertanian Harian Otomatis</div>
""", unsafe_allow_html=True)
with st.expander("Lihat tips pertanian otomatis"):
    for _, row in df.iterrows():
        tips = []
        if row["Curah Hujan (mm)"] < threshold:
            tips.append("lakukan irigasi")
        if row["Suhu Maks (°C)"] > 33:
            tips.append("hati-hati stres panas")
        if row["Kelembapan (%)"] > 85:
            tips.append("waspadai jamur & hama")
        if not tips:
            tips.append("cuaca baik untuk menanam atau memanen")st.markdown(f"📅 {row['Tanggal'].date()}: <span style='color:#2e7d32; font-weight:bold'>{'; '.join(tips).capitalize()}.</span>", unsafe_allow_html=True)

st.markdown("---") st.markdown("© 2025 Desa Lakessi – Aplikasi KKN Mandiri oleh Dian Eka Putra")
