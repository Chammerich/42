# EOS Access

Eigene Web-App, mit der ausgewählte Personen **ausschließlich die Haustür** öffnen
können – ohne Zugriff auf Kamera, Audio, Nachrichten oder Anrufverlauf der
BTicino Classe 300EOS.

**Stand:** Phase 1 – Personen, Zugänge, Einladungslinks und die Seite „Öffnen“
sind gebaut und laufen im Heimnetz. Der Zugang von außen steht noch aus.

> Dieser Ordner liegt vorerst im Repository `42`, hat mit der Werk-Webseite aber
> nichts zu tun und wird von deren Build nicht berührt. Ein eigenes Repository
> wäre der sauberere Ort.

## Was die App kann

**Eingeladene Personen**

- richten über ihren persönlichen Link Benutzername und Passwort ein,
- melden sich einmal an und bleiben angemeldet,
- sehen danach nur eine große Schaltfläche **„Öffnen“**.

**Administratoren** (Seite `/verwaltung`)

- legen Personen mit Name und Funktion an,
- vergeben den Zugang: **einmalig**, **zeitlich begrenzt** oder **dauerhaft**,
- deaktivieren (Person bleibt angemeldet, kann aber nicht öffnen), sperren
  (Person wird sofort abgemeldet) und löschen,
- erstellen Einladungslinks und verschicken sie per Kopieren, WhatsApp oder E-Mail;
  ein neuer Link für ein bestehendes Konto dient als „Passwort vergessen“,
- sehen das Protokoll aller Öffnungen und abgelehnten Versuche,
- prüfen die Verbindung zur Anlage.

**Regeln**

- Einladungslinks gelten einmal und sieben Tage.
- Die Berechtigung wird bei jedem Öffnungsversuch neu geprüft.
- Ein Einmalzugang gilt erst als verbraucht, wenn die Cloud den Befehl angenommen hat.
- Passwörter liegen nur als Hash (scrypt) in der Datenbank, Einladungs- und
  Sitzungs-Tokens ebenfalls nur als Hash.
- Das Netatmo-Konto kennt nur der Server; die Verwaltung hat eine eigene Anmeldung.

## Aufbau

```
Browser ──► EOS Access (FastAPI, ein Container auf der Synology) ──► Netatmo-Cloud ──► Classe 300EOS
                 │
                 └── SQLite-Datei: Personen, Einladungen, Sitzungen, Protokoll
```

| Datei | Aufgabe |
|---|---|
| `eos/gateway.py` | Einzige Stelle, die mit der Netatmo-Cloud spricht. Kann nur: Verbindung prüfen, Haustür öffnen. |
| `eos/access.py` | Berechtigungslogik und Passwort-Hashing, ohne Datenbank und Netz. |
| `eos/store.py` | Datenbank. |
| `eos/main.py` | Web-Schnittstelle und Seiten. |
| `eos/pages/`, `eos/static/` | Oberfläche (Deutsch, für Handy und Desktop). |

