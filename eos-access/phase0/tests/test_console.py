"""Tests gegen eine nachgebaute Netatmo-Cloud.

``pybticino`` läuft dabei unverändert; nur die Basis-URL zeigt auf einen
lokalen Server. So wird geprüft, dass wirklich der erwartete Befehl
gesendet wird und dass Fehlerantworten nicht als Erfolg zählen.
"""

import asyncio
import base64
import threading

import pytest
from aiohttp import web
from fastapi.testclient import TestClient

from app import gateway as gateway_module
from app.main import Settings, create_app

HOME_ID = "home-1"
BRIDGE = "00:03:50:aa:bb:cc"
LOCK = "00:03:50:aa:bb:cc-a0"
LIGHT = "00:03:50:aa:bb:cc-b0"
UNIT = "00:03:50:aa:bb:cc-c0"
PASSWORD = "ein-langes-testpasswort"


class FakeCloud:
    """Minimaler Nachbau der drei benutzten Endpunkte."""

    def __init__(self) -> None:
        self.setstate_calls: list[dict] = []
        self.logins = 0
        self.fail_setstate_with: dict | None = None
        self.http_error: int | None = None
        self.last_interaction = 100

    async def token(self, request: web.Request) -> web.Response:
        form = await request.post()
        if form.get("grant_type") == "password":
            self.logins += 1
            if form.get("password") != "richtig":
                return web.json_response({"error": "invalid_grant"}, status=400)
        return web.json_response({"access_token": "at", "refresh_token": "rt", "expires_in": 10800})

    async def homesdata(self, _: web.Request) -> web.Response:
        modules = [
            {"id": BRIDGE, "type": "BNC1", "name": "Classe 300EOS"},
            {"id": LOCK, "type": "BNDL", "name": "Haustür", "bridge": BRIDGE, "variant": "bncx:bndl_doorlock"},
            {"id": LIGHT, "type": "BNSL", "name": "Treppenlicht", "bridge": BRIDGE},
            {"id": UNIT, "type": "BNEU", "name": "Außenstation", "bridge": BRIDGE},
        ]
        homes = [{"id": HOME_ID, "name": "Zuhause", "modules": modules}, {"id": "leer", "name": "Leer"}]
        return web.json_response({"status": "ok", "body": {"homes": homes, "user": {"email": "eos@example.com"}}})

    async def homestatus(self, _: web.Request) -> web.Response:
        modules = [
            {"id": BRIDGE, "type": "BNC1", "reachable": True},
            {"id": LOCK, "type": "BNDL", "reachable": True, "lock": True, "last_user_interaction": self.last_interaction},
            {"id": LIGHT, "type": "BNSL", "reachable": True, "status": "off"},
        ]
        return web.json_response({"status": "ok", "body": {"home": {"id": HOME_ID, "modules": modules}}})

    async def setstate(self, request: web.Request) -> web.Response:
        self.setstate_calls.append(await request.json())
        if self.http_error:
            return web.json_response({"error": {"code": 13, "message": "kaputt"}}, status=self.http_error)
        if self.fail_setstate_with:
            return web.json_response(self.fail_setstate_with)
        self.last_interaction += 1
        return web.json_response({"status": "ok", "time_server": 1})


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
    monkeypatch.setattr(gateway_module, "SETTLE_SECONDS", 0)
    monkeypatch.setattr(gateway_module, "COOLDOWN_SECONDS", 0)
    yield fake
    asyncio.run_coroutine_threadsafe(runner.cleanup(), loop).result(5)
    loop.call_soon_threadsafe(loop.stop)
    thread.join(5)


def make_client(tmp_path, monkeypatch, netatmo_password="richtig", login=True):
    monkeypatch.setenv("NETATMO_EMAIL", "eos@example.com")
    monkeypatch.setenv("NETATMO_PASSWORD", netatmo_password)
    monkeypatch.setenv("EOS_CONSOLE_PASSWORD", PASSWORD)
    monkeypatch.setenv("EOS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TZ", "Europe/Berlin")
    client = TestClient(create_app(Settings()))
    if login:
        token = base64.b64encode(f"test:{PASSWORD}".encode()).decode()
        client.headers["Authorization"] = f"Basic {token}"
    return client


def test_ohne_passwort_kein_zugriff(cloud, tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch, login=False) as client:
        assert client.get("/").status_code == 401
        assert client.get("/api/overview").status_code == 401
        assert client.post("/api/open", json={"module_id": LOCK, "scenario": "ohne_ruf"}).status_code == 401
        assert client.get("/api/log").status_code == 401
        assert client.get("/", auth=("test", "falsch")).status_code == 401
    assert cloud.setstate_calls == []


def test_start_ohne_konfiguration_scheitert(monkeypatch, tmp_path):
    monkeypatch.setenv("NETATMO_EMAIL", "eos@example.com")
    monkeypatch.setenv("NETATMO_PASSWORD", "richtig")
    monkeypatch.setenv("EOS_CONSOLE_PASSWORD", "")
    with pytest.raises(SystemExit):
        create_app(Settings())


