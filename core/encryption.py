import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError(
            'ENCRYPTION_KEY no está configurada en settings. '
            'Genera una con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt(value: str) -> str:
    """Cifra un string y retorna el token cifrado como string."""
    if not value:
        return value
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Descifra un token Fernet y retorna el string original."""
    if not value:
        return value
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        return ''


def compute_hmac(value: str) -> str:
    """Genera un HMAC-SHA256 del valor usando SECRET_KEY como clave."""
    secret = settings.SECRET_KEY.encode()
    return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()


def verify_integrity(value: str, expected_hmac: str) -> bool:
    """Verifica que el HMAC del valor coincida con el esperado."""
    return hmac.compare_digest(compute_hmac(value), expected_hmac)