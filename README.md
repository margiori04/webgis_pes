# WebGIS Landmark (Python)

WebGIS interaktif berbasis Streamlit + Folium untuk melihat titik koordinat dari file Excel landmark.

## Fitur
- Peta interaktif dengan marker dan clustering untuk titik yang berdekatan.
- Klik marker untuk melihat ringkasan dan tautan petunjuk arah.
- Pilih titik untuk melihat detail atribut lengkap.
- Filter kata kunci, kategori, tipe, dan status.
- Tombol petunjuk arah ke titik terpilih melalui Google Maps.
- Tabel data hasil filter dan unduh CSV.
- Tampilan responsif untuk desktop maupun perangkat mobile.

## Menjalankan di komputer
Disarankan Python 3.10 atau lebih baru.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Setelah berjalan, buka alamat lokal yang ditampilkan Streamlit (biasanya http://localhost:8501).

## Deploy agar bisa diakses pengguna lain
Unggah folder proyek ini ke server Python atau layanan hosting yang mendukung Streamlit. Jangan mengunggah data yang memuat informasi pribadi ke layanan publik tanpa memastikan izin dan pengaturan akses yang sesuai.

## Catatan
- Koordinat berasal dari file Excel sumber; titik tanpa koordinat valid tidak ditampilkan.
- Peta dasar dan petunjuk arah memerlukan internet.
- Tombol arah membuka Google Maps dengan titik tujuan yang dipilih; Google Maps dapat memakai lokasi perangkat untuk menentukan titik awal jika diizinkan.
