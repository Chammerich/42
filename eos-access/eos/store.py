"""Datenbank: Benutzer, Einladungen, Sitzungen und Protokoll in einer SQLite-Datei."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .access import hash_password, new_token, token_hash, verify_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    function      TEXT NOT NULL DEFAULT '',
    username      TEXT UNIQUE COLLATE NOCASE,   -- leer, bis die Einladung eingelöst ist
    password_hash TEXT,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'active',
    access_type   TEXT NOT NULL DEFAULT 'permanent',
    valid_from    INTEGER,
    valid_until   INTEGER,
    once_used_at  INTEGER,
    created_at    INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS invites (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS log (
    id         INTEGER PRIMARY KEY,
    time       INTEGER NOT NULL,
    user_name  TEXT NOT NULL,                   -- Name bleibt lesbar, auch wenn die Person gelöscht wird
    event      TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '',
    latency_ms INTEGER
);
"""


class UsernameTaken(Exception):
    pass


class Store:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    def _one(self, sql: str, *args: Any) -> dict[str, Any] | None:
        row = self._db.execute(sql, args).fetchone()
        return dict(row) if row else None

    def _all(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        return [dict(row) for row in self._db.execute(sql, args).fetchall()]

    # --- Benutzer ---

    def users(self) -> list[dict[str, Any]]:
        return self._all("SELECT * FROM users ORDER BY is_admin DESC, name COLLATE NOCASE")

    def user(self, user_id: int) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE id = ?", user_id)

    def user_by_username(self, username: str) -> dict[str, Any] | None:
        return self._one("SELECT * FROM users WHERE username = ?", username.strip())

    def create_user(self, now: int, **fields: Any) -> dict[str, Any]:
        fields["created_at"] = now
        columns = ", ".join(fields)
        marks = ", ".join("?" for _ in fields)
        cursor = self._db.execute(f"INSERT INTO users ({columns}) VALUES ({marks})", tuple(fields.values()))
        return self.user(cursor.lastrowid)  # type: ignore[return-value]

    def update_user(self, user_id: int, **fields: Any) -> None:
        if fields:
            assignments = ", ".join(f"{column} = ?" for column in fields)
            self._db.execute(f"UPDATE users SET {assignments} WHERE id = ?", (*fields.values(), user_id))

    def delete_user(self, user_id: int) -> None:
        self._db.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def ensure_admin(self, username: str, password: str, now: int) -> None:
        """Legt das Administratorkonto aus der Konfiguration an bzw. gleicht es ab.

        So lässt sich ein vergessenes Administratorpasswort über die
        Konfigurationsdatei jederzeit neu setzen.
        """
        admin = self.user_by_username(username)
        if admin is None:
            self.create_user(
                now,
                name="Administrator",
                function="Verwaltung",
                username=username,
                password_hash=hash_password(password),
                is_admin=1,
            )
            return
        changes: dict[str, Any] = {"is_admin": 1, "status": "active"}
        if not verify_password(password, admin["password_hash"]):
            changes["password_hash"] = hash_password(password)
        self.update_user(admin["id"], **changes)

    def set_credentials(self, user_id: int, username: str, password: str) -> None:
        try:
            self.update_user(user_id, username=username.strip(), password_hash=hash_password(password))
        except sqlite3.IntegrityError as err:
            raise UsernameTaken from err

    # --- Einladungen: je Person höchstens eine gültige ---

    def create_invite(self, user_id: int, expires_at: int) -> str:
        token = new_token()
        self._db.execute("DELETE FROM invites WHERE user_id = ?", (user_id,))
        self._db.execute("INSERT INTO invites VALUES (?, ?, ?)", (token_hash(token), user_id, expires_at))
        return token

    def invite(self, token: str, now: int) -> dict[str, Any] | None:
        return self._one("SELECT * FROM invites WHERE token_hash = ? AND expires_at > ?", token_hash(token), now)

    def invite_expiry(self, user_id: int, now: int) -> int | None:
        row = self._one("SELECT expires_at FROM invites WHERE user_id = ? AND expires_at > ?", user_id, now)
        return row["expires_at"] if row else None

    def consume_invite(self, token: str) -> None:
        self._db.execute("DELETE FROM invites WHERE token_hash = ?", (token_hash(token),))

    # --- Sitzungen ---

    def create_session(self, user_id: int, expires_at: int) -> str:
        token = new_token()
        self._db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (token_hash(token), user_id, expires_at))
        return token

    def session_user(self, token: str, now: int) -> dict[str, Any] | None:
        return self._one(
            "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
            token_hash(token),
            now,
        )

    def delete_session(self, token: str) -> None:
        self._db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))

    def delete_sessions_of(self, user_id: int) -> None:
        self._db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))

    # --- Protokoll ---

    def add_log(self, now: int, user_name: str, event: str, detail: str = "", latency_ms: int | None = None) -> None:
        self._db.execute(
            "INSERT INTO log (time, user_name, event, detail, latency_ms) VALUES (?, ?, ?, ?, ?)",
            (now, user_name, event, detail, latency_ms),
        )

    def log(self, limit: int = 200) -> list[dict[str, Any]]:
        return self._all("SELECT * FROM log ORDER BY id DESC LIMIT ?", limit)
