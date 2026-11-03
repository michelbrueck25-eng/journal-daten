#!/bin/sh
# Rechnet das Makro-Modell neu: Live-Vorhersagen (modell.json) und Raster (Live Predictions)
cd "$(dirname "$0")" && python3 export.py >/dev/null && python3 export2.py
