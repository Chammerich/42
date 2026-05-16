# Entscheidungen

Chronologisches Logbuch. Was wann beschlossen wurde, mit welcher
Begründung. Nicht jede Diskussion ist hier festgehalten — nur das
Ergebnis.

Neue Einträge oben.

---

## 2026-05-16 — Gründungssitzung

Lange Konzeptdiskussion, in der die Webseite 42 als eigenständiges
Projekt neben der App El Migrante Consciente etabliert wurde.

### Identität

- **Arbeitsname**: `42`. Ironische Vorwegnahme der eigenen Pointe
  (*"Spoileralarm: nicht 42"*). Bleibt bis der echte Titel kommt.
- **Werktitel**: offen. Wird beim Schreiben gefunden, nicht durch Suche.
- **Hauptdomain (Ziel)**: `chammerich.de`. Seit Heute auf Cloudflare.
- **Arbeitsdomain (jetzt)**: `42.chammerich.de`. Bis das Werk steht.
- **App-Domain**: `elmigranteconciente.com` bleibt der App vorbehalten.

### Verhältnis App ↔ Webseite

- Geschwister, kein Verbund. Technisch unabhängig, keine geteilten Daten.
- App = tägliches Werkzeug für den klassischen Migranten.
- Webseite = kuratiertes Werk, Migration als ein Kapitel unter mehreren.
- Auf der Startseite der Webseite ist die App **prominent** eingeladen.

### Konzept "Migration im weiteren Sinne"

- Migration im klassischen Sinne (Lateinamerika → Spanien) bleibt
  **die Achse**, nicht die Metapher.
- Andere Veränderungsprozesse (berufliche, identitäre, philosophische
  Brüche) sind konzentrische Kreise um diese Achse.
- Filter für die Zielgruppe: das Werk soll Menschen abschrecken,
  die glauben alles zu wissen und genial zu sein.

### Inhaltsstruktur

- **Guía**: 15 Kapitel = 1 Einleitung + 14 Themen
- **Manifiesto**: 14 Einträge, einer pro Themenkapitel, je 3 Statements
  mit Optionen `bestätigen / ablehnen / offen` + 3 freie Selbstverpflichtungen
- **Contrato**: aus den Antworten generierter symbolischer Akt,
  beglaubigt vom *Notario del Consciente*, druckbar
- **Eintritt in den Contrato**: freiwillig. Aber wenn, dann verbindlich
  alle 14 Punkte beantworten.
- **Manifiesto wurde temporär auf 10 reduziert** (technische Notbremse).
  Die Vision sind 14. Diese Inkonsistenz wird beim Frontend-Bau behoben.

### Didaktisches Drei-Stufen-System

- Christian schreibt die **Vollversion zuerst**. Die didaktische Struktur
  wird daraus **rückwärts** gewonnen.
- Stufe 1 (Apetuter): Tür öffnen — eine Frage, ein Bild, ein Widerspruch.
  In Christians Stimme, mit konkretem Detail.
- Stufe 2 (Zusammenfassung): eigenständig, bewusst nicht komplex.
  Eine Auswahl, kein Abriss.
- Stufe 3 (Originaltext): unangetastet, in voller Form, mit allen
  Mäandern.
- Jede Stufe muss **für sich vollständig** sein. Keine Hierarchie,
  ein Tiefen-System.

### Schema

- Markdown-Dateien mit YAML-Frontmatter. Eine Datei pro (Kapitel, Sprache).
- Dateiname: `<kapitel-id>.<sprache>.md`
- **Pflichtfelder**: `id`, `sprache`, `titel` — plus mindestens ein
  Inhaltsbaustein.
- Alles andere optional. Komplexität pro Kapitel variabel.
- **Bausteine** sind benannte Abschnitte im Body, eingeleitet durch
  HTML-Kommentar. Neue Bausteine können jederzeit erfunden werden,
  ohne dass alte Kapitel brechen.
- Wenn ein Kapitel etwas Eigenes braucht (interaktives Tool etc.):
  außerhalb des Schemas bauen, im Kapitel verlinken. Reibung ist gewollt.

### Sprachen

- ES als Primärsprache (Mehrheit der Originaltexte).
- DE und EN als gleichberechtigte Sprachen, keine zweitrangigen Übersetzungen.
- Ein Text kann in DE original sein und in ES adaptiert.
- Sprachen sind unabhängig: ein Kapitel kann in ES vollständig sein
  und in DE nur als Apetuter existieren.
- URL-Struktur: `/<sprache>/<kapitel-id>`.

### Adaptionen

- Originale bleiben unverändert. Adaptionen sind *Kinder* mit eigener
  ID, die mit `eltern:` auf das Original verweisen.
- Die Adaption-Beziehung ist auf der Webseite sichtbar — der Leser
  weiß, dass er eine Adaption liest und woher sie kommt.

### Überkapitel

- Lose Tags, keine eigenen Datentypen.
- Definiert unter `/content/uberkapitel/<slug>.md`.
- Ein Kapitel kann zu mehreren Überkapiteln gehören.

### Technik-Stack

- **Frontend**: Astro (statischer Site-Generator)
- **Inhalte**: Markdown + YAML-Frontmatter
- **Versionierung**: Git auf GitHub, Repo `Chammerich/42`, public
- **Hosting**: Cloudflare Workers (Static Assets über `wrangler.jsonc`)
- **CMS**: später (Sveltia CMS bevorzugt). Erstmal Markdown direkt.

### Verworfen

- Headless CMS mit eigener Datenbank (Vendor-Lock, Migrationsrisiko)
- Netlify als Hosting (Build-Minuten-Falle)
- claude-mem / Mem0 als Memory-Lösung (für Claude Code, nicht Claude.ai;
  zu teuer; löst nicht das richtige Problem)

### Arbeitsmodus

- Claude.ai Pro als Plattform.
- Memory-Disziplin über docs/-Dateien im Repo, nicht über Plugins.
- Jeder Chat beginnt mit *"Lies docs/HANDOVER.md"*.
- Jeder Chat endet mit Update von AKTUELL.md und ENTSCHEIDUNGEN.md.
- Ein Chat = ein konkretes Ziel. Brainstorming bewusst getrennt.
