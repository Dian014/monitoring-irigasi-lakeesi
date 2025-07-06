import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monitoring Irigasi Desa Lakessi", layout="wide")

# Header aplikasi
st.title("Prediksi Curah Hujan dan Jadwal Irigasi - Desa Lakessi")
st.markdown("""
Desa Lakessi, Kabupaten Sidenreng Rappang (Sidrap) memiliki potensi pertanian yang besar.  
Aplikasi ini membantu petani memantau cuaca dan kebutuhan irigasi secara otomatis tanpa harus ke lapangan.  
Dikembangkan oleh Dian Eka Putra | Email: ekaputradian01@gmail.com | WA: 085654073752
""")

# Tambahkan gambar irigasi yang relevan
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/6/6b/Irrigation_System_in_Paddy_Field.JPG",
    caption="Sistem Irigasi Sawah Desa Lakessi",
    use_container_width=True
)

# Koordinat Desa Lakessi
latitude = -4.02
longitude = 119.44

# Ambil data cuaca dari Open-Meteo API
url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={latitude}&longitude={longitude}&"
    f"daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean&timezone=auto"
)
response = requests.get(url)
data = response.json()

# Buat DataFrame dari data yang diambil
df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"]
})

# Slider untuk atur threshold curah hujan
threshold = st.slider("Atur batas curah hujan untuk irigasi (mm):", 0, 20, 5)

# Tampilkan data tabel cuaca harian
st.subheader("Data Cuaca Harian Desa Lakessi")
st.dataframe(df, use_container_width=True)

# Plot grafik curah hujan
st.subheader("Grafik Curah Hujan Harian")
fig, ax = plt.subplots()
ax.plot(df["Tanggal"], df["Curah Hujan (mm)"], marker='o', label='Curah Hujan')
ax.axhline(y=threshold, color='r', linestyle='--', label='🔴 Ambang Batas Irigasi')
ax.set_xlabel("Tanggal")
ax.set_ylabel("Curah Hujan (mm)")
ax.set_title("Grafik Curah Hujan Harian Desa Lakessi")
plt.xticks(rotation=45)
ax.legend()
st.pyplot(fig)

# Keterangan grafik
st.markdown("""
**Keterangan Grafik:**  
- 🔴 Garis merah putus-putus menunjukkan ambang batas curah hujan (threshold).  
- Jika curah hujan harian **di bawah garis ini**, maka **irigasi diperlukan**.  
- Titik-titik pada grafik mewakili nilai curah hujan harian.
""")

# Rekomendasi irigasi berdasarkan threshold
st.subheader("Rekomendasi Irigasi Harian")
for _, row in df.iterrows():
    if row["Curah Hujan (mm)"] < threshold:
        st.write(f"{row['Tanggal'].date()} → **Irigasi Diperlukan** (Curah hujan: {row['Curah Hujan (mm)']} mm)")
    else:
        st.write(f"{row['Tanggal'].date()} → Tidak perlu irigasi (Curah hujan: {row['Curah Hujan (mm)']} mm)")

# Tips pertanian otomatis berdasarkan suhu dan kelembapan
st.subheader("Tips Pertanian Harian Berdasarkan Cuaca")
for _, row in df.iterrows():
    if row["Suhu Maks (°C)"] > 33:
        st.write(f"{row['Tanggal'].date()} → Waspadai kekeringan, suhu tinggi.")
    elif row["Kelembapan (%)"] > 85:
        st.write(f"{row['Tanggal'].date()} → Udara sangat lembap, awasi hama dan jamur.")
    else:
        st.write(f"{row['Tanggal'].date()} → Cuaca mendukung aktivitas pertanian hari ini.")

# Footer
st.markdown("---")
st.markdown("Aplikasi ini dikembangkan untuk mendukung petani di Desa Lakessi, Sidrap dalam pengelolaan irigasi dan kegiatan pertanian berbasis data cuaca.")
