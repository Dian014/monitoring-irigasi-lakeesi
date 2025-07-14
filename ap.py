import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
import numpy as np

# ------------------ KONFIGURASI ------------------
st.set_page_config(
    page_title="🌾 Dashboard Cerdas Pertanian Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ JUDUL ------------------
st.title("Dashboard Pertanian Cerdas – Kelurahan Lakessi")
st.markdown("""
📍 *Lokasi: Kelurahan Lakessi, Kecamatan Maritengngae, Sidrap, Sulawesi Selatan*  
🧑‍💻 *Pengembang: Dian Eka Putra* | 📧 ekaputradian01@gmail.com | 📱 085654073752  
""")

# ------------------ KOORDINAT ------------------
LAT, LON = -3.947760, 119.810237

# ------------------ PETA CURAH HUJAN ------------------
with st.expander("🌧️ Peta Curah Hujan Real-time (OpenWeatherMap)"):
    m = folium.Map(location=[LAT, LON], zoom_start=13, control_scale=True)
    OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")
    if OWM_API_KEY:
        tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
        folium.TileLayer(tiles=tile_url, attr="© OpenWeatherMap", name="Curah Hujan", overlay=True, control=True, opacity=0.6).add_to(m)
        folium.Marker([LAT, LON], tooltip="📍 Kelurahan Lakessi").add_to(m)
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
    st.dataframe(df.style.apply(highlight_irigasi, axis=1), use_container_width=True)
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

# ------------------ HITUNG PENDAPATAN MANUAL ------------------
with st.expander("💰 Simulasi Pendapatan Berdasarkan Data Manual"):
    curah = st.number_input("Curah Hujan (mm)", value=5.0)
    suhu = st.number_input("Suhu Maks (°C)", value=31.0)
    kelembaban = st.number_input("Kelembapan (%)", value=80.0)
    luas = st.number_input("Luas Lahan (ha)", value=1.0)
    harga = st.number_input("Harga Gabah (Rp/kg)", value=6500)
    pred_manual = model.predict(np.array([[curah, suhu, kelembaban]]))[0]
    total_produksi = pred_manual * luas
    pendapatan = total_produksi * harga
    st.metric("🌾 Estimasi Panen", f"{pred_manual:,.0f} kg/ha")
    st.metric("📦 Total Produksi", f"{total_produksi:,.0f} kg")
    st.success(f"💵 Estimasi Pendapatan: Rp {pendapatan:,.0f}")

# ------------------ ANALISIS RISIKO HAMA ------------------
with st.expander("🦠 Prediksi Risiko Serangan Hama & Penyakit"):
    for _, row in df.iterrows():
        risiko = []
        if row["Kelembapan (%)"] > 85 and row["Suhu Maks (°C)"] > 30:
            risiko.append("⚠️ Potensi tinggi hawar daun bakteri")
        if row["Curah Hujan (mm)"] > 10 and row["Kelembapan (%)"] > 80:
            risiko.append("⚠️ Waspadai jamur & blas")
        if not risiko:
            risiko.append("✅ Aman")
        st.markdown(f"{row['Tanggal'].date()}: {'; '.join(risiko)}")

# ------------------ REKOMENDASI PEMUPUKAN ------------------
with st.expander("🧪 Rekomendasi Jadwal & Jenis Pemupukan"):
    st.markdown("""
    💡 **Pupuk Dasar (Urea, TSP, KCl):** 7 hari setelah tanam  
    💡 **Pupuk Susulan I:** 21 HST – cocok saat suhu tinggi & curah rendah  
    💡 **Pupuk Susulan II:** 35–40 HST – sesuaikan kelembapan tanah  
    """)

# ------------------ CEK KONDISI TANAMAN ------------------
with st.expander("🌿 Diagnosa Kesehatan Tanaman Manual"):
    warna = st.selectbox("🟢 Warna Daun", ["Hijau segar", "Kuning pucat", "Coklat", "Bercak putih"])
    tinggi = st.number_input("📏 Tinggi Tanaman (cm)", value=50)
    gejala = st.text_area("🩺 Gejala Lain (Opsional)")

    if warna != "Hijau segar":
        st.warning("⚠️ Daun tidak sehat. Periksa unsur hara & hama.")
    elif tinggi < 30:
        st.info("ℹ️ Pertumbuhan lambat. Evaluasi irigasi & pupuk.")
    else:
        st.success("✅ Tanaman sehat.")

# ------------------ TIPS PERTANIAN HARIAN ------------------
with st.expander("🧠 Tips Harian Otomatis Berdasarkan Cuaca"):
    for _, row in df.iterrows():
        tips = []
        if row["Curah Hujan (mm)"] < threshold:
            tips.append("Periksa kelembaban tanah")
        if row["Suhu Maks (°C)"] > 33:
            tips.append("Waspadai stres panas pada tanaman")
        if row["Kelembapan (%)"] > 85:
            tips.append("Waspadai jamur dan bakteri")
        if not tips:
            tips.append("Cuaca ideal untuk pertumbuhan")
        st.markdown(f"📅 {row['Tanggal'].date()}: {'; '.join(tips)}")

# ------------------ PENGINGAT TUGAS PETANI ------------------
with st.expander("📆 Pengingat Aktivitas Harian"):
    task = st.text_input("➕ Tambahkan Tugas:")
    if "task_list" not in st.session_state:
        st.session_state.task_list = []
    if st.button("Simpan"):
        if task:
            st.session_state.task_list.append(task)
    for t in st.session_state.task_list:
        st.markdown(f"- ✅ {t}")

# ------------------ HARGA PASAR ------------------
with st.expander("💹 Harga Pasar Komoditas (Dummy)"):
    st.table(pd.DataFrame({
        "Komoditas": ["Gabah Kering", "Jagung", "Beras Medium"],
        "Harga (Rp/kg)": [6500, 5300, 10500]
    }))

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("© 2025 – Kelurahan Lakessi | Dashboard Pertanian Digital by Dian Eka Putra")
