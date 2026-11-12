"""Encryption of stored mailbox passwords (Fernet, key from settings.MAIL_ENCRYPTION_KEY or SECRET_KEY)."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet():
    secret = settings.MAIL_ENCRYPTION_KEY or settings.SECRET_KEY
    key = base64.urlsafe_b64encode(hashlib.sha256(f'inbox-mail-password:{secret}'.encode()).digest())
    return Fernet(key)


def encrypt(value):
    return _fernet().encrypt(value.encode()).decode() if value else ''


def decrypt(token):
    """Return the plain text, or '' if the token cannot be decrypted (e.g. the key was changed)."""
    if not token:
        return ''
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return ''
