# Wege zu Cicero – Per Aspera ad Astra

Anki-Karteikarten zum Lehrbuch und Kurs ***Wege zu Ciceo. Per Aspera ad Astra.**
Intensivkurs für Studierende zur Vorbereitung auf die Cicerolektüre*.

Dieses Buch dient vielen Latein-Kursen der Universität Heidelberg als
Unterrichtsmaterial und Lektüre. Zum Bestehen der Prüfung sind die Vokabeln
und besonders deren ausgewählte Bedeutungen entscheidend.

## Installation

1. Letzte Version der `.akpg`-Datei unter
   [*Releases*](https://github.com/lsg551/anki-wege-zu-cicero/releases)
   herunterladen.
2. Anki öffnen: `Import File` > `.akpg`-Datei auswählen.
3. Medien und Deck-Presets als Optionen beim Import inkludieren.

Das war's.

Siehe [*Anki: Importing Packaged Decks*](https://docs.ankiweb.net/manual/importing/packaged-decks)
für mehr Informationen.

### Upgrade auf neuere Version

Wenn eine `.akpg`-Datei bereits importiert, nun aber mit einer neuen Version
aktualisiert werden soll, die [Installationsschritte](#installation) einfach
ein weiteres Mal durchführen. Anki aktualisiert das alte Deck automatisch.

## Angaben zum Buch

```
Titel   :  Wege zu Ciceo. Per Aspera ad Astra. Intensivkurs für Studierende zur Vorbereitung auf die Cicerolektüre
Autor   :  Glaesser, Roland
Verlag  :  WINTER, Heidelberg
Auflage :  3., überarbeitete und erweiterte
Jahr    :  2012
ISBN    :  978-3-8253-5985-0
```

> [!INFO]
> Mir liegt nur die dritte Auflage vor (2012, ISBN 978-3-8253-5985-0).
> Inzwischen ist jedoch eine vierte erschienen, deren Inhalt entsprechend nicht
> in die Karteikarten mit einfließen konnte. Angeblich unterscheiden sich beide
> Auflagen aber nur marginal und für viele Kurse irrelevant.
>
> Ergänzungen und Beiträge hierzu sind willkommen; siehe
> [Contributing](#contributing) für Instruktionen.

## Inhalt & Aufbau

Die Anki-Karteikarten enthalten neben den Vokabeln der einzelnen Lektionen auch
Beispiele, Eselsbrücken (z.B. Lehnwörter) oder andere Angaben. Die Karteikarten
sind dabei wie im Buch nach Lektionen gegliedert.

Einige spezielle Sub-Decks behandeln Grammatikfragen oder üben Flexions- oder
Personalmorpheme.

#### Lektionen

> [!WARNING]
> Die Karteikarten wurden über mehrere Semester des Scheiterns hinweg
> angefertigt. Einige Neuerungen wurden erst kürzlich eingeführt (z.B.
> spezialisiertere *Note Types*) und müssen für Karten späterer Lektionen
> noch hinzugefügt werden.
>
> **Bis einschließlich Lektion 12 sind jedoch alle Vokabeln in irgendeiner Form
> enthalten.**

- [ ] I. Lectio Prima
- [ ] II. Lectio Secunda
- [ ] III. Lectio Tertia
- [ ] IV. Lectio Quarta
- [ ] V. Lectio Quinta
- [ ] VI. Lectio Sexta
- [ ] VII. Lectio Septima
- [ ] VIII. Lectio Octava
- [ ] IX. Lectio Nona
- [ ] X. Lectio Decima
- [ ] XI. Lectio Unodecima
- [ ] XII. Lectio Duodecima
- [ ] XIII. Lectio Tertia Decima
- [ ] XIV. Lectio Quarta Decima
- [ ] XV. Lectio Quinta Decima
- [ ] XVI. Lectio Sexta Decima
- [ ] XVII. Lectio Septima Decima
- [ ] XVIII. Lectio Duodevicesima
- [ ] XIX. Lectio Undevicesima
- [ ] XX. Lectio Vicesima

#### Änderungen und Unterschiede zum Lehrbuch

- Vereinzelt wurden weitere Bedeutungen hinzugefügt, wenn es semantisch nicht
  verschieden ist aber dem Erlernen hilft.
- Einige Duplikate wurden entfernt resp. vereint.
- Einige redundante Oberflächenformen (z.B. *est*) wurden entfernt und/oder ihre
  Lexeme integriert (z.B. *est* → *esse*).
- Mehr Diakritika wurden annotiert.

#### Note Types und Cards

Statt jedes Lexem und seine Bedeutung in naive Frage-Antwort-Paare zu packen,
werden abhängig der lexikalischen Kategorie (*Wortart*) dedizierte
[*Note Types*](https://docs.ankiweb.net/manual/getting-started#note-types)
genutzt. Diese erlauben es mehr Information in zusätzlichen
[*Feldern*](https://docs.ankiweb.net/manual/getting-started#notes-%26-fields)
zu annotieren, für regelmäßige Verben z.B. alle vier Lexioneinträge, oder für
Substantive zusätzlich das Genus.

Aus einer *Note* können dann mehrere
[*Cards*](https://docs.ankiweb.net/manual/getting-started#card-types) generiert
werden. Bei Verben lernt man dann z.B. nicht einfach nur »Welche Bedeutung hat
`<LEXEM>`?«, sondern:

1. Bedeutung fragen: »Was bedeutet `<LEXEM>`?«
2. Konjugationsklasse fragen: »Zu welcher Konjugationsklasse gehört `<LEXEM>`?«
3. Lexikoneintrag vervollständigen: »Gegeben der Infinitiv, wie Latein
   Präsens/Perfekt 1.Ps.Sg.Ind.Akt. und PPP?«
4. usw.

Wem das zu viel ist, kann die *Card Types* selbstverständlich auf einen
einzelnen im Frage-Antwort-Format reduzieren.

<details><summary>Alle speziellen <i>Note & Card Types</i>…</summary>
<p>

**Note Types**

- `Frage-Antwort` normale Frage-Antwort-Paare, besonders für Grammatikfragen
  etc.
- `Vokabeln (unidirektional)` Standard-Card-Typ für Vokabeln, mit Feldern für
  Lexem, Bedeutung, lexikalischer Kategorie und Details (Beispiele usw.).
- `Vokabeln (Substantiv)` speziell für Substantive, die Nominativ/Genitiv Sg.
  sowie Deklinationsklasse und Genus enthalten.
- `Vokabeln (Verb)` speziell für regelmäßige Verben, mit Feldern für alle vier
  Lexikonformen (Infinitiv, Präsens, Perfekt, PPP), Konjugationsklasse,
  Bedeutung und Details.
- `Vokabeln (Verb, unregelmäßig)` Anpassung für unregelmäßige Verben mit jeder
  Permutation aus Kasus und Person; pro Zeitform notwendig.

**Card Types**

- *TBA*

</p>
</details>

## Contributing

Korrekturen, Ergänzungen, etc. weden begrüßt.

Um das überarbeitete Deck zu exportieren:

1. Anki-Deck *Latein* durch Anklicken auswählen.
2. Auf das Einstellungs-Zahnrad klicken: `Export` und folgende Einstellungen
   übernehmen:
    - *Export format*: `Anki Deck Package (.akpg)`
    - *Include*: `Latein`
    - Optionen: {`Include deck presets`, `Include media`}
3. Auf `Export…` klicken.

Für die resultierende `.akkg`-Datei bitte einen Pull Request öffnen. Siehe
[*Anki: Exporting*](https://docs.ankiweb.net/manual/exporting) für mehr
Informationen.

Alternativ kann auch ein Issue mit den Änderungen als Freitext eröffnet werden.

## Lizenz

Eigenständige Beiträge zu diesem Anki-Deck, einschließlich selbst verfasster
Beispielsätze, Erklärungen, Lernnotizen, etc., unterliegen der
[Creative Commons Attribution 4.0 International License (CC BY 4.0)](./LICENSE.md),
sofern nicht anders angegeben.

Dies umfasst nicht das Material Dritter, inklusive Inhalt aus dem Quellbuch, und
unterliegt weiterhin den Rechten und Lizenzbedingungen der jeweiligen
Rechteinhaber.

Einige der Beispiele stammen wortgetreu aus dem Buch selbst, andere aus weiteren
Online-Quellen.
