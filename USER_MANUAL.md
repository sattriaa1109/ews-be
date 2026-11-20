# User Manual — EWS Monitoring Media TNI AD

Sistem pemantau otomatis pemberitaan media online terkait TNI Angkatan Darat.
Sistem ini mengambil berita dari RSS feed, mendeteksi berita bernada negatif/sensitif,
lalu menampilkannya di dashboard web. Alert bisa difilter berdasarkan level 1–5.

> **Panduan singkat untuk tim operator (non-teknis):** lihat `PANDUAN_OPERATOR.md`.

---

## Ringkasan Cepat (Quick Start)

```
1. Siapkan PostgreSQL di host/VM, lalu buat user & database (lihat bagian 2)
2. Salin .env:          cp .env.example .env
3. Isi .env:            DATABASE_URL (host Postgres), RSS_FEEDS (opsional)
4. Install dependency:  pip install -r requirements.txt
5. Jalankan:            uvicorn api.main:app --reload
6. Buka dashboard:      http://localhost:8000
7. Cek status:          http://localhost:8000/api/status
```

> Tidak pakai Docker. Driver `pg8000` sudah termasuk di requirements.

---

## 1. Komponen Sistem

| Komponen | Peran |
|---|---|
| **Scraper** (`scraper/scraper.py`) | Mengunduh artikel dari daftar RSS feed dan menyimpannya ke database |
| **Detector** (`detector/detector.py`) | Menilai artikel: apakah relevan dengan TNI AD dan mengandung kata negatif, lalu memberi skor |
| **Config** (`config.py`) | Mengatur kata kunci, threshold, dan pemetaan skor ke level 1–5 |
| **Scheduler** (`scheduler.py`) | Menjalankan scraper otomatis setiap interval tertentu |
| **API + Dashboard** (`api/main.py`, `templates/dashboard.html`) | Halaman web untuk melihat riwayat alert + endpoint JSON untuk frontend lain |
| **Database** | PostgreSQL di host/VM (driver `pg8000`, tanpa Docker) |

### Alur kerja

```
RSS Feed → Scraper → Database → Detector (skor severity)
                                    │
                                    ├─ ≥ ALERT_THRESHOLD → buat Alert (level 1–5)
                                    └─ < ALERT_THRESHOLD → dilewati
Dashboard / API ← baca dari Database (bisa difilter per level)
```

1. Scraper mengambil artikel baru dari tiap feed (berjalan tiap `SCRAPE_INTERVAL_MINUTES` menit, dan sekali saat aplikasi start).
2. Setiap artikel baru diperiksa oleh Detector:
   - Harus mengandung minimal satu **kata konteks** (mis. "TNI AD", "Kodam", "polisi").
   - Dihitung skor berdasarkan **kata negatif** yang muncul × bobot kategorinya.
   - Jika skor **≥ ALERT_THRESHOLD**, dibuat record **Alert** dengan level 1–5.
3. Alert yang sudah dibuat tampil di dashboard `GET /` dan bisa diakses lewat `GET /api/alerts`.

---

## 2. Instalasi & Menjalankan

### A. Siapkan PostgreSQL (tanpa Docker)

```bash
# Debian/Ubuntu
sudo apt install -y postgresql
sudo systemctl enable --now postgresql

# Buat user & database
sudo -u postgres psql -c "CREATE USER ews_user WITH PASSWORD 'ews_pass';"
sudo -u postgres createdb -O ews_user ews_db
```

Jika koneksi localhost ditolak dengan `Ident authentication failed`, ubah metode
autentikasi `host` untuk `127.0.0.1/32` di `pg_hba.conf` menjadi `scram-sha-256`
(atau `md5`), lalu `sudo systemctl reload postgresql`.

### B. Jalankan aplikasi

Persyaratan: Python 3.10+. Jalankan dari folder root proyek.

**Linux (BE / VM Linux):**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
python seed_dummy.py          # opsional
uvicorn api.main:app --reload
```

**Windows (PowerShell):**
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
python seed_dummy.py
uvicorn api.main:app --reload
```
Jika aktivasi venv ditolak, jalankan dulu
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

Windows yang tidak install Postgres lokal bisa arahkan `DATABASE_URL` di `.env` ke
`postgresql+pg8000://ews_user:ews_pass@<IP-VM>:5432/ews_db` (buka port 5432 di firewall VM).

**VM server/admin:** pakai `uvicorn api.main:app --host 0.0.0.0 --port 8000`
supaya bisa diakses dari komputer lain, lalu buka port 8000 di firewall VM.
File `.env` tidak ikut ter-commit, jadi harus dibuat manual di VM.
Data tersimpan di PostgreSQL — backup pakai `pg_dump`, bukan salin file DB.

