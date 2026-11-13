# EWS Monitoring Media & Isu Potensial

Sistem pemantau otomatis pemberitaan media online terkait TNI AD, dengan alert real-time ke Telegram.

> **Dokumentasi:**
> - Panduan lengkap (instalasi, konfigurasi, maintenance): [`USER_MANUAL.md`](USER_MANUAL.md)
> - Panduan singkat operator (non-teknis): [`PANDUAN_OPERATOR.md`](PANDUAN_OPERATOR.md)

## Struktur Proyek

```
ews-backend/
├── scraper/        # ambil artikel dari RSS feed
├── detector/       # keyword matching + scoring severity
├── notifier/       # kirim alert ke Telegram
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

1. Copy `.env.example` jadi `.env`, isi `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID`
   - Buat bot lewat @BotFather di Telegram untuk dapat token
   - Chat ID bisa didapat dengan invite bot ke grup lalu cek lewat `https://api.telegram.org/bot<TOKEN>/getUpdates`
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
- **Agregator:** Google News (berita populer + pencarian `TNI AD`, `Kodam`, `TNI Angkatan Darat`, `Kemhan`, `Oknum TNI`, `Prajurit TNI`)
- **Regional ANTARA:** 26 feed dari Sumatra, Jawa, Bali & Nusa Tenggara, Kalimantan, Sulawesi, Maluku, dan Papua

Untuk menambah feed lain, isi `RSS_FEEDS` di `.env` (dipisahkan koma). Daftar lengkap ada di
`DEFAULT_RSS_FEEDS` dan `REGIONAL_RSS_FEEDS` pada `config.py`.

## Menyesuaikan Keyword Library

Semua kata kunci ada di `config.py`:
- `CONTEXT_KEYWORDS`: kata yang menandakan artikel relevan dengan TNI AD
- `NEGATIVE_KEYWORDS`: kategori kata sensitif beserta bobotnya
- `ALERT_THRESHOLD`: skor minimum supaya alert dikirim

Tinggal tambah/kurangi kata di dictionary ini tanpa perlu ubah logic lain.

## API Endpoints

- `GET /` — dashboard riwayat alert (HTML)
- `GET /api/status` — status sistem (total artikel, total alert, waktu scrape terakhir)
- `GET /api/alerts` — daftar alert dalam format JSON
