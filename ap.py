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
import pytz
import subprocess
import json
import os
from rapidfuzz import process, fuzz

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
st.title("Dashboard Pertanian Cerdas – Kelurahan Lakessi")
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

# ------------------ PREDIKSI PANEN (Manual + Otomatis) ------------------
with st.expander("Prediksi Panen"):

    # Input manual
    st.subheader("Input Manual")
    ch_manual = st.number_input("Curah Hujan (mm)", value=5.0, key="manual_ch")
    suhu_manual = st.number_input("Suhu Maks (°C)", value=32.0, key="manual_suhu")
    hum_manual = st.number_input("Kelembapan (%)", value=78.0, key="manual_hum")
    luas_manual = st.number_input("Luas Lahan (ha)", value=1.0, key="manual_luas")
    harga_manual = st.number_input("Harga Gabah (Rp/kg)", value=6500, key="manual_harga")

    pred_manual = model.predict([[ch_manual, suhu_manual, hum_manual]])[0]
    total_manual = pred_manual * luas_manual
    pendapatan_manual = total_manual * harga_manual

    # Prediksi otomatis (dari data harian rata-rata)
    st.subheader("Prediksi Otomatis (Berdasarkan Data Cuaca)")
    luas_auto = st.number_input("Luas Sawah (ha) (otomatis)", value=1.0, key="auto_luas")
    harga_auto = st.number_input("Harga Gabah (Rp/kg) (otomatis)", value=6500, key="auto_harga")

    if not df_harian.empty:
        input_auto = df_harian[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
        pred_auto = model.predict(input_auto)[0]
    else:
        pred_auto = 0
    total_auto = pred_auto * luas_auto
    pendapatan_auto = total_auto * harga_auto

    # Proyeksi Panen Tahunan Otomatis (2 Kali Panen)
    st.markdown("### 📆 Proyeksi Panen Tahunan")

    # Gunakan data 7 hari pertama untuk panen 1
    df_panen1 = df_harian.head(7)
    input_panen1 = df_panen1[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    pred1 = model.predict(input_panen1)[0]

    # Gunakan data hari ke-8 sampai ke-14 untuk panen 2 (anggap beda musim)
    df_panen2 = df_harian[7:14] if len(df_harian) >= 14 else df_harian.tail(7)
    input_panen2 = df_panen2[["Curah Hujan (mm)", "Suhu Maks (°C)", "Kelembapan (%)"]].mean().values.reshape(1, -1)
    pred2 = model.predict(input_panen2)[0]

    # Input luas & harga
    luas_ha = st.number_input("Luas Lahan (ha)", value=1.0, key="luas_tahunan")
    harga_rp = st.number_input("Harga Gabah (Rp/kg)", value=6500, key="harga_tahunan")

    # Perhitungan
    total1 = pred1 * luas_ha
    total2 = pred2 * luas_ha
    hasil_total = total1 + total2
    uang_total = hasil_total * harga_rp

    # Tampilkan hasil
    st.write("#### 🌾 Panen Pertama")
    st.write(f"- Prediksi Hasil: {pred1:,.0f} kg/ha | Total: {total1:,.0f} kg | Rp {total1 * harga_rp:,.0f}")

    st.write("#### 🌾 Panen Kedua")
    st.write(f"- Prediksi Hasil: {pred2:,.0f} kg/ha | Total: {total2:,.0f} kg | Rp {total2 * harga_rp:,.0f}")

    st.success(f"🟩 Total Panen Tahunan: {hasil_total:,.0f} kg | Rp {uang_total:,.0f}")

# Tanya Jawab Pertanian Manual
# -------------------- Fungsi Pencarian Jawaban dengan Fuzzy Matching -------------------- #
faq_pairs = [
    # Padi
    ("mengapa padi saya kuning", "Padi kuning biasanya karena kekurangan nitrogen, kurang air, atau serangan hama."),
    ("cara mengatasi padi kuning", "Berikan pupuk nitrogen, perbaiki irigasi, dan cek hama."),
    ("mengapa padi layu", "Layu dapat disebabkan kekurangan air, penyakit layu bakteri, atau akar rusak."),
    ("hama wereng pada padi", "Wereng menghisap getah tanaman dan bisa merusak padi."),
    ("pengendalian hama wereng", "Gunakan insektisida yang tepat dan varietas tahan hama."),
    ("penyakit bercak daun pada padi", "Biasanya disebabkan jamur, gunakan fungisida."),
    ("penyebab padi kerontang", "Kerontang terjadi akibat kurangnya penyerbukan atau kekurangan hara."),
    ("waktu tanam padi terbaik", "Musim hujan biasanya waktu terbaik untuk tanam padi."),
    ("apa itu padi organik", "Padi yang dibudidayakan tanpa bahan kimia sintetis."),
    ("cara meningkatkan hasil panen padi", "Gunakan benih unggul, pupuk tepat, dan pengendalian hama baik."),

    # Jagung
    ("cara menanam jagung", "Pilih lahan bersih, tanam benih unggul, berikan pupuk dan air cukup."),
    ("penyakit hawar daun jagung", "Penyakit jamur yang menyebabkan daun mengering, kendalikan dengan fungisida."),
    ("hama ulat pada jagung", "Ulat memakan daun jagung, kendalikan dengan insektisida atau musuh alami."),
    ("waktu panen jagung", "Panen ketika biji sudah keras dan kering."),

    # Kedelai
    ("cara budidaya kedelai", "Tanam di lahan gembur, berikan pupuk dan air cukup."),
    ("penyakit karat pada kedelai", "Penyakit jamur menyebabkan bercak oranye pada daun."),
    ("hama penggerek batang kedelai", "Serangga yang merusak batang, kendalikan dengan insektisida."),

    # Irigasi & Curah Hujan
    ("apa itu irigasi", "Pengairan lahan untuk memenuhi kebutuhan air tanaman."),
    ("jenis irigasi", "Irigasi tetes, sprinkler, banjir, dan lainnya."),
    ("curah hujan yang ideal untuk padi", "Sekitar 1000-2000 mm/tahun, tergantung varietas."),
    ("cara mengukur curah hujan", "Gunakan alat penakar hujan."),
    ("irigasi tetes", "Memberikan air langsung ke akar dengan jumlah kecil."),

    # Pupuk & Tanah
    ("jenis pupuk untuk padi", "Urea, SP-36, KCl adalah pupuk utama."),
    ("pupuk organik", "Pupuk alami seperti kompos dan pupuk kandang."),
    ("kapan waktu memupuk padi", "Saat umur 20-30 hari dan menjelang berbunga."),
    ("fungsi pupuk N", "Meningkatkan pertumbuhan daun dan batang."),
    ("fungsi pupuk P", "Meningkatkan perkembangan akar dan pembungaan."),
    ("fungsi pupuk K", "Meningkatkan ketahanan tanaman terhadap penyakit."),

    # Hama & Penyakit Umum
    ("jenis hama padi", "Wereng, penggerek batang, kutu daun, tikus."),
    ("cara mengendalikan hama tikus", "Perangkap dan rodentisida aman."),
    ("penyakit blas pada padi", "Penyakit jamur yang menyebabkan bercak hitam pada daun."),
    ("penyakit hawar daun", "Penyakit jamur yang membuat daun mengering dan mati."),
    ("cara mengatasi penyakit tanaman", "Gunakan fungisida dan sanitasi lahan."),

    # Lingkungan & Pengelolaan Lahan
    ("apa itu pertanian berkelanjutan", "Pertanian yang menjaga keseimbangan lingkungan."),
    ("cara mencegah erosi tanah", "Terasering, mulsa, dan penanaman pohon pelindung."),
    ("apa itu agroforestri", "Sistem campuran pohon dan tanaman pertanian."),
    ("cara menjaga kualitas air irigasi", "Hindari pencemaran dan lakukan filtrasi."),
    ("cara mengatasi kekeringan lahan", "Mulsa, irigasi efisien, dan tanaman tahan kekeringan."),

    # Teknik Budidaya & Praktik Terbaik
    ("cara rotasi tanaman", "Ganti tanaman setiap musim untuk mencegah hama dan menjaga tanah."),
    ("manfaat mulsa", "Menjaga kelembaban tanah dan mencegah gulma."),
    ("cara penyiangan gulma", "Manual atau penggunaan herbisida selektif."),
    ("apa itu penanaman serentak", "Menanam pada waktu yang sama untuk mengendalikan hama."),

    # Cuaca & Prediksi Panen
    ("pengaruh suhu terhadap tanaman", "Suhu mempengaruhi fotosintesis dan metabolisme."),
    ("cara memprediksi hasil panen", "Data cuaca, tanah, dan pengelolaan tanaman."),
    ("apa itu kelembapan tanah", "Jumlah air yang tersedia di tanah."),
    ("cara mengukur kelembapan tanah", "Sensor kelembapan atau metode gravimetri."),
    ("pengaruh curah hujan terhadap panen", "Curah hujan cukup penting untuk pertumbuhan."),

    # Variasi typo dan singkatan umum
    ("padi kuning", "Padi kuning biasanya karena kekurangan hara."),
    ("padi layu", "Padi layu bisa karena kekurangan air atau penyakit."),
    ("irigasi", "Irigasi adalah pengairan lahan."),
    ("curah hujan", "Jumlah air hujan di suatu tempat."),
    ("hama padi", "Hama umum padi termasuk wereng dan tikus."),
    ("pupuk padi", "Pupuk utama padi adalah Urea, SP-36, dan KCl."),
    ("kualitas air", "Air harus bersih untuk irigasi."),
    ("penyakit tanaman", "Gunakan fungisida untuk mengatasi penyakit."),
    ("kelembapan tanah", "Kelembapan tanah penting bagi tanaman."),
    ("pengaruh suhu", "Suhu mempengaruhi metabolisme tanaman."),

    # Tambahan umum lain
    ("apa itu penyerbukan", "Proses perpindahan serbuk sari ke kepala putik."),
    ("cara meningkatkan kesuburan tanah", "Tambahkan pupuk organik dan lakukan rotasi tanaman."),
    ("apa itu pupuk hayati", "Pupuk yang mengandung mikroorganisme bermanfaat."),
    ("cara mengatasi kekeringan", "Gunakan mulsa dan irigasi yang tepat."),
    ("apa itu gulma", "Tanaman pengganggu yang bersaing dengan tanaman utama."),
    ("cara pengendalian gulma", "Penyiangan manual atau herbisida."),
    ("apa itu erosi", "Hilangnya lapisan tanah atas oleh air atau angin."),
    ("cara menjaga kelembaban tanah", "Penggunaan mulsa dan irigasi teratur."),
    ("apa itu rehabilitasi lahan", "Pemulihan lahan yang rusak agar dapat produktif kembali."),
    ("cara memanfaatkan limbah pertanian", "Dijadikan kompos atau bahan bakar biomassa."),
    # Padi lanjut
    ("penyebab daun padi berlubang", "Biasanya karena serangan hama penggerek daun atau ulat."),
    ("cara mengatasi daun padi berlubang", "Semprot insektisida dan gunakan varietas tahan hama."),
    ("padi gagal panen", "Bisa karena kekeringan, serangan hama parah, atau penyakit berat."),
    ("penyakit hawar daun", "Penyakit jamur yang menyebabkan daun mengering dan gugur."),
    ("pengendalian penyakit hawar daun", "Gunakan fungisida dan rotasi tanaman."),
    ("kapan pemupukan padi", "Umumnya pada fase vegetatif dan generatif."),
    ("pupuk susulan padi", "Diberikan saat tanaman mulai berbunga agar hasil optimal."),
    ("penyebab padi keriting", "Kekurangan unsur hara atau serangan hama."),
    ("cara mengatasi padi keriting", "Berikan pupuk daun dan kendalikan hama."),
    ("penyebab padi busuk", "Serangan jamur seperti padi bercak dan jamur batang."),
    ("apa itu padi organik", "Padi yang dibudidayakan tanpa pestisida dan pupuk kimia."),
    ("cara tanam padi organik", "Gunakan pupuk organik, pestisida alami, dan pengelolaan tanah baik."),
    ("berat panen padi per hektar", "Rata-rata 5-7 ton gabah kering tergantung varietas dan pengelolaan."),

    # Jagung lanjut
    ("hama wereng jagung", "Wereng jagung menyerang daun dan batang, menyebabkan layu."),
    ("penyakit busuk batang jagung", "Biasanya disebabkan jamur, kendalikan dengan fungisida."),
    ("pupuk terbaik untuk jagung", "Pupuk NPK dan Urea, sesuai kebutuhan tanah."),
    ("kapan panen jagung", "Setelah 90-110 hari setelah tanam tergantung varietas."),
    ("penyebab jagung gagal panen", "Serangan hama, kekurangan air, atau cuaca ekstrem."),

    # Kedelai lanjut
    ("penyebab daun kedelai keriting", "Infeksi virus atau serangan hama."),
    ("cara mengatasi virus pada kedelai", "Gunakan benih sehat dan kendalikan vektor serangga."),
    ("hama kutu daun kedelai", "Kutu daun menyebabkan daun menguning dan rontok."),
    ("waktu tanam kedelai", "Pada musim kemarau awal dengan pengairan memadai."),

    # Irigasi dan pengairan lanjut
    ("apa itu irigasi tetes", "Metode pengairan yang mengalirkan air langsung ke akar."),
    ("keuntungan irigasi tetes", "Hemat air dan mencegah pemborosan."),
    ("irigasi banjir", "Pengairan lahan dengan cara membanjiri seluruh area."),
    ("kapan irigasi dilakukan", "Saat curah hujan kurang dari kebutuhan tanaman."),
    ("cara cek kelembaban tanah", "Gunakan sensor kelembaban atau metode manual seperti cocol tanah."),
    ("irigasi otomatis", "Pengairan yang dikontrol dengan sistem elektronik sesuai kebutuhan tanaman."),
    ("penyebab irigasi tidak merata", "Saluran tersumbat atau desain sistem yang buruk."),
    ("cara memperbaiki saluran irigasi", "Bersihkan dan perbaiki kerusakan fisik saluran."),

    # Curah hujan dan cuaca lanjut
    ("apa itu kelembapan relatif", "Persentase kadar uap air di udara dibandingkan kapasitas maksimum."),
    ("pengaruh curah hujan rendah", "Tanaman bisa stres kekurangan air dan pertumbuhan terganggu."),
    ("curah hujan tinggi berdampak apa", "Bisa menyebabkan genangan dan penyakit jamur."),
    ("alat ukur suhu", "Termometer."),
    ("alat ukur kelembapan", "Higrometer atau sensor kelembapan."),

    # Pupuk dan tanah lanjut
    ("fungsi pupuk organik", "Meningkatkan kesuburan dan struktur tanah."),
    ("pupuk kimia yang umum", "Urea, SP-36, KCl, NPK."),
    ("apa itu pupuk dasar", "Pupuk yang diberikan sebelum tanam."),
    ("apa itu pupuk susulan", "Pupuk yang diberikan setelah tanaman tumbuh."),
    ("tanda kekurangan nitrogen", "Daun menguning terutama daun tua."),
    ("tanda kekurangan fosfor", "Tanaman tumbuh lambat dan warna daun gelap."),
    ("tanda kekurangan kalium", "Daun menguning di tepi dan mudah rusak."),
    ("pengaruh pH tanah", "pH mempengaruhi ketersediaan hara untuk tanaman."),
    ("cara memperbaiki pH tanah asam", "Tambahkan kapur atau dolomit."),

    # Hama & penyakit lanjut
    ("jenis hama tikus", "Tikus sawah, tikus rumah, tikus ladang."),
    ("cara mengendalikan hama tikus", "Perangkap, rodentisida, dan sanitasi lahan."),
    ("penyakit blas", "Penyakit jamur yang menyebabkan bercak hitam."),
    ("penyakit hawar", "Penyakit jamur yang menyebabkan daun layu."),
    ("penyakit bulai", "Penyakit yang menyebabkan bulir kosong."),
    ("pengendalian penyakit", "Gunakan fungisida dan varietas tahan."),
    ("serangga penghisap getah", "Wereng dan kutu daun."),
    ("serangga penggerek batang", "Penggerek batang merusak jaringan dalam tanaman."),

    # Lingkungan & pengelolaan lahan lanjut
    ("apa itu konservasi tanah", "Upaya mencegah erosi dan degradasi tanah."),
    ("cara konservasi tanah", "Terasering, mulsa, penanaman pohon."),
    ("apa itu agroekologi", "Sistem pertanian yang ramah lingkungan."),
    ("pengelolaan limbah pertanian", "Dijadikan kompos atau biogas."),
    ("pengaruh polusi air irigasi", "Merusak tanaman dan mengurangi hasil panen."),

    # Teknik budidaya & praktik terbaik lanjut
    ("apa itu tanam tumpangsari", "Menanam dua jenis tanaman secara bersamaan."),
    ("manfaat tanam tumpangsari", "Mengoptimalkan lahan dan mengendalikan hama."),
    ("apa itu sistem tanam jajar legowo", "Baris tanaman dibuat lebih renggang untuk sirkulasi udara."),
    ("manfaat sistem legowo", "Meningkatkan hasil dan mengurangi penyakit."),
    ("apa itu pemangkasan", "Mengurangi bagian tanaman untuk memperbaiki pertumbuhan."),

    # Cuaca & prediksi lanjut
    ("apa itu indeks panas tanaman", "Pengukuran stres panas pada tanaman."),
    ("cara memprediksi hasil panen", "Menggunakan data cuaca, tanah, dan pemodelan statistik."),
    ("pengaruh angin kencang", "Merusak tanaman dan mempercepat penguapan air."),
    ("pengaruh kelembapan tinggi", "Meningkatkan risiko penyakit jamur."),

    # Terminologi umum & typo tambahan
    ("padi kuneng", "Padi kuning biasanya karena kekurangan hara."),
    ("padi kering", "Bisa disebabkan kekurangan air atau penyakit."),
    ("penyakit padi", "Penyakit umum padi termasuk blas, hawar, dan bulai."),
    ("cara tanam jagung", "Pilih lahan bersih, berikan pupuk, dan siram cukup."),
    ("hama padi wereng", "Wereng adalah hama yang menghisap getah tanaman."),
    ("pupuk urea", "Pupuk nitrogen untuk pertumbuhan vegetatif."),
    ("pupuk sp36", "Pupuk fosfor untuk perkembangan akar."),
    ("kapan panen padi", "Biasanya 3-4 bulan setelah tanam."),
    ("kapan panen jagung", "Setelah 3-4 bulan sesuai varietas."),

    # Tips dan trik
    ("tips menanam padi", "Gunakan benih unggul, jaga irigasi dan kendalikan hama."),
    ("tips irigasi hemat", "Gunakan sistem irigasi tetes atau jadwal irigasi tepat."),
    ("cara menghindari gulma", "Penyiangan rutin dan mulsa."),
    ("cara meningkatkan hasil panen", "Pengelolaan tanah baik, pupuk tepat, dan kendali hama."),
    ("cara mendeteksi penyakit tanaman", "Perhatikan gejala seperti perubahan warna dan tekstur daun."),

    # Tanya umum terkait pertanian
    ("apa itu pertanian modern", "Pertanian yang menggunakan teknologi dan ilmu pengetahuan terkini."),
    ("apa itu smart farming", "Pertanian dengan otomatisasi dan sensor canggih."),
    ("apa itu drone pertanian", "Drone yang digunakan untuk pemantauan dan penyemprotan."),
    ("apa itu hidroponik", "Budidaya tanaman tanpa tanah menggunakan larutan nutrisi."),
    ("apa itu aquaponik", "Sistem gabungan budidaya ikan dan tanaman."),

    # Pertanyaan seputar lingkungan
    ("bagaimana menjaga lingkungan pertanian", "Kurangi penggunaan pestisida, gunakan pupuk organik, dan konservasi air."),
    ("apa itu deforestasi", "Penggundulan hutan yang berdampak buruk pada ekosistem."),
    ("bagaimana perubahan iklim mempengaruhi pertanian", "Cuaca ekstrem dan pola hujan yang tidak menentu dapat merusak tanaman."),

    # Pertanyaan soal peralatan
    ("alat untuk mengukur pH tanah", "pH meter atau kertas lakmus."),
    ("alat pengukur curah hujan", "Penakar hujan."),
    ("alat pengukur kelembapan tanah", "Sensor kelembapan atau tensiometer."),

    # Pertanyaan seputar hasil panen dan pasar
    ("bagaimana menentukan harga gabah", "Bergantung kualitas, pasokan, dan permintaan pasar."),
    ("apa itu gabah kering", "Gabah yang sudah dikeringkan untuk penyimpanan."),

    # Tambahan typo dan variasi bahasa gaul
    ("padi kuneng", "Padi kuning biasanya karena kekurangan hara."),
    ("padi kering banget", "Mungkin tanaman kurang air atau terkena penyakit."),
    ("padi rusak", "Periksa hama dan penyakit serta kondisi air."),
    ("tanem padi gimana", "Gunakan benih bagus, siram teratur, dan pupuk tepat."),
    ("jagung ga tumbuh", "Cek kualitas benih dan kondisi tanah serta air."),
    ("pupuk kurang", "Tanaman akan terlihat layu dan kuning."),

def cari_jawaban(pertanyaan, faq_list, threshold=70):
    pertanyaan = pertanyaan.lower()
    pertanyaan = pertanyaan.strip()
    # Cari pertanyaan paling mirip
    hasil = process.extractOne(pertanyaan, [q for q, _ in faq_list], scorer=fuzz.token_set_ratio)
    if hasil and hasil[1] >= threshold:
        for q, a in faq_list:
            if q == hasil[0]:
                return a
    return "Maaf, saya belum punya jawaban untuk pertanyaan itu. Silakan tanyakan hal lain."

# -------------------- Streamlit Chatbot Interface -------------------- #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🌾 Chatbot FAQ Pertanian (Offline, Gratis)")

user_input = st.text_input("Tanyakan apa saja tentang pertanian, irigasi, cuaca, hama, dan lingkungan:")

if user_input:
    st.session_state.chat_history.append(("🧑", user_input))
    jawaban = cari_jawaban(user_input, faq_pairs)
    st.session_state.chat_history.append(("🤖", jawaban))

for role, msg in st.session_state.chat_history:
    if role == "🧑":
        st.markdown(f"**{role}**: {msg}")
    else:
        st.markdown(f"**{role}**: {msg}")
        
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

# ------------------ LAPORAN WARGA ------------------
LAPORAN_FILE = "laporan_warga.json"

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "laporan" not in st.session_state:
    st.session_state.laporan = load_data(LAPORAN_FILE)

if "laporan_update" not in st.session_state:
    st.session_state.laporan_update = False  # flag untuk rerun laporan

with st.expander("Laporan Warga"):
    with st.form("form_laporan"):
        nama = st.text_input("Nama")
        kontak = st.text_input("Kontak")
        jenis = st.selectbox("Jenis", ["Masalah Irigasi", "Gangguan Hama", "Kondisi Cuaca", "Lainnya"])
        lokasi = st.text_input("Lokasi")
        isi = st.text_area("Deskripsi")
        kirim = st.form_submit_button("Kirim")

        if kirim:
            if nama.strip() and kontak.strip() and isi.strip():
                new_laporan = {
                    "Nama": nama.strip(),
                    "Kontak": kontak.strip(),
                    "Jenis": jenis,
                    "Lokasi": lokasi.strip(),
                    "Deskripsi": isi.strip(),
                    "Tanggal": datetime.now(pytz.timezone("Asia/Makassar")).strftime("%d %B %Y %H:%M")
                }
                st.session_state.laporan.append(new_laporan)
                save_data(LAPORAN_FILE, st.session_state.laporan)
                st.session_state.laporan_update = True
                st.success("Laporan berhasil dikirim.")
            else:
                st.warning("Lengkapi semua isian sebelum mengirim laporan.")

    # Tampilkan laporan warga (di luar form)
    for i, lap in enumerate(st.session_state.laporan):
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(
                f"**{lap['Tanggal']}**  \n"
                f"*{lap['Jenis']}* oleh **{lap['Nama']}**  \n"
                f"{lap['Lokasi']}  \n"
                f"{lap['Deskripsi']}"
            )
        with col2:
            if st.button("🗑️ Hapus", key=f"del_lap_{i}"):
                st.session_state.laporan.pop(i)
                save_data(LAPORAN_FILE, st.session_state.laporan)
                st.session_state.laporan_update = True

# ------------------ PENGINGAT HARIAN ------------------
TODO_FILE = "todo_harian.json"

def load_todo():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_todo(data):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "todo" not in st.session_state:
    st.session_state.todo = load_todo()

if "todo_update" not in st.session_state:
    st.session_state.todo_update = False  # flag untuk rerun todo

with st.expander("Pengingat Harian (To-Do List)"):
    tugas_baru = st.text_input("Tambah Tugas Baru:")
    if st.button("✅ Simpan", key="btn_simpan_tugas"):
        if tugas_baru.strip():
            st.session_state.todo.append(tugas_baru.strip())
            save_todo(st.session_state.todo)
            st.session_state.todo_update = True
        else:
            st.warning("⚠️ Tugas tidak boleh kosong.")

    for i, tugas in enumerate(st.session_state.todo):
        col1, col2 = st.columns([0.9, 0.1])
        col1.markdown(f"- {tugas}")
        if col2.button("🗑️ Hapus", key=f"hapus_todo_{i}"):
            st.session_state.todo.pop(i)
            save_todo(st.session_state.todo)
            st.session_state.todo_update = True

# Panggil rerun sekali jika ada update di laporan atau todo
# Panggil rerun sekali jika ada update di laporan atau todo
if st.session_state.laporan_update or st.session_state.todo_update:
    st.session_state.laporan_update = False
    st.session_state.todo_update = False
    try:
        st.runtime.scriptrunner.request_rerun()
    except Exception as e:
        st.error(f"Terjadi error saat reload: {e}")

# Footer
st.markdown("---")
st.caption("© 2025 – Kelurahan Lakessi | Dashboard Pertanian Digital oleh Dian Eka Putra")
