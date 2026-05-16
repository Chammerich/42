# Die App "El Migrante Consciente"

Schwester-Projekt von 42, technisch unabhängig. Wichtig für jede
Claude-Instanz in 42, weil 42 ihre DNA erbt und ihre Funktion
abgrenzt.

## Was sie ist

Eine PWA (installierbare Web-App) für lateinamerikanische Migranten
in Spanien. Smartphone-fokussiert. Wird nicht gelesen, sie wird
genutzt — Tagesimpuls, Reflexion, Selbstverpflichtung, Wissenstexte,
Werkzeuge, alles in einer einzigen HTML-Datei, offline-fähig, ohne
Tracking.

Live unter [elmigranteconciente.com](https://elmigranteconciente.com).
Aktuell Version v1.0.164. Repository
[github.com/Chammerich/elmigranteconciente](https://github.com/Chammerich/elmigranteconciente),
Hosting GitHub Pages.

## Was sie nicht ist

Sie ist kein Coaching-Tool. Kein Selbsthilfe-Buch. Keine Plattform
mit Streaks oder Gamification. Sie verspricht nichts. Sie behauptet
nicht, dass Migration "lösbar" ist.

Sie sagt: hier ist jemand, der ähnliches durchgemacht hat, hier
sind seine Beobachtungen, hier sind Werkzeuge, die helfen können.
Mehr nicht.

## Inhalt — acht Bereiche

- **Prólogo** — Einführung: warum die App existiert
- **Mi Día** — Tagesimpuls (rotierend durch 14 Themen), Weisheit,
  Reflexionsfrage, Voces-Section (anonyme Stimmen)
- **Mi Manifiesto** — 14 Selbstverpflichtungen, je mit Erklärung,
  drei konkreten Aktionen, Reflexionsfragen. Aktuell 10 aktiv
  (technische Notbremse, Vision sind 14). Aus den Antworten
  entsteht ein **Contrato**, beglaubigt vom *Notario del Consciente*,
  druckbar als symbolischer Akt.
- **La Guía** — 15 Kapitel (1 Einleitung + 14 Themen). Jedes Kapitel
  in drei Stufen: Zusammenfassung, Imperativ, voller Originaltext.
- **Tu mejor Versión** — wissenschaftliche Vertiefungen: Resilienz,
  Selbstanalyse, Leadership, Trauma-Neurobiologie. Mit Glossar.
- **Mis Finanzas** — interaktiver Finanzplaner, zugeschnitten auf
  Migrantensituationen (Steuerwohnsitz, Modelo 720, etc.).
- **Migración & Trámites** — Behördenwege Spanien in zehn
  Untersektionen: Einreise, Visa, Regularisierung, Familie, Arraigo,
  Empadronamiento, Asyl, Staatsbürgerschaft, LGBTQ, Ressourcen.
- **Epílogo** — persönlicher Abschluss.

Querliegend, jederzeit erreichbar:

- **Notfall-Modus** — Floating-Button, geführte Atemübung, drei
  Sofortschritte, stadtspezifische Krisenkontakte
- **Diario** — privates Tagebuch, lokal gespeichert
- **Voces de Migrantes** — anonymes Teilen
- **Fortschritts-Coach** — meldet sich automatisch nach Tag 1, 3, 7, 14, 30

## Worauf sie reagiert

Migranten verlieren oft mehr als ein Land. Sie verlieren ihre
Sprache (zumindest die fließende Version), ihren beruflichen Status,
ihre Kontakte, die Identitätsbestätigung durch das Umfeld. Was
übrig bleibt, ist der eigene Kopf — der nicht immer ein verlässlicher
Begleiter ist.

In diese Lücke springen typischerweise zwei Genres: religiöse
Gemeinschaften und Ratgeber-Literatur ("Migration in 5 Schritten",
"Das Geheimnis der Auswanderer"). Die App stellt eine dritte Option
neben diese beiden. Sie ist säkular, aber nicht zynisch. Sie ist
strukturiert, aber nicht formelhaft. Sie ist konkret, aber nicht
versprechend.

## Hinter der App

Christian Hammerich, geboren 1966. Hat mit 53 Jahren — nach einer
Karriere als COO/CMO bei Volkswagen-Gruppe und Autostadt, vorher
u.a. Banking, Programmierung, Opernregie, Psychotherapeut,
Gastronom Berlin — alles aufgegeben und ist mit Handgepäck nach
Barcelona. Drei Worte Spanisch. Kein Plan, kein Netz.

Genau diese Erfahrung formt den Ton der App. Sie ist nicht von
einem Experten, der Migration *studiert* hat. Sie ist von jemandem,
der den Sprung gemacht hat und im Nachhinein versteht, was passiert
ist. Sie spricht **aus** der Erfahrung, nicht **über** sie.

Das ist der zentrale Unterschied zu praktisch jedem anderen Produkt
in diesem Feld.

## Was 42 daraus erbt

- Die Stimme: autobiografisch, ehrlich, anti-Ratgeber, mit sichtbarer
  Imperfektion
- Das didaktische Drei-Stufen-System (kurz → mittel → lang),
  rückwärts aus der Vollversion gearbeitet
- Mehrsprachigkeit als gleichberechtigt (ES/DE/EN, keine Hierarchie)
- Den Ton beim Schreiben: *"El universo no comete errores"* wird
  immer im Konkreten geerdet
- Die Reibung als Schutz: Werkzeuge entstehen nur, wenn sie
  wirklich gebraucht werden

## Was 42 explizit nicht erbt

- Smartphone-First als Designprämisse (42 darf Desktop-Atem haben)
- Tägliche Nutzung als Designziel (42 ist Reflexionsraum, nicht
  Tagesbegleiter)
- Migration als zentralen Inhalt (42 hat Migration als ein Kapitel
  unter mehreren — Beobachtungen, philosophische Fragen, andere
  Veränderungsprozesse)
- Den operativen Charakter (42 ist editorialer, kuratierter,
  langsamer)

## Bekannte offene Punkte in der App

Damit eine Claude-Instanz nicht denkt, alles sei perfekt — was
nicht stimmt:

- **Manifiesto 10 vs. 14**: temporäre Reduktion. Die Vision sind
  14 Punkte (einer pro Themenkapitel der Guía), je 3 Statements.
  Diese Inkonsistenz wird noch aufgelöst.
- **Sprachen ungleichmäßig**: Kurzversionen in ES/DE/EN,
  Originaltexte nur ES/DE, EN-Vollvarianten fehlen
- **Datenmodell organisch gewachsen**: drei verschiedene Strukturen
  für Mehrsprachigkeit im Code (Object-keyed, Suffix-Konstanten,
  Render-Funktionen). Wird beim Frontend-Bau von 42 sauber
  aufgesetzt — die App-Codebasis bleibt vorerst, wie sie ist.

## Verhältnis App ↔ 42

Geschwister, kein Verbund. Auf der Startseite von 42 wird die App
**prominent** eingeladen — sie ist nicht ein Tool unter vielen,
sondern das praktische Pendant zum kontemplativen Werk. In Kapiteln
von 42, die thematisch mit der App resonieren (Migration im engeren
Sinne), wird sie zusätzlich verlinkt.

Keine geteilten Daten. Keine gemeinsame Benutzerverwaltung. Wer
beides nutzt, bewegt sich bewusst zwischen zwei Räumen.
