# database.py — Setup koneksi database SQLAlchemy
import logging  # Untuk mencatat error saat migrasi ringan

from sqlalchemy import create_engine, text  # create_engine: membuat mesin koneksi ke database
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
    from auth_utils import hash_password
    from models.tables import Article, Alert, User  # noqa: F401  # Impor model supaya tabel terdaftar di metadata
    Base.metadata.create_all(bind=engine)  # Buat semua tabel yang belum ada di database

    # Pastikan kolom region ada jika tabel articles sudah ada sebelumnya.
    # SQLite tidak mendukung "ADD COLUMN IF NOT EXISTS", jadi cek dulu daftar kolomnya.
    try:
        from sqlalchemy import inspect

        columns = {col["name"] for col in inspect(engine).get_columns("articles")}
        if "region" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE articles ADD COLUMN region VARCHAR(100) DEFAULT 'Nasional'"))
    except Exception:
        logging.getLogger(__name__).exception("Gagal memastikan kolom region pada tabel articles")

    # Seed default admin & staff jika belum ada
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@ews.mil.id",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=1
            )
            db.add(admin_user)
            db.commit()

        staff_user = db.query(User).filter(User.username == "staff").first()
        if not staff_user:
            staff_user = User(
                username="staff",
                email="staff@ews.mil.id",
                hashed_password=hash_password("staff123"),
                role="staff",
                is_active=1
            )
            db.add(staff_user)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
