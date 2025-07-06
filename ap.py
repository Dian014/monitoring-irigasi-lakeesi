import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monitoring Irigasi Desa Lakessi", layout="wide")

# CSS padding & spacing
st.markdown("""
<style>
.main {padding:2rem;}
h1, h2 {color:#2e7d32;}
.highlight {background-color:#a5d6a7;padding:8px;border-radius:4px;margin:5px 0;}
footer {text-align:center;color:gray;font-size:0.8rem;}
</style>
""", unsafe_allow_html=True)

# Header gambar
st.image(
    "https://images.unsplash.com/photo-1592153823269-812be9a1b5a6?auto=format&fit=crop&w=1350&q=80",
    use_container_width=True,
    caption="Irigasi Sawah di Desa Lakessi"
)

st.title("📊 Prediksi Curah Hujan & Rekomendasi Irigasi – Desa Lakessi")
st.write("Aplikasi ini menampilkan prakiraan curah hujan harian dan membantu menentukan apakah perlu melakukan irigasi.")


# Ambil data cuaca
latitude, longitude = -4.02, 119.44
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=precipitation_sum&timezone=auto"
data = requests.get(url).json()
df = pd.DataFrame({"Tanggal": pd.to_datetime(data["daily"]["time"]),
                   "Curah Hujan (mm)": data["daily"]["precipitation_sum"]})

# Slider threshold & jangka waktu grafik
threshold = st.sidebar.slider("🔧 Batas minimum curah hujan (mm):", 0, 20, 5)
days = st.sidebar.selectbox("Tampilkan untuk hari ke depan:", [3, 5, 7, len(df)], index=2)

df_show = df.head(days)

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📈 Grafik Curah Hujan")
    fig, ax = plt.subplots(figsize=(7,4))
    ax.plot(df_show["Tanggal"], df_show["Curah Hujan (mm)"], marker="o", color="#2e7d32", label="Curah Hujan")
    ax.axhline(threshold, color="red", linestyle="--", label=f"Threshold ({threshold} mm)")
    ax.set_xlabel("Tanggal"); ax.set_ylabel("Curah Hujan (mm)")
    ax.legend(); plt.xticks(rotation=45)
    st.pyplot(fig)
    st.markdown("""
    **Cara Membaca Grafik**:
    - 🔵 Titik hijau = prakiraan curah hujan.
    - 🔴 Garis merah = batas irigasi.
    - Tanda ❗ berarti irigasi disarankan jika titik di bawah garis merah.
    """)

with col2:
    st.subheader("💧 Rekomendasi Irigasi")
    for _, r in df_show.iterrows():
        txt = f"{r['Tanggal'].date()}: {r['Curah Hujan (mm)']:.2f} mm "
        if r['Curah Hujan (mm)'] < threshold:
            st.markdown(f"<div class='highlight'>🔴 {txt}→ *Irigasi diperlukan*</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"🟢 {txt}→ Irigasi tidak diperlukan", unsafe_allow_html=True)

# Dummy info tanah
st.subheader("🌱 Info Tambahan Tanah")
st.write("- Kelembapan: _(data sensor belum tersedia)_")
st.write("- Jenis tanah: _Andosol (Sangat subur, cocok padi)_")

# Footer kontak
st.markdown("---")
st.markdown("""
**Dian Eka Putra**  
📧 ekaputradian01@gmail.com  
📱 WA 085654073752  

*Proyek KKN Mandiri – Desa Lakessi, Sidrap*  
""", unsafe_allow_html=True)
st.markdown("<footer>© 2025 Desa Lakessi</footer>", unsafe_allow_html=True)
