import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.title("Prediksi Curah Hujan dan Jadwal Irigasi Desa Lakeesi")

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

# Slider untuk threshold irigasi
threshold = st.slider("Atur batas curah hujan untuk irigasi (mm):", 0, 20, 5)

st.subheader("Data Curah Hujan Harian")
st.write(df)

# Plot grafik
fig, ax = plt.subplots()
ax.plot(df['Tanggal'], df['Curah Hujan (mm)'], marker='o')
ax.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold: {threshold} mm')
ax.set_xlabel('Tanggal')
ax.set_ylabel('Curah Hujan (mm)')
ax.set_title('Grafik Curah Hujan Harian')
plt.xticks(rotation=45)
ax.legend()
st.pyplot(fig)

# Rekomendasi irigasi berdasarkan threshold
st.subheader("Rekomendasi Irigasi")
for i, row in df.iterrows():
    if row['Curah Hujan (mm)'] < threshold:
        st.write(f"{row['Tanggal'].date()}: Irigasi diperlukan (curah hujan {row['Curah Hujan (mm)']} mm)")
    else:
        st.write(f"{row['Tanggal'].date()}: Tidak perlu irigasi (curah hujan {row['Curah Hujan (mm)']} mm)")
