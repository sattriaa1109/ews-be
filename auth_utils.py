# auth_utils.py — Fungsi hashing & verifikasi password yang dipakai bersama
# (API, seeder, dan inisialisasi database) supaya formatnya selalu sama:
# "<salt>$<sha256(salt + password)>"
import hashlib
import secrets


def hash_password(password: str) -> str:
    """Buat hash password baru dengan salt acak."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Cek password terhadap hash yang tersimpan."""
    try:
        salt, pwd_hash = stored_hash.split("$")
        return hashlib.sha256((salt + password).encode()).hexdigest() == pwd_hash
    except Exception:
        return False
