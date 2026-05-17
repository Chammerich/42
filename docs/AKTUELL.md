# Aktuell

Wo wir gerade stehen. Was als Nächstes ansteht.

Letztes Update: 2026-05-17

## Status

- Repository `Chammerich/42` auf GitHub angelegt, public
- Astro-Setup mit i18n (ES default, DE, EN als gleichberechtigt) läuft
- Drei Platzhalter-Startseiten in den drei Sprachen
- Stiltokens aus docs/STYLEGUIDE.md in src/styles/global.css übernommen
- Cloudflare Workers mit `wrangler.jsonc` konfiguriert
- Cloudflare-Deploy läuft
- `chammerich.de` als Cloudflare-Zone aktiv
- `42.chammerich.de` als Custom Domain konfiguriert
- Schema in docs/SCHEMA.md festgehalten
- Zwei Beispielkapitel migriert (Lucifer komplett, Schlüsselkind partiell)
- Ein Überkapitel definiert (`observaciones`)
- **Form gefunden**: dreispaltige Matrix-Struktur, dokumentiert in
  docs/MATRIX.md (siehe Eintrag 2026-05-17 in ENTSCHEIDUNGEN.md)
- **Werktitel-Kandidat** in Prüfung: *42 — das Leben, das Universum
  und alles* (URL-Form: `42-das-leben-das-universum-und-alles`)

## Offene Punkte (geordnet nach Priorität)

### Zentral

1. **Klammertext schreiben.** Der oberste Layer der Webseite. Trägt
   die gesamte Architektur. Wenn er nicht trägt, trägt nichts.
   Christian schreibt, Claude formatiert.

2. **Erste Brücken schreiben.** Stufe 2 mit Deckel, kuratorische
   Stimme. Anspruchsvollster Texttyp im Werk.

### Frontend bauen

3. **Drei-Spalten-Layout** für Desktop, vertikale Auflösung mit
   Goldmarken am Rand für Mobile. STYLEGUIDE.md erweitern.
4. **Kapitel-Detailseite**: Markdown-Dateien aus `/content/kapitel/`
   als Astro Content Collection einbinden. Bausteine im Body parsen.
5. **Notiz-Komponente**: Lesefenster (Modal auf Desktop, Bottom-Sheet
   auf Mobile), ansteuerbar aus der Brücken-Spalte.
6. **Spur-Spalte (rechts)**: dynamisch mit dem Scrollen, zeigt was
   der Klammertext gerade berührt.
7. **Burger-Navigation**: Vollständige Übersicht aller Überkapitel
   und Kapitel. Sprachumschalter.
8. **App-Einladung auf Startseite**: prominent, als bewusster Eingang.

### Inhalte migrieren

9. Vollständige Migration der bestehenden Texte aus den .docx-Quellen
   ins Schema. Mindestens die App-Texte (Guía, Manifiesto, Anhänge)
   konsistent in allen drei Sprachen.
10. *Lucifer* und *Schlüsselkind* in DE und EN ergänzen.
11. *Kommunikation & Führung* als Adaptions-Beispiel.

### Offene Schema-Entscheidung

12. Notizen als eigener Inhaltstyp (`/content/notizen/<id>.<sprache>.md`)
    oder als sehr kurze Kapitel ohne Burger-Menü-Eintrag? Entscheidung
    fällt beim Frontend-Bau.

### Später

13. Sveltia CMS aufsetzen, sobald das Schema sich bewährt hat
14. Werktitel endgültig fixieren, Domain entsprechend anpassen
15. Titel-Schreibweisen pro Sprache klären (Cover-Form vs. URL-Form)

## Offene Fragen, auf die Christian noch nicht geantwortet hat

- Welche Texte aus dem Bestand zuerst migriert werden sollen
- Wie viele Adaptionen geplant sind (vs. nur Übersetzungen)
- Titel-Endentscheidung

## Tokens / Secrets

- GitHub-Token wird **temporär** im Chat geteilt und nach Gebrauch
  revoked. **Nicht persistent im Memory speichern.**
- Strato-Zugangsdaten werden **nicht** im Chat geteilt — DNS läuft
  jetzt über Cloudflare.
