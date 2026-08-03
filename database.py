# database.py — Setup koneksi database SQLAlchemy
from sqlalchemy import create_engine  # create_engine: membuat mesin koneksi ke database
from sqlalchemy.orm import sessionmaker, declarative_base  # sessionmaker: pabrik sesi DB; declarative_base: dasar model ORM

from config import DATABASE_URL  # Ambil URL koneksi database dari config

# SQLite butuh opsi khusus agar bisa diakses lintas thread; database lain tidak perlu
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Buat engine (penghubung) ke database sesuai URL yang dikonfigurasi
engine = create_engine(DATABASE_URL, connect_args=connect_args)
# SessionLocal adalah pabrik sesi: setiap pemakaian menghasilkan koneksi baru ke database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base dipakai sebagai kelas dasar semua model (tabel) ORM
Base = declarative_base()


def get_db():
    """Generator dependency FastAPI: buka sesi DB, serahkan ke pemanggil, tutup otomatis."""
    db = SessionLocal()  # Buat satu sesi database
    try:
        yield db  # Serahkan sesi ke endpoint yang memakai dependency ini
    finally:
        db.close()  # Pastikan sesi ditutup walau terjadi error


def init_db():
    from models.tables import Article, Alert  # noqa: F401  # Impor model supaya tabel terdaftar di metadata
    Base.metadata.create_all(bind=engine)  # Buat semua tabel yang belum ada di database
