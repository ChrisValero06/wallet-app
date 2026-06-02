import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError("ENCRYPTION_KEY no configurada")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(data: str) -> str:
    return _get_fernet().encrypt(data.encode()).decode()


def decrypt(encrypted: str) -> str:
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        raise ValueError("No se pudo descifrar el dato — clave incorrecta o dato corrupto")


def hash_identifier(identifier: str) -> str:
    return hashlib.sha256(identifier.strip().encode()).hexdigest()


def mask_identifier(identifier: str, method_type: str) -> str:
    clean = identifier.strip()
    if len(clean) <= 4:
        return "*" * len(clean)
    last4 = clean[-4:]
    if method_type == "card":
        groups = len(clean) // 4
        masked_groups = " ".join(["****"] * (groups - 1)) if groups > 1 else "****"
        return f"{masked_groups} {last4}"
    return f"{'*' * (len(clean) - 4)}{last4}"
