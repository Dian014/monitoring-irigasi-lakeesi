import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
from io import BytesIO
import base64
from datetime import datetime
import subprocess
import json

# ------------------ KONFIGURASI AWAL ------------------
st.set_page_config(
    page_title="Sistem Pertanian Cerdas Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ INPUT KOORDINAT ------------------
LAT = st.sidebar.number_input("Latitude", value=-3.921406, format="%.6f")
LON = st.sidebar.number_input("Longitude", value=119.772731, format="%.6f")

# ------------------ HEADER ------------------
st.title("Sistem Monitoring Irigasi & Pertanian Lakessi")
st.markdown("""
Lokasi: Kelurahan Lakessi, Maritengngae, Sidrap – Sulawesi Selatan  
Dikembangkan oleh Dian Eka Putra | Email: ekaputradian01@gmail.com | WA: 085654073752
""")

# ------------------ PETA CURAH HUJAN ------------------
with st.expander("Peta Curah Hujan Real-time"):
    m = folium.Map(location=[LAT, LON], zoom_start=13, control_scale=True)
    OWM_API_KEY = st.secrets.get("OWM_API_KEY", "")
    if OWM_API_KEY:
        tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}"
        folium.TileLayer(
            tiles=tile_url, attr="© OpenWeatherMap",
            name="Curah Hujan", overlay=True, control=True, opacity=0.6
        ).add_to(m)
    folium.Marker([LAT, LON], tooltip="Lokasi Terpilih").add_to(m)
    st_folium(m, width="100%", height=400)

# ------------------ AMBIL DATA CUACA ------------------
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}&"
    "daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&"
    "hourly=temperature_2m,precipitation,relative_humidity_2m&timezone=auto"
)
resp = requests.get(weather_url)
data = resp.json()

# ------------------ DATAFRAME HARIAN ------------------
df_harian = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": np.round(data["daily"]["precipitation_sum"], 1),
    "Suhu Maks (°C)": np.round(data["daily"]["temperature_2m_max"], 1),
    "Suhu Min (°C)": np.round(data["daily"]["temperature_2m_min"], 1),
    "Kelembapan (%)": np.round(data["daily"]["relative_humidity_2m_mean"], 1)
})

threshold = st.sidebar.slider("Batas Curah Hujan untuk Irigasi (mm):", 0, 20, 5)
df_harian["Rekomendasi Irigasi"] = df_harian["Curah Hujan (mm)"].apply(
    lambda x: "Irigasi Diperlukan" if x < threshold else "Cukup"
)

# ------------------ TAMPILKAN TABEL DATA ------------------
with st.expander("Tabel Data Cuaca Harian"):
    st.dataframe(df_harian, use_container_width=True)

    # Export CSV
    csv = df_harian.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "data_cuaca_harian.csv", "text/csv")

        # Export Excel (pakai xlsxwriter)
    excel_io = BytesIO()
    with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
        df_harian.to_excel(writer, index=False, sheet_name="Cuaca Harian")
        workbook  = writer.book
        worksheet = writer.sheets["Cuaca Harian"]
        # Set lebar kolom tanggal dan format tanggal
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        worksheet.set_column('A:A', 15, date_format)
    excel_io.seek(0)
    st.download_button("Download Excel", data=excel_io.read(), file_name="data_cuaca_harian.xlsx")

    # Export PDF (ubah jadi download file HTML saja agar tidak error)
    pdf_html = df_harian.to_html(index=False)
    b64 = base64.b64encode(pdf_html.encode("utf-8")).decode("utf-8")
    href = f'<a href="data:text/html;base64,{b64}" download="laporan_cuaca_harian.html">📥 Download Laporan (HTML)</a>'
    st.markdown(href, unsafe_allow_html=True)


# ------------------ DATAFRAME PER JAM ------------------
df_jam = pd.DataFrame({
    "Waktu": pd.to_datetime(data["hourly"]["time"]),
    "Curah Hujan (mm)": data["hourly"]["precipitation"],
    "Suhu (°C)": data["hourly"]["temperature_2m"],
    "Kelembapan (%)": data["hourly"]["relative_humidity_2m"]
})

# ------------------ TAMPILKAN GRAFIK ------------------
with st.expander("Grafik Harian"):
    st.plotly_chart(px.bar(df_harian, x="Tanggal", y="Curah Hujan (mm)", title="Curah Hujan Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Maks (°C)", title="Suhu Maksimum Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Min (°C)", title="Suhu Minimum Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Kelembapan (%)", title="Kelembapan Harian"), use_container_width=True)