Akun dummy yang tersedia: `admin`/`admin123`, `staff`/`staff123`,
`operator1`/`operator123`, `operator2`/`operator123`, `analis1`/`analis123`,
`viewer1`/`viewer123`.

### C. Docker (legacy, jangan dipakai)

`docker-compose.yml` dan `docker/` hanya arsip. Jalur utama sekarang PostgreSQL
langsung di host/VM; tidak perlu `docker compose up`.

---

## 3. Konfigurasi

### A. File `.env`

| Variabel | Deskripsi |
|---|---|
| `DATABASE_URL` | Koneksi PostgreSQL. Default: `postgresql+pg8000://ews_user:ews_pass@localhost:5432/ews_db`. Ganti `localhost` dengan IP VM jika diakses dari komputer lain |
| `SCRAPE_INTERVAL_MINUTES` | Interval scraping dalam menit (mis. `5` = tiap 5 menit) |
| `SCRAPER_MAX_WORKERS` | Jumlah feed yang diunduh secara paralel. Default `8` |
| `RSS_FEEDS` | **Tambahan** URL RSS, dipisahkan koma. Sumber default sudah aktif otomatis dari `config.py`, jadi variabel ini boleh dikosongkan |

Sumber berita default yang sudah aktif tanpa konfigurasi tambahan:

- **Media nasional:** ANTARA (terkini, hukum, politik, ekonomi), CNN Indonesia, Sindonews, CNBC Indonesia, Tribunnews, JPNN, iNews, Katadata
- **Instansi pemerintah:** Kementerian Pertahanan (Kemhan), Badan Narkotika Nasional (BNN)
- **Agregator:** Google News (berita populer + pencarian kata kunci `TNI AD`, `Kodam`, `TNI Angkatan Darat`, `Kemhan`, `Oknum TNI`, `Prajurit TNI`)
- **Regional ANTARA:** Aceh, Sumut, Sumbar, Riau, Kepri, Jambi, Bengkulu, Sumsel, Babel, Lampung, Jabar, Jateng, Jatim, Bali, Mataram, Kupang, Kaltim, Kalteng, Kalbar, Kalsel, Makassar, Manado, Sulteng, Sultra, Ambon, dan Papua

### B. Kata kunci di `config.py`

Semua aturan deteksi dikendalikan di `config.py`. Tidak perlu mengubah kode lain.

| Pengaturan | Fungsi |
|---|---|
| `CONTEXT_KEYWORDS` | Artikel harus mengandung minimal salah satu kata ini agar dianggap relevan (mengurangi false positive) |
| `NEGATIVE_KEYWORDS` | Kategori kata sensitif + bobot. Skor = jumlah kata yang cocok × bobot kategori |
| `ALERT_THRESHOLD` | Skor minimum agar artikel menjadi alert. Default `2` |
| `LEVEL_RANGES` / `get_alert_level()` | Pemetaan skor ke level 1–5 yang dipakai di dashboard & API |

Daftar kategori `NEGATIVE_KEYWORDS` beserta bobotnya:

| Kategori | Contoh kata | Bobot |
|---|---|---|
| `pelanggaran_hukum` | korupsi, suap, pungli | 3 |
| `kekerasan` | kekerasan, penembakan, bentrok | 3 |
| `ham` | pelanggaran HAM, penyiksaan, hilang paksa | 4 |
| `disiplin_internal` | desersi, oknum, sanksi | 2 |
| `isu_viral` | viral, trending, heboh | 1 |

**Contoh perhitungan skor:** artikel berjudul *"Oknum TNI AD diduga terlibat korupsi"*:
- "TNI AD" → konteks cocok.
- "oknum" (bobot 2) + "korupsi" (bobot 3) → skor = 5.
- Karena 5 ≥ 2, artikel menjadi alert.

> **Catatan penting:** perubahan `config.py` hanya berlaku untuk **artikel baru** yang di-scrape setelahnya. Artikel lama tidak dievaluasi ulang otomatis. Untuk mengevaluasi ulang data lama, jalankan skrip di bagian **Pemeliharaan**.

---

## 4. Level Alert (1–5)

Level dihitung otomatis dari `severity_score`, tidak perlu diisi manual:

| Level | Rentang skor | Keterangan |
|---|---|---|
| 1 | < 3 | Rendah |
| 2 | 3–4 | Sedang |
| 3 | 5–6 | Cukup serius |
| 4 | 7–8 | Serius |
| 5 | ≥ 9 | Sangat serius |

