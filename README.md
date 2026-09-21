# 🌐 Global Macro Cockpit — Streamlit Cloud Edition

Echtzeit-Makroökonomisches Scoring-Dashboard, gehostet auf Streamlit Cloud.
**Kostenlos · Immer online · Täglich automatisch aktualisiert.**

---

## 🚀 Deployment in 5 Schritten (ca. 10 Minuten)

### Schritt 1 — GitHub-Konto erstellen (falls noch nicht vorhanden)
👉 https://github.com/join

### Schritt 2 — Neues Repository erstellen
1. Auf **"New repository"** klicken
2. Name: `macro-cockpit` (oder beliebig)
3. **Public** auswählen (für kostenloses Streamlit-Hosting erforderlich)
4. Auf **"Create repository"** klicken

### Schritt 3 — Dateien hochladen
Im neuen Repository auf **"uploading an existing file"** klicken und
alle Dateien aus diesem ZIP hochladen:

```
app.py
requirements.txt
modules/
  __init__.py
  data_loader.py
  scoring.py
  charts.py
  alerts.py
  report.py
.streamlit/
  config.toml
```

> ⚠️ Die Datei `.streamlit/secrets.toml` **NICHT** hochladen —
> sie enthält den API-Key und bleibt lokal!

### Schritt 4 — Streamlit Cloud verbinden
1. 👉 https://share.streamlit.io → **"Sign in with GitHub"**
2. Auf **"New app"** klicken
3. Repository: `dein-username/macro-cockpit`
4. Branch: `main`
5. Main file: `app.py`
6. Auf **"Advanced settings"** klicken → **Secrets** eintragen:

```toml
FRED_API_KEY = "558469b9dd6ae900b9e4958a41344862"
```

7. Auf **"Deploy!"** klicken

### Schritt 5 — Fertig! 🎉
Nach ca. 2 Minuten ist die App unter einer URL wie
`https://dein-username-macro-cockpit.streamlit.app` erreichbar.

---

## ♻️ Automatische Aktualisierung

Die Daten werden **täglich automatisch** erneuert (24h-Cache).
Manuelles Update jederzeit über den Button **"Daten jetzt aktualisieren"**
in der Sidebar.

---

## 📊 Features

| Feature | Beschreibung |
|---|---|
| **Live-Daten** | FRED API — UNRATE, FEDFUNDS, T10Y2Y, CPI, GDP, Ölpreis, GPR |
| **6 Block-Scores** | Konjunktur · Frühindikatoren · Inflation · Fiskal · Exogen · Gesamt |
| **4 Regionen** | USA (live) · Eurozone · China · Japan |
| **Weltindex** | Gewichteter Aggregatindex (in Sidebar konfigurierbar) |
| **Historische Charts** | Score-Verlauf + Zinskurve & Inflation je Region |
| **Alerts** | Regelbasiert, Schwellenwerte in Sidebar einstellbar |
| **Radar-Chart** | Regionenvergleich aller Block-Scores |
| **HTML-Report** | Ein-Klick-Export |
| **Dunkel-Theme** | Optimiert für lange Nutzung |

---

## 🌡️ Score-Interpretation

| Score | Phase |
|---|---|
| 0–20 | Depression |
| 21–40 | Rezession |
| 41–55 | Erholung |
| 56–70 | Aufschwung |
| 71–85 | Späte Expansion |
| 86–100 | Peak / Überhitzung |

---

## 📡 Datenquellen

| Region | Quelle | Live? |
|---|---|---|
| USA | FRED (Federal Reserve) | ✅ Täglich |
| Eurozone | FRED/Eurostat + ECB | ✅ Monatlich via FRED |
| China | FRED/NBS + IMF | ⚡ Monatlich via FRED |
| Japan | FRED/BOJ + IMF | ⚡ Monatlich via FRED |

---

## ⚙️ Lokale Entwicklung

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## ⚠️ Hinweis
Kein Anlageberatung. Ausschließlich zur Analyse und Veranschaulichung.

---
*Streamlit · Plotly · Pandas · FRED API*
