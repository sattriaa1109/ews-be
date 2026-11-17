# Panduan Operator — EWS Monitoring Media TNI AD

Panduan ringkas untuk tim yang mengoperasikan sistem setiap hari.
Tidak perlu paham pemrograman — cukup ikuti langkah-langkah berikut.

---

## 1. Apa Fungsi Sistem Ini?

Sistem memantau berita dari internet (media online) secara otomatis, lalu:

1. **Mengumpulkan** berita dari banyak sumber (ANTARA, CNN Indonesia, Sindonews, CNBC Indonesia, Tribunnews, JPNN, iNews, Katadata, Kemhan, BNN, Google News, dan ANTARA regional) — otomatis setiap beberapa menit.
2. **Mendeteksi** berita negatif/sensitif yang menyangkut TNI AD (mis. korupsi, kekerasan, pelanggaran HAM).
3. **Menampilkan** berita yang terdeteksi di **dashboard web**.
4. **Memberi tahu** lewat **Telegram** secara otomatis.

Kesimpulannya: operator tidak perlu memantau media satu-satu. Cukup buka dashboard atau cek Telegram.

---

## 2. Cara Membuka Dashboard

1. Buka browser (Chrome/Edge/Firefox).
2. Ketik alamat dashboard:
   ```
   http://localhost:8000
   ```
   (atau alamat server yang sudah disiapkan tim IT, mis. `http://192.168.1.10:8000`)
3. Dashboard akan terlihat seperti ini:

   - **Baris ringkasan (atas):** Total artikel di-scrape dan Total alert.
   - **Tabel:** daftar alert berisi waktu, judul, sumber, skor, kategori, kata terdeteksi, dan status kirim.
   - Halaman **otomatis memperbarui tiap 30 detik** — tidak perlu menekan refresh.

### Cara membaca tabel

| Kolom | Artinya |
|---|---|
| **Waktu** | Kapan alert terdeteksi |
| **Judul** | Judul berita. **Klik** untuk membuka berita aslinya |
| **Sumber** | Media asal berita |
| **Skor** | Tingkat keparahan. **Merah** = serius (≥ 6), **kuning** = sedang |
| **Kategori** | Jenis masalah (hukum, kekerasan, HAM, disiplin, viral) |
| **Kata Terdeteksi** | Kata kunci negatif yang muncul di berita |
| **Status Kirim** | **Terkirim** = sudah masuk Telegram, **Gagal/Pending** = belum masuk |

---

## 3. Notifikasi Telegram

- Semua alert juga dikirim ke grup Telegram yang sudah ditentukan.
- Format pesan: peringatan berisi judul, sumber, skor, kategori, dan tombol **"Baca artikel"**.
- Jika tidak ada pesan yang masuk, cek langkah **Pemecahan Masalah** di bawah.

---

## 4. Pemecahan Masalah (untuk operator)

**Dashboard tidak bisa dibuka / koneksi ditolak**
- Sistem mungkin sedang mati. Hubungi tim IT, atau cek apakah server menyala.

**Dashboard terbuka, tapi tabel kosong "Belum ada alert."**
- Itu artinya belum ada berita negatif yang memenuhi kriteria — **bukan kerusakan**.
- Lihat **Total artikel di-scrape** di baris ringkasan:
  - Jika angka total artikel **besar** (ratusan) → sistem berjalan normal, cuma belum ada berita yang cocok.
  - Jika angka total artikel **0** → ada masalah pengambilan berita. Hubungi tim IT.

**Tidak ada notifikasi Telegram, padahal dashboard ada alert**
- Buka alert tersebut, cek kolom **Status Kirim**.
- Jika **Gagal/Pending**, berarti token/chat ID bot salah atau bot dikeluarkan dari grup. Hubungi tim IT.

---

## 5. Apa yang Harus Dilakukan Setiap Hari?

1. Buka dashboard **minimal 1–2 kali sehari** (pagi & sore).
2. Cek alert yang masuk — baca judulnya, klik untuk melihat berita asli.
3. Pastikan **Total artikel di-scrape** bertambah (artinya sistem masih mengambil berita).
4. Konfirmasi notifikasi Telegram masih masuk.

> Jika ada alert dengan skor tinggi (merah), segera laporkan ke pimpinan/pejabat terkait.

---

## 6. Informasi Teknis untuk Tim IT

| Item | Nilai |
|---|---|
| Port dashboard | `8000` |
| Endpoint status | `http://<server>:8000/api/status` |
| Endpoint data alert (JSON) | `http://<server>:8000/api/alerts?limit=50` |
| Container aplikasi | `ews_app` |
| Container database | `ews_db` |
| Log aplikasi | `docker compose logs -f app` |
| Interval pengambilan berita | sesuai `SCRAPE_INTERVAL_MINUTES` di `.env` |

Panduan teknis lengkap (instalasi, konfigurasi kata kunci, maintenance):
lihat `USER_MANUAL.md`.
