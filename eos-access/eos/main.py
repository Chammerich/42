"""EOS Access – Web-App zum Öffnen der Haustür.

Eingeladene Personen sehen nach der Anmeldung nur eine Schaltfläche „Öffnen“.
Administratoren verwalten Personen, Zugänge und Einladungslinks. Die
BTicino-Anlage wird ausschließlich über ``Gateway`` angesprochen.
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Callable, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from .access import decide, describe, verify_password
from .gateway import Gateway, GatewayBusy, GatewayError
from .store import Store, UsernameTaken

STATIC_DIR = Path(__file__).parent / "static"  # ohne Anmeldung abrufbar: nur Gestaltung und Hilfsskript
PAGES_DIR = Path(__file__).parent / "pages"
COOKIE = "eos_session"
SESSION_SECONDS = 365 * 24 * 3600  # lange Anmeldedauer: einmal anmelden, danach direkt „Öffnen“
INVITE_SECONDS = 7 * 24 * 3600


class Settings:
    """Konfiguration aus Umgebungsvariablen (auf der Synology: Datei ``zugangsdaten.env``)."""

    def __init__(self) -> None:
        env = os.environ
        self.netatmo_email = env.get("NETATMO_EMAIL", "").strip()
        self.netatmo_password = env.get("NETATMO_PASSWORD", "")
        self.admin_user = env.get("EOS_ADMIN_USER", "").strip() or "admin"
        # EOS_CONSOLE_PASSWORD stammt aus der Testkonsole und gilt weiter, damit die alte Datei genügt.
        self.admin_password = env.get("EOS_ADMIN_PASSWORD") or env.get("EOS_CONSOLE_PASSWORD", "")
        self.home_id = env.get("EOS_HOME_ID", "").strip() or None
        self.door_module_id = env.get("EOS_DOOR_MODULE_ID", "").strip() or None
        self.public_url = env.get("EOS_PUBLIC_URL", "").strip().rstrip("/") or None
        self.timezone = env.get("TZ", "Europe/Berlin")
        self.data_dir = Path(env.get("EOS_DATA_DIR", "/data"))

    def problems(self) -> list[str]:
        found = []
        if not self.netatmo_email or not self.netatmo_password:
            found.append("NETATMO_EMAIL und NETATMO_PASSWORD müssen gesetzt sein.")
        if not self.admin_password:
            found.append("EOS_ADMIN_PASSWORD muss gesetzt sein.")
        return found


# --- Eingaben ---


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=200)


class PersonFields(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    function: str | None = Field(default=None, max_length=80)
    is_admin: bool | None = None
    access_type: Literal["once", "period", "permanent"] | None = None
    valid_from: int | None = None
    valid_until: int | None = None
    status: Literal["active", "inactive", "blocked"] | None = None

    @model_validator(mode="after")
    def check_period(self) -> "PersonFields":
        if self.access_type == "period":
            if not self.valid_until:
                raise ValueError("Für einen zeitlich begrenzten Zugang fehlt das Ende.")
            if self.valid_from and self.valid_from >= self.valid_until:
                raise ValueError("Das Ende muss nach dem Beginn liegen.")
        return self


class NewPerson(PersonFields):
    name: str = Field(min_length=1, max_length=80)
    access_type: Literal["once", "period", "permanent"]


def create_app(
    settings: Settings | None = None,
    gateway: Gateway | None = None,
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    settings = settings or Settings()
    problems = settings.problems()
    if problems:
        raise SystemExit("Konfiguration unvollständig:\n- " + "\n- ".join(problems))

    def now() -> int:
        return int(clock())

    store = Store(settings.data_dir / "eos-access.db")
    store.ensure_admin(settings.admin_user, settings.admin_password, now())
    gw = gateway or Gateway(
        settings.netatmo_email,
        settings.netatmo_password,
        token_file=settings.data_dir / "netatmo-tokens.json",
        timezone=settings.timezone,
        home_id=settings.home_id,
        door_module_id=settings.door_module_id,
    )
    open_lock = asyncio.Lock()  # Prüfen, Öffnen und Verbrauchen eines Einmalzugangs gehören zusammen

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await gw.close()
        store.close()

    app = FastAPI(title="EOS Access", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # --- Anmeldung ---

    def session_user(request: Request) -> dict[str, Any] | None:
        token = request.cookies.get(COOKIE)
        user = store.session_user(token, now()) if token else None
        return user if user and user["status"] != "blocked" else None

    async def require_user(request: Request) -> dict[str, Any]:
        user = session_user(request)
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bitte anmelden.")
        return user

    async def require_admin(user: Annotated[dict[str, Any], Depends(require_user)]) -> dict[str, Any]:
        if not user["is_admin"]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur für die Verwaltung.")
        return user

    User = Annotated[dict[str, Any], Depends(require_user)]
    Admin = Annotated[dict[str, Any], Depends(require_admin)]

    def start_session(request: Request, response: Response, user_id: int) -> None:
        token = store.create_session(user_id, now() + SESSION_SECONDS)
        response.set_cookie(
            COOKIE,
            token,
            max_age=SESSION_SECONDS,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )

    def page(name: str) -> FileResponse:
        return FileResponse(PAGES_DIR / name, headers={"Cache-Control": "no-store"})

    # --- Seiten ---

    @app.get("/")
    async def open_page(request: Request) -> Response:
        return page("oeffnen.html") if session_user(request) else RedirectResponse("/anmelden", 303)

    @app.get("/anmelden")
    async def login_page(request: Request) -> Response:
        return RedirectResponse("/", 303) if session_user(request) else page("anmelden.html")

    @app.get("/einladung/{token}")
    async def invite_page(token: str) -> Response:
        return page("einladung.html")

    @app.get("/verwaltung")
    async def admin_page(request: Request) -> Response:
        user = session_user(request)
        if user is None:
            return RedirectResponse("/anmelden", 303)
        return page("verwaltung.html") if user["is_admin"] else RedirectResponse("/", 303)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # --- Anmelden, Abmelden, Einladung einlösen ---

    @app.post("/api/login")
    async def login(body: Credentials, request: Request, response: Response) -> dict[str, bool]:
        user = store.user_by_username(body.username)
        if user is None or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Benutzername oder Passwort stimmt nicht.")
        if user["status"] == "blocked":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieser Zugang ist gesperrt.")
        start_session(request, response, user["id"])
        return {"ok": True}

    @app.post("/api/logout")
    async def logout(request: Request, response: Response) -> dict[str, bool]:
        token = request.cookies.get(COOKIE)
        if token:
            store.delete_session(token)
        response.delete_cookie(COOKIE)
        return {"ok": True}

    def valid_invite(token: str) -> tuple[dict[str, Any], dict[str, Any]]:
        invite = store.invite(token, now())
        user = store.user(invite["user_id"]) if invite else None
        if user is None or user["status"] == "blocked":
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dieser Einladungslink ist ungültig oder abgelaufen.")
        return invite, user

    @app.get("/api/invite/{token}")
    async def invite_info(token: str) -> dict[str, Any]:
        _, user = valid_invite(token)
        return {"name": user["name"], "username": user["username"]}

    @app.post("/api/invite/{token}")
    async def redeem_invite(token: str, body: Credentials, request: Request, response: Response) -> dict[str, bool]:
        _, user = valid_invite(token)
        try:
            store.set_credentials(user["id"], body.username, body.password)
        except UsernameTaken:
            raise HTTPException(status.HTTP_409_CONFLICT, "Dieser Benutzername ist schon vergeben.") from None
        store.consume_invite(token)  # der Link gilt genau einmal
        store.delete_sessions_of(user["id"])
        store.add_log(now(), user["name"], "konto_eingerichtet")
        start_session(request, response, user["id"])
        return {"ok": True}

    # --- Die eine Funktion für eingeladene Personen ---

    def me_view(user: dict[str, Any]) -> dict[str, Any]:
        decision = decide(user, now(), settings.timezone)
        return {
            "name": user["name"],
            "is_admin": bool(user["is_admin"]),
            "can_open": decision.allowed,
            "message": decision.message,
            "access": describe(user, settings.timezone),
        }

    @app.get("/api/me")
    async def me(user: User) -> dict[str, Any]:
        return me_view(user)

    @app.post("/api/open")
    async def open_door(user: User) -> dict[str, Any]:
        async with open_lock:
            user = store.user(user["id"]) or user  # Stand von jetzt, nicht vom Beginn der Anfrage
            decision = decide(user, now(), settings.timezone)
            if not decision.allowed:
                store.add_log(now(), user["name"], "abgelehnt", decision.message)
                return {"ok": False, **me_view(user)}
            try:
                result = await gw.open()
            except GatewayBusy:
                return {"ok": False, **me_view(user), "message": "Die Tür wurde gerade eben geöffnet."}
            except GatewayError as err:
                store.add_log(now(), user["name"], "fehlgeschlagen", str(err))
                return {"ok": False, **me_view(user), "message": "Die Tür ist gerade nicht erreichbar."}
            if not result.accepted:
                store.add_log(now(), user["name"], "fehlgeschlagen", result.detail, result.latency_ms)
                return {"ok": False, **me_view(user), "message": "Das hat nicht geklappt. Bitte noch einmal versuchen."}

            # Erst jetzt, nach angenommenem Befehl, gilt ein Einmalzugang als verbraucht.
            if user["access_type"] == "once" and not user["is_admin"]:
                store.update_user(user["id"], once_used_at=now())
                user = store.user(user["id"]) or user
            store.add_log(now(), user["name"], "geoeffnet", result.detail, result.latency_ms)
            return {"ok": True, **me_view(user), "message": "Tür freigegeben."}

    # --- Verwaltung ---

    def invite_url(request: Request, token: str) -> str:
        base = settings.public_url or str(request.base_url).rstrip("/")
        return f"{base}/einladung/{token}"

    def new_invite(request: Request, user_id: int) -> dict[str, Any]:
        expires_at = now() + INVITE_SECONDS
        token = store.create_invite(user_id, expires_at)
        return {"url": invite_url(request, token), "expires_at": expires_at}

    def person_view(user: dict[str, Any]) -> dict[str, Any]:
        decision = decide(user, now(), settings.timezone)
        return {
            **{key: user[key] for key in ("id", "name", "function", "username", "status", "access_type")},
            **{key: user[key] for key in ("valid_from", "valid_until", "once_used_at")},
            "is_admin": bool(user["is_admin"]),
            "has_account": user["password_hash"] is not None,
            "state": decision.code,
            "invite_expires_at": store.invite_expiry(user["id"], now()),
            "is_config_admin": (user["username"] or "").lower() == settings.admin_user.lower(),
        }

    def person_or_404(user_id: int) -> dict[str, Any]:
        user = store.user(user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Diese Person gibt es nicht mehr.")
        return user

    def access_changes(body: PersonFields) -> dict[str, Any]:
        """Eine neue Zugangsart ersetzt die alte vollständig – auch ein verbrauchter Einmalzugang gilt wieder."""
        if body.access_type is None:
            return {}
        period = body.access_type == "period"
        return {
            "access_type": body.access_type,
            "valid_from": body.valid_from if period else None,
            "valid_until": body.valid_until if period else None,
            "once_used_at": None,
        }

    @app.get("/api/admin/people")
    async def people(_: Admin) -> list[dict[str, Any]]:
        return [person_view(user) for user in store.users()]

    @app.post("/api/admin/people")
    async def create_person(body: NewPerson, request: Request, _: Admin) -> dict[str, Any]:
        user = store.create_user(
            now(),
            name=body.name.strip(),
            function=(body.function or "").strip(),
            is_admin=int(bool(body.is_admin)),
            **access_changes(body),
        )
        return {"person": person_view(user), "invite": new_invite(request, user["id"])}

    @app.patch("/api/admin/people/{user_id}")
    async def update_person(user_id: int, body: PersonFields, admin: Admin) -> dict[str, Any]:
        user = person_or_404(user_id)
        own_account = user["id"] == admin["id"]
        if own_account and (body.status in ("inactive", "blocked") or body.is_admin is False):
            raise HTTPException(status.HTTP_409_CONFLICT, "Das eigene Konto lässt sich so nicht ändern.")
        changes = access_changes(body)
        if body.name is not None:
            changes["name"] = body.name.strip()
        if body.function is not None:
            changes["function"] = body.function.strip()
        if body.is_admin is not None:
            changes["is_admin"] = int(body.is_admin)
        if body.status is not None:
            changes["status"] = body.status
        store.update_user(user_id, **changes)
        if body.status == "blocked":
            store.delete_sessions_of(user_id)  # gesperrt heißt: sofort abgemeldet
        return person_view(person_or_404(user_id))

    @app.post("/api/admin/people/{user_id}/invite")
    async def invite_person(user_id: int, request: Request, _: Admin) -> dict[str, Any]:
        person_or_404(user_id)
        return new_invite(request, user_id)

    @app.delete("/api/admin/people/{user_id}")
    async def delete_person(user_id: int, admin: Admin) -> dict[str, bool]:
        user = person_or_404(user_id)
        if user["id"] == admin["id"]:
            raise HTTPException(status.HTTP_409_CONFLICT, "Das eigene Konto lässt sich nicht löschen.")
        store.delete_user(user_id)
        return {"ok": True}

    @app.get("/api/admin/log")
    async def read_log(_: Admin) -> list[dict[str, Any]]:
        return store.log()

    @app.get("/api/admin/status")
    async def connection_status(_: Admin) -> dict[str, Any]:
        try:
            return {"ok": True, **await gw.status()}
        except GatewayError as err:
            return {"ok": False, "message": str(err)}

    return app
