import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
import numpy as np
import openai

# ------------------ KONFIGURASI ------------------
st.set_page_config(
    page_title="🌾 Sistem Pertanian Cerdas Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ INPUT KOORDINAT DINAMIS ------------------
LAT = st.sidebar.number_input("Latitude", value=-3.947760, format="%.6f")
LON = st.sidebar.number_input("Longitude", value=119.810237, format="%.6f")

# ------------------ INISIALISASI OPENAI ------------------
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    openai.api_key = None

# ------------------ JUDUL ------------------
st.title("🌱 Sistem Pertanian Cerdas – Kelurahan Lakessi")
st.markdown("""
📍 *Lokasi: Kelurahan Lakessi, Kecamatan Maritengngae, Sidrap, Sulawesi Selatan*  
🧑‍💻 *Pengembang: Dian Eka Putra* | 📧 ekaputradian01@gmail.com | 📱 085654073752  
""")

# ------------------ PETA CURAH HUJAN ------------------
with st.expander("🌧️ Peta Curah Hujan Real-time (OpenWeatherMap)"):
    m = folium.Map(location=[LAT, LON], zoom_start=13, control_scale=True)
    OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")
    if OWM_API_KEY:
        tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
        folium.TileLayer(tiles=tile_url, attr="© OpenWeatherMap", name="Curah Hujan", overlay=True, control=True, opacity=0.6).add_to(m)
        folium.Marker([LAT, LON], tooltip="📍 Lokasi Terpilih").add_to(m)
    st_folium(m, width="100%", height=400)

# ------------------ DATA CUACA PER JAM ------------------
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=temperature_2m,precipitation,relative_humidity_2m&timezone=auto"
)
resp = requests.get(weather_url)
data = resp.json()

# ------------------ TABEL DATA ------------------
df = pd.DataFrame({
    "Waktu": pd.to_datetime(data["hourly"]["time"]),
    "Curah Hujan (mm)": np.round(data["hourly"]["precipitation"], 2),
    "Suhu (°C)": np.round(data["hourly"]["temperature_2m"], 1),
    "Kelembapan (%)": np.round(data["hourly"]["relative_humidity_2m"], 1)
})

threshold = st.sidebar.slider("💧 Ambang Curah Hujan untuk Irigasi (mm):", 0.0, 10.0, 0.2, step=0.1)
df["Status Irigasi"] = df["Curah Hujan (mm)"].apply(lambda x: "🚿 Irigasi Dibutuhkan" if x < threshold else "✅ Cukup Air")

with st.expander("📋 Data Cuaca dan Status Irigasi Per Jam"):
    st.dataframe(df.tail(24).style.format({
        "Curah Hujan (mm)": "{:.2f}",
        "Suhu (°C)": "{:.1f}",
        "Kelembapan (%)": "{:.1f}"
    }), use_container_width=True)

# ------------------ GRAFIK ------------------
with st.expander("📊 Grafik Tren Cuaca Per Jam"):
    fig1 = px.bar(df.tail(48), x="Waktu", y="Curah Hujan (mm)", title="Curah Hujan")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(df.tail(48), x="Waktu", y="Suhu (°C)", title="Suhu")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(df.tail(48), x="Waktu", y="Kelembapan (%)", title="Kelembapan")
    st.plotly_chart(fig3, use_container_width=True)

# ------------------ PREDIKSI HASIL PANEN ------------------
with st.expander("🤖 Prediksi Hasil Panen Otomatis"):
    history_df = pd.DataFrame({
        "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
        "Suhu (°C)": [30, 32, 29, 31, 33],
        "Kelembapan (%)": [75, 80, 78, 82, 79],
        "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
    })
    X = history_df[["Curah Hujan (mm)", "Suhu (°C)", "Kelembapan (%)"]]
    y = history_df["Hasil Panen (kg/ha)"]
    model = LinearRegression().fit(X, y)
    X_now = df[["Curah Hujan (mm)", "Suhu (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    prediksi = model.predict(X_now)[0]
    st.metric("📈 Prediksi Panen Saat Ini (kg/ha)", f"{prediksi:,.0f}")

# ------------------ CHATBOT PERTANIAN ------------------
with st.expander("🤖 Tanya Jawab AI GPT: Asisten Pertanian Lakessi"):
    prompt = st.text_input("Tanya tentang pertanian, pupuk, hama, dll:")
    if prompt:
        if not openai.api_key:
            st.error("⚠️ API Key OpenAI tidak tersedia.")
        else:
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Kamu adalah ahli pertanian lokal yang memberikan jawaban ringkas, tepat, dan praktis untuk petani di Sulawesi Selatan."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.5
                )
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# ------------------ FORM PELAPORAN ------------------
with st.expander("📝 Laporan Warga"):
    with st.form("form_laporan"):
        nama = st.text_input("Nama")
        kontak = st.text_input("Kontak")
        jenis = st.selectbox("Jenis", ["Masalah Irigasi", "Gangguan Hama", "Kondisi Cuaca", "Lainnya"])
        lokasi = st.text_input("Lokasi")
        isi = st.text_area("Deskripsi")
        kirim = st.form_submit_button("Kirim")

        if kirim and nama and kontak and isi:
            if "laporan" not in st.session_state:
                st.session_state.laporan = []
            st.session_state.laporan.append({
                "Nama": nama, "Kontak": kontak, "Jenis": jenis, "Lokasi": lokasi, "Deskripsi": isi
            })
            st.success("✅ Laporan berhasil dikirim!")

    if "laporan" in st.session_state and st.session_state.laporan:
        st.markdown("### Daftar Laporan")
        for i, lap in enumerate(st.session_state.laporan):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"**{lap['Jenis']}** oleh {lap['Nama']} - {lap['Deskripsi']} (Lokasi: {lap['Lokasi']})")
            with col2:
                if st.button("❌", key=f"hapus_laporan_{i}"):
                    st.session_state.laporan.pop(i)
                    st.experimental_rerun()

# ------------------ PENGINGAT TUGAS ------------------
with st.expander("📆 Pengingat Harian"):
    tugas = st.text_input("Tambah Tugas:")
    if "tugas_list" not in st.session_state:
        st.session_state.tugas_list = []
    if tugas and st.button("Simpan Tugas"):
        st.session_state.tugas_list.append(tugas)
    for i, t in enumerate(st.session_state.tugas_list):
        col1, col2 = st.columns([0.9, 0.1])
        col1.markdown(f"- ✅ {t}")
        if col2.button("❌", key=f"hapus_tugas_{i}"):
            st.session_state.tugas_list.pop(i)
            st.experimental_rerun()

# ------------------ HARGA PASAR ------------------
with st.expander("💹 Harga Komoditas"):
    st.table(pd.DataFrame({
        "Komoditas": ["Gabah Kering", "Jagung", "Beras Medium"],
        "Harga (Rp/kg)": [6500, 5300, 10500]
    }))

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("© 2025 – Kelurahan Lakessi | Dashboard Pertanian Digital oleh Dian Eka Putra")
