"""Passwort-Hashing mit scrypt aus der Standardbibliothek (keine Zusatz-Pakete).

Format: scrypt$n$r$p$salt_b64$hash_b64. Die Parameter stehen im Hash, so lassen
sich spätere Verschärfungen einführen, ohne alte Hashes ungültig zu machen.
"""

import base64
import hashlib
import hmac
import os

_N, _R, _P = 2**14, 8, 1
_MAXMEM = 128 * 1024 * 1024
_dummy: str | None = None


def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32, maxmem=_MAXMEM
    )


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = _derive(password, salt, _N, _R, _P)
    b64 = lambda raw: base64.b64encode(raw).decode("ascii")  # noqa: E731
    return f"scrypt${_N}${_R}${_P}${b64(salt)}${b64(digest)}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest_b64)
        actual = _derive(password, base64.b64decode(salt_b64), int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def burn_time(password: str) -> None:
    """Rechnet bei unbekanntem Benutzernamen einmal scrypt, damit die
    Antwortzeit nicht verrät, ob es den Benutzer gibt."""
    global _dummy
    if _dummy is None:
        _dummy = hash_password("dummy-password")
    verify_password(password, _dummy)
