# User Manual — EWS Monitoring Media TNI AD

Sistem pemantau otomatis pemberitaan media online terkait TNI Angkatan Darat.
Sistem ini mengambil berita dari RSS feed, mendeteksi berita bernada negatif/sensitif,
lalu menampilkannya di dashboard web dan mengirim peringatan ke Telegram secara real-time.

> **Panduan singkat untuk tim operator (non-teknis):** lihat `PANDUAN_OPERATOR.md`.

---

## Ringkasan Cepat (Quick Start)

```
1. Salin .env:          cp .env.example .env
2. Isi .env:            DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RSS_FEEDS
3. Jalankan (Docker):   docker compose up -d --build
4. Buka dashboard:      http://localhost:8000
5. Cek status:          http://localhost:8000/api/status
```

> Jika hanya ingin lihat dashboard di komputer sendiri tanpa Docker & Telegram,
> isi `.env` dengan `DATABASE_URL=sqlite:///./ews_local.db`, kosongkan token Telegram,
> lalu `pip install -r requirements.txt` dan `uvicorn api.main:app --reload`.

---

## 1. Komponen Sistem

| Komponen | Peran |
|---|---|
| **Scraper** (`scraper/scraper.py`) | Mengunduh artikel dari daftar RSS feed dan menyimpannya ke database |
| **Detector** (`detector/detector.py`) | Menilai artikel: apakah relevan dengan TNI AD dan mengandung kata negatif, lalu memberi skor |
| **Notifier** (`notifier/telegram_bot.py`) | Mengirim alert ke grup/channel Telegram |
| **Scheduler** (`scheduler.py`) | Menjalankan scraper otomatis setiap interval tertentu |
| **API + Dashboard** (`api/main.py`, `templates/dashboard.html`) | Halaman web untuk melihat riwayat alert + endpoint JSON untuk frontend lain |
| **Database** | PostgreSQL (produksi) atau SQLite (cadangan) |

### Alur kerja

```
RSS Feed → Scraper → Database → Detector (skor severity)
                                    │
                                    ├─ ≥ ALERT_THRESHOLD → buat Alert → Kirim Telegram
                                    └─ < ALERT_THRESHOLD → dilewati
Dashboard / API ← baca dari Database
```

1. Scraper mengambil artikel baru dari tiap feed (berjalan tiap `SCRAPE_INTERVAL_MINUTES` menit, dan sekali saat aplikasi start).
2. Setiap artikel baru diperiksa oleh Detector:
   - Harus mengandung minimal satu **kata konteks** (mis. "TNI AD", "Kodam", "polisi").
   - Dihitung skor berdasarkan **kata negatif** yang muncul × bobot kategorinya.
   - Jika skor **≥ ALERT_THRESHOLD**, dibuat record **Alert** dan dikirim ke Telegram.
3. Alert yang sudah dibuat tampil di dashboard `GET /` dan bisa diakses lewat `GET /api/alerts`.

---

## 2. Instalasi & Menjalankan

### A. Menjalankan dengan Docker (cara yang disarankan)

Persyaratan: Docker & Docker Compose terpasang.

1. Siapkan konfigurasi:
   ```bash
   cp .env.example .env
   ```
2. Isi `.env` (lihat bagian **Konfigurasi**).
3. Jalankan:
   ```bash
   docker compose up -d --build
   ```
4. Buka dashboard di `http://localhost:8000`.

Perintah berguna lainnya:

```bash
docker compose logs -f app   # lihat log aplikasi
docker compose restart app   # restart aplikasi
docker compose down          # hentikan semua container
```

### B. Menjalankan tanpa Docker (development)

1. Persyaratan: Python 3.10+, PostgreSQL berjalan di `localhost:5432` (atau pakai SQLite).
2. Buat database PostgreSQL:
   ```bash
   createdb ews_db
   ```
3. Siapkan `.env` (untuk SQLite, ganti `DATABASE_URL` menjadi `sqlite:///./ews_local.db`).
4. Install dependency:
   ```bash
   pip install -r requirements.txt
   ```
5. Jalankan server:
   ```bash
   uvicorn api.main:app --reload
   ```
6. Buka dashboard di `http://localhost:8000`.

---

## 3. Konfigurasi

### A. File `.env`

| Variabel | Deskripsi |
|---|---|
| `DATABASE_URL` | Koneksi database. Contoh Postgres: `postgresql://ews_user:ews_pass@localhost:5432/ews_db`. Contoh SQLite: `sqlite:///./ews_local.db` |
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram (dari @BotFather). Kosongkan untuk menonaktifkan notifikasi |
| `TELEGRAM_CHAT_ID` | ID chat/group/channel tujuan notifikasi |
| `SCRAPE_INTERVAL_MINUTES` | Interval scraping dalam menit (mis. `5` = tiap 5 menit) |
| `RSS_FEEDS` | Daftar URL RSS, dipisahkan koma. Contoh: `https://www.antaranews.com/rss/terkini.xml,https://www.kemhan.go.id/feed` |

