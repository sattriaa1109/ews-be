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
├── models/         # SQLAlchemy models (Article, Alert)
├── templates/      # HTML dashboard
├── docker/         # Dockerfile
├── config.py       # semua konfigurasi & keyword library
├── database.py     # setup DB session
├── scheduler.py    # APScheduler job periodik
└── docker-compose.yml
```

## Cara Menjalankan (Development)

1. Copy `.env.example` jadi `.env`, lalu sesuaikan `DATABASE_URL` bila perlu
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Jalankan server:
   ```
   uvicorn api.main:app --reload
   ```
4. Buka dashboard di `http://localhost:8000`

## Cara Menjalankan (Docker - untuk serah terima ke tim TKJ)

```
docker compose up -d --build
```

Ini akan menjalankan 2 container:
- `ews_app` — aplikasi FastAPI + scraper + scheduler (port 8000)
- `ews_db` — PostgreSQL (port 5432)

Tim TKJ tinggal:
- Pastikan port 8000 dibuka di firewall (UFW) sesuai kebutuhan akses
- Setup reverse proxy (nginx) kalau perlu domain/HTTPS
- Pastikan `docker compose up -d` dijalankan otomatis saat server boot (bisa pakai `systemd` service atau `restart: unless-stopped` yang sudah diatur di compose file)
- Monitoring resource container bisa pakai `docker stats` atau tools seperti Portainer

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
