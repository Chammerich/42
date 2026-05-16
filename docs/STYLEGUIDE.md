# Styleguide

Visuell konsequent zur App, aber editorialer.
Die App ist Werkzeug — kompakt, klare Aktionen, warme Farben.
Die Webseite ist Werk — Atem, Lesefläche, kühlere Tonalität.

## Farben

```
--gold        #c8922a   /* Primär-Akzent, übernommen aus App */
--gold-light  #e8b84b   /* Hover, sekundär */
--ink         #1a1208   /* Schrift dunkel */
--graphite    #3d3a35   /* Schrift mittel */
--ash         #6e6960   /* Schrift gedämpft, Metadaten */
--paper       #f5f3ee   /* Hintergrund hell */
--mist        #e8e4dc   /* Hintergrund Sektionen */
--line        #c9c3b6   /* Trennlinien, dezent */
```

Grau und Gold als Grundfarben. Keine sättigungsstarken Töne.

## Typografie

**Schriftart: Arial Nova** (laut User-Präferenz)
Fallback-Kette: `'Arial Nova', 'Arial', 'Helvetica Neue', sans-serif`

Arial Nova ist auf Windows verbreitet, auf Mac/Linux nicht standardmäßig.
Wir liefern sie nicht als Web-Font aus — wer sie hat, sieht sie;
wer nicht, sieht Arial. Das ist akzeptabel, weil die Unterschiede
klein sind und die typografische Disziplin (Größe, Zeilenabstand,
Spacing) den Charakter stärker prägt als die Schrift selbst.

**Größen:**

```
--text-xs    13px   /* Metadaten, Fußnoten */
--text-base  16px   /* Fließtext */
--text-md    18px   /* Eingang, Apetuter */
--text-lg    22px   /* Kapitel-Untertitel */
--text-xl    28px   /* Kapitel-Titel */
--text-2xl   36px   /* Werk-Titel auf Startseite */
```

**Zeilenabstand: 1.7 für Fließtext.**
Längere Lesezeilen brauchen Luft.

**Lesezeilen-Maximum: 65 Zeichen (~36em).**
Klassisch, augenschonend. Schmaler Spaltensatz, kein Vollbreit-Text.

## Komponenten

### Kapitel-Kopf

```
[Überkapitel-Slug, klein, ash]
[Titel, Kapitel-Titel-Größe]
[Untertitel, lg, kursiv, graphite]
[Entstehungskontext, xs, ash]
```

### Textblock

Reiner Fließtext, max. 36em breit, zentriert auf der Seite,
mit großzügigem Abstand zwischen Absätzen.

### Baustein-Trennung

Bausteine werden visuell nur dezent voneinander getrennt — kein
Boxen-Design. Ein vergrößerter Abstand und gelegentlich eine
schmale Trennlinie in `--line` reicht.

### Imperativ-Baustein

Hervorgehoben: kursiv, größer als Fließtext, mit Goldakzent.
Funktioniert als Schlussakkord, nicht als Banner.

### Querverweis-Block

Am Ende eines Kapitels. Schmal, mit deiner kuratorischen Notiz,
einem Link zum verwandten Kapitel.

### Burger-Menü

Klassisch. Hamburger oben rechts, öffnet eine Liste aller
Überkapitel und Kapitel. Sprachumschalter am Kopf des Menüs.

## Bewegung

Keine. Oder fast keine. Kein Carousel, kein Hero-Video, kein Parallax.
Ein dezenter Hover-Effekt auf Links (Goldakzent unterstrichen) reicht.

Die Webseite muss nicht beweisen, dass sie lebendig ist. Sie ist es,
durch ihre Inhalte.
