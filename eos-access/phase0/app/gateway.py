"""BTicino-Gateway: die einzige Stelle, die mit der Netatmo-Cloud spricht.

Dünne Schicht über ``pybticino`` (dieselbe Bibliothek, die auch die
Home-Assistant-Integration ``bticino_intercom`` verwendet). Sie kann genau
drei Dinge: verbinden, den Zustand der Anlage lesen, einen Öffnungsbefehl
senden. Kamera, Audio, Ereignisse und Anrufverlauf werden bewusst nicht
angefasst.

Wichtig für die Bewertung der Ergebnisse: Die Cloud bestätigt nur, dass sie
den Befehl *angenommen* hat. Ob die Tür physisch aufgegangen ist, meldet die
Anlage nicht zurück.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from pybticino import ApiError, AsyncAccount, AuthError, AuthHandler

# Modultypen der Netatmo-Cloud für BTicino-Anlagen.
KIND_BY_TYPE = {
    "BNDL": "lock",  # Türöffner (door lock)
    "BNSL": "light",  # Treppenlicht-Relais – bei manchen Installationen hängt hier die Tür
    "BNVL": "light",
    "BNEU": "external_unit",  # Außenstation
}
KIND_BY_SUBTYPE = {
    "bndl_doorlock": "lock",
    "bnsl_staircase_light": "light",
    "bnvl_video_doorentry_light": "light",
    "bneu_external_unit": "external_unit",
}

# Befehl je Modulart: Türöffner bekommen einen Öffnungsimpuls, Relais werden eingeschaltet.
OPEN_STATE = {"lock": {"lock": False}, "light": {"on": True}}

# Zustandsfelder, die sich ständig von selbst ändern und nichts über die Tür aussagen.
NOISE_FIELDS = {"uptime", "wifi_strength", "last_seen"}

SETTLE_SECONDS = 2.0  # Wartezeit, bevor der Zustand nach dem Befehl erneut gelesen wird
COOLDOWN_SECONDS = 3.0  # Schutz vor Doppelklicks


class GatewayError(Exception):
    """Fehler, der dem Bediener im Klartext angezeigt werden kann."""


@dataclass
class OpenResult:
    """Ergebnis eines Öffnungsbefehls – so wie es ins Protokoll geschrieben wird."""

    module_id: str
    module_name: str
    accepted: bool
    latency_ms: int
    detail: str
    response: dict[str, Any] = field(default_factory=dict)
    changed: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def module_kind(module: dict[str, Any]) -> str:
    """Ordnet ein Modul aus der Cloud-Topologie einer Art zu."""
    variant = module.get("variant")
    if isinstance(variant, str) and ":" in variant:
        subtype = variant.split(":", 1)[1]
        if subtype in KIND_BY_SUBTYPE:
            return KIND_BY_SUBTYPE[subtype]
    if not module.get("bridge") and ":" in str(module.get("id", "")):
        # Module ohne Bridge mit MAC-Adresse als ID sind das Gerät selbst (z. B. die Classe 300EOS).
        return KIND_BY_TYPE.get(str(module.get("type")), "bridge")
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
    """Übersetzt einen pybticino-Fehler in eine Meldung, mit der der Bediener etwas anfangen kann.

    pybticino meldet auch Netzwerkprobleme beim Anmelden als ``AuthError``;
    nur der Text verrät, ob wirklich die Zugangsdaten abgelehnt wurden.
    """
    if isinstance(err, AuthError) and "Invalid credentials" in str(err):
        return (
            "Netatmo hat die Zugangsdaten abgelehnt. E-Mail und Passwort prüfen – es muss ein "
            "Konto der Home + Security-App sein (nicht „BTicino Door Entry“)."
        )
    return f"Netatmo-Cloud nicht erreichbar oder Anfrage abgelehnt: {err}"


class Gateway:
    """Verbindung zur Anlage über das Netatmo-Konto."""

    def __init__(
        self,
        username: str,
        password: str,
        token_file: Path,
        timezone: str,
        home_id: str | None = None,
    ) -> None:
        self._token_file = token_file
        self._timezone = timezone
        self._wanted_home_id = home_id or None
        self._home_id: str | None = None
        self._lock = asyncio.Lock()
        self._last_open = 0.0
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

    # --- Lesen ---

    async def _ensure_home(self, refresh: bool = False) -> str:
        if self._home_id and not refresh:
            return self._home_id
        try:
            await self._account.async_update_topology()
        except (AuthError, ApiError) as err:
            raise GatewayError(explain(err)) from err

        homes = self._account.homes
        if self._wanted_home_id:
            if self._wanted_home_id not in homes:
                raise GatewayError(f"EOS_HOME_ID {self._wanted_home_id} gehört nicht zu diesem Konto.")
            self._home_id = self._wanted_home_id
            return self._home_id

        with_modules = [home for home in homes.values() if home.modules]
        if not with_modules:
            raise GatewayError(
                "Das Konto sieht kein Zuhause mit Geräten. Wurde das Testkonto in der "
                "Home + Security-App eingeladen und die Einladung angenommen?"
            )
        if len(with_modules) > 1:
            names = ", ".join(f"{home.name} ({home.id})" for home in with_modules)
            raise GatewayError(f"Mehrere Zuhause gefunden – bitte EOS_HOME_ID setzen: {names}")
        self._home_id = with_modules[0].id
        return self._home_id

    async def _status_by_module(self, home_id: str) -> dict[str, dict[str, Any]]:
        try:
            status = await self._account.async_get_home_status(home_id)
        except (ApiError, AuthError) as err:
            raise GatewayError(explain(err)) from err
        modules = status.get("body", {}).get("home", {}).get("modules", [])
        return {module["id"]: module for module in modules if "id" in module}

    async def overview(self) -> dict[str, Any]:
        """Topologie und aktueller Zustand – das ist der Verbindungstest."""
        home_id = await self._ensure_home(refresh=True)
        home = self._account.homes[home_id]
        status = await self._status_by_module(home_id)
        modules = []
        for module in home.modules:
            live = status.get(module.id, {})
            kind = module_kind(module.raw_data)
            modules.append(
                {
                    "id": module.id,
                    "name": module.name,
                    "type": module.type,
                    "kind": kind,
                    "bridge": module.bridge,
                    "reachable": live.get("reachable"),
                    "openable": kind in OPEN_STATE,
                    "status": live,
                }
            )
        return {
            "account": self._account.user,
            "home": {"id": home.id, "name": home.name},
            "modules": modules,
        }

    # --- Öffnen ---

    async def open(self, module_id: str) -> OpenResult:
        """Sendet einen Öffnungsbefehl an genau ein Modul."""
        async with self._lock:
            wait = COOLDOWN_SECONDS - (time.monotonic() - self._last_open)
            if wait > 0:
                raise GatewayError(f"Bitte {wait:.0f} s warten – der letzte Befehl ist gerade erst gesendet worden.")

            home_id = await self._ensure_home()
            home = self._account.homes[home_id]
            module = next((m for m in home.modules if m.id == module_id), None)
            if module is None:
                raise GatewayError(f"Modul {module_id} gibt es in diesem Zuhause nicht.")
            kind = module_kind(module.raw_data)
            if kind not in OPEN_STATE:
                raise GatewayError(f"Modul „{module.name}“ ({module.type}) ist kein Türöffner und kein Relais.")

            before = (await self._status_by_module(home_id)).get(module_id, {})
            self._last_open = time.monotonic()
            started = time.monotonic()
            try:
                response = await self._account.async_set_module_state(
                    home_id=home_id,
                    module_id=module_id,
                    bridge_id=module.bridge,
                    state=dict(OPEN_STATE[kind]),
                    timezone=self._timezone,
                )
            except (ApiError, AuthError) as err:
                latency = int((time.monotonic() - started) * 1000)
                return OpenResult(module_id, module.name, False, latency, f"Befehl abgelehnt: {err}")
            latency = int((time.monotonic() - started) * 1000)

            errors = response_errors(response)
            accepted = response.get("status") == "ok" and not errors
            if accepted:
                detail = "Von der Cloud angenommen."
            elif errors:
                detail = f"Cloud meldet Fehler: {json.dumps(errors, ensure_ascii=False)}"
            else:
                detail = f"Unerwartete Antwort: status={response.get('status')!r}"

            changed: dict[str, Any] = {}
            if accepted:
                await asyncio.sleep(SETTLE_SECONDS)
                try:
                    after = (await self._status_by_module(home_id)).get(module_id, {})
                    changed = {
                        key: {"vorher": before.get(key), "nachher": after.get(key)}
                        for key in sorted((set(before) | set(after)) - NOISE_FIELDS)
                        if before.get(key) != after.get(key)
                    }
                except GatewayError:
                    pass  # der Befehl selbst war erfolgreich; der Vergleich ist nur Zusatzinformation

            return OpenResult(module_id, module.name, accepted, latency, detail, response, changed)

    async def close(self) -> None:
        await self._auth.close_session()
