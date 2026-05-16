# Architektur

Was wir gewählt haben und warum. Damit später nachvollziehbar ist,
welche Entscheidungen aus welchem Grund getroffen wurden.

## Stack

**Frontend: Astro**
Statischer Site-Generator. Schlank, inhaltsgetrieben, gute
Mehrsprachigkeit. Erzeugt reines HTML — keine schwere JavaScript-Last
für den Leser. Passt zu einem Werk, das gelesen werden will.

**Inhalte: Markdown mit YAML-Frontmatter**
Lesbar, portierbar, versionierbar. Wenn das Projekt in zehn Jahren
ein anderes System bekommt, sind die Texte trotzdem noch da und
maschinenlesbar. Keine Datenbank, kein Vendor-Lock.

**Versionierung: Git auf GitHub**
Repository unter `github.com/chammerich/42`, public. Jede Änderung
ist nachvollziehbar. Texte gehören dir, nicht einem Anbieter.

**Hosting: Cloudflare Pages**
Unbegrenzte Builds und Bandbreite im kostenlosen Plan.
Statische Auslieferung weltweit, keine Build-Minute-Falle wie
bei Netlify.

**CMS: später**
Erst wenn das Schema sich bewährt hat, kommt Sveltia CMS dazu.
Bis dahin werden Inhalte direkt als Markdown bearbeitet — entweder
im GitHub-Web-Editor oder lokal.

## Sprachen

`es` ist Primärsprache (Mehrheit der Originaltexte).
`de` und `en` sind gleichberechtigte Sprachen, keine zweitrangigen
"Übersetzungen". Ein Text kann in DE original sein und in ES adaptiert.

URL-Struktur: `chammerich.de/<sprache>/<kapitel-id>`
Beispiel: `chammerich.de/es/lucifer`, `chammerich.de/de/schluesselkind`

Die Startseite leitet auf die Browser-Sprache, lässt sich aber
umstellen.

## Verbindung zur App

App: `elmigranteconciente.com` (klassische Migration, tägliches Werkzeug)
Werk: `chammerich.de` (die ganze Sammlung)

Auf der Startseite des Werks wird die App prominent eingeladen.
In den Migrations-Kapiteln wird sie zusätzlich angeboten, wo sinnvoll.

Beide Projekte bleiben technisch unabhängig — keine geteilten Daten,
keine gemeinsame Benutzerverwaltung. Sie sind Geschwister, kein
Verbund.

## Werkzeuge (Tools)

Werkzeuge wie Finanzplaner oder Notfall-Modus existieren in der App.
Auf der Webseite können neue Werkzeuge entstehen — aber nur, wenn
ein Kapitel sie wirklich braucht. Reibung ist gewollt: sie verhindert,
dass Werkzeuge aus Bequemlichkeit entstehen statt aus Notwendigkeit.

## Was nicht eingebaut wird, bis ein Grund vorliegt

- Suche (kommt, wenn der Inhalt umfangreich genug ist)
- Kommentare (passen nicht zur Anti-Ratgeber-Haltung)
- Analytics jeglicher Art (Datenschutz, Haltung)
- Newsletter-Anmeldung (kein "Engagement-Funnel")
- Login (das Werk ist offen lesbar)
