import json
from pathlib import Path
from urllib.parse import quote
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, Fullscreen, LocateControl

st.set_page_config(page_title="WebGIS Landmark", page_icon="📍", layout="wide", initial_sidebar_state="collapsed")

# Tampilan light mode, responsif, tanpa sidebar yang menimpa konten di layar kecil
st.markdown("""
<style>
:root { color-scheme: light; --primary:#2563eb; --surface:#ffffff; --muted:#64748b; }
#MainMenu, footer {visibility:hidden;}
header[data-testid="stHeader"] {background:rgba(255,255,255,.94);}
.stApp {background:#f5f7fb; color:#172033;}
.block-container {max-width:1200px; padding:1rem 1.1rem 4rem;}
[data-testid="stSidebar"] {background:#fff; border-right:1px solid #e2e8f0;}
[data-testid="stMetric"] {background:#fff; padding:14px 16px; border:1px solid #e2e8f0; border-radius:18px; box-shadow:0 2px 8px rgba(15,23,42,.04);}
[data-testid="stMetricLabel"] {color:#64748b;}
[data-testid="stMetricValue"] {color:#0f172a; font-weight:750;}
.stButton button, .stLinkButton a, [data-testid="stDownloadButton"] button {border-radius:14px; min-height:44px; font-weight:650;}
.stTextInput input, [data-baseweb="select"] > div {border-radius:12px;}
[data-testid="stExpander"] {border:1px solid #e2e8f0; border-radius:16px; overflow:hidden; background:#fff;}
.mobile-hero {padding:20px 22px; border:1px solid #dbeafe; border-radius:22px; background:linear-gradient(135deg,#ffffff,#eff6ff); margin-bottom:16px; box-shadow:0 4px 14px rgba(37,99,235,.06);}
.mobile-hero .eyebrow {font-size:11px; letter-spacing:1.4px; text-transform:uppercase; color:#2563eb; font-weight:800;}
.mobile-hero h1 {font-size:clamp(25px,4vw,34px); color:#0f172a; margin:5px 0 6px; padding:0;}
.mobile-hero p {color:#475569; margin:0; font-size:14px;}
.section-label {font-size:19px; font-weight:750; color:#0f172a; margin:18px 0 8px;}
[data-testid="stDataFrame"] {border:1px solid #e2e8f0; border-radius:14px; overflow:hidden;}
@media (max-width: 700px) {
 .block-container {padding:.65rem .65rem 3rem;}
 [data-testid="stMetric"] {padding:10px; border-radius:14px;}
 [data-testid="stMetricValue"] {font-size:1.25rem;}
 .mobile-hero {padding:16px; border-radius:18px;}
 /* Sidebar jangan pernah menimpa halaman pada ponsel; filter berada di panel utama. */
 [data-testid="stSidebar"] {display:none !important;}
 [data-testid="stHorizontalBlock"] {gap:.5rem;}
 iframe[title="streamlit_folium.st_folium"] {width:100% !important; max-width:100% !important;}
}
</style>
<div class="mobile-hero"><div class="eyebrow">Peta lapangan · Badung</div><h1>📍 WebGIS Landmark</h1><p>Temukan titik, lihat detail, dan mulai navigasi ke lokasi pilihan.</p></div>
""", unsafe_allow_html=True)
DATA_PATH = Path(__file__).parent / "landmark.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, dtype={"id": str, "wid": str, "iddesa": str})
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)].copy()
    for col in df.columns:
        df[col] = df[col].where(pd.notna(df[col]), "")
    return df

def safe(v, fallback="—"):
    s = str(v).strip()
    return s if s and s.lower() != "nan" else fallback

df = load_data()
st.caption("Peta interaktif titik landmark. Ketuk marker untuk melihat informasi dan petunjuk arah.")