### B. Kata kunci di `config.py`

Semua aturan deteksi dikendalikan di `config.py`. Tidak perlu mengubah kode lain.

| Pengaturan | Fungsi |
|---|---|
| `CONTEXT_KEYWORDS` | Artikel harus mengandung minimal salah satu kata ini agar dianggap relevan (mengurangi false positive) |
| `NEGATIVE_KEYWORDS` | Kategori kata sensitif + bobot. Skor = jumlah kata yang cocok × bobot kategori |
| `ALERT_THRESHOLD` | Skor minimum agar artikel menjadi alert. Default `2` |

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

## 4. Setup Notifikasi Telegram

1. Di Telegram, cari **@BotFather**, buat bot baru dengan perintah `/newbot`, ikuti instruksinya. Simpan token yang diberikan.
2. Buat grup (atau channel) tempat notifikasi dikirim, lalu tambahkan bot ke grup tersebut sebagai anggota.
3. Ambil `chat_id`:
   - Kirim satu pesan apa saja ke grup yang berisi bot.
   - Buka di browser:
     ```
     https://api.telegram.org/bot<TOKEN>/getUpdates
     ```
   - Cari nilai `chat` → `id` di hasilnya (untuk grup biasanya angka negatif, mis. `-1001234567890`).
4. Isi `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` di `.env`, lalu restart aplikasi.

---

## 5. Menggunakan Dashboard

Buka `http://localhost:8000` (halaman ini auto-refresh tiap 30 detik).

| Kolom | Penjelasan |
|---|---|
| **Waktu** | Waktu alert dibuat |
| **Judul** | Judul artikel (klik untuk membuka sumbernya) |
| **Sumber** | Nama feed/media asal |
| **Skor** | Skor severity (merah = ≥ 6, kuning = di bawah itu) |
| **Kategori** | Kategori negatif yang terdeteksi |
| **Kata Terdeteksi** | Kata kunci negatif yang muncul |
| **Status Kirim** | `Terkirim` = sudah masuk Telegram, `Gagal/Pending` = belum/kegagalan |

Bagian atas halaman menampilkan ringkasan: **Total artikel di-scrape** dan **Total alert**.

### Endpoint API

| Endpoint | Fungsi |
|---|---|
| `GET /` | Halaman dashboard (HTML) |
| `GET /api/status` | Status sistem: total artikel, total alert, waktu scrape terakhir |
| `GET /api/alerts?limit=50` | Daftar alert terbaru dalam format JSON (untuk frontend lain) |

Contoh pemakaian:
```bash
curl http://localhost:8000/api/status
curl "http://localhost:8000/api/alerts?limit=10"
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

> Skrip ini hanya membuat alert, **tidak** mengirim notifikasi Telegram.

### Menghapus semua alert

```bash
# PostgreSQL
PGPASSWORD=ews_pass psql -h localhost -U ews_user -d ews_db -c "DELETE FROM alerts;"
```

### Membaca log

```bash
docker compose logs -f app     # dengan Docker
uvicorn api.main:app --reload  # tanpa Docker: lihat output konsol
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
| `Total artikel` tetap 0 | RSS feed tidak bisa diakses, atau `RSS_FEEDS` kosong di `.env`. Cek log: `docker compose logs app` |
| Notifikasi Telegram tidak terkirim | `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` belum diisi, atau chat_id salah. Cek status "Gagal/Pending" di dashboard dan log notifier |
| Setelah ubah kata kunci hasilnya tidak berubah | Perubahan hanya berlaku untuk artikel baru. Evaluasi ulang data lama (lihat bagian Pemeliharaan) |
| Error koneksi database | Pastikan PostgreSQL berjalan dan `DATABASE_URL` di `.env` benar |

---

## 8. Penyerahan ke Tim Ops (TKJ)

Untuk produksi / serah terima:
1. Jalankan `docker compose up -d --build`.
2. Pastikan port **8000** terbuka di firewall (mis. `ufw allow 8000`).
3. Jika perlu domain/HTTPS, pasang reverse proxy (mis. nginx) di depan port 8000.
4. Pastikan service berjalan otomatis saat server boot (`restart: unless-stopped` sudah diatur di `docker-compose.yml`).
5. Pantau resource dengan `docker stats` atau Portainer.