from datetime import datetime as dt

# ------------------ GRAFIK JAM KE DEPAN ------------------
df_jam_prediksi = df_jam[df_jam["Waktu"] > dt.now()].head(48)
with st.expander("Grafik Per Jam (48 Jam Ke Depan)"):
    if df_jam_prediksi.empty:
        st.warning("Tidak ada data prediksi ke depan tersedia saat ini.")
    else:
        st.plotly_chart(px.line(df_jam_prediksi, x="Waktu", y="Curah Hujan (mm)", title="Prediksi Curah Hujan per Jam (48 Jam Ke Depan)"), use_container_width=True)
        st.plotly_chart(px.line(df_jam_prediksi, x="Waktu", y="Suhu (°C)", title="Prediksi Suhu per Jam (48 Jam Ke Depan)"), use_container_width=True)
        st.plotly_chart(px.line(df_jam_prediksi, x="Waktu", y="Kelembapan (%)", title="Prediksi Kelembapan per Jam (48 Jam Ke Depan)"), use_container_width=True)

# ------------------ MODEL PREDIKSI ------------------
model_df = pd.DataFrame({
    "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
    "Suhu (°C)": [30, 32, 29, 31, 33],
    "Kelembapan (%)": [75, 80, 78, 82, 79],
    "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
})
model = LinearRegression().fit(
    model_df.drop("Hasil Panen (kg/ha)", axis=1), model_df["Hasil Panen (kg/ha)"]
)

if not df_harian.empty:
    input_now = df_harian[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    hasil = model.predict(input_now)[0]
else:
    hasil = 0

# ------------------ PREDIKSI PANEN OTOMATIS ------------------
with st.expander("Prediksi Panen Otomatis"):
    luas_sawah = st.number_input("Luas Sawah (ha)", value=1.0, key="luas_sawah")
    harga_gabah = st.number_input("Harga Gabah (Rp/kg)", value=6500, key="harga_gabah")
    total_kg = hasil * luas_sawah
    total_rp = total_kg * harga_gabah
    st.metric("Prediksi Panen (kg/ha)", f"{hasil:,.0f}")
    st.success(f"Total Panen: {total_kg:,.0f} kg | Perkiraan Pendapatan: Rp {total_rp:,.0f}")

    pred_mingguan = hasil * 7 * luas_sawah
    pred_bulanan = hasil * 30 * luas_sawah
    pendapatan_mingguan = pred_mingguan * harga_gabah
    pendapatan_bulanan = pred_bulanan * harga_gabah

    st.write("### Proyeksi Panen Lebih Panjang:")
    st.write(f"- Mingguan: {pred_mingguan:,.0f} kg | Rp {pendapatan_mingguan:,.0f}")
    st.write(f"- Bulanan: {pred_bulanan:,.0f} kg | Rp {pendapatan_bulanan:,.0f}")

# Tanya Jawab Pertanian Manual
st.markdown("---")
st.title("Tanya Jawab Pertanian")

faq_dict = {
    "Apa solusi hama wereng pada padi?": "Gunakan insektisida berbahan aktif imidakloprid secara teratur dan pantau populasi hama secara berkala.",
    "Kapan waktu terbaik untuk tanam padi?": "Waktu terbaik adalah awal musim hujan, sekitar Oktober-November.",
    "Apa yang harus dilakukan saat curah hujan tinggi?": "Pastikan drainase sawah baik dan hindari pemupukan saat hujan deras.",
    "Apa jenis pupuk terbaik untuk padi?": "Gunakan kombinasi Urea, SP-36 dan KCl dengan dosis sesuai fase pertumbuhan.",
    "Bagaimana cara mengatasi tanah asam?": "Gunakan kapur dolomit untuk menetralkan pH tanah.",
    "Bagaimana cara meningkatkan hasil panen?": "Gunakan benih unggul, pupuk berimbang, dan lakukan pengendalian hama terpadu."
}

pertanyaan_manual = st.text_input("Tulis pertanyaan Anda:")
if st.button("Jawab Pertanyaan"):
    jawaban = faq_dict.get(pertanyaan_manual.strip(), "Maaf, jawaban belum tersedia dalam basis data. Silakan konsultasi dengan penyuluh pertanian setempat.")
    st.success("Jawaban:")
    st.write(jawaban)

# Fitur Tambahan: Kalkulator Pupuk
with st.expander("Kalkulator Pemupukan Dasar"):
    tanaman = st.selectbox("Jenis Tanaman", ["Padi", "Jagung", "Kedelai"])
    luas_lahan = st.number_input("Luas Lahan (ha)", value=1.0, key="pupuk_luas")

    dosis = {
        "Padi": {"Urea": 250, "SP-36": 100, "KCl": 100},
        "Jagung": {"Urea": 300, "SP-36": 150, "KCl": 100},
        "Kedelai": {"Urea": 100, "SP-36": 100, "KCl": 75},
    }
    pupuk = dosis[tanaman]
    st.write("### Kebutuhan Pupuk per Jenis:")
    for jenis, kg_per_ha in pupuk.items():
        total_kg = kg_per_ha * luas_lahan
        st.write(f"- {jenis}: {total_kg} kg")

# Perhitungan manual prediksi panen
with st.expander("Hitung Manual Prediksi Panen"):
    ch = st.number_input("Curah Hujan (mm)", value=5.0, key="manual_ch")
    suhu = st.number_input("Suhu Maks (°C)", value=32.0, key="manual_suhu")
    hum = st.number_input("Kelembapan (%)", value=78.0, key="manual_hum")
    luas = st.number_input("Luas Lahan (ha)", value=1.0, key="manual_luas")
    harga = st.number_input("Harga Gabah (Rp/kg)", value=6500, key="manual_harga")

    pred_manual = model.predict([[ch, suhu, hum]])[0]
    total_manual = pred_manual * luas
    pendapatan_manual = total_manual * harga

    st.metric("Prediksi Panen Manual (kg/ha)", f"{pred_manual:,.0f}")
    st.success(f"Total: {total_manual:,.0f} kg | Rp {pendapatan_manual:,.0f}")

with st.expander("Laporan Warga"):
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
                "Nama": nama,
                "Kontak": kontak,
                "Jenis": jenis,
                "Lokasi": lokasi,
                "Deskripsi": isi,
                "Tanggal": datetime.now().strftime("%d %B %Y %H:%M")
            })
            st.success("Laporan terkirim!")

    if "laporan" in st.session_state:
        for i, lap in enumerate(st.session_state.laporan):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(
                    f"{lap['Tanggal']}**  \n"
                    f"{lap['Jenis']}: {lap['Deskripsi']} oleh *{lap['Nama']}* – Lokasi: {lap['Lokasi']}"
                )
            with col2:
                if st.button("Hapus", key=f"del_lap_{i}"):
                    st.session_state.laporan.pop(i)
                    st.experimental_rerun()

