import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monitoring Irigasi Desa Lakessi", layout="wide")

# Header aplikasi
st.title("Prediksi Curah Hujan dan Jadwal Irigasi - Desa Lakessi")
st.markdown("""
Desa Lakessi, Kabupaten Sidenreng Rappang (Sidrap) adalah wilayah agraris yang mengandalkan irigasi untuk pertanian.  
Aplikasi ini membantu petani memantau data cuaca dan kebutuhan irigasi secara otomatis tanpa perlu turun ke lapangan.  
Dikembangkan oleh Dian Eka Putra | Email: ekaputradian01@gmail.com | WA: 085654073752
""")

# Gambar irigasi
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/6/6b/Irrigation_System_in_Paddy_Field.JPG", 
    caption="Sistem Irigasi Sawah Desa Lakessi",
    use_container_width=True
)

# Koordinat Desa Lakessi
latitude = -4.02
longitude = 119.44

# Fungsi ambil data cuaca, cache 1 jam
@st.cache_data(ttl=3600)
def fetch_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&daily=temperature_2m_min,temperature_2m_max,"
        f"precipitation_sum,relative_humidity_2m_mean,weathercode&timezone=auto"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

weather_data = fetch_weather(latitude, longitude)

# Data cuaca ke dataframe
df = pd.DataFrame({
    "Tanggal": pd.to_datetime(weather_data["daily"]["time"]),
    "Curah Hujan (mm)": weather_data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": weather_data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": weather_data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": weather_data["daily"]["relative_humidity_2m_mean"]
})

# Slider threshold curah hujan irigasi
threshold = st.slider("Atur batas curah hujan (mm) untuk menentukan kebutuhan irigasi:", 0, 20, 5)

# Tampilkan tabel data cuaca
st.subheader("Data Cuaca Harian Desa Lakessi")
st.dataframe(df, use_container_width=True)

# Grafik curah hujan dengan threshold
st.subheader("Grafik Curah Hujan Harian")
fig, ax = plt.subplots(figsize=(10,4))
ax.plot(df["Tanggal"], df["Curah Hujan (mm)"], marker='o', label="Curah Hujan")
ax.axhline(y=threshold, color='red', linestyle='--', label=f"Batas Irigasi: {threshold} mm")
ax.set_xlabel("Tanggal")
ax.set_ylabel("Curah Hujan (mm)")
ax.set_title("Curah Hujan Harian Desa Lakessi")
plt.xticks(rotation=45)
ax.legend()
st.pyplot(fig)

# Penjelasan grafik
st.markdown("""
**Cara Membaca Grafik:**  
- Garis merah putus-putus adalah batas minimal curah hujan untuk irigasi.  
- Jika curah hujan di bawah batas ini, maka irigasi diperlukan untuk menjaga tanaman tetap sehat dan optimal.
""")

# Rekomendasi irigasi otomatis
st.subheader("Rekomendasi Irigasi Harian")
for i, row in df.iterrows():
    if row["Curah Hujan (mm)"] < threshold:
        st.write(f"{row['Tanggal'].date()} → Irigasi diperlukan (Curah hujan: {row['Curah Hujan (mm)']} mm)")
    else:
        st.write(f"{row['Tanggal'].date()} → Tidak perlu irigasi (Curah hujan: {row['Curah Hujan (mm)']} mm)")

# Tips pertanian berbasis cuaca
st.subheader("Tips Pertanian Harian Berdasarkan Cuaca")
for i, row in df.iterrows():
    tips = []
    if row["Suhu Maks (°C)"] > 33:
        tips.append("Waspadai suhu tinggi yang dapat menyebabkan stres tanaman.")
    if row["Kelembapan (%)"] > 85:
        tips.append("Kelembapan tinggi, awasi risiko jamur dan penyakit tanaman.")
    if row["Curah Hujan (mm)"] > 15:
        tips.append("Curah hujan tinggi, pastikan saluran irigasi lancar untuk mencegah genangan.")
    if not tips:
        tips.append("Cuaca mendukung aktivitas pertanian hari ini.")
    st.write(f"{row['Tanggal'].date()} → " + " ".join(tips))

# Footer
st.markdown("---")
st.markdown("Aplikasi ini bertujuan membantu petani Desa Lakessi dalam mengoptimalkan irigasi dan pengelolaan pertanian berbasis data cuaca terkini.")
