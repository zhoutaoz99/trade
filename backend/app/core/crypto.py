"""API secret encryption utilities."""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

_BACKEND = "local_encrypted"


def _derive_fernet() -> Fernet:
    salt = b"um-futures-sim-salt"  # fixed salt; in production use per-instance salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.secret_key.encode()))
    return Fernet(key)


_fernet = _derive_fernet()


def encrypt_api_secret(plaintext: str) -> str:
    token = _fernet.encrypt(plaintext.encode())
    return f"{_BACKEND}:{token.decode()}"


def decrypt_api_secret(ciphertext: str) -> str:
    prefix, token = ciphertext.split(":", 1)
    if prefix != _BACKEND:
        raise ValueError(f"Unknown encryption backend: {prefix}")
    return _fernet.decrypt(token.encode()).decode()