with st.expander("🔎 Cari dan filter titik", expanded=False):
    st.caption("Filter ditampilkan di halaman utama agar tidak tertutup panel samping pada layar ponsel.")
    search = st.text_input("Cari nama / ID / WID / deskripsi", placeholder="Contoh: Tiyingan")
    cats = sorted([str(x) for x in df["kategori_landmark"].unique() if str(x).strip()])
    selected_cats = st.multiselect("Kategori landmark", cats, default=cats)
    types = sorted([str(x) for x in df["tipe_landmark"].unique() if str(x).strip()])
    selected_types = st.multiselect("Tipe landmark", types, default=types)
    only_status = st.checkbox("Hanya status aktif (status = 1)", value=True)
    cluster = st.checkbox("Kelompokkan marker berdekatan", value=True)

filtered = df.copy()
if search.strip():
    mask = filtered.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
    filtered = filtered[mask]
if selected_cats:
    filtered = filtered[filtered["kategori_landmark"].astype(str).isin(selected_cats)]
else:
    filtered = filtered.iloc[0:0]
if selected_types:
    filtered = filtered[filtered["tipe_landmark"].astype(str).isin(selected_types)]
else:
    filtered = filtered.iloc[0:0]
if only_status:
    filtered = filtered[filtered["status"].astype(str).isin(["1", "1.0"])]

c1,c2,c3 = st.columns(3)
c1.metric("Total titik sesuai filter", f"{len(filtered):,}".replace(",", "."))
c2.metric("Kategori", str(filtered["kategori_landmark"].nunique()) if len(filtered) else "0")
c3.metric("Titik dengan koordinat", f"{len(df):,}".replace(",", "."))

if filtered.empty:
    st.warning("Tidak ada titik yang cocok. Ubah kata kunci atau filter.")
    st.stop()

# Center map on filtered locations
center = [float(filtered["latitude"].median()), float(filtered["longitude"].median())]
m = folium.Map(
    location=center,
    zoom_start=16 if len(filtered) < 100 else 13,
    control_scale=True,
    tiles=None,
    prefer_canvas=True,
)
# Gunakan satu basemap saja. Sebelumnya layer CARTO ditumpuk di atas OSM,
# sehingga tile CARTO bertuliskan API KEY REQUIRED menutupi peta.
folium.TileLayer(
    tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    name="OpenStreetMap",
    overlay=False,
    control=True,
    max_zoom=19,
).add_to(m)
Fullscreen(position="topleft").add_to(m)
LocateControl(auto_start=False, position="topleft").add_to(m)
group = MarkerCluster(name="Titik landmark").add_to(m) if cluster else folium.FeatureGroup(name="Titik landmark").add_to(m)

for _, r in filtered.iterrows():
    lat, lon = float(r["latitude"]), float(r["longitude"])
    name = safe(r.get("nama_krt"), safe(r.get("deskripsi_project"), "Landmark"))
    dest = f"{lat},{lon}"
    direction_url = "https://www.google.com/maps/dir/?api=1&destination=" + quote(dest) + "&travelmode=driving"
    detail_url = "https://www.google.com/maps/search/?api=1&query=" + quote(dest)
    popup_html = f"""
    <div style="font-family:Arial,sans-serif;min-width:220px;max-width:280px">
      <div style="font-size:15px;font-weight:700;margin-bottom:6px">{name}</div>
      <div><b>ID:</b> {safe(r.get('id'))}</div>
      <div><b>WID:</b> {safe(r.get('wid'))}</div>
      <div><b>Kategori:</b> {safe(r.get('kategori_landmark'))}</div>
      <div><b>Tipe:</b> {safe(r.get('tipe_landmark'))}</div>
      <div><b>Deskripsi:</b> {safe(r.get('deskripsi_project'))}</div>
      <div><b>Koordinat:</b> {lat:.6f}, {lon:.6f}</div>
      <div style="margin-top:10px"><a href="{direction_url}" target="_blank" rel="noopener">🧭 Petunjuk arah ke titik ini</a></div>
      <div style="margin-top:5px"><a href="{detail_url}" target="_blank" rel="noopener">Buka lokasi di Google Maps</a></div>
    </div>"""
    color = "green" if str(r.get("status")) in ("1", "1.0") else "gray"
    folium.Marker(
        [lat, lon],
        tooltip=f"{name} · ID {safe(r.get('id'))}",
        popup=folium.Popup(popup_html, max_width=320),
        icon=folium.Icon(color=color, icon="map-marker", prefix="fa")
    ).add_to(group)

