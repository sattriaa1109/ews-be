# models/tables.py — Definisi tabel database menggunakan SQLAlchemy ORM
from datetime import datetime, timezone  # datetime & timezone untuk menghasilkan nilai waktu

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float  # Tipe-tipe kolom SQLAlchemy
from sqlalchemy.orm import relationship  # relationship: untuk mendefinisikan relasi antar model

from config import get_alert_level  # Pemetaan skor severity ke level 1-5
from database import Base  # Base = kelas dasar semua model ORM


class Article(Base):
    """Model tabel `articles`: menyimpan hasil scraping berita."""
    __tablename__ = "articles"  # Nama tabel di database

    id = Column(Integer, primary_key=True, index=True)  # Primary key auto-increment, di-index agar cepat dicari
    title = Column(String(500), nullable=False)  # Judul artikel, wajib diisi (nullable=False)
    link = Column(String(1000), unique=True, nullable=False)  # URL artikel, unique = mencegah artikel duplikat
    source = Column(String(200))  # Nama sumber berita (misalnya nama feed)
    published_at = Column(DateTime, nullable=True)  # Waktu artikel terbit (nullable, kadang feed tidak mencantumkan)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Waktu artikel di-scrape, default = waktu sekarang UTC
    raw_summary = Column(Text, nullable=True)  # Isi/ringkasan artikel dalam bentuk teks polos
    region = Column(String(100), default="Nasional")  # Wilayah/regional berita (misal: Sumatra, Jawa, dll)

    alert = relationship("Alert", back_populates="article", uselist=False)  # Relasi 1-1 ke Alert (uselist=False)


class User(Base):
    """Model tabel `users`: menyimpan data pengguna (admin, staff, dll)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="staff")  # admin, staff, viewer, dll
    is_active = Column(Integer, default=1)  # 1 = aktif, 0 = nonaktif
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    """Model tabel `alerts`: menyimpan artikel yang lolos deteksi (peringatan)."""
    __tablename__ = "alerts"  # Nama tabel di database

    id = Column(Integer, primary_key=True, index=True)  # Primary key auto-increment
    article_id = Column(Integer, ForeignKey("articles.id"), unique=True)  # Foreign key ke tabel articles, unik = 1 artikel maksimal 1 alert
    severity_score = Column(Float, default=0)  # Skor keparahan hasil deteksi detector
    matched_categories = Column(String(500))  # Kategori yang cocok, disimpan dipisah koma
    matched_words = Column(Text)  # Kata kunci yang terdeteksi
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Waktu alert dibuat, default = sekarang UTC

    article = relationship("Article", back_populates="alert")  # Relasi balik ke Article

    @property
    def level(self) -> int:
        """Level alert 1-5, dihitung dari skor severity."""
        return get_alert_level(self.severity_score)
