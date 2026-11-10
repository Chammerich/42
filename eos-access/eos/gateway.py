"""BTicino-Gateway: die einzige Stelle, die mit der Netatmo-Cloud spricht.

Dünne Schicht über ``pybticino``. Sie kann genau zwei Dinge: den Zustand der
Verbindung melden und die Haustür öffnen. Kamera, Audio, Ereignisse und
Anrufverlauf werden bewusst nicht angefasst – was es hier nicht gibt, kann
auch kein Benutzer von EOS Access erreichen.

Die Cloud bestätigt nur, dass sie den Befehl *angenommen* hat. Ob die Tür
physisch aufgegangen ist, meldet die Anlage nicht zurück (am 10.11.2026 an
der Anlage geprüft).
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pybticino import ApiError, AsyncAccount, AuthError, AuthHandler

# Modultypen der Netatmo-Cloud für BTicino-Anlagen.
KIND_BY_TYPE = {
    "BNDL": "lock",  # Türöffner
    "BNSL": "light",  # Treppenlicht-Relais – bei manchen Installationen hängt hier die Tür
    "BNVL": "light",
    "BNEU": "external_unit",
}
KIND_BY_SUBTYPE = {
    "bndl_doorlock": "lock",
    "bnsl_staircase_light": "light",
    "bnvl_video_doorentry_light": "light",
    "bneu_external_unit": "external_unit",
}

# Befehl je Modulart: Türöffner bekommen einen Öffnungsimpuls, Relais werden eingeschaltet.
OPEN_STATE = {"lock": {"lock": False}, "light": {"on": True}}

COOLDOWN_SECONDS = 3.0  # zwei Befehle direkt hintereinander bringen nichts


class GatewayError(Exception):
    """Fehler mit einer Meldung, die dem Administrator angezeigt werden kann."""


class GatewayBusy(GatewayError):
    """Die Tür wurde gerade eben schon geöffnet."""


@dataclass
class OpenResult:
    accepted: bool
    latency_ms: int
    detail: str


def module_kind(module: dict[str, Any]) -> str:
    """Ordnet ein Modul aus der Cloud-Topologie einer Art zu."""
    variant = module.get("variant")
    if isinstance(variant, str) and ":" in variant:
        subtype = variant.split(":", 1)[1]
        if subtype in KIND_BY_SUBTYPE:
            return KIND_BY_SUBTYPE[subtype]
    return KIND_BY_TYPE.get(str(module.get("type")), "other")


def response_errors(response: dict[str, Any]) -> list[Any]:
    """Sammelt Fehlermeldungen aus einer setstate-Antwort.

    Die Cloud antwortet auch bei abgelehnten Befehlen teils mit HTTP 200 und
    legt die Fehler in ``errors`` bzw. ``body.errors`` ab.
    """
    errors: list[Any] = []
    for container in (response, response.get("body") or {}):
        found = container.get("errors") if isinstance(container, dict) else None
        if found:
            errors.extend(found if isinstance(found, list) else [found])
    return errors


def explain(err: Exception) -> str:
    """Übersetzt einen pybticino-Fehler in eine verständliche Meldung.

    pybticino meldet auch Netzwerkprobleme beim Anmelden als ``AuthError``;
    nur der Text verrät, ob wirklich die Zugangsdaten abgelehnt wurden.
    """
    if isinstance(err, AuthError) and "Invalid credentials" in str(err):
        return (
            "Netatmo hat die Zugangsdaten abgelehnt. E-Mail und Passwort prüfen – es muss ein "
            "Konto der Home + Security-App sein (nicht „BTicino Door Entry“)."
        )
    return f"Netatmo-Cloud nicht erreichbar oder Anfrage abgelehnt: {err}"


def token_rejected(err: ApiError) -> bool:
    """Erkennt eine Ablehnung wegen des Zugriffstokens.

    pybticino verpackt HTTP-Fehler teils ein zweites Mal und verliert dabei den
    Statuscode (er steht dann nur noch im Text).
    """
    return err.status_code in (401, 403) or any(f"API Error {code}" in str(err) for code in (401, 403))


class Gateway:
    """Verbindung zur Anlage über das Netatmo-Konto von EOS Access."""

    def __init__(
        self,
        username: str,
        password: str,
        token_file: Path,
        timezone: str,
        home_id: str | None = None,
        door_module_id: str | None = None,
    ) -> None:
        self._token_file = token_file
        self._timezone = timezone
        self._wanted_home_id = home_id or None
        self._wanted_door_id = door_module_id or None
        self._home_id: str | None = None
        self._door: Any = None
        self._lock = asyncio.Lock()
        self._last_open = float("-inf")
        self._auth = AuthHandler(username, password, token_callback=self._save_tokens)
        self._account = AsyncAccount(self._auth)
        self._restore_tokens()

    # --- Token-Ablage: verhindert, dass bei jedem Neustart das Passwort gesendet wird ---

    def _restore_tokens(self) -> None:
        try:
            data = json.loads(self._token_file.read_text())
            self._auth.set_tokens(data["access_token"], data["refresh_token"], data.get("expires_at"))
        except (OSError, ValueError, KeyError):
            pass  # keine oder unbrauchbare Ablage -> normale Anmeldung

    async def _save_tokens(self, tokens: dict[str, Any]) -> None:
        self._token_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._token_file.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as handle:
            json.dump(tokens, handle)
        os.replace(tmp, self._token_file)

    # --- Zuhause und Haustür bestimmen ---

    def _pick_home(self) -> Any:
        homes = self._account.homes
        if self._wanted_home_id:
            if self._wanted_home_id not in homes:
                raise GatewayError(f"EOS_HOME_ID {self._wanted_home_id} gehört nicht zu diesem Konto.")
            return homes[self._wanted_home_id]
        with_modules = [home for home in homes.values() if home.modules]
        if not with_modules:
            raise GatewayError(
                "Das Netatmo-Konto sieht kein Zuhause mit Geräten. Wurde es in der "
                "Home + Security-App eingeladen und die Einladung angenommen?"
            )
        if len(with_modules) > 1:
            names = ", ".join(f"{home.name} ({home.id})" for home in with_modules)
            raise GatewayError(f"Mehrere Zuhause gefunden – bitte EOS_HOME_ID setzen: {names}")
        return with_modules[0]

    def _pick_door(self, home: Any) -> Any:
        if self._wanted_door_id:
            door = next((m for m in home.modules if m.id == self._wanted_door_id), None)
            if door is None:
                raise GatewayError(f"EOS_DOOR_MODULE_ID {self._wanted_door_id} gibt es in diesem Zuhause nicht.")
            if module_kind(door.raw_data) not in OPEN_STATE:
                raise GatewayError(f"Modul „{door.name}“ ({door.type}) ist kein Türöffner und kein Relais.")
            return door
        locks = [m for m in home.modules if module_kind(m.raw_data) == "lock"]
        if not locks:
            raise GatewayError("Die Anlage meldet keinen Türöffner. Bitte EOS_DOOR_MODULE_ID setzen.")
        if len(locks) > 1:
            names = ", ".join(f"{m.name} ({m.id})" for m in locks)
            raise GatewayError(f"Mehrere Türöffner gefunden – bitte EOS_DOOR_MODULE_ID setzen: {names}")
        return locks[0]

    async def _load(self, refresh: bool = False) -> tuple[str, Any]:
        if self._door is not None and self._home_id and not refresh:
            return self._home_id, self._door
        try:
            await self._account.async_update_topology()
        except (AuthError, ApiError) as err:
            raise GatewayError(explain(err)) from err
        home = self._pick_home()
        self._door = self._pick_door(home)
        self._home_id = home.id
        return home.id, self._door

    # --- Öffentliche Funktionen ---

    async def status(self) -> dict[str, Any]:
        """Verbindungstest für die Verwaltung: Konto, Zuhause und die Haustür."""
        home_id, door = await self._load(refresh=True)
        try:
            status = await self._account.async_get_home_status(home_id)
        except (ApiError, AuthError) as err:
            raise GatewayError(explain(err)) from err
        modules = status.get("body", {}).get("home", {}).get("modules", [])
        live = next((m for m in modules if m.get("id") == door.id), {})
        return {
            "account": self._account.user,
            "home": self._account.homes[home_id].name,
            "door": {"name": door.name, "type": door.type, "reachable": live.get("reachable")},
        }

    async def _send_open(self, home_id: str, door: Any) -> dict[str, Any]:
        return await self._account.async_set_module_state(
            home_id=home_id,
            module_id=door.id,
            bridge_id=door.bridge,
            state=dict(OPEN_STATE[module_kind(door.raw_data)]),
            timezone=self._timezone,
        )

    async def open(self) -> OpenResult:
        """Sendet den Öffnungsbefehl an die Haustür."""
        async with self._lock:
            if time.monotonic() - self._last_open < COOLDOWN_SECONDS:
                raise GatewayBusy("Die Tür wurde gerade eben geöffnet.")
            home_id, door = await self._load()

            started = time.monotonic()
            try:
                try:
                    response = await self._send_open(home_id, door)
                except ApiError as err:
                    if not token_rejected(err):
                        raise
                    # Die Cloud hat das Zugriffstoken verworfen: einmal frisch anmelden und wiederholen.
                    await self._auth.authenticate()
                    response = await self._send_open(home_id, door)
            except (ApiError, AuthError) as err:
                latency = int((time.monotonic() - started) * 1000)
                return OpenResult(False, latency, explain(err))
            latency = int((time.monotonic() - started) * 1000)

            errors = response_errors(response)
            if response.get("status") == "ok" and not errors:
                self._last_open = time.monotonic()
                return OpenResult(True, latency, f"Von der Cloud angenommen ({door.name}).")
            if errors:
                return OpenResult(False, latency, f"Cloud meldet Fehler: {json.dumps(errors, ensure_ascii=False)}")
            return OpenResult(False, latency, f"Unerwartete Antwort: status={response.get('status')!r}")

    async def close(self) -> None:
        await self._auth.close_session()
