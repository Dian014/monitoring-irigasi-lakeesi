import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
import numpy as np

# ------------------ KONFIGURASI AWAL ------------------
st.set_page_config(
    page_title="Sistem Pertanian Cerdas Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ INPUT KOORDINAT DINAMIS ------------------
LAT = st.sidebar.number_input("Latitude", value=-3.921406, format="%.6f")
LON = st.sidebar.number_input("Longitude", value=119.772731, format="%.6f")

# ------------------ HEADER ------------------
st.title("\ud83c\udf31 Sistem Monitoring Irigasi & Pertanian Lakessi")
st.markdown("""
\ud83d\udccd Kelurahan Lakessi, Maritengngae, Sidrap – Sulawesi Selatan  
\ud83e\uddd1‍\ud83d\udcbb *Dikembangkan oleh Dian Eka Putra* | \ud83d\udce7 ekaputradian01@gmail.com | \ud83d\udcf1 085654073752
""")

# ------------------ PETA CURAH HUJAN ------------------
with st.expander("\ud83d\uddfa\ufe0f Peta Curah Hujan Real-time"):
    m = folium.Map(location=[LAT, LON], zoom_start=13, control_scale=True)
    OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")
    if OWM_API_KEY:
        tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
        folium.TileLayer(tiles=tile_url, attr="© OpenWeatherMap", name="Curah Hujan", overlay=True, control=True, opacity=0.6).add_to(m)
    folium.Marker([LAT, LON], tooltip="\ud83d\udccd Lokasi Terpilih").add_to(m)
    st_folium(m, width="100%", height=400)

# ------------------ DATA CUACA ------------------
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}&"
    "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    "hourly=temperature_2m,precipitation,relative_humidity_2m&timezone=auto"
)
resp = requests.get(weather_url)
data = resp.json()

# ------------------ DATAFRAME ------------------
df_harian = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": np.round(data["daily"]["precipitation_sum"], 1),
    "Suhu Maks (\u00b0C)": np.round(data["daily"]["temperature_2m_max"], 1),
    "Suhu Min (\u00b0C)": np.round(data["daily"]["temperature_2m_min"], 1),
    "Kelembapan (%)": np.round(data["daily"]["relative_humidity_2m_mean"], 1)
})

threshold = st.sidebar.slider("\ud83d\udca7 Batas Curah Hujan untuk Irigasi (mm):", 0, 20, 5)
df_harian["Rekomendasi Irigasi"] = df_harian["Curah Hujan (mm)"].apply(lambda x: "\ud83d\udebf Irigasi Diperlukan" if x < threshold else "\u2705 Cukup")

# ------------------ GRAFIK ------------------
with st.expander("\ud83d\udcca Grafik Harian"):
    st.plotly_chart(px.bar(df_harian, x="Tanggal", y="Curah Hujan (mm)", title="Curah Hujan Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Maks (°C)", title="Suhu Maksimum Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Min (°C)", title="Suhu Minimum Harian"), use_container_width=True)

# ------------------ DATA PER JAM ------------------
df_jam = pd.DataFrame({
    "Waktu": pd.to_datetime(data["hourly"]["time"]),
    "Curah Hujan (mm)": data["hourly"]["precipitation"],
    "Suhu (\u00b0C)": data["hourly"]["temperature_2m"],
    "Kelembapan (%)": data["hourly"]["relative_humidity_2m"]
})

with st.expander("\ud83d\udcc9 Grafik Per Jam"):
    st.plotly_chart(px.line(df_jam.tail(48), x="Waktu", y="Curah Hujan (mm)", title="Curah Hujan per Jam"), use_container_width=True)
    st.plotly_chart(px.line(df_jam.tail(48), x="Waktu", y="Suhu (°C)", title="Suhu per Jam"), use_container_width=True)

# ------------------ TABEL ------------------
with st.expander("\ud83d\udccb Data Harian"):
    st.dataframe(df_harian, use_container_width=True)

with st.expander("\ud83d\udcca Data Per Jam (48 jam terakhir)"):
    st.dataframe(df_jam.tail(48), use_container_width=True)