# Pengingat harian (to-do)
with st.expander("Pengingat Harian"):
    tugas = st.text_input("Tambah tugas:")
    if "todo" not in st.session_state:
        st.session_state.todo = []
    if tugas and st.button("Simpan", key="btn_simpan_tugas"):
        st.session_state.todo.append(tugas)
    for i, t in enumerate(st.session_state.todo):
        col1, col2 = st.columns([0.9, 0.1])
        col1.markdown(f"- {t}")
        if col2.button("Hapus", key=f"hapus_todo_{i}"):
            st.session_state.todo.pop(i)
            st.experimental_rerun()

# Harga komoditas
with st.expander("Harga Komoditas"):
    st.table(pd.DataFrame({
        "Komoditas": ["Gabah Kering", "Jagung", "Beras Medium"],
        "Harga (Rp/kg)": [6500, 5300, 10500]
    }))

# ------------------ TIPS PERTANIAN ------------------
with st.expander("Tips Pertanian Harian Otomatis"):
    for _, row in df_harian.iterrows():
        tips = []
        if row["Curah Hujan (mm)"] < threshold:
            tips.append("Lakukan irigasi untuk menjaga kelembaban tanah")
        if row["Suhu Maks (°C)"] > 33:
            tips.append("Waspadai stres panas pada padi")
        if row["Kelembapan (%)"] > 85:
            tips.append("Tingkatkan kewaspadaan terhadap penyakit jamur")
        if not tips:
            tips.append("Kondisi ideal untuk pertumbuhan padi")
        st.markdown(f" {row['Tanggal'].date()}: {'; '.join(tips)}")

# Footer
st.markdown("---")
st.caption("© 2025 – Kelurahan Lakessi | Dashboard Pertanian Digital oleh Dian Eka Putra")
