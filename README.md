# Wege zu Cicero – Per Aspera ad Astra

Anki-Karteikarten zum Lehrbuch und Kurs ***Wege zu Ciceo. Per Aspera ad Astra.**
Intensivkurs für Studierende zur Vorbereitung auf die Cicerolektüre*.

Dieses Buch dient vielen Latein-Kursen der Universität Heidelberg als
Unterrichtsmaterial und Lektüre. Zum Bestehen der Prüfung sind die Vokabeln
und besonders deren ausgewählte Bedeutungen entscheidend.

## Installation

1. Letzte Version der `.akpg`-Datei unter
   [*Releases*](https://github.com/lsg551/anki-wege-zu-cicero/releases)
   oder [`anki-wege-zu-cicero.apkg`](https://github.com/lsg551/anki-wege-zu-cicero/blob/main/anki-wege-zu-cicero.apkg)
   direkt (vom <tt>main</tt>-Branch) herunterladen.
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
> [Contributing](./CONTRIBUTING.md) für Instruktionen.

## Inhalt & Aufbau

Das Haupt-Deck <tt>Latein</tt> ist in Subdecks nach Lektion gegliedert:

```
Latein
┣━ 01. Lectio Prima
┣━ 02. Lectio Secunda
┣━ … 
┗━ 20. Lectio Vicesima
```

Die einzelnen Karteikarten der Lektionen enthalten neben den Vokabeln[^vocab]
der einzelnen Lektionen auch Beispiele, Eselsbrücken (z.B. Lehnwörter) oder
andere Angaben.

[^vocab]: Inklusive derer, die nicht im Vokabelverzeichnis der Lektionen
aufgeführt sind, sondern nur unterhalb der Lektionstexte (oder im alphabetischen
Vokabelberzeichnis).

Jede Lektion enthält dabei auch die für sie relevanten Grammatikfragen sowie
Karteikarten, die das Flexionssystem üben.

> [!TIP]
> Diese Nicht-Vokabelkarteikarten kann man mittels Tags filtern! Zum Beispiel
> `Latein::Grammatik` oder `Latein::Flexion::a-Deklination`.

> [!WARNING]
> Die Karteikarten wurden über mehrere Semester angefertigt. Einige Neuerungen
> wurden erst kürzlich eingeführt (z.B. spezialisiertere *Note Types*) und
> müssen für einige Lektionen noch hinzugefügt werden.
>
> **Bis einschließlich Lektion 12 sind jedoch alle Vokabeln in irgendeiner Form
> enthalten.**

- [x] I. Lectio Prima
- [x] II. Lectio Secunda
- [ ] III. Lectio Tertia (enthalten, noch nicht migriert)
- [ ] IV. Lectio Quarta (enthalten, noch nicht migriert)
- [ ] V. Lectio Quinta (enthalten, noch nicht migriert)
- [ ] VI. Lectio Sexta (enthalten, noch nicht migriert)
- [ ] VII. Lectio Septima (enthalten, noch nicht migriert)
- [ ] VIII. Lectio Octava (enthalten, noch nicht migriert)
- [ ] IX. Lectio Nona (enthalten, noch nicht migriert)
- [ ] X. Lectio Decima (enthalten, noch nicht migriert)
- [ ] XI. Lectio Unodecima (enthalten, noch nicht migriert)
- [ ] XII. Lectio Duodecima (enthalten, noch nicht migriert)
- [ ] XIII. Lectio Tertia Decima
- [ ] XIV. Lectio Quarta Decima
- [ ] XV. Lectio Quinta Decima
- [ ] XVI. Lectio Sexta Decima
- [ ] XVII. Lectio Septima Decima
- [ ] XVIII. Lectio Duodevicesima
- [ ] XIX. Lectio Undevicesima
- [ ] XX. Lectio Vicesima

### Änderungen und Unterschiede zum Lehrbuch

- Vereinzelt wurden weitere Bedeutungen hinzugefügt, wenn es semantisch nicht
  verschieden ist aber dem Erlernen hilft.
- Einige Duplikate wurden entfernt resp. vereint.
- Einige redundante Oberflächenformen (z.B. *est*) wurden entfernt und/oder ihre
  Lexeme integriert (z.B. *est* → *esse*).
- Mehr Diakritika wurden annotiert.

### Notes & Cards

Anki hat ein etwas komplexeres und leicht verwirrendes Systems als "nur"
einfache Frage-Antwort-Karteikarten. Die "Karteikarte" besteht aus den
[*Notes*](https://docs.ankiweb.net/manual/getting-started#note-types), die es
über konfigurierbare
[*Fields*](https://docs.ankiweb.net/manual/getting-started#notes-%26-fields)
erlauben, mehr als nur Fragen und Antworten hinzuzufügen.

Bei vielen Vokablen werden neben Lexem und Bedeutung auch Wortart, Zeitform,
Deklinationsklasse o.Ä. annotiert. Daneben gibt es für unterschiedliche
Wortarten verschiedene *Note Types*[^types]. Unregelmäßige Verben benötigen z.B.
andere *Fields* als regelmäßige Verben, um ihrer Unregelmäßigkeit beim Lernen
gerecht zu werden.

[^types]: Technisch sind "Note" und "Note Type" nicht dasselbe. Ersteres ist
eine konkrete Entität der letzteren, die Vorlage/Template. Eine "Note" enthält
echte Daten und kann im Anki-Browser gefiltert/gesucht werden. Einer "Note Type"
begegnet man nur, wenn man sie modifiziert (z.B. deren *Fields*). Dies gilt
analog auch für "Card" und "Card Type". Praktisch ist der Unterschied aber kaum
relevant.

Diese *Note Types* bestimmen aber noch nicht, wie die "Karteikarte" dann beim
Lernenden angezeigt wird. Anki erlaubt es, aus einer *Note* ein oder mehr
[*Cards*](https://docs.ankiweb.net/manual/getting-started#card-types) zu
generieren, wobei per
[*Templating*](https://docs.ankiweb.net/manual/templates/intro) die Vorder-
und Hinteransicht der Karteikarte nach Belieben mit verschiedenen *Fields*
angepasst werden kann.

Bei Vokabeln könnte man z.B. statt nur Latein-Deutsch auch Deutsch-Latein
lernen, ohne dafür zwei *Notes* zu erstellen. Oder zusätzlich Deklinationsklasse
abfragen usw.

---

Von diesem System wird aktiv Gebrauch gemacht:

<details><summary>Alle speziellen Note & Card Types (<i>Klicken zum Ausklappen</i>)</summary>
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

> [!TIP]
> Besonders die *Cards* <tt>Vokabeln</tt> erzeugen sehr viele Karteikarten. Am
> Anfang des Lateinkurses kann dies noch von Vorteil sein, in späteren Lektionen
> jedoch übermäßig wirken.
>
> Wem das zu viel ist, kann diese *Card Types* (z.B. eine Teilmenge)
> deaktivieren. Dazu gibt es mehrere Möglichkeiten, unter anderem:
>
> **(1) Die unerwünschten *Card Types* einfach löschen.**
>
> 1. Menüleiste: `Notes > Manage Note Types`
> 2. In dem neuen Fenster den entsprechenden *Note Type* auswählen: `Cards`
>    klicken
> 3. Im neuen Fenster unter `Card Type` auswählen, dann auf Dropdown `Options`
>    und `Remove Card Type...`
>
> **(2) Die unerwünschren Karteikarten "aussetzen" (*suspend*) oder "vergraben"
> (*bury*).**
>
> 1. Der Anki-Browser hat in den linken Sidebar die Möglichkeit, unter
>    *Note Types* auch nach *Card Types* zu filtern. Zum Beispiel, wenn man
>    für regelmäßige Verben nicht ständig den Infinitv abgefragt bekommen
>    möchte: `Note types > Vokabeln (Verb) > Nur Infinitiv`.
> 2. Im Anki-Browser den Toggle-Button auf *Cards* (statt *Notes*) umschalten.
> 3. Alle Karten in der Liste gefilterten Liste auswählen und Rechtsklick:
>    - `Toggle Suspend` dauerhaft aus Lernbetrieb nehmen, oder
>    - `Toggle Bury` temporär für einen Tag aus dem Lernbetrieb nehmen.
>
> *Suspend* markiert die *Card* dann gelb, *bury* hingegen rot. Zum
> Unterschied *suspend* vs *bury* siehe
> [*Anki: Editing and More*](https://docs.ankiweb.net/manual/studying#editing-and-more).
>
> Man kann auch *Notes* aussetzen. Hier muss man aufpassen, dass man diese
> Operation auf *Cards* durchführt.

## Bekannte Probleme

- Die native Anki-Suchfunktion unterscheidet zwischen Symbolen mit und ohne
  Diakritika. D.h. <tt>a</tt> und <tt>ā</tt> sind zwei distinkte Zeichen. Beim
  Suchen kann dies kontraintuitiv sein, wenn <tt>advoco</tt> <tt>advocō</tt>
  nicht findet.

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
