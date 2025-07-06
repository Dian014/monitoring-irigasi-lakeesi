import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Mengatur layout aplikasi
st.set_page_config(
    page_title="Monitoring Irigasi Desa Lakessi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS
st.markdown("""
<style>
    .highlight {background-color: #a5d6a7; padding: 10px; border-radius: 5px; margin-bottom: 10px;}
    footer {text-align: center; color: grey; font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# Gambar header (pilih salah satu URL dari carousel)
st.image(
    "https://images.app.goo.gl/pEAPbsG81Ph6une78",
    use_container_width=True,
    caption="Sistem Irigasi Sawah"
)

# Judul dan deskripsi
st.title("🌧️ Prediksi Curah Hujan & Irigasi Desa Lakessi")
st.write("Aplikasi ini membantu petani dan pengelola desa memonitor curah hujan dan rekomendasi irigasi secara real-time.")

# Ambil data dari Open-Meteo
latitude, longitude = -4.02, 119.44
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=precipitation_sum&timezone=auto"
data = requests.get(url).json()
dates = pd.to_datetime(data['daily']['time'])
precipitation = data['daily']['precipitation_sum']
df = pd.DataFrame({"Tanggal": dates, "Curah Hujan (mm)": precipitation})

# Slider threshold
threshold = st.sidebar.slider("Threshold curah hujan (mm):", min_value=0, max_value=20, value=5)

# Layout dua kolom
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Grafik Curah Hujan Harian")
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(df['Tanggal'], df['Curah Hujan (mm)'], marker='o', color="#2e7d32")
    ax.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold = {threshold} mm')
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Curah Hujan (mm)")
    ax.legend()
    st.pyplot(fig)

with col2:
    st.subheader("🚰 Rekomendasi Irigasi")
    for _, row in df.iterrows():
        msg = f"{row['Tanggal'].date()}: Curah hujan {row['Curah Hujan (mm)']:.2f} mm"
        if row['Curah Hujan (mm)'] < threshold:
            st.markdown(f"<div class='highlight'>🔴 {msg} → Irigasi diperlukan</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"🟢 {msg} → Tidak perlu irigasi", unsafe_allow_html=True)

# Footer kontak & credit
st.markdown("---")
st.markdown("""
**Dian Eka Putra**  
📧 ekaputradian01@gmail.com  
📱 WA 085654073752  

*Proyek KKN Mandiri – Desa Lakessi, Kecamatan Maritenggae, Kabupaten Sidrap*  
""", unsafe_allow_html=True)

st.markdown("<footer>© 2025 Desa Lakessi</footer>", unsafe_allow_html=True)
