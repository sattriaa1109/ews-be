# seed_user_dummy.py — Memasukkan user contoh (dummy) ke database
# Cara pakai:  python seed_user_dummy.py
# Aman dijalankan berulang: user yang sudah ada (berdasarkan username) dilewati.
import logging

from auth_utils import hash_password
from database import SessionLocal, init_db
from models.tables import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_user")


# Data dummy. Password sudah diketahui supaya mudah dipakai untuk testing login.
DUMMY_USERS = [
    {"username": "operator1", "email": "operator1@ews.mil.id", "password": "operator123", "role": "staff"},
    {"username": "operator2", "email": "operator2@ews.mil.id", "password": "operator123", "role": "staff"},
    {"username": "analis1", "email": "analis1@ews.mil.id", "password": "analis123", "role": "staff"},
    {"username": "viewer1", "email": "viewer1@ews.mil.id", "password": "viewer123", "role": "viewer"},
]


def seed_users(db) -> int:
    """Masukkan DUMMY_USERS ke session DB yang diberikan. Return jumlah user baru."""
    created = 0
    for item in DUMMY_USERS:
        existing = db.query(User).filter(User.username == item["username"]).first()
        if existing:
            logger.info(f"User sudah ada, dilewati: {item['username']}")
            continue
        db.add(
            User(
                username=item["username"],
                email=item["email"],
                hashed_password=hash_password(item["password"]),
                role=item["role"],
                is_active=1,
            )
        )
        db.commit()
        created += 1
        logger.info(f"User dummy dibuat: {item['username']} ({item['role']})")
    return created


def main():
    init_db()  # Pastikan tabel users (dan admin/staff default) sudah ada
    db = SessionLocal()
    try:
        created = seed_users(db)
        logger.info(f"Selesai. {created} user dummy dimasukkan.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
