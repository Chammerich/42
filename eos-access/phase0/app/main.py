"""EOS Access – Phase 0: Testkonsole.

Kleine, passwortgeschützte Weboberfläche für das Heimnetz. Sie beantwortet
die offene technische Frage des Projekts: Lässt sich die Haustür über die
Netatmo-Cloud zuverlässig öffnen – ohne Ruf und während eines Gesprächs?

Noch keine Benutzer, keine Einladungen, keine Berechtigungen.
"""

import json
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from .gateway import Gateway, GatewayError

STATIC_DIR = Path(__file__).parent / "static"
Scenario = Literal["ohne_ruf", "ruf_klingelt", "gespraech_aktiv"]


class Settings:
    """Konfiguration aus Umgebungsvariablen (auf der Synology: Datei ``.env``)."""

    def __init__(self) -> None:
        self.netatmo_email = os.environ.get("NETATMO_EMAIL", "").strip()
        self.netatmo_password = os.environ.get("NETATMO_PASSWORD", "")
        self.console_password = os.environ.get("EOS_CONSOLE_PASSWORD", "")
        self.home_id = os.environ.get("EOS_HOME_ID", "").strip() or None
        self.timezone = os.environ.get("TZ", "Europe/Berlin")
        self.data_dir = Path(os.environ.get("EOS_DATA_DIR", "/data"))

    def problems(self) -> list[str]:
        found = []
        if not self.netatmo_email or not self.netatmo_password:
            found.append("NETATMO_EMAIL und NETATMO_PASSWORD müssen gesetzt sein.")
        if not self.console_password:
            found.append("EOS_CONSOLE_PASSWORD muss gesetzt sein.")
        return found


class TestLog:
    """Testprotokoll als JSON-Datei. Für die wenigen Einträge einer Testphase genügt das."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def entries(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self._path.read_text())
        except (OSError, ValueError):
            return []

    def _write(self, entries: list[dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(entries, ensure_ascii=False, indent=2))
        os.replace(tmp, self._path)

    def add(self, entry: dict[str, Any]) -> None:
        entries = self.entries()
        entries.append(entry)
        self._write(entries)

    def set_door_opened(self, entry_id: str, door_opened: bool) -> dict[str, Any] | None:
        entries = self.entries()
        for entry in entries:
            if entry["id"] == entry_id:
                entry["door_opened"] = door_opened
                self._write(entries)
                return entry
        return None


class OpenRequest(BaseModel):
    module_id: str = Field(min_length=1, max_length=64)
    scenario: Scenario


class ConfirmRequest(BaseModel):
    door_opened: bool


def create_app(settings: Settings | None = None, gateway: Gateway | None = None) -> FastAPI:
    settings = settings or Settings()
    problems = settings.problems()
    if problems:
        raise SystemExit("Konfiguration unvollständig:\n- " + "\n- ".join(problems))

    log = TestLog(settings.data_dir / "testprotokoll.json")
    gw = gateway or Gateway(
        settings.netatmo_email,
        settings.netatmo_password,
        token_file=settings.data_dir / "netatmo-tokens.json",
        timezone=settings.timezone,
        home_id=settings.home_id,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await gw.close()

    app = FastAPI(title="EOS Access – Testkonsole", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    basic = HTTPBasic(realm="EOS Access Testkonsole")

    def require_login(credentials: Annotated[HTTPBasicCredentials, Depends(basic)]) -> None:
        given = credentials.password.encode()
        expected = settings.console_password.encode()
        if not secrets.compare_digest(given, expected):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Falsches Passwort.",
                headers={"WWW-Authenticate": 'Basic realm="EOS Access Testkonsole"'},
            )

    protected = [Depends(require_login)]

    @app.get("/", dependencies=protected)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/api/overview", dependencies=protected)
    async def overview() -> dict[str, Any]:
        try:
            return await gw.overview()
        except GatewayError as err:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(err)) from err

    @app.post("/api/open", dependencies=protected)
    async def open_door(request: OpenRequest) -> dict[str, Any]:
        try:
            result = await gw.open(request.module_id)
        except GatewayError as err:
            raise HTTPException(status.HTTP_409_CONFLICT, str(err)) from err
        entry = {
            "id": uuid.uuid4().hex,
            "time": datetime.now(ZoneInfo(settings.timezone)).isoformat(timespec="seconds"),
            "scenario": request.scenario,
            "door_opened": None,  # trägt der Tester anschließend ein
            **result.as_dict(),
        }
        log.add(entry)
        return entry

    @app.post("/api/log/{entry_id}/confirm", dependencies=protected)
    async def confirm(entry_id: str, request: ConfirmRequest) -> dict[str, Any]:
        entry = log.set_door_opened(entry_id, request.door_opened)
        if entry is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Eintrag nicht gefunden.")
        return entry

    @app.get("/api/log", dependencies=protected)
    async def read_log() -> list[dict[str, Any]]:
        return log.entries()

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
