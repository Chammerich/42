# Entscheidungen

Chronologisches Logbuch. Was wann beschlossen wurde, mit welcher
Begründung. Nicht jede Diskussion ist hier festgehalten — nur das
Ergebnis.

Neue Einträge oben.

---

## 2026-05-17 — Die Form gefunden

Sparring-Sitzung, in der die Architektur der Webseite als logische
Konsequenz der inhaltlichen These entwickelt wurde. Detaillierte
Ausarbeitung in docs/MATRIX.md.

### Leitsatz

**Die Form ist die These.** *Sternenstaub mit Boden* — lineare Zeit
und Sprung ins Zusammenhängende — wird nicht behauptet, sondern
durch das Layout vollzogen. Die Seite belehrt nicht, sie führt vor.

### Drei-Spalten-Architektur (Desktop)

- **Linke Spalte (50%)** — Klammertext. Christians Stimme, lineare
  Erzählung. Typografisch ruhig: keine Inline-Links, keine goldenen
  Akzente im Fließtext.
- **Mittlere Spalte (25%)** — Brücken. Kuratoren-Stimme zweiter Ordnung.
  Knapp, kursiv, mit goldener Marke. *Stufe 2 mit Deckel* (nie länger
  als eine Zusammenfassung sein dürfte).
- **Rechte Spalte (25%)** — Spur durch den Klammertext. Wandert beim
  Scrollen mit. Keine Inhaltsliste, sondern was *dieser Text* berührt.

### Drei Sprungrichtungen aus der mittleren Spalte

- **Tiefer** — Notiz (Lesefenster, max ~300 Wörter) oder volles Kapitel.
- **Weiterweben** — anderes Kapitel.
- **In die Praxis** — Werkzeug (App, Tools, etc.).

### Hierarchie der Lesetiefen

1. Klammertext
2. Brücke (Stufe 2 mit Deckel)
3. Notiz (Mikro-Inhalt, kontextgebunden, ohne eigene Adresse)
4. Kapitel (volle Drei-Stufen-Logik)
5. Werkzeug (außerhalb des Schemas)

### Mobile-Lösung

Drei Spalten kollabieren zu einer. Klammertext bleibt in voller Form.
Brücken und Spur werden zu kleinen goldenen Marken am rechten Rand
des Fließtexts — antippbar, öffnen ein Bottom-Sheet. Keine
Notbehelfslösung: Vertikalität ersetzt Horizontalität, das Prinzip
bleibt identisch.

### Werktitel — Kandidat in Prüfung

**42 — das Leben, das Universum und alles**

Mit zwei Schreibweisen:
- **Cover/Editorial:** `42 — das Leben, das Universum und alles`
  (Gedankenstrich, Komma, normale Typografie)
- **URL/Slug:** `42-das-leben-das-universum-und-alles`

Begründung: Die Adams-Anspielung nimmt dem Werk die feierliche Pose
schon im Titel. Die Selbstironie macht große Wahrheiten erst tragbar.
Die Ikarus-These im Werk trägt die Pointe — *wer nach der absoluten
Antwort sucht, verbrennt* — sie muss nicht wiederholt werden. Der
Titel ist der Versuch, das Werk ist die Konsequenz.

Filterfunktion gewollt: wer den Witz nicht aushält, geht. Wer ihn
aushält, ist die Zielgruppe.

Endentscheidung steht aus.

### Achtsamkeit: intentional statt makellos

Präzisierung zu STIL.md: Imperfektion ist Signal — aber ein Signal
funktioniert nur, wenn es sich vom Rauschen abhebt. Jede Ellipse soll
eine gewollte sein, jeder Gedankenstrich gewählt. Achtsamkeit beim
Schreiben *und* beim Nicht-Glätten. Höherer Maßstab als literarische
Sorgfalt, nicht weniger Imperfektion, sondern bewusstere.

### Konsequenz

Wenn die Form die These trägt, ist jede schludrige Brücke ein
argumentatives Eigentor. Brücken werden die anspruchsvollsten Texte
des Werks. Klammertext wird die zentrale Schreibaufgabe vor allem
anderen.

### Sparringspartner-Rolle

Neben der Werk-Arbeit gibt es eine zweite Rolle: Sparringspartner.
Ehrlich, knapp, kein Coaching, keine Schmeichelei. Christian beendet
das Gespräch, nicht Claude. Im Memory festgehalten.

### Schema-Folgen

SCHEMA.md bleibt unverändert — die Architektur sitzt darüber. Eine
offene Frage: ob Notizen ein eigener Inhaltstyp werden (`/content/notizen/`)
oder als sehr kurze Kapitel ohne Burger-Menü-Eintrag laufen.

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