def test_verbindung_zeigt_module(cloud, tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        data = client.get("/api/overview").json()
    assert data["home"] == {"id": HOME_ID, "name": "Zuhause"}
    kinds = {module["name"]: (module["kind"], module["openable"]) for module in data["modules"]}
    assert kinds == {
        "Classe 300EOS": ("bridge", False),
        "Haustür": ("lock", True),
        "Treppenlicht": ("light", True),
        "Außenstation": ("external_unit", False),
    }
    assert (tmp_path / "netatmo-tokens.json").stat().st_mode & 0o777 == 0o600


def test_falsches_netatmo_passwort_wird_erklaert(cloud, tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch, netatmo_password="falsch") as client:
        response = client.get("/api/overview")
    assert response.status_code == 502
    assert "Zugangsdaten abgelehnt" in response.json()["detail"]


def test_netzausfall_wird_nicht_als_falsches_passwort_gemeldet(tmp_path, monkeypatch):
    monkeypatch.setattr("pybticino.auth.BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setattr("pybticino.account.BASE_URL", "http://127.0.0.1:9")
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get("/api/overview")
    assert response.status_code == 502
    assert "nicht erreichbar" in response.json()["detail"]
    assert "Zugangsdaten" not in response.json()["detail"]


def test_oeffnen_sendet_genau_den_tuerbefehl(cloud, tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        entry = client.post("/api/open", json={"module_id": LOCK, "scenario": "ohne_ruf"}).json()
        assert entry["accepted"] is True
        assert entry["door_opened"] is None
        assert entry["changed"] == {"last_user_interaction": {"vorher": 100, "nachher": 101}}
        assert cloud.setstate_calls[0]["home"] == {
            "id": HOME_ID,
            "modules": [{"id": LOCK, "lock": False, "bridge": BRIDGE}],
            "timezone": "Europe/Berlin",
        }

        confirmed = client.post(f"/api/log/{entry['id']}/confirm", json={"door_opened": True}).json()
        assert confirmed["door_opened"] is True
        log = client.get("/api/log").json()
        assert [(e["scenario"], e["door_opened"]) for e in log] == [("ohne_ruf", True)]
        assert client.post("/api/log/gibtsnicht/confirm", json={"door_opened": True}).status_code == 404


def test_relais_wird_eingeschaltet(cloud, tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        client.post("/api/open", json={"module_id": LIGHT, "scenario": "gespraech_aktiv"})
    assert cloud.setstate_calls[0]["home"]["modules"] == [{"id": LIGHT, "on": True, "bridge": BRIDGE}]


@pytest.mark.parametrize("module_id", [UNIT, BRIDGE, "unbekannt"])
def test_andere_module_werden_nie_angesteuert(cloud, tmp_path, monkeypatch, module_id):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.post("/api/open", json={"module_id": module_id, "scenario": "ohne_ruf"})
    assert response.status_code == 409
    assert cloud.setstate_calls == []


def test_fehler_im_antwortkoerper_zaehlt_nicht_als_erfolg(cloud, tmp_path, monkeypatch):
    cloud.fail_setstate_with = {"status": "ok", "body": {"errors": [{"code": 5, "id": LOCK}]}}
    with make_client(tmp_path, monkeypatch) as client:
        entry = client.post("/api/open", json={"module_id": LOCK, "scenario": "ohne_ruf"}).json()
    assert entry["accepted"] is False
    assert '"code": 5' in entry["detail"]


def test_http_fehler_wird_protokolliert(cloud, tmp_path, monkeypatch):
    cloud.http_error = 403
    with make_client(tmp_path, monkeypatch) as client:
        entry = client.post("/api/open", json={"module_id": LOCK, "scenario": "ruf_klingelt"}).json()
        assert entry["accepted"] is False
        assert "403" in entry["detail"]
        assert len(client.get("/api/log").json()) == 1


def test_doppelklick_sendet_nur_einen_befehl(cloud, tmp_path, monkeypatch):
    monkeypatch.setattr(gateway_module, "COOLDOWN_SECONDS", 60)
    with make_client(tmp_path, monkeypatch) as client:
        first = client.post("/api/open", json={"module_id": LOCK, "scenario": "ohne_ruf"})
        second = client.post("/api/open", json={"module_id": LOCK, "scenario": "ohne_ruf"})
    assert first.status_code == 200
    assert second.status_code == 409
    assert len(cloud.setstate_calls) == 1


def test_neustart_meldet_sich_nicht_erneut_mit_passwort_an(cloud, tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        client.get("/api/overview")
    with make_client(tmp_path, monkeypatch) as client:
        assert client.get("/api/overview").status_code == 200
    assert cloud.logins == 1
