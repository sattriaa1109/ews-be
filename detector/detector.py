# detector/detector.py — Mendeteksi berita negatif yang menyinggung TNI AD
import logging  # Untuk menulis log

from config import CONTEXT_KEYWORDS, NEGATIVE_KEYWORDS, ALERT_THRESHOLD  # Ambil kata kunci & threshold dari config
from models.tables import Alert  # Model tabel alert

logger = logging.getLogger("detector")  # Logger khusus untuk modul detector


def _contains(text: str, keyword: str) -> bool:
    """Cek apakah keyword ada di dalam text (case-insensitive / tidak peduli huruf besar-kecil)."""
    return keyword.lower() in text.lower()  # Samakan huruf kecil dulu, lalu cek keanggotaan


def _has_context(text: str) -> bool:
    """Artikel harus menyinggung TNI AD / entitas terkait dulu,
    biar gak nangkep berita yang gak relevan sama sekali."""
    return any(_contains(text, kw) for kw in CONTEXT_KEYWORDS)  # True jika ada minimal 1 kata konteks yang cocok


def score_text(text: str) -> tuple[float, list[str], list[str]]:
    """Hitung skor severity dari sebuah teks.
    Return: (skor_total, kategori_yang_match, kata_yang_match)
    """
    total_score = 0.0  # Akumulasi skor, mulai dari 0
    matched_categories = []  # Daftar kategori yang cocok
    matched_words = []  # Daftar kata kunci yang cocok

    for category, rule in NEGATIVE_KEYWORDS.items():  # Loop tiap kategori beserta aturannya
        hits = [w for w in rule["words"] if _contains(text, w)]  # Kumpulkan kata kategori ini yang muncul di teks
        if hits:  # Ada kata yang cocok
            total_score += rule["weight"] * len(hits)  # Skor += bobot kategori × jumlah kata yang cocok
            matched_categories.append(category)  # Catat kategori ini ke daftar
            matched_words.extend(hits)  # Gabungkan kata-kata yang cocok ke daftar kata

    return total_score, matched_categories, matched_words  # Kembalikan (skor, kategori, kata)


def evaluate_article(db, article) -> Alert | None:
    """Evaluasi satu artikel: cek konteks lalu skor. Kalau lolos threshold,
    buat record Alert. Return Alert kalau dibuat, None kalau tidak."""
    full_text = f"{article.title} {article.raw_summary or ''}"  # Gabungkan judul + isi artikel jadi satu teks

    if not _has_context(full_text):  # Tidak mengandung konteks TNI AD → bukan target
        return None  # Abaikan artikel ini

    score, categories, words = score_text(full_text)  # Hitung skor + kumpulkan kategori/kata yang terdeteksi

    if score < ALERT_THRESHOLD:  # Skor di bawah ambang batas
        return None  # Tidak cukup serius → jangan buat alert

    alert = Alert(  # Buat record alert baru
        article_id=article.id,  # Kaitkan alert dengan artikel ini
        severity_score=score,  # Simpan skor keparahan
        matched_categories=",".join(categories),  # Simpan kategori (dipisah koma)
        matched_words=", ".join(sorted(set(words))),  # Simpan kata unik yang terurut (dipisah koma-spasi)
    )
    db.add(alert)  # Daftarkan alert ke sesi
    db.commit()  # Simpan ke database
    db.refresh(alert)  # Muat ulang agar mendapatkan id dari database

    logger.info(f"Alert dibuat untuk artikel #{article.id} dengan skor {score}")  # Log keberhasilan

    return alert  # Kembalikan alert yang baru dibuat
