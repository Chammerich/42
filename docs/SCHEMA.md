# Schema

Wie ein Kapitel aufgebaut ist. Pragmatisch und flexibel.
Pflicht ist nur, was nötig ist, damit das System funktioniert.
Alles andere ist optional und kann später dazukommen.

## Dateiformat

Jedes Kapitel ist eine Markdown-Datei mit YAML-Frontmatter.
Eine Datei pro (Kapitel, Sprache).

Dateiname: `<kapitel-id>.<sprache>.md`

Beispiel:
- `lucifer.es.md` — Lucifer auf Spanisch
- `lucifer.de.md` — derselbe Text auf Deutsch
- `kommunikation-fuehrung.de.md` — Originalfassung
- `kommunikation-fuehrung-migracion.es.md` — Adaption (Kind)

## Frontmatter

### Pflicht

```yaml
id: lucifer                    # Stabiler Schlüssel, ändert sich nie
sprache: es                    # ISO-Code: es, de, en, ...
titel: Lucifer – El Maldito    # Anzeigetitel
```

Plus mindestens **ein Inhaltsbaustein** im Body der Datei.

### Optional, aber empfohlen

```yaml
untertitel: Una reflexión sobre el perdón y la manipulación
uberkapitel: observaciones    # Slug eines Überkapitels

entstehung:
  jahr: 2024
  ort: Barcelona
  kontext: Frei formuliert. Wozu, für wen, in welchem Moment.

eltern: kommunikation-fuehrung      # Wenn Adaption: Original-ID
geschwister: [lucifer]              # Wenn Übersetzung: parallele IDs

querverweise:
  - kapitel: schluesselkind
    notiz: |
      Beide Texte stellen die gleiche Frage von verschiedenen Seiten:
      darf man unterscheiden, oder muss man alles akzeptieren?

status: veroeffentlicht       # entwurf | ueberarbeitung | veroeffentlicht
datum: 2024-11-03             # Letzte inhaltliche Änderung
```

### Bausteine im Body

Bausteine sind benannte Abschnitte im Markdown-Body, eingeleitet
durch einen HTML-Kommentar. Jedes Kapitel wählt aus, welche es
braucht. Reihenfolge frei.

```markdown
<!-- baustein: apetuter -->
Zwei, drei Sätze. Die Tür.

<!-- baustein: zusammenfassung -->
Der mittlere Text. In sich vollständig, bewusst nicht komplex.
Wer hier aufhört, hat trotzdem etwas Vollständiges gelesen.

<!-- baustein: originaltext -->
Der lange Text. In der vollen Form. Hier darf Christians
Stil mäandern: Ellipsen, Gedankenstriche, autobiografische
Schleifen.

<!-- baustein: wissenschaft -->
Erdung, mit Fachbegriffen.

<!-- baustein: glossar -->
- **Neuroplastizität**: Die Fähigkeit des Gehirns, sich zu reorganisieren.

<!-- baustein: imperativ -->
Hör auf zu warten. Fang an.

<!-- baustein: reflexionsfragen -->
- Was hast du in deinem Leben hingenommen, ohne es zu hinterfragen?

<!-- baustein: zitate -->
> "Monsters never die. Invite them in and dance with them."
> — Lady Gaga

<!-- baustein: beobachtung -->
Eine Szene, ein Bild, autobiografisch.

<!-- baustein: philosophie -->
Die Sternenstaub-Ebene. Immer mit Rückführung ins Konkrete.

<!-- baustein: tool -->
bezeichnung: Berry-Modell — interaktiv durchspielen
url: /tools/berry
notiz: Wer das Modell selbst durchgehen will, kann es hier tun.
```

## Drei Prinzipien

1. **Bausteine werden hinzugefügt, nicht hardcodiert.** Neue Bausteintypen
   können jederzeit erfunden werden, ohne dass alte Kapitel brechen.

2. **Versionierung pro Kapitel.** Jede Datei hat ihre eigene Git-Historie.
   Eine Änderung an einem Text bricht nichts anderes.

3. **Sprachen sind unabhängig.** Ein Kapitel kann in ES vollständig sein
   und in DE nur als Apetuter existieren. Die Webseite zeigt, was da ist,
   sagt klar, was fehlt, und drängt zu nichts.

## Spezialfälle

### Wenn ein Kapitel etwas Eigenes braucht

Manche Kapitel werden Werkzeuge brauchen, die nicht in dieses Schema
passen — interaktive Visualisierungen, Rechner, Karten. Diese werden
als eigenständige Seiten/Komponenten außerhalb des Schemas gebaut
und im Kapitel mit dem `tool`-Baustein verlinkt.

### Wenn ein Text adaptiert wurde

Original bleibt erhalten. Die Adaption ist ein eigenes Kapitel mit
eigener ID, das mit `eltern:` auf die Original-ID verweist. Auf
der Webseite ist diese Beziehung sichtbar — der Leser weiß, dass er
eine Adaption liest und woher sie kommt.

### Überkapitel

Sind keine eigenen Datentypen, sondern lose Tags. Definiert in
`/content/uberkapitel/<slug>.md` mit eigenem Titel, Beschreibung,
optional Reihenfolge der Kapitel. Ein Kapitel kann zu einem Überkapitel
gehören, muss aber nicht. Ein Kapitel kann auch zu mehreren gehören
(dann `uberkapitel: [observaciones, preguntas-grandes]`).