folium.LayerControl(collapsed=True).add_to(m)
map_result = st_folium(m, height=460, use_container_width=True, returned_objects=["last_object_clicked", "last_object_clicked_popup"])

# Clicked marker coords, then resolve nearest source row for details
clicked = map_result.get("last_object_clicked") if map_result else None
chosen_idx = None
if clicked and clicked.get("lat") is not None and clicked.get("lng") is not None:
    distances = (filtered["latitude"] - float(clicked["lat"]))**2 + (filtered["longitude"] - float(clicked["lng"]))**2
    chosen_idx = distances.idxmin()
    # prevent accidental selection when click is far from any marker
    if float(distances.loc[chosen_idx]) > 0.0000005:
        chosen_idx = None

st.markdown("<div class='section-label'>Detail titik</div>", unsafe_allow_html=True)
options = filtered.index.tolist()
def label_for(i):
    r = filtered.loc[i]
    return f"{safe(r.get('nama_krt'), safe(r.get('deskripsi_project'), 'Landmark'))} | ID {safe(r.get('id'))}"
default_position = options.index(chosen_idx) if chosen_idx in options else 0
selected_index = st.selectbox("Pilih titik untuk melihat detail", options, index=default_position, format_func=label_for)
r = filtered.loc[selected_index]
name = safe(r.get("nama_krt"), safe(r.get("deskripsi_project"), "Landmark"))
lat, lon = float(r["latitude"]), float(r["longitude"])
d1,d2,d3 = st.columns(3)
d1.markdown(f"**Nama / KRT**  \n{safe(r.get('nama_krt'))}")
d2.markdown(f"**Kategori / tipe**  \n{safe(r.get('kategori_landmark'))} / {safe(r.get('tipe_landmark'))}")
d3.markdown(f"**Koordinat**  \n`{lat:.6f}, {lon:.6f}`")
with st.expander("Informasi lengkap", expanded=True):
    detail_cols = st.columns(3)
    fields = [
        ("ID", "id"), ("WID", "wid"), ("Deskripsi proyek", "deskripsi_project"),
        ("ID desa", "iddesa"), ("Status", "status"), ("Akurasi GPS (m)", "accuracy"),
        ("Dibuat oleh", "user_creator_nama"), ("Waktu dibuat", "user_created_at"),
        ("Waktu unggah", "user_upload_at"), ("Jumlah ART tani", "jumlah_art_tani"),
        ("Subsektor", "subsektor"), ("Kode kategori", "kode_kategori"),
        ("Kode tipe landmark", "kode_landmark_tipe")
    ]
    for j,(label,key) in enumerate(fields):
        with detail_cols[j % 3]:
            st.markdown(f"**{label}**  \n{safe(r.get(key))}")
    photo = safe(r.get("photo_url"), "")
    if photo.startswith("http"):
        st.markdown(f"[Lihat foto landmark]({photo})")
directions = "https://www.google.com/maps/dir/?api=1&destination=" + quote(f"{lat},{lon}") + "&travelmode=driving"
google_maps = "https://www.google.com/maps/search/?api=1&query=" + quote(f"{lat},{lon}")
b1,b2 = st.columns(2)
b1.link_button("🧭 Tunjukkan arah ke titik ini", directions, use_container_width=True)
b2.link_button("📍 Buka di Google Maps", google_maps, use_container_width=True)

with st.expander("Tabel data yang sedang ditampilkan"):
    visible_cols = [c for c in ["id","wid","nama_krt","kategori_landmark","tipe_landmark","deskripsi_project","latitude","longitude","status"] if c in filtered.columns]
    st.dataframe(filtered[visible_cols].reset_index(drop=True), use_container_width=True, hide_index=True)
    st.download_button("Unduh data hasil filter (CSV)", filtered.to_csv(index=False).encode("utf-8-sig"),
                       file_name="landmark_hasil_filter.csv", mime="text/csv")

st.caption("Petunjuk arah dibuka melalui Google Maps. Peta dasar OpenStreetMap membutuhkan koneksi internet.")
