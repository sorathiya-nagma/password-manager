import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet():
    configured_key = settings.VAULT_FERNET_KEY.strip()
    if configured_key:
        return Fernet(configured_key.encode())

    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_value(value):
    if not value:
        return ''
    return _fernet().encrypt(value.encode()).decode()


def decrypt_value(token):
    if not token:
        return ''
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return '[Unable to decrypt: check VAULT_FERNET_KEY]'
