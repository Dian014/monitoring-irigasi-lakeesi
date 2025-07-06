import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Konfigurasi halaman
st.set_page_config(
    page_title="Monitoring Irigasi Desa Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Gaya CSS
st.markdown("""
<style>
    .highlight {background-color: #a5d6a7; padding: 10px; border-radius: 5px; margin-bottom: 10px;}
    footer {text-align: center; color: grey; font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# Gambar header (opsional: ganti URL ini sesuai gambar dari Lakessi)
st.image(
    "https://images.unsplash.com/photo-1592153823269-812be9a1b5a6?auto=format&fit=crop&w=1350&q=80",
    use_container_width=True,
    caption="Sistem Irigasi Sawah di Desa Lakessi"
)

# Judul
st.title("🌧️ Prediksi Curah Hujan & Rekomendasi Irigasi - Desa Lakessi")
st.write("Aplikasi ini membantu memantau curah hujan dan memberikan rekomendasi waktu irigasi berdasarkan data prakiraan cuaca harian.")

# Ambil data prakiraan cuaca
latitude, longitude = -4.02, 119.44
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=precipitation_sum&timezone=auto"
data = requests.get(url).json()
dates = pd.to_datetime(data['daily']['time'])
precipitation = data['daily']['precipitation_sum']
df = pd.DataFrame({"Tanggal": dates, "Curah Hujan (mm)": precipitation})

# Sidebar threshold
threshold = st.sidebar.slider("Atur batas minimum curah hujan (mm):", 0, 20, 5)

# Kolom utama
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Grafik Prakiraan Curah Hujan Harian")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df['Tanggal'], df['Curah Hujan (mm)'], marker='o', color="#2e7d32", label="Curah Hujan")
    ax.axhline(y=threshold, color='red', linestyle='--', label=f"Batas Irigasi ({threshold} mm)")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Curah Hujan (mm)")
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.markdown("### 🧾 Cara Membaca Grafik:")
    st.markdown("""
    - **Garis Hijau (🔵)** menunjukkan curah hujan yang diprediksi untuk setiap hari.
    - **Garis Merah Putus-putus (🔴)** adalah ambang batas curah hujan (threshold).  
    - Jika **titik hijau berada di bawah garis merah**, maka **irigasi disarankan dilakukan** karena curah hujan rendah.  
    - Jika **titik hijau berada di atas garis merah**, maka **tanaman cukup mendapat air dari hujan** dan **irigasi tidak perlu**.
    """)

with col2:
    st.subheader("💧 Rekomendasi Irigasi")
    for _, row in df.iterrows():
        msg = f"{row['Tanggal'].date()}: Curah hujan {row['Curah Hujan (mm)']:.2f} mm"
        if row['Curah Hujan (mm)'] < threshold:
            st.markdown(f"<div class='highlight'>🔴 {msg} → Irigasi diperlukan</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"🟢 {msg} → Tidak perlu irigasi", unsafe_allow_html=True)

# Footer kontak
st.markdown("---")
st.markdown("""
**Dian Eka Putra**  
📧 ekaputradian01@gmail.com  
📱 WA 085654073752  

*Proyek KKN Mandiri – Desa Lakessi, Kecamatan Maritenggae, Kabupaten Sidrap*  
""", unsafe_allow_html=True)

st.markdown("<footer>© 2025 Desa Lakessi</footer>", unsafe_allow_html=True)
