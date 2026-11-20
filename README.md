# EWS Monitoring Media & Isu Potensial

Sistem pemantau otomatis pemberitaan media online terkait TNI AD, dengan dashboard alert dan filter level 1–5.

> **Dokumentasi:**
> - Panduan lengkap (instalasi, konfigurasi, maintenance): [`USER_MANUAL.md`](USER_MANUAL.md)
> - Panduan singkat operator (non-teknis): [`PANDUAN_OPERATOR.md`](PANDUAN_OPERATOR.md)

## Struktur Proyek

```
ews-backend/
├── scraper/        # ambil artikel dari RSS feed
├── detector/       # keyword matching + scoring severity
├── api/            # FastAPI: dashboard + REST endpoint
├── models/             # SQLAlchemy models (Article, Alert, User)
├── templates/          # HTML dashboard
├── auth_utils.py       # hash & verifikasi password (dipakai bersama)
├── seed_dummy.py       # seed artikel/alert + user dummy
├── seed_user_dummy.py  # seed user dummy saja
├── config.py           # semua konfigurasi & keyword library
├── database.py         # setup DB session
├── scheduler.py        # APScheduler job periodik
├── docker/             # legacy, tidak dipakai
└── docker-compose.yml  # legacy, tidak dipakai
```

## Cara Menjalankan (PostgreSQL langsung, tanpa Docker)

PostgreSQL dipasang langsung di host/VM. Driver `pg8000` sudah ada di `requirements.txt`
(pure Python, tidak butuh `pg_config`/`psycopg2`).

### 1. Siapkan PostgreSQL di server/VM

```bash
# Debian/Ubuntu
sudo apt install -y postgresql
sudo systemctl enable --now postgresql

# Buat user & database
sudo -u postgres psql -c "CREATE USER ews_user WITH PASSWORD 'ews_pass';"
sudo -u postgres createdb -O ews_user ews_db
```

Kalau koneksi localhost ditolak dengan `Ident authentication failed`, ubah baris `host`
di `pg_hba.conf` menjadi `scram-sha-256` (atau `md5`) untuk `127.0.0.1/32`, lalu
`sudo systemctl reload postgresql`.

### 2. Jalankan aplikasi

**Linux (BE / VM Linux):**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
python seed_dummy.py          # opsional, data dummy
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
Jika aktivasi venv ditolak: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

**Server admin (VM):** untuk akses LAN, ganti `--reload` dengan
`--host 0.0.0.0 --port 8000`, lalu buka port **8000** di firewall VM.
File `.env` tidak ikut ter-commit — harus dibuat manual di VM.
Data tersimpan di PostgreSQL (bukan file DB), jadi backup pakai `pg_dump`.

**Windows yang tidak install Postgres lokal:** cukup arahkan `DATABASE_URL` di `.env`
ke IP VM, mis. `postgresql+pg8000://ews_user:ews_pass@<IP-VM>:5432/ews_db`,
dan buka port **5432** di firewall VM.

Akun dummy: `admin`/`admin123`, `staff`/`staff123`, `operator1`/`operator123`,
`operator2`/`operator123`, `analis1`/`analis123`, `viewer1`/`viewer123`.

## Catatan Docker (legacy, jangan dipakai)

`docker-compose.yml` dan `docker/` masih ada di repo sebagai arsip, tapi jalur utama
sekarang PostgreSQL langsung di host/VM. Tidak perlu `docker compose up`.

## Sumber Berita

Sumber default sudah aktif otomatis (tidak perlu diisi di `.env`):

- **Media nasional:** ANTARA (terkini, hukum, politik, ekonomi), CNN Indonesia, Sindonews, CNBC Indonesia, Tribunnews, JPNN, iNews, Katadata
- **Instansi pemerintah:** Kemhan, BNN
- **Agregator (RSS):** Google News (berita populer + pencarian `TNI AD`, `Kodam`, `TNI Angkatan Darat`, `Kemhan`, `Oknum TNI`, `Prajurit TNI`)
- **Regional ANTARA:** 26 feed dari Sumatra, Jawa, Bali & Nusa Tenggara, Kalimantan, Sulawesi, Maluku, dan Papua

Untuk menambah feed RSS lain, isi `RSS_FEEDS` di `.env` (dipisahkan koma). Daftar lengkap ada di
`DEFAULT_RSS_FEEDS` dan `REGIONAL_RSS_FEEDS` pada `config.py`.

### Google Custom Search Engine (CSE) API (opsional)

Selain RSS, sistem dapat mengambil hasil dari [Google Programmable Search Engine](https://programmablesearchengine.google.com/) melalui JSON API:

1. Buat API key di [Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview)
2. Buat Search Engine (CSE) dan salin **Search engine ID** (`cx`)
3. Isi variabel berikut di `.env`:
   - `GOOGLE_CSE_API_KEY` — API key
   - `GOOGLE_CSE_ID` — Search engine ID (`cx`)
   - `GOOGLE_CSE_QUERIES` — (opsional) daftar query dipisah koma; default: `TNI AD,Kodam,TNI Angkatan Darat,Oknum TNI,Prajurit TNI`
   - `GOOGLE_CSE_NUM_RESULTS` — (opsional) jumlah hasil per query, maks 10 (default 10)

Jika `GOOGLE_CSE_API_KEY` dan `GOOGLE_CSE_ID` diisi, hasil CSE akan otomatis ikut diambil pada setiap siklus scrape dan diproses seperti sumber lainnya (deduplikasi, deteksi, alert).

## Menyesuaikan Keyword Library

Semua kata kunci ada di `config.py`:
- `CONTEXT_KEYWORDS`: kata yang menandakan artikel relevan dengan TNI AD
- `NEGATIVE_KEYWORDS`: kategori kata sensitif beserta bobotnya
- `ALERT_THRESHOLD`: skor minimum supaya alert dibuat
- `LEVEL_RANGES`: pemetaan skor ke level alert 1–5 (dipakai filter dashboard & API)

Tinggal tambah/kurangi kata di dictionary ini tanpa perlu ubah logic lain.

## Level Alert (1–5)

Level dihitung otomatis dari `severity_score`, bisa difilter di dashboard atau lewat query param `?level=`.

| Level | Rentang skor |
|---|---|
| 1 | < 3 |
| 2 | 3–4 |
| 3 | 5–6 |
| 4 | 7–8 |
| 5 | ≥ 9 |

## API Endpoints

- `GET /` — dashboard riwayat alert (HTML), filter dengan `?level=1` s.d. `?level=5`
- `GET /api/status` — status sistem (total artikel, total alert, waktu scrape terakhir)
- `GET /api/alerts?level=1&limit=50` — daftar alert dalam format JSON (`level` opsional)
