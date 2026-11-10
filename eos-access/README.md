# EOS Access

Eigene Web-App, mit der ausgewählte Personen **ausschließlich die Haustür** öffnen
können – ohne Zugriff auf Kamera, Audio, Nachrichten oder Anrufverlauf der
BTicino Classe 300EOS.

**Stand:** Phase 0 – Technik prüfen, bevor die Benutzerverwaltung gebaut wird.

> Dieser Ordner liegt vorerst im Repository `42`, hat mit der Werk-Webseite aber
> nichts zu tun und wird von deren Build nicht berührt. Ein eigenes Repository
> wäre der sauberere Ort, sobald das Projekt weitergeht.

## Ergebnis der Machbarkeitsprüfung

Geprüft am 10.11.2026 im Quellcode von
[`bticino_intercom`](https://github.com/k-the-hidden-hero/bticino_intercom) v2.0.4
und der darunterliegenden Bibliothek `pybticino` 1.10.0.

**Das Projekt ist umsetzbar.** Die Classe 300EOS wird ausdrücklich unterstützt.

So funktioniert die Türöffnung technisch: ein einzelner HTTPS-Aufruf an die
Netatmo-Cloud (`/syncapi/v1/setstate`) mit `{"lock": false}` für das
Türöffner-Modul (Typ `BNDL`). Der Aufruf hat keinen Bezug zu einem Ruf – er
funktioniert laut Maintainer auch ohne aktiven Ruf (Issue #57), genau wie in der
offiziellen App.

### Was der Test an der eigenen Anlage klären muss

| Risiko | Bedeutung |
|---|---|
| **Keine physische Rückmeldung** | Die Cloud antwortet mit „ok“, sobald sie den Befehl angenommen hat – auch wenn sich nichts bewegt (Issue #57). „Einmalzugang verbrauchen“ kann sich deshalb nur auf *angenommen* stützen, nicht auf *Tür offen*. |
| **Welches Modul hängt an der Haustür?** | Je nach Verdrahtung ist es ein Türöffner (`BNDL`) oder ein Relais (`BNSL`); bei einer 300EOS gab es genau diesen Fall (Issue #4). |
| **Inoffizielle Schnittstelle** | `pybticino` meldet sich wie die Android-App „Home + Security“ an. Netatmo kann das jederzeit ändern oder unterbinden; es gibt keine Zusage. |
| **Cloud-Abhängigkeit** | Ohne Internet an Anlage oder NAS und ohne erreichbare Netatmo-Cloud geht keine Tür auf. Eine lokale Schnittstelle gibt es nicht. |

### Zwei Änderungen am ursprünglichen Plan

1. **Home Assistant ist nicht nötig.** Die Integration ist nur eine Hülle um
   `pybticino`. Das FastAPI-Backend kann die Bibliothek direkt benutzen. Das spart
   einen zweiten Container, HACS, die Abhängigkeit von Home Assistant ≥ 2026.5 und
   eine zweite Anmeldeoberfläche im Netz.
2. **„Keine Freigabe ins Internet“ heißt: nur im Heim-WLAN.** Wer vor der Tür steht
   und nicht im WLAN ist, erreicht die App nicht. Für die erste Stufe ist das so
   gewollt; für echte Gäste braucht es später einen gesicherten Zugang von außen
   (z. B. Tunnel mit HTTPS). Das wird nach Phase 0 entschieden.

### Netatmo-Konto

EOS Access bekommt ein **eigenes Netatmo-Konto**, das in der Home + Security-App
als Mitglied eingeladen wird. Gründe: Dasselbe Konto gleichzeitig in App und
Dienst führt zu Verbindungsabbrüchen, und das persönliche Passwort bleibt vom NAS
fern. Technisch darf dieses Konto in der Cloud alles, was ein Mitglied darf – die
Beschränkung auf „nur öffnen“ entsteht dadurch, dass EOS Access nichts anderes
anbietet und die Zugangsdaten das NAS nie verlassen.

## Phasen

| Phase | Inhalt | Stand |
|---|---|---|
| 0 | Testkonsole: Verbindung, Test-Öffnung, Protokoll | fertig zum Ausprobieren |
| 1 | Benutzer, Rollen, Berechtigungen (einmalig / befristet / dauerhaft), Einladungslinks, Seite mit „Öffnen“, Öffnungsprotokoll | offen |
| 2 | Verwaltungsoberfläche, Sperren, Schutz gegen Durchprobieren, Datensicherung | offen |
| 3 | Zugang von außerhalb des Heimnetzes | offen, Entscheidung nach Phase 0 |

## Phase 0: Testkonsole auf der Synology

Die Testkonsole ist eine kleine, passwortgeschützte Webseite im Heimnetz. Sie
zeigt, ob die Verbindung steht und welche Module die Anlage meldet, sendet auf
Knopfdruck einen Öffnungsbefehl und führt ein Protokoll, in das du einträgst, ob
die Tür wirklich aufging.

### Vorbereitung

1. Unter [my.netatmo.com](https://my.netatmo.com) ein neues Konto für EOS Access anlegen.
2. In der Home + Security-App (mit dem eigenen Konto) dieses Konto ins Zuhause
   einladen und die Einladung mit dem neuen Konto annehmen.

### Einrichtung

1. Den Ordner `eos-access/phase0` auf das NAS kopieren, z. B. nach
   `/docker/eos-access-phase0`.
2. Dort `.env.example` nach `.env` kopieren und ausfüllen (Netatmo-Zugangsdaten
   des neuen Kontos, ein Passwort für die Testkonsole mit mindestens 12 Zeichen,
   Zeitzone).
3. Container Manager → **Projekt** → **Erstellen** → den Ordner auswählen; die
   vorhandene `compose.yaml` verwenden und das Projekt bauen und starten.
4. Im Browser `http://192.168.86.250:8321` öffnen. Benutzername beliebig,
   Passwort wie in `.env`.

### Testablauf

Zu zweit testen: eine Person an der Tür, eine an der Konsole.

1. **Verbindung:** Abschnitt 1 muss das Zuhause und die Module zeigen.
2. **Richtiges Modul finden:** Jedes Modul mit Schaltfläche einmal auslösen und
   notieren, welches die Haustür öffnet.
3. **Drei Situationen**, jeweils mehrfach: ohne Ruf · während es klingelt ·
   während eines laufenden Gesprächs. Nach jedem Versuch „Ja“ oder „Nein“
   eintragen.
4. **Über mehrere Tage wiederholen**, auch morgens nach einer Nacht ohne Nutzung –
   so zeigt sich, ob die Anmeldung von selbst frisch bleibt.

**Bestanden**, wenn über mindestens 20 Versuche an mehreren Tagen jeder
angenommene Befehl die Tür geöffnet hat und die Antwortzeit durchgehend unter etwa
drei Sekunden lag. Dann folgt Phase 1.

### Hinweise

- Die Konsole ist nur für die Testphase gedacht. Sie spricht unverschlüsseltes
  HTTP und gehört nicht ins Internet. Nach den Tests das Projekt im Container
  Manager stoppen.
- `.env` bleibt auf dem NAS und wird nicht ins Git übernommen.
- Protokoll und Anmelde-Token liegen im Docker-Volume `eos_data`.

### Entwicklung

```sh
cd eos-access/phase0
python3.13 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

Die Tests lassen `pybticino` unverändert gegen eine nachgebaute Netatmo-Cloud
laufen und prüfen unter anderem, dass nur Türöffner und Relais angesteuert werden
und dass Fehlerantworten nie als Erfolg zählen.
