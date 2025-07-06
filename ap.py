import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monitoring Irigasi Desa Lakessi", layout="wide")

# Header Aplikasi
st.title("🚜 Prediksi Curah Hujan dan Jadwal Irigasi - Desa Lakessi")
st.markdown("""
Desa Lakessi, Kabupaten Sidenreng Rappang (Sidrap) memiliki potensi pertanian yang tinggi.  
Aplikasi ini membantu memantau cuaca dan kebutuhan irigasi **tanpa perlu ke lapangan**.  
Dikembangkan oleh **Dian Eka Putra** | 📧 ekaputradian01@gmail.com | 📱 085654073752
""")

# Tambahkan Gambar
st.image("https://upload.wikimedia.org/wikipedia/commons/6/6b/Irrigation_System_in_Paddy_Field.JPG", 
         caption="Ilustrasi Irigasi Sawah", use_container_width=True)

# Koordinat Desa Lakessi
latitude = -4.02
longitude = 119.44

# Ambil data cuaca
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,weathercode&timezone=auto"
response = requests.get(url)
data = response.json()

# Buat DataFrame utama
df = pd.DataFrame({
    "Tanggal": pd.to_datetime(data["daily"]["time"]),
    "Curah Hujan (mm)": data["daily"]["precipitation_sum"],
    "Suhu Maks (°C)": data["daily"]["temperature_2m_max"],
    "Suhu Min (°C)": data["daily"]["temperature_2m_min"],
    "Kelembapan (%)": data["daily"]["relative_humidity_2m_mean"]
})

# Slider threshold
threshold = st.slider("🌧️ Atur batas curah hujan untuk irigasi (mm):", 0, 20, 5)

# Tampilkan Tabel
st.subheader("📊 Data Cuaca Harian Desa Lakessi")
st.dataframe(df, use_container_width=True)

# Grafik Curah Hujan
st.subheader("📈 Grafik Curah Hujan Harian")
fig, ax = plt.subplots()
ax.plot(df["Tanggal"], df["Curah Hujan (mm)"], marker='o', label='Curah Hujan')
ax.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold: {threshold} mm')
ax.set_xlabel("Tanggal")
ax.set_ylabel("Curah Hujan (mm)")
ax.set_title("Grafik Curah Hujan Harian Desa Lakessi")
plt.xticks(rotation=45)
ax.legend()
st.pyplot(fig)

# Keterangan Grafik
st.markdown("""
🔴 Garis merah putus-putus menunjukkan ambang batas curah hujan.  
Jika curah hujan **di bawah garis ini**, maka **irigasi diperlukan**.
""")

# Rekomendasi Irigasi
st.subheader("💧 Rekomendasi Irigasi Harian")
for i, row in df.iterrows():
    if row["Curah Hujan (mm)"] < threshold:
        st.write(f"📅 {row['Tanggal'].date()} → **Irigasi Diperlukan** (Curah hujan: {row['Curah Hujan (mm)']} mm)")
    else:
        st.write(f"📅 {row['Tanggal'].date()} → Tidak Perlu Irigasi (Curah hujan: {row['Curah Hujan (mm)']} mm)")

# Tips Otomatis
st.subheader("💡 Tips Otomatis Berdasarkan Cuaca")
for i, row in df.iterrows():
    if row["Suhu Maks (°C)"] > 33:
        st.write(f"🔥 {row['Tanggal'].date()} → Waspadai kekeringan, suhu tinggi.")
    elif row["Kelembapan (%)"] > 85:
        st.write(f"🌧️ {row['Tanggal'].date()} → Udara sangat lembap, awasi hama/jamur.")
    else:
        st.write(f"✅ {row['Tanggal'].date()} → Cuaca normal, cocok untuk kegiatan tani.")

# Footer
st.markdown("---")
st.markdown("📍 Aplikasi ini dikembangkan untuk mendukung petani di **Desa Lakessi, Sidrap** agar lebih mudah mengatur irigasi secara cerdas berbasis cuaca.")
