# journal-daten

Tägliche Makrodaten für das Trading-Journal. Ein geplantes Programm legt hier jeden Morgen neue Dateien ab:

- `wirtschaft.csv`: Wirtschaftskalender (neue Ist-Werte und Termine)
- `lage.csv`: Lage und Nachrichten
- `manifest.json`: Zeitstempel und Dateiliste. Das Journal lädt beim Öffnen nur, wenn `updated` neuer ist als beim letzten Abruf.
