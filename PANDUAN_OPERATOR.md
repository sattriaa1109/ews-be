# Panduan Operator — EWS Monitoring Media TNI AD

Panduan ringkas untuk tim yang mengoperasikan sistem setiap hari.
Tidak perlu paham pemrograman — cukup ikuti langkah-langkah berikut.

---

## 1. Apa Fungsi Sistem Ini?

Sistem memantau berita dari internet (media online) secara otomatis, lalu:

1. **Mengumpulkan** berita dari banyak sumber (ANTARA, CNN Indonesia, Sindonews, CNBC Indonesia, Tribunnews, JPNN, iNews, Katadata, Kemhan, BNN, Google News, dan ANTARA regional) — otomatis setiap beberapa menit.
2. **Mendeteksi** berita negatif/sensitif yang menyangkut TNI AD (mis. korupsi, kekerasan, pelanggaran HAM).
3. **Menampilkan** berita yang terdeteksi di **dashboard web**, lengkap dengan skor dan level 1–5.

Kesimpulannya: operator tidak perlu memantau media satu-satu. Cukup buka dashboard dan gunakan filter level.

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
   - **Tabel:** daftar alert berisi waktu, judul, sumber, skor, level, kategori, dan kata terdeteksi.
   - Halaman **otomatis memperbarui tiap 30 detik** — tidak perlu menekan refresh.

### Cara membaca tabel

| Kolom | Artinya |
|---|---|
| **Waktu** | Kapan alert terdeteksi |
| **Judul** | Judul berita. **Klik** untuk membuka berita aslinya |
| **Sumber** | Media asal berita |
| **Skor** | Tingkat keparahan. **Merah** = serius (≥ 6), **kuning** = sedang |
| **Level** | 1 (rendah) s.d. 5 (sangat serius), dihitung otomatis dari skor |
| **Kategori** | Jenis masalah (hukum, kekerasan, HAM, disiplin, viral) |
| **Kata Terdeteksi** | Kata kunci negatif yang muncul di berita |

---

## 3. Filter Level di Dashboard

- Di atas tabel ada **Filter Level**: pilih **Semua level** atau level **1–5**.
- Level 1 = skor < 3, level 2 = 3–4, level 3 = 5–6, level 4 = 7–8, level 5 = ≥ 9.
- Pilihan langsung diterapkan dan tetap aktif saat halaman memperbarui diri tiap 30 detik.
- Klik **Hapus filter** untuk menampilkan semua alert kembali.

---

## 4. Pemecahan Masalah (untuk operator)

**Dashboard tidak bisa dibuka / koneksi ditolak**
- Sistem mungkin sedang mati. Hubungi tim IT, atau cek apakah server menyala.

**Dashboard terbuka, tapi tabel kosong "Belum ada alert."**
- Itu artinya belum ada berita negatif yang memenuhi kriteria — **bukan kerusakan**.
- Lihat **Total artikel di-scrape** di baris ringkasan:
  - Jika angka total artikel **besar** (ratusan) → sistem berjalan normal, cuma belum ada berita yang cocok.
  - Jika angka total artikel **0** → ada masalah pengambilan berita. Hubungi tim IT.

**Tabel hanya menampilkan level tertentu**
- Cek pilihan **Filter Level** di atas tabel. Pilih **Semua level** atau klik **Hapus filter** untuk melihat semua alert.

---

## 5. Apa yang Harus Dilakukan Setiap Hari?

1. Buka dashboard **minimal 1–2 kali sehari** (pagi & sore).
2. Cek alert yang masuk — baca judulnya, klik untuk melihat berita asli.
3. Pastikan **Total artikel di-scrape** bertambah (artinya sistem masih mengambil berita).
4. Gunakan filter level untuk fokus pada alert prioritas tinggi.

> Jika ada alert level 4 atau 5 (skor tinggi), segera laporkan ke pimpinan/pejabat terkait.

---

## 6. Informasi Teknis untuk Tim IT

| Item | Nilai |
|---|---|
| Port dashboard | `8000` |
| Endpoint status | `http://<server>:8000/api/status` |
| Endpoint data alert (JSON) | `http://<server>:8000/api/alerts?level=5&limit=50` (`level` opsional) |
| Proses aplikasi | `uvicorn api.main:app` (jalankan di terminal/virtual environment) |
| Database | PostgreSQL `ews_db` di server/VM (user `ews_user`) |
| Log aplikasi | output terminal tempat `uvicorn` dijalankan (atau `journalctl` jika pakai systemd) |
| Interval pengambilan berita | sesuai `SCRAPE_INTERVAL_MINUTES` di `.env` |

Panduan teknis lengkap (instalasi, konfigurasi kata kunci, maintenance):
lihat `USER_MANUAL.md`.
