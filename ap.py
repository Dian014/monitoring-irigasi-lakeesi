import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
import numpy as np
import random
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
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")  # simpan API key di Streamlit secrets
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

# ------------------ DATA CUACA ------------------
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}&"
    "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&timezone=auto"
)
resp = requests.get(weather_url)
data = resp.json()

# ------------------ TABEL DATA ------------------
df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": np.round(data["daily"]["precipitation_sum"], 1),
    "Suhu Maks (°C)": np.round(data["daily"]["temperature_2m_max"], 1),
    "Suhu Min (°C)": np.round(data["daily"]["temperature_2m_min"], 1),
    "Kelembapan (%)": np.round(data["daily"]["relative_humidity_2m_mean"], 1)
})

# ------------------ REKOMENDASI IRIGASI ------------------
threshold = st.sidebar.slider("💧 Ambang Curah Hujan untuk Irigasi (mm):", 0, 20, 5)
df["Status Irigasi"] = df["Curah Hujan (mm)"].apply(lambda x: "🚿 Irigasi Dibutuhkan" if x < threshold else "✅ Cukup Air")

def highlight_irigasi(row):
    color = '#ffe6e6' if row["Status Irigasi"] == "🚿 Irigasi Dibutuhkan" else '#e6ffe6'
    return ['background-color: {}'.format(color)] * len(row)

with st.expander("📋 Data Cuaca dan Status Irigasi Harian"):
    st.dataframe(df.style.apply(highlight_irigasi, axis=1).format({
        "Curah Hujan (mm)": "{:.1f}",
        "Suhu Maks (°C)": "{:.1f}",
        "Suhu Min (°C)": "{:.1f}",
        "Kelembapan (%)": "{:.1f}"
    }), use_container_width=True)
    st.download_button("⬇ Unduh Data CSV", data=df.to_csv(index=False), file_name="cuaca_irigasi_lakessi.csv")

# ------------------ GRAFIK ------------------
with st.expander("📊 Grafik Tren Cuaca Harian"):
    fig1 = px.bar(df, x="Tanggal", y="Curah Hujan (mm)", color="Curah Hujan (mm)", title="Curah Hujan Harian")
    fig1.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Ambang Irigasi ({threshold} mm)")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(df, x="Tanggal", y=["Suhu Maks (°C)", "Suhu Min (°C)"], title="Suhu Harian", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(df, x="Tanggal", y="Kelembapan (%)", title="Kelembapan Harian", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

# ------------------ ESTIMASI TANAM & PANEN ------------------
with st.expander("🌱 Estimasi Jadwal Tanam & Panen"):
    waktu_tanam = df["Tanggal"].min().date()
    waktu_panen = waktu_tanam + pd.Timedelta(days=100)
    st.info(f"🧮 Waktu tanam: {waktu_tanam} | 🌾 Perkiraan panen: {waktu_panen} (Siklus padi 100 hari)")

# ------------------ PREDIKSI HASIL PANEN ------------------
with st.expander("🤖 Prediksi Hasil Panen Otomatis (ML Linear Regression)"):
    history_df = pd.DataFrame({
        "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
        "Suhu Maks (°C)": [30, 32, 29, 31, 33],
        "Kelembapan (%)": [75, 80, 78, 82, 79],
        "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
    })
    X = history_df[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]]
    y = history_df["Hasil Panen (kg/ha)"]
    model = LinearRegression().fit(X, y)
    X_now = df[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    prediksi = model.predict(X_now)[0]
    st.metric("📈 Prediksi Panen Saat Ini (kg/ha)", f"{prediksi:,.0f}")

# ------------------ CHATBOT PERTANIAN GPT NYATA (OpenAI >= 1.0.0) ------------------
with st.expander("🤖 Tanya Jawab AI GPT Nyata: Asisten Pertanian Lakessi"):
    prompt = st.text_input("Tanya tentang pertanian, pupuk, hama, dll:")
    if prompt:
        if not openai.api_key:
            st.error("⚠️ API Key OpenAI tidak ditemukan! Simpan API key di secrets dengan key 'OPENAI_API_KEY'")
        else:
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Kamu adalah asisten pertanian yang membantu dengan info relevan di Kelurahan Lakessi."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7,
                )
                answer = response.choices[0].message.content
                st.success(f"🧠 Jawaban AI:\n{answer}")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memanggil OpenAI: {e}")

# ------------------ FORM PELAPORAN WARGA ------------------
with st.expander("📝 Form Pelaporan Warga Kelurahan Lakessi"):
    with st.form("laporan_warga_form"):
        nama = st.text_input("Nama Pelapor")
        kontak = st.text_input("Kontak (WhatsApp/HP)")
        jenis_laporan = st.selectbox("Jenis Laporan", ["Masalah Irigasi", "Gangguan Hama", "Kondisi Cuaca", "Lainnya"])
        deskripsi = st.text_area("Deskripsi Singkat")
        lokasi = st.text_input("Lokasi (misal: RT/RW, Blok, Jalan)")
        submit = st.form_submit_button("Kirim Laporan")

        if submit:
            if not nama or not kontak or not deskripsi:
                st.warning("Mohon isi semua kolom wajib: Nama, Kontak, dan Deskripsi.")
            else:
                if "laporan_list" not in st.session_state:
                    st.session_state.laporan_list = []
                laporan_baru = {
                    "Nama": nama,
                    "Kontak": kontak,
                    "Jenis Laporan": jenis_laporan,
                    "Deskripsi": deskripsi,
                    "Lokasi": lokasi,
                    "Status": "Baru"
                }
                st.session_state.laporan_list.append(laporan_baru)
                st.success("✅ Laporan berhasil dikirim! Terima kasih atas partisipasi Anda.")

    if "laporan_list" in st.session_state and st.session_state.laporan_list:
        st.markdown("### Daftar Laporan Warga:")
        for i, lap in enumerate(st.session_state.laporan_list):
            st.markdown(f"**{i+1}. {lap['Jenis Laporan']}** - {lap['Deskripsi']} (oleh {lap['Nama']}, {lap['Kontak']}) - Lokasi: {lap['Lokasi']} - Status: {lap['Status']}")

# ------------------ PENGINGAT TUGAS ------------------
with st.expander("📆 Pengingat Aktivitas Harian"):
    task = st.text_input("➕ Tambahkan Tugas:")
    if "task_list" not in st.session_state:
        st.session_state.task_list = []
    if task and st.button("Simpan"):
        st.session_state.task_list.append(task)
    if st.session_state.task_list:
        for i, t in enumerate(st.session_state.task_list):
            col1, col2 = st.columns([0.9, 0.1])
            col1.markdown(f"- ✅ {t}")
            if col2.button("❌", key=f"hapus_{i}"):
                st.session_state.task_list.pop(i)
                st.experimental_rerun()

# ------------------ HARGA PASAR ------------------
with st.expander("💹 Harga Pasar Komoditas (Dummy)"):
    st.table(pd.DataFrame({
        "Komoditas": ["Gabah Kering", "Jagung", "Beras Medium"],
        "Harga (Rp/kg)": [6500, 5300, 10500]
    }))

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("© 2025 – Kelurahan Lakessi | Dashboard Pertanian Digital by Dian Eka Putra")