# ------------------ PREDIKSI OTOMATIS ------------------
model_df = pd.DataFrame({
    "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
    "Suhu (\u00b0C)": [30, 32, 29, 31, 33],
    "Kelembapan (%)": [75, 80, 78, 82, 79],
    "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
})
model = LinearRegression().fit(model_df.drop("Hasil Panen (kg/ha)", axis=1), model_df["Hasil Panen (kg/ha)"])
input_now = df_harian[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
hasil = model.predict(input_now)[0]

with st.expander("\ud83e\ude32 Prediksi Panen Otomatis"):
    luas_sawah = st.number_input("Luas Sawah (ha)", value=1.0)
    harga_gabah = st.number_input("Harga Gabah (Rp/kg)", value=6500)
    total_kg = hasil * luas_sawah
    total_rp = total_kg * harga_gabah
    st.metric("Prediksi Panen", f"{hasil:,.0f} kg/ha")
    st.success(f"Total: {total_kg:,.0f} kg | Rp {total_rp:,.0f}")

# ------------------ PERHITUNGAN MANUAL ------------------
with st.expander("\ud83d\udd8b\ufe0f Hitung Manual Prediksi Panen"):
    ch = st.number_input("Curah Hujan (mm)", value=5.0)
    suhu = st.number_input("Suhu Maks (\u00b0C)", value=32.0)
    hum = st.number_input("Kelembapan (%)", value=78.0)
    luas = st.number_input("Luas Lahan (ha)", value=1.0, key="manual_luas")
    harga = st.number_input("Harga Gabah (Rp/kg)", value=6500, key="manual_harga")

    pred_manual = model.predict([[ch, suhu, hum]])[0]
    total_manual = pred_manual * luas
    pendapatan_manual = total_manual * harga

    st.metric("Prediksi Panen Manual", f"{pred_manual:,.0f} kg/ha")
    st.success(f"Total: {total_manual:,.0f} kg | Rp {pendapatan_manual:,.0f}")

# ------------------ FORM TANYA JAWAB ------------------
with st.expander("\ud83d\udcac Tanya Jawab Pertanian (Manual)"):
    pertanyaan = st.text_input("Masukkan pertanyaan Anda:")
    if pertanyaan:
        st.info("(Simulasi Jawaban) Fitur OpenAI dimatikan untuk versi gratis. Jawaban disesuaikan manual oleh tim pertanian.")
        st.write("Contoh jawaban: Gunakan pupuk urea pada masa pertumbuhan vegetatif untuk mendorong perkembangan daun.")

# ------------------ FORM PELAPORAN ------------------
with st.expander("\ud83d\udcdd Laporan Warga"):
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
            st.session_state.laporan.append({"Nama": nama, "Kontak": kontak, "Jenis": jenis, "Lokasi": lokasi, "Deskripsi": isi})
            st.success("\u2705 Laporan terkirim!")
    if "laporan" in st.session_state:
        for i, lap in enumerate(st.session_state.laporan):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"**{lap['Jenis']}**: {lap['Deskripsi']} oleh {lap['Nama']} – Lokasi: {lap['Lokasi']}")
            with col2:
                if st.button("\u274c", key=f"del_lap_{i}"):
                    st.session_state.laporan.pop(i)
                    st.experimental_rerun()

# ------------------ TO-DO ------------------
with st.expander("\ud83d\udcc6 Pengingat Harian"):
    tugas = st.text_input("Tambah tugas:")
    if "todo" not in st.session_state:
        st.session_state.todo = []
    if tugas and st.button("Simpan"):
        st.session_state.todo.append(tugas)
    for i, t in enumerate(st.session_state.todo):
        col1, col2 = st.columns([0.9, 0.1])
        col1.markdown(f"- {t}")
        if col2.button("\u274c", key=f"hapus_todo_{i}"):
            st.session_state.todo.pop(i)
            st.experimental_rerun()

# ------------------ HARGA KOMODITAS ------------------
with st.expander("\ud83d\udcc9 Harga Komoditas"):
    st.table(pd.DataFrame({
        "Komoditas": ["Gabah Kering", "Jagung", "Beras Medium"],
        "Harga (Rp/kg)": [6500, 5300, 10500]
    }))

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("\u00a9 2025 – Kelurahan Lakessi | Dashboard Pertanian Digital oleh Dian Eka Putra")
