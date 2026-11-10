"""Nachgebaute Netatmo-Cloud und ein Test-Client mit stellbarer Uhr.

``pybticino`` läuft unverändert; nur die Basis-URL zeigt auf einen lokalen
Server. So wird geprüft, was wirklich an die Cloud gesendet würde.
"""

import asyncio
import threading
from contextlib import ExitStack

import pytest
from aiohttp import web
from fastapi.testclient import TestClient

from eos import gateway as gateway_module
from eos.main import Settings, create_app

HOME_ID = "home-1"
BRIDGE = "00:03:50:aa:bb:cc"
LOCK = "aabbcc-a06f-000000000001"
LIGHT = "aabbcc-1e60-000000000002"
UNIT = "aabbcc-a06f-000000000003"
ADMIN_PASSWORD = "adminpasswort"
START = 1_800_000_000  # fester Startzeitpunkt der Testuhr


class FakeCloud:
    def __init__(self) -> None:
        self.setstate_calls: list[dict] = []
        self.logins = 0
        self.setstate_replies: list[tuple[int, dict]] = []  # vorgemerkte Antworten, danach „ok“
        self.extra_lock = False

    async def token(self, request: web.Request) -> web.Response:
        form = await request.post()
        if form.get("grant_type") == "password":
            self.logins += 1
            if form.get("password") != "richtig":
                return web.json_response({"error": "invalid_grant"}, status=400)
        return web.json_response({"access_token": "at", "refresh_token": "rt", "expires_in": 10800})

    async def homesdata(self, _: web.Request) -> web.Response:
        modules = [
            {"id": BRIDGE, "type": "BNCX", "name": "Classe 300EOS with Netatmo"},
            {"id": UNIT, "type": "BNEU", "name": "Placa exterior", "bridge": BRIDGE},
            {"id": LOCK, "type": "BNDL", "name": "Cerradura", "bridge": BRIDGE},
            {"id": LIGHT, "type": "BNSL", "name": "Luz de escaleras", "bridge": BRIDGE},
        ]
        if self.extra_lock:
            modules.append({"id": "garage", "type": "BNDL", "name": "Garage", "bridge": BRIDGE})
        homes = [{"id": HOME_ID, "name": "Zuhause", "modules": modules}, {"id": "leer", "name": "Leer"}]
        return web.json_response({"status": "ok", "body": {"homes": homes, "user": {"email": "eos@example.com"}}})

    async def homestatus(self, _: web.Request) -> web.Response:
        modules = [{"id": LOCK, "type": "BNDL", "reachable": True, "lock": True}]
        return web.json_response({"status": "ok", "body": {"home": {"id": HOME_ID, "modules": modules}}})

    async def setstate(self, request: web.Request) -> web.Response:
        self.setstate_calls.append(await request.json())
        if self.setstate_replies:
            code, body = self.setstate_replies.pop(0)
            return web.json_response(body, status=code)
        return web.json_response({"status": "ok", "time_server": 1})

    def opened(self) -> list[dict]:
        """Die Modulbefehle aller bisherigen Öffnungsversuche."""
        return [call["home"]["modules"][0] for call in self.setstate_calls]


@pytest.fixture
def cloud(monkeypatch):
    fake = FakeCloud()
    app = web.Application()
    app.router.add_post("/oauth2/token", fake.token)
    app.router.add_post("/api/homesdata", fake.homesdata)
    app.router.add_post("/syncapi/v1/homestatus", fake.homestatus)
    app.router.add_post("/syncapi/v1/setstate", fake.setstate)

    loop = asyncio.new_event_loop()
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "127.0.0.1", 0)
    loop.run_until_complete(site.start())
    port = site._server.sockets[0].getsockname()[1]
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    monkeypatch.setattr("pybticino.auth.BASE_URL", base)
    monkeypatch.setattr("pybticino.account.BASE_URL", base)
    monkeypatch.setattr(gateway_module, "COOLDOWN_SECONDS", 0)
    yield fake
    asyncio.run_coroutine_threadsafe(runner.cleanup(), loop).result(5)
    loop.call_soon_threadsafe(loop.stop)
    thread.join(5)


class Clock:
    def __init__(self) -> None:
        self.now = float(START)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class Browser:
    """Ein Besucher mit eigenen Cookies. Alle Besucher teilen sich einen Client und damit eine Ereignisschleife."""

    def __init__(self, client: TestClient) -> None:
        self._client = client
        self.cookies: dict[str, str] = {}

    def request(self, method: str, url: str, **kwargs):
        self._client.cookies.clear()
        headers = {"Cookie": "; ".join(f"{k}={v}" for k, v in self.cookies.items())} if self.cookies else {}
        response = self._client.request(method, url, headers=headers, **kwargs)
        for header in response.headers.get_list("set-cookie"):
            name, _, value = header.split(";", 1)[0].partition("=")
            if value.strip('"'):
                self.cookies[name] = value
            else:
                self.cookies.pop(name, None)
        return response

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request("DELETE", url, **kwargs)


class Site:
    """Die laufende App samt Uhr; ``browser()`` liefert je Person einen eigenen Besucher."""

    def __init__(self, client: TestClient, clock: Clock) -> None:
        self._client = client
        self.clock = clock

    def browser(self) -> Browser:
        return Browser(self._client)

    def admin(self) -> Browser:
        client = self.browser()
        assert client.post("/api/login", json={"username": "admin", "password": ADMIN_PASSWORD}).status_code == 200
        return client

    def invite(self, admin: Browser, **fields) -> tuple[int, str]:
        """Legt eine Person an und gibt (id, Pfad des Einladungslinks) zurück."""
        body = {"name": "Gast", "access_type": "permanent", **fields}
        data = admin.post("/api/admin/people", json=body).json()
        return data["person"]["id"], data["invite"]["url"].split("http://testserver")[1]

    def guest(self, admin: Browser, username: str = "gast", **fields) -> tuple[int, Browser]:
        """Legt eine Person an, löst ihre Einladung ein und gibt (id, angemeldeter Client) zurück."""
        user_id, path = self.invite(admin, **fields)
        client = self.browser()
        token = path.rsplit("/", 1)[1]
        response = client.post(f"/api/invite/{token}", json={"username": username, "password": "geheim"})
        assert response.status_code == 200, response.text
        return user_id, client


@pytest.fixture
def make_site(cloud, tmp_path, monkeypatch):
    stack = ExitStack()

    def build(**env) -> Site:
        values = {
            "NETATMO_EMAIL": "eos@example.com",
            "NETATMO_PASSWORD": "richtig",
            "EOS_ADMIN_PASSWORD": ADMIN_PASSWORD,
            "EOS_DATA_DIR": str(tmp_path),
            "TZ": "Europe/Berlin",
            **env,
        }
        for key in ("EOS_CONSOLE_PASSWORD", "EOS_ADMIN_USER", "EOS_HOME_ID", "EOS_DOOR_MODULE_ID", "EOS_PUBLIC_URL"):
            monkeypatch.delenv(key, raising=False)
        for key, value in values.items():
            monkeypatch.setenv(key, value)
        clock = Clock()
        client = stack.enter_context(TestClient(create_app(Settings(), clock=clock), follow_redirects=False))
        return Site(client, clock)

    with stack:
        yield build


@pytest.fixture
def site(make_site) -> Site:
    return make_site()
