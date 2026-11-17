# database.py — Setup koneksi database SQLAlchemy
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
    import hashlib
    import secrets
    from models.tables import Article, Alert, User  # noqa: F401  # Impor model supaya tabel terdaftar di metadata
    Base.metadata.create_all(bind=engine)  # Buat semua tabel yang belum ada di database

    # Pastikan kolom region ada jika tabel articles sudah ada sebelumnya di database
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE articles ADD COLUMN IF NOT EXISTS region VARCHAR(100) DEFAULT 'Nasional';"))
    except Exception:
        pass

    # Seed default admin & staff jika belum ada
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.sha256((salt + "admin123").encode()).hexdigest()
            admin_user = User(
                username="admin",
                email="admin@ews.mil.id",
                hashed_password=f"{salt}${pwd_hash}",
                role="admin",
                is_active=1
            )
            db.add(admin_user)
            db.commit()

        staff_user = db.query(User).filter(User.username == "staff").first()
        if not staff_user:
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.sha256((salt + "staff123").encode()).hexdigest()
            staff_user = User(
                username="staff",
                email="staff@ews.mil.id",
                hashed_password=f"{salt}${pwd_hash}",
                role="staff",
                is_active=1
            )
            db.add(staff_user)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
