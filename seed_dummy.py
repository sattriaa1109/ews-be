# seed_dummy.py — Memasukkan data contoh (dummy) ke database
# Dipakai untuk menguji dashboard saat belum ada alert asli.
# Cara pakai:  python seed_dummy.py
import logging

from database import SessionLocal
from models.tables import Article, Alert
from seed_user_dummy import seed_users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


DUMMY_ARTICLES = [
    {
        "title": "Oknum TNI AD diduga terlibat pungli di proyek pemerintah",
        "link": "https://example.com/berita/1",
        "source": "Media Contoh A",
        "raw_summary": "Seorang oknum prajurit TNI AD diduga melakukan pungli dan penyalahgunaan wewenang dalam proyek pemerintah daerah.",
        "score": 6,
        "categories": "pelanggaran_hukum,disiplin_internal",
        "words": "oknum, pungli, penyalahgunaan wewenang",
    },
    {
        "title": "Babinsa tersangka kasus penganiayaan warga di Jawa Barat",
        "link": "https://example.com/berita/2",
        "source": "Media Contoh B",
        "raw_summary": "Seorang Babinsa ditetapkan sebagai tersangka penganiayaan setelah baku tembak dengan warga di Jawa Barat. Kasus ini viral dan ramai diperbincangkan.",
        "score": 7,
        "categories": "kekerasan,isu_viral",
        "words": "penganiayaan, baku tembak, viral, ramai diperbincangkan",
    },
    {
        "title": "Pangdam soroti dugaan penyiksaan dalam penegakan hukum di Kodam",
        "link": "https://example.com/berita/3",
        "source": "Media Contoh C",
        "raw_summary": "Pangdam meminta investigasi dugaan penyiksaan dan intimidasi warga yang dilakukan anggota dalam operasi di wilayah Kodam.",
        "score": 8,
        "categories": "ham",
        "words": "penyiksaan, intimidasi warga",
    },
    {
        "title": "KPK periksa pejabat Kemhan terkait dugaan suap pengadaan",
        "link": "https://example.com/berita/4",
        "source": "Media Contoh D",
        "raw_summary": "KPK memeriksa pejabat Kemhan terkait dugaan suap dalam pengadaan barang dan jasa di lingkungan TNI Angkatan Darat.",
        "score": 5,
        "categories": "pelanggaran_hukum",
        "words": "suap, korupsi",
    },
]


def main():
    db = SessionLocal()
    created = 0
    try:
        for item in DUMMY_ARTICLES:
            exists = db.query(Article).filter(Article.link == item["link"]).first()
            if exists:
                logger.info(f"Artikel sudah ada, dilewati: {item['title']}")
                continue
            article = Article(
                title=item["title"],
                link=item["link"],
                source=item["source"],
                raw_summary=item["raw_summary"],
            )
            db.add(article)
            db.commit()
            db.refresh(article)
            db.add(
                Alert(
                    article_id=article.id,
                    severity_score=item["score"],
                    matched_categories=item["categories"],
                    matched_words=item["words"],
                )
            )
            db.commit()
            created += 1
            logger.info(f"Alert contoh dibuat: {item['title']}")
        logger.info(f"Selesai. {created} alert contoh dimasukkan.")
        # User dummy ikut di-seed agar akun untuk login tersedia saat testing
        seed_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