Cara memakai filter:
- Di dashboard, pilih level pada **Filter Level** lalu klik **Terapkan** (pilihan langsung tersimpan di URL).
- Lewat API: `GET /api/alerts?level=4&limit=50`.
- Filter tetap aktif walau halaman auto-refresh tiap 30 detik.
- Batas tiap level bisa diubah lewat `LEVEL_RANGES` di `config.py`, lalu restart aplikasi.

---

## 5. Menggunakan Dashboard

Buka `http://localhost:8000` (halaman ini auto-refresh tiap 30 detik).

| Kolom | Penjelasan |
|---|---|
| **Waktu** | Waktu alert dibuat |
| **Judul** | Judul artikel (klik untuk membuka sumbernya) |
| **Sumber** | Nama feed/media asal |
| **Skor** | Skor severity (merah = ≥ 6, kuning = di bawah itu) |
| **Level** | Level 1–5 hasil pemetaan skor (lihat bagian 4) |
| **Kategori** | Kategori negatif yang terdeteksi |
| **Kata Terdeteksi** | Kata kunci negatif yang muncul |

Bagian atas halaman menampilkan ringkasan: **Total artikel di-scrape** dan **Total alert**.

### Endpoint API

| Endpoint | Fungsi |
|---|---|
| `GET /` | Halaman dashboard (HTML) |
| `GET /api/status` | Status sistem: total artikel, total alert, waktu scrape terakhir |
| `GET /api/alerts?level=1..5&limit=50` | Daftar alert terbaru dalam format JSON; `level` opsional |

Contoh pemakaian:
```bash
curl http://localhost:8000/api/status
curl "http://localhost:8000/api/alerts?level=5&limit=10"
```

---

## 6. Pemeliharaan

### Mengevaluasi ulang artikel lama setelah mengubah kata kunci

```bash
python -c "
from database import SessionLocal
from models.tables import Article, Alert
from detector.detector import evaluate_article

db = SessionLocal()
created = 0
for a in db.query(Article).all():
    if db.query(Alert).filter(Alert.article_id == a.id).first():
        continue
    if evaluate_article(db, a):
        created += 1
print('alert baru:', created)
db.close()
"
```

> Skrip ini hanya membuat alert; level tetap dihitung otomatis dari skor saat ditampilkan.

### Menghapus semua alert

```bash
# PostgreSQL
PGPASSWORD=ews_pass psql -h localhost -U ews_user -d ews_db -c "DELETE FROM alerts;"
```

### Membaca log

```bash
uvicorn api.main:app --reload                    # lihat output konsol
sudo journalctl -u ews-backend.service -f        # kalau pakai systemd
```

### Melihat isi database langsung

```bash
PGPASSWORD=ews_pass psql -h localhost -U ews_user -d ews_db
```

---

## 7. FAQ & Pemecahan Masalah

| Masalah | Kemungkinan penyebab & solusi |
|---|---|
| Dashboard tampil "Belum ada alert." | Belum ada artikel yang lolos threshold. Cek `Total artikel` di ringkasan — jika 0, berarti scraper gagal (lihat log). Jika angka artikel besar tapi alert 0, artinya tidak ada berita yang memenuhi konteks + skor. Coba longgarkan `CONTEXT_KEYWORDS` / turunkan `ALERT_THRESHOLD`, lalu evaluasi ulang data lama |
| `Total artikel` tetap 0 | RSS feed tidak bisa diakses, atau `RSS_FEEDS` kosong di `.env`. Cek output konsol / `journalctl -u ews-backend.service` |
| Filter level tidak berubah | Pastikan URL dashboard membawa `?level=...`. Klik **Hapus filter** untuk kembali ke semua level, atau cek `LEVEL_RANGES` di `config.py` |
| Setelah ubah kata kunci hasilnya tidak berubah | Perubahan hanya berlaku untuk artikel baru. Evaluasi ulang data lama (lihat bagian Pemeliharaan) |
| Error koneksi database | Pastikan PostgreSQL berjalan dan `DATABASE_URL` di `.env` benar |

---

## 8. Penyerahan ke Tim Ops (TKJ)

Untuk produksi / serah terima:
1. Pasang & siapkan PostgreSQL di VM (bagian 2A), lalu buat `.env` dari `.env.example`.
2. Jalankan aplikasi dengan `uvicorn api.main:app --host 0.0.0.0 --port 8000`.
3. Pastikan port **8000** terbuka di firewall (mis. `sudo ufw allow 8000/tcp`).
4. Jika perlu domain/HTTPS, pasang reverse proxy (mis. nginx) di depan port 8000.
5. Buat systemd service agar aplikasi otomatis jalan saat VM boot; backup database
   berkala dengan `pg_dump -U ews_user ews_db > backup.sql`.
6. Pantau resource VM dengan `top`/`htop`; tidak perlu Docker/Portainer.