Home Assistant wird nicht gebraucht: Die Community-Integration
[`bticino_intercom`](https://github.com/k-the-hidden-hero/bticino_intercom) ist
eine Hülle um die Bibliothek `pybticino`, die EOS Access direkt benutzt.

## Leitlinie: einfach vor streng

Entscheidung vom 10.11.2026: EOS Access öffnet nur die Hauseingangstür; die
Wohnungstür hat ein eigenes Sicherheitssystem. Bequemlichkeit geht deshalb vor
Härtung.

- Keine Zwei-Faktor-Anmeldung, keine Passwortregeln, Anmeldung gilt ein Jahr.
- Ein Zugang von außerhalb des Heim-WLANs ist kein Tabu.
- Was unabhängig von der Tür gilt: Das Netatmo-Konto sieht auch Kamera und
  Anrufverlauf, seine Zugangsdaten bleiben deshalb auf dem NAS. Und bei einem
  Zugang von außen wird nur EOS Access erreichbar gemacht, nicht das NAS selbst.

## Erkenntnisse zur Anlage

Geprüft am 10.11.2026 im Quellcode von `bticino_intercom` v2.0.4 / `pybticino`
1.10.0 und mit einer Testkonsole an der eigenen Anlage.

- Die Tür wird mit einem einzelnen HTTPS-Aufruf an die Netatmo-Cloud geöffnet
  (`/syncapi/v1/setstate`, `{"lock": false}`).
- Die Cloud meldet vier Module: das Gerät selbst (`BNCX`), die Außenstation
  (`BNEU`), den Türöffner „Cerradura“ (`BNDL`) und das Treppenlicht „Luz de
  escaleras“ (`BNSL`). **Die Haustür hängt am Türöffner „Cerradura“.** EOS Access
  findet ihn von selbst, solange es nur einen Türöffner gibt.
- Öffnen ohne aktiven Ruf funktioniert. Antwortzeit der Cloud rund 100 ms.
- **Keine physische Rückmeldung:** Die Cloud bestätigt nur, dass sie den Befehl
  angenommen hat. Das wertet EOS Access als Erfolg.
- Noch nicht geprüft: Öffnen während es klingelt und während eines Gesprächs.

**Bleibende Risiken**

| Risiko | Bedeutung |
|---|---|
| Inoffizielle Schnittstelle | `pybticino` meldet sich wie die Android-App „Home + Security“ an. Netatmo kann das jederzeit ändern oder unterbinden. |
| Cloud-Abhängigkeit | Ohne Internet an Anlage oder NAS und ohne erreichbare Netatmo-Cloud geht keine Tür auf. |
| Nur im Heimnetz | Solange es keinen Zugang von außen gibt, erreichen Gäste die App nur im WLAN. |

## Phasen

| Phase | Inhalt | Stand |
|---|---|---|
| 0 | Testkonsole: Verbindung, Test-Öffnung | abgeschlossen, Konsole entfernt |
| 1 | Personen, Zugangsarten, Einladungslinks, „Öffnen“, Protokoll | gebaut |
| 2 | Zugang von außerhalb des Heimnetzes (HTTPS) | offen |
| 3 | Datensicherung, Schutz gegen Durchprobieren von Passwörtern | offen |

## Einrichtung auf der Synology

1. Den Ordner `eos-access` (mit `Dockerfile`, `docker-compose.yml`,
   `requirements.txt` und dem Unterordner `eos`) auf das NAS kopieren, z. B. nach
   `/docker/eos-access`.
2. Dort `zugangsdaten.env.example` nach `zugangsdaten.env` kopieren und ausfüllen:
   Netatmo-Zugangsdaten des eigenen Kontos für EOS Access und ein Passwort für die
   Verwaltung. Die `zugangsdaten.env` der Testkonsole funktioniert unverändert
   weiter; ihr `EOS_CONSOLE_PASSWORD` gilt dann als Passwort der Verwaltung.
3. Container Manager → **Projekt** → **Erstellen** → den Ordner als Pfad wählen,
   die vorhandene `docker-compose.yml` verwenden, bauen und starten.
4. Im Browser `http://192.168.86.250:8321` öffnen und als `admin` anmelden.

**Hinweise**

- Personen, Protokoll und das Netatmo-Token liegen im Docker-Volume `eos_data`.
  Es übersteht Neustarts und einen Neubau des Projekts.
- Das Passwort der Verwaltung lässt sich jederzeit in `zugangsdaten.env` ändern;
  es gilt nach dem nächsten Neustart des Projekts.
- Meldet die Anlage mehrere Türöffner, nennt die Verwaltung unter „Anlage“ deren
  Kennungen; die richtige kommt als `EOS_DOOR_MODULE_ID` in `zugangsdaten.env`.
- Die App spricht im Heimnetz unverschlüsseltes HTTP. Für den Zugang von außen
  kommt HTTPS davor; `EOS_PUBLIC_URL` legt dann die Adresse in den Einladungslinks fest.

## Entwicklung

```sh
cd eos-access
python3.13 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

Die Tests lassen `pybticino` unverändert gegen eine nachgebaute Netatmo-Cloud
laufen. Sie prüfen unter anderem, dass ohne Anmeldung nichts erreichbar ist, dass
Gäste nicht in die Verwaltung kommen, dass jede Zugangsart zur richtigen Zeit
greift und dass ein Einmalzugang bei einem Fehler der Cloud erhalten bleibt.
