"""Berechtigungslogik: Darf diese Person jetzt die Tür öffnen?

Reine Funktionen ohne Datenbank und ohne Netz. Sie werden bei *jedem*
Öffnungsversuch mit dem frisch geladenen Benutzer aufgerufen.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

ACCESS_TYPES = ("once", "period", "permanent")
STATUSES = ("active", "inactive", "blocked")


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str  # ok | blocked | inactive | not_yet | expired | used
    message: str  # so, wie die Person es zu lesen bekommt


def format_time(timestamp: int, timezone: str) -> str:
    return datetime.fromtimestamp(timestamp, ZoneInfo(timezone)).strftime("%d.%m.%Y, %H:%M Uhr")


def decide(user: Mapping[str, Any], now: int, timezone: str) -> Decision:
    """Prüft Status und Zugangsart eines Benutzers zum Zeitpunkt ``now``."""
    if user["status"] == "blocked":
        return Decision(False, "blocked", "Dieser Zugang ist gesperrt.")
    if user["status"] != "active":
        return Decision(False, "inactive", "Dein Zugang ist derzeit nicht aktiv.")
    if user["is_admin"]:
        return Decision(True, "ok", "")

    kind = user["access_type"]
    if kind == "permanent":
        return Decision(True, "ok", "")
    if kind == "once":
        if user["once_used_at"]:
            return Decision(False, "used", "Dein einmaliger Zugang wurde bereits genutzt.")
        return Decision(True, "ok", "")
    if kind == "period":
        if user["valid_from"] and now < user["valid_from"]:
            start = format_time(user["valid_from"], timezone)
            return Decision(False, "not_yet", f"Dein Zugang beginnt am {start}.")
        if user["valid_until"] and now >= user["valid_until"]:
            return Decision(False, "expired", "Dein Zugang ist abgelaufen.")
        return Decision(True, "ok", "")
    return Decision(False, "inactive", "Dein Zugang ist derzeit nicht aktiv.")


def describe(user: Mapping[str, Any], timezone: str) -> str:
    """Kurzbeschreibung des Zugangs für die Seite der Person."""
    if user["is_admin"]:
        return "Verwaltung"
    if user["access_type"] == "permanent":
        return "Dauerhafter Zugang"
    if user["access_type"] == "once":
        return "Einmaliger Zugang"
    if user["valid_until"]:
        return f"Zugang bis {format_time(user['valid_until'], timezone)}"
    return "Zeitlich begrenzter Zugang"


# --- Passwörter und Geheimnisse ---

_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    try:
        scheme, salt, digest = (stored or "").split("$")
        if scheme != "scrypt":
            return False
        candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), **_SCRYPT)
        return hmac.compare_digest(candidate, bytes.fromhex(digest))
    except ValueError:
        return False


def new_token() -> str:
    return secrets.token_urlsafe(24)


def token_hash(token: str) -> str:
    """In der Datenbank liegen nur Hashes von Einladungs- und Sitzungs-Tokens."""
    return hashlib.sha256(token.encode()).hexdigest()
