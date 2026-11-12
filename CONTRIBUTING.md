# Contributing

Korrekturen, Ergänzungen und Verbesserungen sind willkommen.

## Ohne Git-Kenntnisse: Änderung als Issue vorschlagen

1. Die aktuelle Version aus den
   [Releases](https://github.com/lsg551/anki-wege-zu-cicero/releases)
   importieren, damit das Deck dem Stand des Repositorys entspricht.
2. In Anki das Deck *Latein* überarbeiten.
3. Das Deck exportieren: Deck anklicken, Zahnrad → `Export`, Format
   `Anki Deck Package (.apkg)`, *Include* `Latein`, Option
   `Include deck presets` einschalten. Siehe
   [*Anki: Exporting*](https://docs.ankiweb.net/manual/exporting).
4. Die exportierte Datei umbenennen, sodass sie zusätzlich auf `.zip` endet
   (`…apkg` → `…apkg.zip`). GitHub akzeptiert keine `.apkg`-Dateien.
5. Ein [neues Issue](https://github.com/lsg551/anki-wege-zu-cicero/issues/new/choose)
   mit der Vorlage *Änderung oder Korrektur vorschlagen* öffnen und die
   umbenannte Datei anhängen.

Ein Bot vergleicht die angehängte Datei mit dem Deck im Repository und
kommentiert die Unterschiede als Diff. Ist die Datei nicht lesbar, weist ein
Kommentar auf das Umbenennen hin. Anschließend prüft ein Maintainer den Diff und
integriert die Änderungen.

## Mit Git

Das Repository enthält `dump/`, eine textbasierte Fassung des Decks. Sie wird
mit [`anki-tools`](https://github.com/lsg551/anki-tools) aus einer `.apkg`-Datei
erzeugt und **nicht von Hand bearbeitet**. Änderungen werden in Anki vorgenommen
und dann neu gedumpt. Importiere vorher die aktuelle Version aus den Releases,
damit dein Deck dem Stand des Repositorys entspricht.

```bash
uv run anki-tools dump anki-wege-zu-cicero.apkg -o dump/ --with-deck-configs --no-media
uv run anki-tools build dump -o anki-wege-zu-cicero.apkg
```

Für einen Pull Request `dump/` und `anki-wege-zu-cicero.apkg` zusammen
committen. Die CI prüft, dass beide zueinander passen.
