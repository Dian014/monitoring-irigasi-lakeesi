import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Monitoring Irigasi dan Pertanian Desa Lakessi", layout="wide")

# Header
st.title("Monitoring Irigasi & Data Pertanian Desa Lakessi")
st.markdown("""
Aplikasi ini membantu petani Desa Lakessi memantau cuaca, curah hujan, estimasi kebutuhan irigasi, dan informasi pertanian lain secara otomatis tanpa perlu ke lapangan.

Dikembangkan oleh Dian Eka Putra | 📧 ekaputradian01@gmail.com | 📱 085654073752
""")

# Lokasi Desa Lakessi
latitude = -4.02
longitude = 119.44

# Tampilkan peta lokasi
st.subheader("📍 Lokasi Desa Lakessi")
st.map(pd.DataFrame({'lat':[latitude],'lon':[longitude]}))

# Ambil data cuaca dari Open-Meteo (lebih lengkap)
url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={latitude}&longitude={longitude}&"
    f"daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,"
    f"windspeed_10m_max,weathercode&timezone=auto"
)
response = requests.get(url)
data = response.json()

# Data harian
df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"],
    "Kecepatan Angin (km/jam)": data["daily"]["windspeed_10m_max"],
    "Kode Cuaca": data["daily"]["weathercode"]
})

# Fungsi sederhana estimasi evapotranspirasi (ET0) harian (mm/hari)
def estimasi_et0(t_min, t_max, rh):
    # Rumus Hargreaves sederhana
    et0 = 0.0023 * ((t_max + t_min) / 2 + 17.8) * ((t_max - t_min) ** 0.5) * (0.408)
    # Koreksi kelembapan sederhana (misal kelembapan tinggi kurangi evapotranspirasi)
    if rh > 80:
        et0 *= 0.7
    elif rh < 40:
        et0 *= 1.2
    return round(et0, 2)

df['Evapotranspirasi (ET0) mm/hari'] = df.apply(lambda r: estimasi_et0(r['Suhu Min (°C)'], r['Suhu Maks (°C)'], r['Kelembapan (%)']), axis=1)

# Slider threshold irigasi
threshold = st.slider("Atur batas curah hujan untuk irigasi (mm):", 0, 20, 5)

# Tampilkan tabel ringkas data dan rekomendasi
st.subheader("📋 Rekap Data Harian dan Rekomendasi Irigasi")

def interpret_weather_code(code):
    # Interpretasi kode cuaca Open-Meteo singkat
    mapping = {
        0: "Cerah",
        1: "Cerah Berawan",
        2: "Berawan",
        3: "Mendung",
        45: "Kabut",
        48: "Kabut dengan Deposit Es",
        51: "Hujan Ringan",
        53: "Hujan Sedang",
        55: "Hujan Lebat",
        61: "Hujan Lokal",
        63: "Hujan Lebat Lokal",
        65: "Hujan Sangat Lebat",
        71: "Salju Ringan",
        73: "Salju Sedang",
        75: "Salju Lebat",
        80: "Hujan Lokal dengan Petir",
        81: "Hujan Lebat Lokal dengan Petir",
        82: "Hujan Sangat Lebat dengan Petir",
        # Tambah sesuai dokumentasi Open-Meteo jika perlu
    }
    return mapping.get(code, "Data Cuaca Tidak Diketahui")

df['Status Cuaca'] = df['Kode Cuaca'].apply(interpret_weather_code)
df['Rekomendasi Irigasi'] = df.apply(lambda r: "Irigasi Diperlukan" if r['Curah Hujan (mm)'] < threshold else "Tidak Perlu Irigasi", axis=1)

# Tabel lengkap
st.dataframe(df[['Tanggal', 'Curah Hujan (mm)', 'Evapotranspirasi (ET0) mm/hari', 'Suhu Maks (°C)', 'Suhu Min (°C)', 'Kelembapan (%)', 'Kecepatan Angin (km/jam)', 'Status Cuaca', 'Rekomendasi Irigasi']], use_container_width=True)

# Grafik Curah Hujan dan Evapotranspirasi
st.subheader("📈 Grafik Curah Hujan dan Evapotranspirasi Harian")

fig, ax1 = plt.subplots(figsize=(10,5))
ax2 = ax1.twinx()

ax1.plot(df['Tanggal'], df['Curah Hujan (mm)'], 'b-o', label='Curah Hujan (mm)')
ax1.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold Curah Hujan ({threshold} mm)')

ax2.plot(df['Tanggal'], df['Evapotranspirasi (ET0) mm/hari'], 'g--s', label='Evapotranspirasi (ET0) (mm/hari)')

ax1.set_xlabel('Tanggal')
ax1.set_ylabel('Curah Hujan (mm)', color='b')
ax2.set_ylabel('Evapotranspirasi (mm/hari)', color='g')
plt.xticks(rotation=45)

# Legend gabungan
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

st.pyplot(fig)

# Keterangan Grafik
st.markdown("""
📌 **Keterangan Grafik:**  
🔴 Garis merah putus-putus adalah batas ambang curah hujan untuk rekomendasi irigasi.  
🔵 Titik biru menunjukkan curah hujan harian.  
🟢 Titik hijau putus-putus menunjukkan estimasi evapotranspirasi (ET0), yang mengindikasikan kebutuhan air tanaman akibat penguapan dan transpirasi.  
""")

# Tips Pertanian Otomatis Berdasarkan Data
st.subheader("💡 Tips Pertanian Harian Berdasarkan Cuaca")

for _, row in df.iterrows():
    if row['Suhu Maks (°C)'] > 33:
        st.write(f"🔥 {row['Tanggal'].date()} - Suhu tinggi, waspadai tanaman kekeringan.")
    elif row['Kelembapan (%)'] > 85:
        st.write(f"🌧️ {row['Tanggal'].date()} - Udara lembap, perhatikan risiko hama dan jamur.")
    elif row['Curah Hujan (mm)'] < threshold:
        st.write(f"💧 {row['Tanggal'].date()} - Curah hujan rendah, disarankan irigasi.")
    else:
        st.write(f"✅ {row['Tanggal'].date()} - Cuaca mendukung aktivitas pertanian.")

# Footer
st.markdown("---")
st.markdown("Aplikasi ini membantu petani Desa Lakessi dalam pengelolaan irigasi dan kegiatan pertanian secara efektif dengan data cuaca terbaru.")

