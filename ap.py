import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monitoring Irigasi Desa Lakessi", layout="wide")

# Gambar header
st.image(
    "https://images.unsplash.com/photo-1592153823269-812be9a1b5a6",
    use_container_width=True,
    caption="Sistem Irigasi untuk Pertanian di Desa Lakessi"
)

# Judul utama
st.markdown(
    "<h1 style='text-align: center; color: #2e7d32;'>📊 Monitoring Curah Hujan & Rekomendasi Irigasi Desa Lakessi</h1>",
    unsafe_allow_html=True
)

# Koordinat Desa Lakessi (estimasi)
latitude = -4.02
longitude = 119.44

# Ambil data cuaca dari Open-Meteo API
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=precipitation_sum&timezone=auto"
response = requests.get(url)
data = response.json()

# Ambil data curah hujan harian
dates = data['daily']['time']
precipitation = data['daily']['precipitation_sum']
df = pd.DataFrame({
    'Tanggal': pd.to_datetime(dates),
    'Curah Hujan (mm)': precipitation
})

# Slider untuk menentukan ambang batas irigasi
threshold = st.slider("🔧 Atur batas curah hujan untuk irigasi (mm):", 0, 20, 5)

# Layout: Dua kolom
col1, col2 = st.columns([2, 1])

# Kolom kiri: Tabel & grafik
with col1:
    st.subheader("📅 Data Curah Hujan Harian")
    st.dataframe(df, use_container_width=True)

    # Grafik curah hujan
    fig, ax = plt.subplots()
    ax.plot(df['Tanggal'], df['Curah Hujan (mm)'], marker='o', color='green')
    ax.axhline(y=threshold, color='red', linestyle='--', label=f'Threshold: {threshold} mm')
    ax.set_xlabel('Tanggal')
    ax.set_ylabel('Curah Hujan (mm)')
    ax.set_title('Grafik Curah Hujan Harian')
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)

# Kolom kanan: Rekomendasi Irigasi
with col2:
    st.subheader("🚿 Rekomendasi Irigasi")
    for i, row in df.iterrows():
        if row['Curah Hujan (mm)'] < threshold:
            st.markdown(f"<span style='color: red;'>{row['Tanggal'].date()}: 💧 Irigasi diperlukan ({row['Curah Hujan (mm)']} mm)</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color: green;'>{row['Tanggal'].date()}: ✅ Tidak perlu irigasi ({row['Curah Hujan (mm)']} mm)</span>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<small>🌾 Aplikasi ini dibuat untuk Program KKN Mandiri di Desa Lakessi, Kecamatan Maritengngae, Kabupaten Sidrap.<br>📬 Kontak: <a href='mailto:ekaputradian01@gmail.com'>ekaputradian01@gmail.com</a></small>",
    unsafe_allow_html=True
)
