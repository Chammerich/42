import sqlite3

import pytest

from eos import gateway as gateway_module
from eos.main import Settings, create_app

from .conftest import ADMIN_PASSWORD, BRIDGE, LIGHT, LOCK, START

DAY = 24 * 3600


def open_door(client):
    return client.post("/api/open").json()


# --- Zugriffsschutz ---


def test_ohne_anmeldung_ist_nichts_erreichbar(site, cloud):
    client = site.browser()
    assert client.get("/").headers["location"] == "/anmelden"
    assert client.get("/verwaltung").headers["location"] == "/anmelden"
    assert client.post("/api/open").status_code == 401
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/admin/people").status_code == 401
    assert client.get("/api/admin/log").status_code == 401
    assert cloud.opened() == []


def test_gaeste_kommen_nicht_in_die_verwaltung(site):
    admin = site.admin()
    _, guest = site.guest(admin)
    assert guest.get("/verwaltung").headers["location"] == "/"
    assert guest.get("/api/admin/people").status_code == 403
    assert guest.get("/api/admin/log").status_code == 403
    assert guest.get("/api/admin/status").status_code == 403
    assert guest.post("/api/admin/people", json={"name": "X", "access_type": "permanent"}).status_code == 403
    assert guest.delete("/api/admin/people/1").status_code == 403


