# Aktuell

Wo wir gerade stehen. Was als Nächstes ansteht.

Letztes Update: 2026-05-16

## Status

- Repository `Chammerich/42` auf GitHub angelegt, public
- Astro-Setup mit i18n (ES default, DE, EN als gleichberechtigt) läuft
- Drei Platzhalter-Startseiten in den drei Sprachen
- Stiltokens aus docs/STYLEGUIDE.md in src/styles/global.css übernommen
- Cloudflare Workers mit `wrangler.jsonc` konfiguriert
- Cloudflare-Deploy läuft ("Status grün")
- `chammerich.de` als Cloudflare-Zone aktiv
- `42.chammerich.de` als Custom Domain konfiguriert, **DNS-Propagation läuft**
- Schema in docs/SCHEMA.md festgehalten
- Zwei Beispielkapitel migriert (Lucifer komplett, Schlüsselkind partiell)
- Ein Überkapitel definiert (`observaciones`)

## Offene Punkte (geordnet nach Priorität)

### Sofort

1. Bestätigung, dass `42.chammerich.de` aktiv ist (DNS-Propagation abwarten)

### Frontend bauen

2. **Kapitel-Detailseite**: Markdown-Dateien aus `/content/kapitel/`
   als Astro Content Collection einbinden. Bausteine im Body parsen
   und mit unterschiedlichen visuellen Behandlungen rendern.
3. **Übersichtsseite**: Liste aller Kapitel pro Sprache, optional
   gruppiert nach Überkapitel.
4. **Burger-Navigation**: alle Überkapitel und Kapitel erreichbar.
5. **App-Einladung auf Startseite**: prominent, nicht als Banner,
   sondern als bewusster Eingang.
6. **Klammer-Text**: der Eingang ins Werk, in Christians Stimme.
   Christian schreibt, Claude formatiert.

### Inhalte migrieren

7. Vollständige Migration der bestehenden Texte aus den .docx-Quellen
   ins Schema. Mindestens die App-Texte (Guía, Manifiesto, Anhänge)
   konsistent in allen drei Sprachen.
8. *Lucifer* und *Schlüsselkind* in DE und EN ergänzen (sobald Christian
   sie hat oder freigibt).
9. *Kommunikation & Führung* als Adaptions-Beispiel — sobald Christian
   den Originaltext und die Adaption bereitstellt.

### Später

10. Sveltia CMS aufsetzen, sobald das Schema sich bewährt hat
11. Tools-Architektur (analog Finanzplaner der App) für Werkzeuge,
    die einzelne Kapitel ergänzen
12. Werktitel finden und Domain entsprechend anpassen

## Offene Fragen, auf die Christian noch nicht geantwortet hat

- Werktitel (steht auf "kommt beim Schreiben")
- Welche Texte aus dem Bestand zuerst migriert werden sollen
- Wie viele Adaptionen geplant sind (vs. nur Übersetzungen)

## Tokens / Secrets

- GitHub-Token wird **temporär** im Chat geteilt und nach Gebrauch
  revoked. **Nicht persistent im Memory speichern.**
- Strato-Zugangsdaten werden **nicht** im Chat geteilt — DNS läuft
  jetzt über Cloudflare.
