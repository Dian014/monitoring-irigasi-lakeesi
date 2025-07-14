import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
import numpy as np
import io

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

# Data per jam
df_jam = pd.DataFrame({
    "Waktu": pd.to_datetime(data["hourly"]["time"]),
    "Curah Hujan (mm)": data["hourly"]["precipitation"],
    "Suhu (°C)": data["hourly"]["temperature_2m"],
    "Kelembapan (%)": data["hourly"]["relative_humidity_2m"]
})

# ------------------ GRAFIK ------------------
with st.expander("Grafik Harian"):
    st.plotly_chart(px.bar(df_harian, x="Tanggal", y="Curah Hujan (mm)", title="Curah Hujan Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Maks (°C)", title="Suhu Maksimum Harian"), use_container_width=True)
    st.plotly_chart(px.line(df_harian, x="Tanggal", y="Suhu Min (°C)", title="Suhu Minimum Harian"), use_container_width=True)

with st.expander("Grafik Per Jam"):
    st.plotly_chart(px.line(df_jam.tail(48), x="Waktu", y="Curah Hujan (mm)", title="Curah Hujan per Jam"), use_container_width=True)
    st.plotly_chart(px.line(df_jam.tail(48), x="Waktu", y="Suhu (°C)", title="Suhu per Jam"), use_container_width=True)

# ------------------ TABEL ------------------
with st.expander("Data Harian"):
    st.dataframe(df_harian, use_container_width=True)

with st.expander("Data Per Jam (48 jam terakhir)"):
    st.dataframe(df_jam.tail(48), use_container_width=True)

# ------------------ MODEL PREDIKSI ------------------
model_df = pd.DataFrame({
    "Curah Hujan (mm)": [3.2, 1.0, 5.5, 0.0, 6.0],
    "Suhu (°C)": [30, 32, 29, 31, 33],
    "Kelembapan (%)": [75, 80, 78, 82, 79],
    "Hasil Panen (kg/ha)": [5100, 4800, 5300, 4500, 5500]
})
model = LinearRegression().fit(model_df.drop("Hasil Panen (kg/ha)", axis=1), model_df["Hasil Panen (kg/ha)"])

# Fungsi prediksi panen lebih panjang (harian/mingguan)
def prediksi_panen_berkala(df, periode='harian'):
    hasil_prediksi = []
    if periode == 'harian':
        for i, row in df.iterrows():
            x = np.array([[row["Curah Hujan (mm)"], row["Suhu Maks (°C)"], row["Kelembapan (%)"]]])
            hasil_prediksi.append(model.predict(x)[0])
        df["Prediksi Panen (kg/ha)"] = hasil_prediksi
        return df[["Tanggal", "Prediksi Panen (kg/ha)"]]
    elif periode == 'mingguan':
        df_week = df.resample('W-Mon', on="Tanggal").mean().reset_index()
        hasil_prediksi = []
        for i, row in df_week.iterrows():
            x = np.array([[row["Curah Hujan (mm)"], row["Suhu Maks (°C)"], row["Kelembapan (%)"]]])
            hasil_prediksi.append(model.predict(x)[0])
        df_week["Prediksi Panen (kg/ha)"] = hasil_prediksi
        return df_week[["Tanggal", "Prediksi Panen (kg/ha)"]]
    else:
        return pd.DataFrame()

# ------------------ PREDIKSI PANEN OTOMATIS ------------------
with st.expander("Prediksi Panen Otomatis"):
    luas_sawah = st.number_input("Luas Sawah (ha)", value=1.0)
    harga_gabah = st.number_input("Harga Gabah (Rp/kg)", value=6500, key="harga_otomatis")
    total_kg = hasil * luas_sawah
    total_rp = total_kg * harga_gabah
    st.metric("Prediksi Panen", f"{hasil:,.0f} kg/ha")
    st.success(f"Total: {total_kg:,.0f} kg | Rp {total_rp:,.0f}")

    if st.button("💾 Simpan Hasil Prediksi Otomatis"):
        # Simpan hasil prediksi otomatis
        prediksi_otomatis = pd.DataFrame({
            "Luas Sawah (ha)": [luas_sawah],
            "Harga Gabah (Rp/kg)": [harga_gabah],
            "Prediksi Panen (kg/ha)": [hasil],
            "Total Panen (kg)": [total_kg],
            "Total Pendapatan (Rp)": [total_rp]
        })
        csv = prediksi_otomatis.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Unduh Hasil Prediksi Otomatis (CSV)", data=csv, file_name="prediksi_otomatis.csv", mime="text/csv")

    # Prediksi panen lebih panjang
    periode_prediksi = st.selectbox("Pilih Periode Prediksi", options=["harian", "mingguan"])
    df_prediksi_berkala = prediksi_panen_berkala(df_harian, periode=periode_prediksi)
    st.dataframe(df_prediksi_berkala)

    if st.button("💾 Simpan Prediksi Berkala"):
        csv_berkala = df_prediksi_berkala.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Unduh Prediksi Berkala (CSV)", data=csv_berkala, file_name=f"prediksi_berkala_{periode_prediksi}.csv", mime="text/csv")

# ------------------ PERHITUNGAN MANUAL ------------------
with st.expander("Hitung Manual Prediksi Panen"):
    ch = st.number_input("Curah Hujan (mm)", value=5.0)
    suhu = st.number_input("Suhu Maks (°C)", value=32.0)
    hum = st.number_input("Kelembapan (%)", value=78.0)
    luas = st.number_input("Luas Lahan (ha)", value=1.0)
    harga = st.number_input("Harga Gabah (Rp/kg)", value=6500, key="harga_manual")
    pred_manual = model.predict([[ch, suhu, hum]])[0]
    total_manual = pred_manual * luas
    pendapatan_manual = total_manual * harga
    st.metric("Prediksi Panen Manual", f"{pred_manual:,.0f} kg/ha")
    st.success(f"Total: {total_manual:,.0f} kg | Rp {pendapatan_manual:,.0f}")

    if st.button("💾 Simpan Hasil Prediksi Manual"):
        pred_manual_df = pd.DataFrame({
            "Curah Hujan (mm)": [ch],
            "Suhu Maks (°C)": [suhu],
            "Kelembapan (%)": [hum],
            "Luas Lahan (ha)": [luas],
            "Harga Gabah (Rp/kg)": [harga],
            "Prediksi Panen (kg/ha)": [pred_manual],
            "Total Panen (kg)": [total_manual],
            "Total Pendapatan (Rp)": [pendapatan_manual]
        })
        csv_manual = pred_manual_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Unduh Hasil Prediksi Manual (CSV)", data=csv_manual, file_name="prediksi_manual.csv", mime="text/csv")

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
    if tugas and st.button("Simpan"):
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