def test_start_ohne_adminpasswort_scheitert(monkeypatch, tmp_path):
    monkeypatch.setenv("NETATMO_EMAIL", "eos@example.com")
    monkeypatch.setenv("NETATMO_PASSWORD", "richtig")
    monkeypatch.delenv("EOS_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("EOS_CONSOLE_PASSWORD", raising=False)
    monkeypatch.setenv("EOS_DATA_DIR", str(tmp_path))
    with pytest.raises(SystemExit):
        create_app(Settings())


def test_passwort_der_testkonsole_gilt_als_adminpasswort_weiter(make_site):
    site = make_site(EOS_ADMIN_PASSWORD="", EOS_CONSOLE_PASSWORD="altespasswort")
    assert site.browser().post("/api/login", json={"username": "admin", "password": "altespasswort"}).status_code == 200


def test_falsches_passwort(site):
    client = site.browser()
    response = client.post("/api/login", json={"username": "admin", "password": "falsch"})
    assert response.status_code == 401
    assert client.get("/api/me").status_code == 401
    assert site.browser().post("/api/login", json={"username": "ADMIN", "password": ADMIN_PASSWORD}).status_code == 200


# --- Einladung und Öffnen ---


def test_von_der_einladung_bis_zur_offenen_tuer(site, cloud):
    admin = site.admin()
    user_id, path = site.invite(admin, name="Marta", function="Reinigung")
    token = path.rsplit("/", 1)[1]

    guest = site.browser()
    assert guest.get(path).status_code == 200
    assert guest.get(f"/api/invite/{token}").json() == {"name": "Marta", "username": None}
    assert guest.post(f"/api/invite/{token}", json={"username": "marta", "password": "geheim"}).status_code == 200

    me = guest.get("/api/me").json()
    assert me == {"name": "Marta", "is_admin": False, "can_open": True, "message": "", "access": "Dauerhafter Zugang"}
    assert guest.get("/").status_code == 200

    result = open_door(guest)
    assert result["ok"] is True
    assert cloud.opened() == [{"id": LOCK, "lock": False, "bridge": BRIDGE}]
    assert cloud.setstate_calls[0]["home"]["timezone"] == "Europe/Berlin"

    log = admin.get("/api/admin/log").json()
    assert [(e["user_name"], e["event"]) for e in log] == [("Marta", "geoeffnet"), ("Marta", "konto_eingerichtet")]

    people = {p["name"]: p for p in admin.get("/api/admin/people").json()}
    assert people["Marta"]["has_account"] is True
    assert people["Marta"]["username"] == "marta"
    assert people["Marta"]["invite_expires_at"] is None


def test_einladungslink_gilt_nur_einmal(site):
    admin = site.admin()
    _, path = site.invite(admin)
    token = path.rsplit("/", 1)[1]
    assert site.browser().post(f"/api/invite/{token}", json={"username": "a", "password": "x"}).status_code == 200
    assert site.browser().get(f"/api/invite/{token}").status_code == 404
    assert site.browser().post(f"/api/invite/{token}", json={"username": "b", "password": "x"}).status_code == 404


def test_einladungslink_laeuft_ab(site):
    admin = site.admin()
    _, path = site.invite(admin)
    token = path.rsplit("/", 1)[1]
    site.clock.advance(7 * DAY - 1)
    assert site.browser().get(f"/api/invite/{token}").status_code == 200
    site.clock.advance(1)
    assert site.browser().get(f"/api/invite/{token}").status_code == 404
    assert site.browser().post(f"/api/invite/{token}", json={"username": "a", "password": "x"}).status_code == 404


def test_neuer_link_ersetzt_den_alten_und_setzt_das_passwort_neu(site):
    admin = site.admin()
    user_id, old_client = site.guest(admin, username="marta")
    _, first_path = site.invite(admin, name="Zweite")
    first = first_path.rsplit("/", 1)[1]

    # neuer Link für eine noch nicht eingerichtete Person: der alte ist tot
    second_id = [p for p in admin.get("/api/admin/people").json() if p["name"] == "Zweite"][0]["id"]
    admin.post(f"/api/admin/people/{second_id}/invite")
    assert site.browser().get(f"/api/invite/{first}").status_code == 404

    # neuer Link für ein bestehendes Konto: Passwort neu, alte Sitzung beendet
    token = admin.post(f"/api/admin/people/{user_id}/invite").json()["url"].rsplit("/", 1)[1]
    fresh = site.browser()
    assert fresh.get(f"/api/invite/{token}").json()["username"] == "marta"
    assert fresh.post(f"/api/invite/{token}", json={"username": "marta", "password": "neu"}).status_code == 200
    assert old_client.get("/api/me").status_code == 401
    assert site.browser().post("/api/login", json={"username": "marta", "password": "geheim"}).status_code == 401
    assert site.browser().post("/api/login", json={"username": "marta", "password": "neu"}).status_code == 200


def test_benutzername_ist_eindeutig(site):
    admin = site.admin()
    site.guest(admin, username="marta")
    _, path = site.invite(admin)
    token = path.rsplit("/", 1)[1]
    client = site.browser()
    assert client.post(f"/api/invite/{token}", json={"username": "Marta", "password": "x"}).status_code == 409
    assert client.post(f"/api/invite/{token}", json={"username": "admin", "password": "x"}).status_code == 409
    assert client.post(f"/api/invite/{token}", json={"username": "marta2", "password": "x"}).status_code == 200


def test_passwoerter_und_tokens_liegen_nicht_im_klartext_in_der_datenbank(site, tmp_path):
    admin = site.admin()
    _, path = site.invite(admin, name="Offen")
    site.guest(admin, username="marta")
    dump = "\n".join(sqlite3.connect(tmp_path / "eos-access.db").iterdump())
    assert "geheim" not in dump
    assert ADMIN_PASSWORD not in dump
    assert path.rsplit("/", 1)[1] not in dump
    assert admin.cookies["eos_session"] not in dump


# --- Zugangsarten ---


def test_einmalzugang_wird_erst_nach_angenommenem_befehl_verbraucht(site, cloud):
    admin = site.admin()
    user_id, guest = site.guest(admin, access_type="once")
    assert guest.get("/api/me").json()["access"] == "Einmaliger Zugang"

    cloud.setstate_replies = [
        (500, {"error": {"code": 1, "message": "kaputt"}}),
        (200, {"status": "ok", "body": {"errors": [{"code": 5, "id": LOCK}]}}),
    ]
    assert open_door(guest)["ok"] is False  # HTTP-Fehler der Cloud
    assert open_door(guest)["ok"] is False  # „ok“ mit Fehler im Antwortkörper
    assert guest.get("/api/me").json()["can_open"] is True

    assert open_door(guest)["ok"] is True
    again = open_door(guest)
    assert again["ok"] is False
    assert again["can_open"] is False
    assert "bereits genutzt" in again["message"]
    assert len(cloud.opened()) == 3  # der vierte Versuch erreicht die Cloud gar nicht

    events = [e["event"] for e in admin.get("/api/admin/log").json()]
    assert events == ["abgelehnt", "geoeffnet", "fehlgeschlagen", "fehlgeschlagen", "konto_eingerichtet"]

    # die Verwaltung kann den Zugang erneut vergeben
    admin.patch(f"/api/admin/people/{user_id}", json={"access_type": "once"})
    assert open_door(guest)["ok"] is True


def test_zeitlich_begrenzter_zugang(site, cloud):
    admin = site.admin()
    _, guest = site.guest(admin, access_type="period", valid_from=START + DAY, valid_until=START + 2 * DAY)

    early = open_door(guest)
    assert early["ok"] is False and "beginnt am" in early["message"]

    site.clock.advance(DAY)
    assert open_door(guest)["ok"] is True
    assert open_door(guest)["ok"] is True  # beliebig oft innerhalb des Zeitraums

    site.clock.advance(DAY)
    late = open_door(guest)
    assert late["ok"] is False and "abgelaufen" in late["message"]
    assert len(cloud.opened()) == 2


def test_begrenzter_zugang_braucht_ein_gueltiges_ende(site):
    admin = site.admin()
    assert admin.post("/api/admin/people", json={"name": "X", "access_type": "period"}).status_code == 422
    body = {"name": "X", "access_type": "period", "valid_from": START + 10, "valid_until": START + 5}
    assert admin.post("/api/admin/people", json=body).status_code == 422


# --- Aktivieren, deaktivieren, sperren, löschen ---


def test_deaktivieren_wirkt_beim_naechsten_versuch(site, cloud):
    admin = site.admin()
    user_id, guest = site.guest(admin)
    assert open_door(guest)["ok"] is True

    admin.patch(f"/api/admin/people/{user_id}", json={"status": "inactive"})
    denied = open_door(guest)
    assert denied["ok"] is False and "nicht aktiv" in denied["message"]
    assert guest.get("/api/me").status_code == 200  # bleibt angemeldet, sieht nur keinen Zugang

    admin.patch(f"/api/admin/people/{user_id}", json={"status": "active"})
    assert open_door(guest)["ok"] is True
    assert len(cloud.opened()) == 2


def test_sperren_meldet_sofort_ab_und_verhindert_die_anmeldung(site, cloud):
    admin = site.admin()
    user_id, guest = site.guest(admin, username="marta")
    admin.patch(f"/api/admin/people/{user_id}", json={"status": "blocked"})

    assert guest.post("/api/open").status_code == 401
    assert site.browser().post("/api/login", json={"username": "marta", "password": "geheim"}).status_code == 403
    token = admin.post(f"/api/admin/people/{user_id}/invite").json()["url"].rsplit("/", 1)[1]
    assert site.browser().get(f"/api/invite/{token}").status_code == 404
    assert cloud.opened() == []

    admin.patch(f"/api/admin/people/{user_id}", json={"status": "active"})
    assert site.browser().post("/api/login", json={"username": "marta", "password": "geheim"}).status_code == 200


def test_loeschen_entfernt_konto_und_sitzung_aber_nicht_das_protokoll(site):
    admin = site.admin()
    user_id, guest = site.guest(admin, name="Marta", username="marta")
    open_door(guest)
    assert admin.delete(f"/api/admin/people/{user_id}").json() == {"ok": True}

    assert guest.get("/api/me").status_code == 401
    assert site.browser().post("/api/login", json={"username": "marta", "password": "geheim"}).status_code == 401
    assert [p["name"] for p in admin.get("/api/admin/people").json()] == ["Administrator"]
    assert ("Marta", "geoeffnet") in [(e["user_name"], e["event"]) for e in admin.get("/api/admin/log").json()]
    assert admin.delete(f"/api/admin/people/{user_id}").status_code == 404


def test_admin_kann_sich_nicht_selbst_aussperren(site):
    admin = site.admin()
    own_id = admin.get("/api/admin/people").json()[0]["id"]
    assert admin.delete(f"/api/admin/people/{own_id}").status_code == 409
    assert admin.patch(f"/api/admin/people/{own_id}", json={"status": "blocked"}).status_code == 409
    assert admin.patch(f"/api/admin/people/{own_id}", json={"is_admin": False}).status_code == 409
    assert admin.get("/api/admin/people").status_code == 200


def test_weitere_administratoren(site, cloud):
    admin = site.admin()
    _, second = site.guest(admin, name="Zweiter Admin", username="zwei", is_admin=True)
    assert second.get("/api/me").json()["is_admin"] is True
    assert second.get("/api/admin/people").status_code == 200
    assert second.get("/verwaltung").status_code == 200
    assert open_door(second)["ok"] is True


def test_bearbeiten_aendert_name_funktion_und_zugang(site):
    admin = site.admin()
    user_id, guest = site.guest(admin, name="Marta", access_type="once")
    body = {"name": "Marta P.", "function": "Reinigung", "access_type": "period", "valid_until": START + DAY}
    person = admin.patch(f"/api/admin/people/{user_id}", json=body).json()
    assert (person["name"], person["function"], person["access_type"], person["valid_until"]) == (
        "Marta P.", "Reinigung", "period", START + DAY)
    me = guest.get("/api/me").json()
    assert me["name"] == "Marta P." and me["access"].startswith("Zugang bis ")


# --- Anbindung an die Anlage ---


def test_verbindungsstatus_nennt_die_haustuer(site):
    status = site.admin().get("/api/admin/status").json()
    assert status == {
        "ok": True,
        "invite_base": "http://testserver",
        "invite_only_at_home": True,
        "account": "eos@example.com",
        "home": "Zuhause",
        "door": {"name": "Cerradura", "type": "BNDL", "reachable": True},
    }


def test_mehrere_tueroeffner_brauchen_eine_festlegung(make_site, cloud):
    cloud.extra_lock = True
    site = make_site()
    admin = site.admin()
    status = admin.get("/api/admin/status").json()
    assert status["ok"] is False and "EOS_DOOR_MODULE_ID" in status["message"]
    result = open_door(admin)
    assert result["ok"] is False and "nicht erreichbar" in result["message"]
    assert cloud.opened() == []


def test_haustuer_laesst_sich_festlegen_auch_auf_ein_relais(make_site, cloud):
    cloud.extra_lock = True
    site = make_site(EOS_DOOR_MODULE_ID=LIGHT)
    assert open_door(site.admin())["ok"] is True
    assert cloud.opened() == [{"id": LIGHT, "on": True, "bridge": BRIDGE}]


def test_verworfenes_token_fuehrt_zu_neuer_anmeldung_und_zweitem_versuch(site, cloud):
    admin = site.admin()
    assert open_door(admin)["ok"] is True
    cloud.setstate_replies = [(403, {"error": {"code": 2, "message": "Invalid access token"}})]
    assert open_door(admin)["ok"] is True
    assert cloud.logins == 2
    assert len(cloud.opened()) == 3


def test_zwei_befehle_direkt_hintereinander(site, cloud, monkeypatch):
    monkeypatch.setattr(gateway_module, "COOLDOWN_SECONDS", 60)
    admin = site.admin()
    _, guest = site.guest(admin, access_type="once")
    assert open_door(admin)["ok"] is True
    busy = open_door(guest)
    assert busy["ok"] is False and "gerade eben" in busy["message"]
    assert guest.get("/api/me").json()["can_open"] is True  # Einmalzugang nicht verbraucht
    assert len(cloud.opened()) == 1


def test_einladungslink_nutzt_die_oeffentliche_adresse(make_site):
    site = make_site(EOS_PUBLIC_URL="https://tuer.example.org/")
    data = site.admin().post("/api/admin/people", json={"name": "X", "access_type": "permanent"}).json()
    assert data["invite"]["url"].startswith("https://tuer.example.org/einladung/")
    assert data["invite"]["expires_at"] == START + 7 * DAY


def test_adminpasswort_laesst_sich_ueber_die_konfiguration_neu_setzen(make_site):
    first = make_site()
    people_before = first.admin().get("/api/admin/people").json()
    second = make_site(EOS_ADMIN_PASSWORD="neuespasswort")
    assert second.browser().post("/api/login", json={"username": "admin", "password": ADMIN_PASSWORD}).status_code == 401
    client = second.browser()
    assert client.post("/api/login", json={"username": "admin", "password": "neuespasswort"}).status_code == 200
    assert [p["id"] for p in client.get("/api/admin/people").json()] == [p["id"] for p in people_before]


# --- Zugang von außen ---


def test_hinter_funnel_beginnen_einladungslinks_mit_der_oeffentlichen_adresse(site):
    admin = site.admin()
    funnel = {"X-Forwarded-Host": "haustuer.tail1234.ts.net", "X-Forwarded-Proto": "https"}
    body = {"name": "X", "access_type": "permanent"}
    data = admin.request("POST", "/api/admin/people", json=body, extra_headers=funnel).json()
    assert data["invite"]["url"].startswith("https://haustuer.tail1234.ts.net/einladung/")

    status = admin.request("GET", "/api/admin/status", extra_headers=funnel).json()
    assert (status["invite_base"], status["invite_only_at_home"]) == ("https://haustuer.tail1234.ts.net", False)

    # Anmeldung über HTTPS: das Sitzungs-Cookie wird nur noch verschlüsselt übertragen
    login = {"username": "admin", "password": ADMIN_PASSWORD}
    over_https = site.browser().request("POST", "/api/login", json=login, extra_headers=funnel)
    assert "secure" in over_https.headers["set-cookie"].lower()
    assert "secure" not in site.browser().post("/api/login", json=login).headers["set-cookie"].lower()


@pytest.mark.parametrize(
    "host, at_home",
    [("192.168.86.250:8321", True), ("nas:8321", True), ("nas.local", True), ("10.0.0.5", True), ("tuer.example.org", False)],
)
def test_verwaltung_warnt_bei_adresse_die_nur_zuhause_geht(site, host, at_home):
    status = site.admin().request("GET", "/api/admin/status", extra_headers={"Host": host}).json()
    assert status["invite_base"] == f"http://{host}"
    assert status["invite_only_at_home"] is at_home


def test_passwoerter_lassen_sich_nicht_beliebig_oft_durchprobieren(site):
    admin = site.admin()
    site.guest(admin, username="marta")
    for _ in range(10):
        assert site.browser().post("/api/login", json={"username": "Marta", "password": "falsch"}).status_code == 401
    correct = {"username": "marta", "password": "geheim"}
    assert site.browser().post("/api/login", json=correct).status_code == 429
    assert site.browser().post("/api/login", json={"username": "admin", "password": ADMIN_PASSWORD}).status_code == 200
    assert admin.get("/api/admin/people").status_code == 200  # bestehende Anmeldungen bleiben

    site.clock.advance(15 * 60 + 1)
    assert site.browser().post("/api/login", json=correct).status_code == 200


def test_erfolgreiche_anmeldung_setzt_die_fehlversuche_zurueck(site):
    for _ in range(3):
        for _ in range(9):
            site.browser().post("/api/login", json={"username": "admin", "password": "falsch"})
        assert site.browser().post("/api/login", json={"username": "admin", "password": ADMIN_PASSWORD}).status_code == 200
