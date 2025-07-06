import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# --- Style CSS untuk tambah padding dan warna ---
st.markdown("""
<style>
    .main {
        padding: 2rem 5rem;
        background-color: #f0f2f6;
    }
    h1, h2, h3 {
        color: #2e7d32;
    }
    .highlight {
        background-color: #a5d6a7;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Judul utama dan gambar header
st.title("🌧️ Prediksi Curah Hujan & Jadwal Irigasi Desa Lakeesi")
st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1350&q=80", caption="Sistem Irigasi Sawah", use_column_width=True)

# Koordinat Desa Lakeesi (kira-kira)
latitude = -4.02
longitude = 119.44

# Ambil data cuaca dari Open-Meteo
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=precipitation_sum&timezone=auto"
response = requests.get(url)
data = response.json()

# Ambil data curah hujan harian
dates = data['daily']['time']
precipitation = data['daily']['precipitation_sum']

# Buat DataFrame
df = pd.DataFrame({
    'Tanggal': pd.to_datetime(dates),
    'Curah Hujan (mm)': precipitation
})

# Slider threshold irigasi
threshold = st.slider("⚙️ Atur batas curah hujan untuk irigasi (mm):", 0, 20, 5)

st.subheader("📊 Data Curah Hujan Harian")
# Tampilkan tabel data secara rapi
st.dataframe(df.style.format({"Curah Hujan (mm)": "{:.2f}"}))

# Layout 2 kolom untuk grafik dan rekomendasi
col1, col2 = st.columns([3, 2])

with col1:
    # Plot grafik
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(df['Tanggal'], df['Curah Hujan (mm)'], marker='o', color="#2e7d32")
    ax.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold: {threshold} mm')
    ax.set_xlabel('Tanggal')
    ax.set_ylabel('Curah Hujan (mm)')
    ax.set_title('Grafik Curah Hujan Harian')
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)

with col2:
    st.subheader("🚰 Rekomendasi Irigasi")
    for i, row in df.iterrows():
        tanggal = row['Tanggal'].date()
        curah = row['Curah Hujan (mm)']
        if curah < threshold:
            st.markdown(f"<div class='highlight'>🔴 {tanggal}: Irigasi diperlukan ({curah:.2f} mm)</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"🟢 {tanggal}: Tidak perlu irigasi ({curah:.2f} mm)")

# Footer info kontak
st.markdown("---")
st.markdown("© 2025 KKN Mandiri Desa Lakeesi | Dibuat oleh [Nama Kamu] | Email: kamu@email.com")
