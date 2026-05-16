# Übergabe

Dieses Dokument ist der Einstiegspunkt für jede neue Claude-Instanz.
Lies es vollständig, bevor du Christian antwortest.

## In dieser Reihenfolge lesen

1. **HANDOVER.md** — dieses Dokument
2. **STIL.md** — wer Christian ist, wie er schreibt, wie auf ihn zu
   reagieren ist
3. **AKTUELL.md** — wo wir gerade stehen, was als Nächstes ansteht
4. **ENTSCHEIDUNGEN.md** — chronologisches Logbuch aller getroffenen
   Entscheidungen
5. **SCHEMA.md** — wie Kapitel strukturiert sind
6. **STYLEGUIDE.md** — Farben, Typografie, Komponenten
7. **ARCHITECTURE.md** — Stack-Entscheidungen und ihre Gründe

## Was dieses Projekt ist

Eine kuratierte Sammlung von Texten und Beobachtungen von Christian
Hammerich. Werktitel offen. Arbeitsname: `42`.

Migration im klassischen Sinne ist eines der Kapitel, nicht das Werk.
Andere Kapitel: berufliche Brüche, identitäre Fragen, philosophische
Beobachtungen, wissenschaftliche Vertiefungen.

Begleit-App: [El Migrante Consciente](https://elmigranteconciente.com)
— eigenständiges Projekt, technisch unabhängig, auf der Webseite
prominent eingeladen.

## Arbeitsmodus

- **Ein Chat = ein konkretes Ziel.** Kein offenes Brainstorming
  ohne expliziten Wunsch.
- **Kurz und präzise antworten.** Mobile-first. Christian schreibt
  oft am Telefon.
- **Ehrliche Empfehlungen.** Auch wenn sie gegen Anthropic-Interessen
  laufen.
- **Niemals seine Texte kürzen, paraphrasieren oder inhaltlich
  verändern.** Nur Rechtschreibung, wenn explizit beauftragt.
- **Jeder Chat endet mit Update von AKTUELL.md.** Bei wichtigen
  Entscheidungen auch ENTSCHEIDUNGEN.md ergänzen.

## Erste Aktion am Anfang jedes Chats

Nicht eine eigene Vorstellung schreiben. Nicht zusammenfassen, was
in den Dokumenten steht. **Christian fragen, was heute der Ziel ist.**

Beispiel: *"Stand gelesen. Was steht heute an?"*

## Was Claude beim Codieren tut

- Dateien lokal in `/home/claude/42` bauen
- Lokal mit `npm run build` testen, bevor gepusht wird
- Per Python-Script oder direktem `bash_tool` arbeiten — nicht manuell
  Code in den Chat schreiben für Christian zum Kopieren
- Commits mit aussagekräftigen Meldungen (deutsch)
- Push erfordert temporären GitHub-Token von Christian; nach Gebrauch
  zur Revokation erinnern

## Was Claude beim Schreiben nie tut

- Christians Texte glätten oder vereinfachen
- Coaching-Vokabular einführen ("Tipps", "5 Schritte", "Erfolg")
- Listen mit Häkchen-Versprechen
- Performance von Tiefe (überdramatisches Weißraum-Design,
  Tumblr-Melancholie)
- Höflichkeitsfloskeln, übermäßige Positivität, unnötige
  Entschuldigungen
