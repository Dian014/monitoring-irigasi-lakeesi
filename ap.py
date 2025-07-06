import streamlit as st
import requests, pandas as pd, plotly.express as px, folium
from streamlit_folium import st_folium
from datetime import date, timedelta

st.set_page_config(page_title="🌾 Panel Prakiraan Irigasi Desa Lakessi", layout="wide")
st.markdown("## 🌤 Aplikasi Prediktif Cuaca & Irigasi – Desa Lakessi, Sidrap")

# Tampilan gambar pertanian
st.image(["turn0image0","turn0image1","turn0image3","turn0image5"], caption="👨‍🌾 Sawah & Pertanian Desa Lakessi", use_column_width=True)

LAT, LON = -4.012579, 119.472102
OWM = st.secrets.get("OWM_API_KEY", "")

hari = st.sidebar.slider("Prakiraan cuaca ke depan (hari):", 1, 7, 5)
threshold = st.sidebar.slider("Ideal curah hujan minimal (mm):", 10, 50, 20)

@st.cache_data(ttl=300)
def fetch(days):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude":LAT,"longitude":LON,"daily":"temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean","forecast_days":days,"timezone":"auto"}
    r = requests.get(url,params=params); r.raise_for_status()
    d = r.json()["daily"]
    return pd.DataFrame({"Tanggal":pd.to_datetime(d["time"]),"Hujan":d["precipitation_sum"],"SuhuMax":d["temperature_2m_max"],"SuhuMin":d["temperature_2m_min"],"Kelembapan":d["relative_humidity_2m_mean"]})

df = fetch(hari)

# Peta tanpa spasi kosong
st.subheader("🗺 Peta Infrastruktur & Curah Hujan Prakiraan")
m = folium.Map(location=[LAT,LON],zoom_start=13)
if OWM:
    folium.TileLayer(tiles=f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={OWM}",attr="OpenWeatherMap",overlay=True,opacity=0.6).add_to(m)
folium.CircleMarker([LAT,LON],radius=6,color="blue",fill=True).add_to(m)
st_folium(m,width="100%",height=250,returned_objects=[])

# Data dan rekomendasi
df["Irigasi"] = df["Hujan"].apply(lambda x:f"🚿 Irigasi" if x<threshold else "✅ Optimal")
st.markdown("### 📋 Forecast & Rekomendasi Cuaca")
st.dataframe(df, use_container_width=True)
st.download_button("⬇ Unduh Data CSV", df.to_csv(index=False).encode(), "forecast_lakessi.csv", "text/csv")

# Grafik dengan legenda
st.subheader("📊 Grafik Interaktif")
fig1 = px.bar(df,x="Tanggal",y="Hujan",title="Prakiraan Curah Hujan",color_discrete_sequence=["skyblue"])
fig1.add_hline(y=threshold,line_dash="dash",line_color="red")
fig2 = px.line(df,x="Tanggal",y=["SuhuMax","SuhuMin"],markers=True,title="Suhu Harian (°C)")
fig3 = px.line(df,x="Tanggal",y="Kelembapan",markers=True,color_discrete_sequence=["green"],title="Kelembapan Harian (%)")
st.plotly_chart(fig1,use_container_width=True); st.caption("🔴 Threshold curah hujan")
st.plotly_chart(fig2,use_container_width=True)
st.plotly_chart(fig3,use_container_width=True)

# Tanam & Panen otomatis
def detect(df):
    for i in range(len(df)-2):
        s = df.iloc[i:i+3]
        if all(s["Hujan"]>=threshold) and 25<=s["SuhuMax"].mean()<=33 and s["Kelembapan"].mean()>75:
            return s.iloc[0]["Tanggal"].date()
    return None
tanam = detect(df)
panen = tanam + timedelta(days=110) if tanam else None
st.subheader("🌱 Estimasi Musim Tanam & Panen Padi")
if tanam:
    st.success(f"📌 Tanam: {tanam:%d %b %Y}")
    st.info(f"🌾 Panen: {panen:%d %b %Y}")
else:
    st.warning("📅 Kondisi belum ideal untuk tanam padi dalam periode prakiraan.")

# Tips harian berdasarkan data
st.subheader("📝 Tips Harian Otomatis")
for idx,r in df.iterrows():
    tips=[]
    if r.Hujan<threshold: tips.append("irigasi")
    if r.SuhuMax>33: tips.append("panen awal")
    if r.Kelembapan>85: tips.append("awas jamur")
    if not tips: tips.append("bertani")
    st.markdown(f"- {r.Tanggal:%d-%m-%Y}: {', '.join(tips).capitalize()}")

st.markdown("---")
st.caption("🛰 Data otomatis – Dian Eka Putra | Lokasi akurat: Desa Lakessi, Sidrap")
