import base64
import hashlib
import hmac
import secrets
import struct
import time


def generate_totp_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')


def _normalize_secret(secret):
    padding = '=' * ((8 - len(secret) % 8) % 8)
    return base64.b32decode((secret + padding).upper())


def totp_code(secret, for_time=None, interval=30, digits=6):
    for_time = int(for_time or time.time())
    counter = for_time // interval
    digest = hmac.new(_normalize_secret(secret), struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10 ** digits)).zfill(digits)


def verify_totp(secret, code, window=1):
    if not secret or not code:
        return False
    code = str(code).strip()
    now = int(time.time())
    return any(totp_code(secret, now + step * 30) == code for step in range(-window, window + 1))
