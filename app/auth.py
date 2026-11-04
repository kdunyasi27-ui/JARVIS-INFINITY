import hashlib
import hmac
import secrets

from itsdangerous import URLSafeTimedSerializer, BadSignature

from app.config import settings
from app.db import create_user, get_user_by_email, get_user_by_id


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Şifre en az 10 karakter olmalıdır.")

    salt = secrets.token_bytes(16)

    hashed = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1
    )

    return (
        salt.hex()
        + "$"
        + hashed.hex()
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split("$", 1)

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)

        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1
        )

        return hmac.compare_digest(actual, expected)

    except (ValueError, TypeError):
        return False


def register(email: str, password: str):
    email = email.strip().lower()

    if "@" not in email or len(email) > 254:
        raise ValueError("Geçerli bir e-posta adresi gir.")

    if get_user_by_email(email):
        raise ValueError("Bu e-posta zaten kayıtlı.")

    return create_user(
        email,
        hash_password(password)
    )


def login(email: str, password: str):
    user = get_user_by_email(email.strip().lower())

    if not user or not verify_password(
        password,
        user["password_hash"]
    ):
        return None

    return user


def get_serializer():
    secret = settings.jarvis_api_token

    if not secret or secret == "change-me":
        raise RuntimeError("Güçlü JARVIS_API_TOKEN ayarlanmalı.")

    return URLSafeTimedSerializer(
        secret,
        salt="jarvis-user-session"
    )


def create_session(user_id: int):
    return get_serializer().dumps({
        "user_id": user_id
    })


def read_session(token: str, max_age: int = 86400):
    try:
        data = get_serializer().loads(
            token,
            max_age=max_age
        )

        user_id = int(data["user_id"])
        return get_user_by_id(user_id)

    except (BadSignature, ValueError, KeyError, TypeError):
        return None
