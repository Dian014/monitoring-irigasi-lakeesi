import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
from io import BytesIO
from datetime import timedelta
import base64

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
        folium.TileLayer(tiles=tile_url, attr="© OpenWeatherMap", name="Curah Hujan", overlay=True, control=True, opacity=0.6).add_to(m)
    folium.Marker([LAT, LON], tooltip="Lokasi Terpilih").add_to(m)
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
    "Suhu Maks (°C)": np.round(data["daily"]["temperature_2m_max"], 1),
    "Suhu Min (°C)": np.round(data["daily"]["temperature_2m_min"], 1),
    "Kelembapan (%)": np.round(data["daily"]["relative_humidity_2m_mean"], 1)
})

threshold = st.sidebar.slider("Batas Curah Hujan untuk Irigasi (mm):", 0, 20, 5)
df_harian["Rekomendasi Irigasi"] = df_harian["Curah Hujan (mm)"].apply(lambda x: "Irigasi Diperlukan" if x < threshold else "Cukup")

df_jam = pd.DataFrame({
    "Waktu": pd.to_datetime(data["hourly"]["time"]),
    "Curah Hujan (mm)": data["hourly"]["precipitation"],
    "Suhu (°C)": data["hourly"]["temperature_2m"],
    "Kelembapan (%)": data["hourly"]["relative_humidity_2m"]
})

# ------------------ MODEL PREDIKSI ------------------
model_df = pd.DataFrame({
    "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
    "Suhu (°C)": [30, 32, 29, 31, 33],
    "Kelembapan (%)": [75, 80, 78, 82, 79],
    "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
})
model = LinearRegression().fit(model_df.drop("Hasil Panen (kg/ha)", axis=1), model_df["Hasil Panen (kg/ha)"])

# Pastikan df_harian tidak kosong untuk prediksi
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

    # Prediksi mingguan dan bulanan (proyeksi sederhana)
    pred_mingguan = hasil * 7 * luas_sawah
    pred_bulanan = hasil * 30 * luas_sawah
    pendapatan_mingguan = pred_mingguan * harga_gabah
    pendapatan_bulanan = pred_bulanan * harga_gabah

    st.write("### Proyeksi Panen Lebih Panjang:")
    st.write(f"- Mingguan: {pred_mingguan:,.0f} kg | Rp {pendapatan_mingguan:,.0f}")
    st.write(f"- Bulanan: {pred_bulanan:,.0f} kg | Rp {pendapatan_bulanan:,.0f}")

    # ------------------ SIMPAN DAN EKSPOR ------------------
    if st.button("💾 Simpan Hasil Prediksi ke Session"):
        st.session_state["prediksi"] = {
            "tanggal": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hasil_kg_per_ha": hasil,
            "luas_sawah": luas_sawah,
            "harga_gabah": harga_gabah,
            "total_kg": total_kg,
            "total_rp": total_rp,
            "mingguan_kg": pred_mingguan,
            "mingguan_rp": pendapatan_mingguan,
            "bulanan_kg": pred_bulanan,
            "bulanan_rp": pendapatan_bulanan
        }
        st.success("Hasil prediksi disimpan!")

    if "prediksi" in st.session_state:
        df_pred = pd.DataFrame([st.session_state["prediksi"]])
        st.write("### Data Prediksi Tersimpan")
        st.dataframe(df_pred)

        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Prediksi')
            writer.save()
            processed_data = output.getvalue()
            return processed_data

        def get_table_download_link(df):
            val = to_excel(df)
            b64 = base64.b64encode(val).decode()  # encode to base64
            return f'<a href="data:application/octet-stream;base64,{b64}" download="prediksi_panen.xlsx">📥 Unduh Excel</a>'

        st.markdown(get_table_download_link(df_pred), unsafe_allow_html=True)

        # Export PDF sederhana menggunakan reportlab
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            if st.button("📤 Unduh PDF"):
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                c.drawString(100, 750, "Laporan Prediksi Panen")
                c.drawString(100, 730, f"Tanggal: {st.session_state['prediksi']['tanggal']}")
                c.drawString(100, 710, f"Prediksi (kg/ha): {st.session_state['prediksi']['hasil_kg_per_ha']:.0f}")
                c.drawString(100, 690, f"Luas Sawah (ha): {st.session_state['prediksi']['luas_sawah']}")
                c.drawString(100, 670, f"Harga Gabah (Rp/kg): {st.session_state['prediksi']['harga_gabah']}")
                c.drawString(100, 650, f"Total Panen (kg): {st.session_state['prediksi']['total_kg']:.0f}")
                c.drawString(100, 630, f"Total Pendapatan (Rp): {st.session_state['prediksi']['total_rp']:.0f}")
                c.drawString(100, 610, f"Proyeksi Mingguan (kg): {st.session_state['prediksi']['mingguan_kg']:.0f}")
                c.drawString(100, 590, f"Proyeksi Bulanan (kg): {st.session_state['prediksi']['bulanan_kg']:.0f}")
                c.showPage()
                c.save()
                pdf = buffer.getvalue()
                buffer.close()

                b64_pdf = base64.b64encode(pdf).decode()
                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="prediksi_panen.pdf">📥 Unduh PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
        except ImportError:
            st.warning("Library 'reportlab' belum terpasang, install untuk fitur PDF export.")

# ------------------ PERHITUNGAN MANUAL ------------------
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

# ------------------ TANYA JAWAB MANUAL ------------------
with st.expander("Tanya Jawab Pertanian (Manual)"):
    pertanyaan = st.text_input("Masukkan pertanyaan Anda:")
    if pertanyaan:
        st.info("(Jawaban disesuaikan manual oleh tim pertanian)")
        st.write("Contoh jawaban: Gunakan pupuk urea saat pertumbuhan vegetatif untuk memperkuat batang.")

# ------------------ LAPORAN WARGA ------------------
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
                "Nama": nama, "Kontak": kontak, "Jenis": jenis, "Lokasi": lokasi, "Deskripsi": isi
            })
            st.success("Laporan terkirim!")
    if "laporan" in st.session_state:
        for i, lap in enumerate(st.session_state.laporan):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"{lap['Jenis']}: {lap['Deskripsi']} oleh {lap['Nama']} – Lokasi: {lap['Lokasi']}")
            with col2:
                if st.button("Hapus", key=f"del_lap_{i}"):
                    st.session_state.laporan.pop(i)
                    st.experimental_rerun()

# ------------------ TO-DO ------------------
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

# ------------------ HARGA KOMODITAS ------------------
with st.expander("Harga Komoditas"):
    st.table(pd.DataFrame({
        "Komoditas": ["Gabah Kering", "Jagung", "Beras Medium"],
        "Harga (Rp/kg)": [6500, 5300, 10500]
    }))

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("© 2025 – Kelurahan Lakessi | Dashboard Pertanian Digital oleh Dian Eka Putra")
