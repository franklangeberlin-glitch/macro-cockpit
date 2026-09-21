"""report.py — HTML-Report-Export"""
from datetime import datetime
from modules.scoring import MacroScorer

scorer = MacroScorer()
BL = dict(growth="Konjunktur", leading="Frühindikatoren",
          policy="Inflation & Zinsen", fiscal="Fiskalstress",
          exogenous="Exogene Risiken")


def _c(s):
    if s <= 30: return "#e24b4a"
    if s <= 45: return "#ef9f27"
    if s <= 62: return "#378add"
    if s <= 78: return "#639922"
    return "#1d9e75"


class ReportExporter:
    def build_html(self, scores, data, alerts, focus,
                   world_score, world_weights) -> str:
        now = datetime.now().strftime("%d. %B %Y, %H:%M Uhr")
        regions = list(scores.keys()) if focus == "Alle" else [focus]

        def region_card(r):
            s, d = scores[r], data.get(r, {})
            block_rows = "".join(
                f'<tr><td>{BL[k]}</td>'
                f'<td style="text-align:right;color:{_c(s[k])};font-weight:600;">{s[k]}</td></tr>'
                for k in BL)
            tc = _c(s["total"])
            return f"""<div class="rc">
              <h2>{r} <span style="color:{tc};">{s['total']}</span>
                <span class="badge" style="background:{tc}22;color:{tc};border:1px solid {tc}44;">
                  {scorer.phase(s['total'])}</span></h2>
              <table><tbody>{block_rows}
                <tr style="border-top:2px solid #333;">
                  <td><strong>Gesamt</strong></td>
                  <td style="text-align:right;color:{tc};font-size:1.3rem;font-weight:700;">{s['total']}</td>
                </tr></tbody></table>
              <p class="src">Quelle: {d.get('source_note','FRED/IMF')}</p>
            </div>"""

        al_html = '<p class="ok">✅ Keine kritischen Alerts.</p>'
        if alerts:
            al_html = "".join(
                f'<div class="{"ac" if a["level"]=="crit" else "aw"}">'
                f'<strong>{"🔴" if a["level"]=="crit" else "🟡"} {a["title"]}</strong>'
                f'<br><small>{a["detail"]}</small></div>' for a in alerts)

        wc = _c(world_score)
        cards = "".join(region_card(r) for r in regions)
        wt_html = "".join(f'<span class="wi">{r}: {w}%</span>'
                          for r, w in world_weights.items())

        return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8">
<title>Macro Cockpit Report — {now}</title>
<style>
body{{font-family:'Helvetica Neue',Arial,sans-serif;max-width:920px;
     margin:0 auto;padding:30px 20px;background:#0f0f1a;color:#ddd;}}
h1{{font-size:1.8rem;font-weight:300;border-bottom:1px solid #333;padding-bottom:10px;color:#eee;}}
h2{{font-size:1.05rem;font-weight:500;color:#ccc;margin:0 0 10px;}}
.meta{{font-size:.8rem;color:#666;margin-bottom:20px;}}
.ws{{font-size:4rem;font-weight:700;color:{wc};line-height:1;}}
.wp{{font-size:1.15rem;color:{wc};margin-bottom:20px;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(195px,1fr));gap:14px;margin:20px 0;}}
.rc{{background:#1a1a2e;border-radius:9px;padding:14px;border:1px solid #2a2a44;}}
table{{width:100%;border-collapse:collapse;font-size:.83rem;}}
td{{padding:4px 3px;border-bottom:1px solid #222;}}
.badge{{font-size:.7rem;padding:2px 8px;border-radius:11px;font-weight:600;margin-left:7px;}}
.src{{font-size:.7rem;color:#555;margin-top:8px;}}
.ac{{background:#2d1010;border:1px solid #a32d2d;border-radius:5px;
     padding:9px 13px;margin:6px 0;color:#ffaaaa;}}
.aw{{background:#2d2010;border:1px solid #b07020;border-radius:5px;
     padding:9px 13px;margin:6px 0;color:#ffd080;}}
.ok{{color:#1d9e75;font-size:.88rem;}}
.weights{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0;}}
.wi{{background:#1a1a2e;border-radius:5px;padding:6px 12px;
     font-size:.8rem;border:1px solid #2a2a44;}}
footer{{margin-top:30px;font-size:.7rem;color:#444;
        border-top:1px solid #222;padding-top:12px;}}
</style></head><body>
<h1>🌐 Global Macro Cockpit — Report</h1>
<p class="meta">Erstellt: {now} · Fokus: {focus} · v4 Cloud</p>
<div style="font-size:.8rem;color:#888;margin-bottom:4px;">WELTINDEX</div>
<div class="ws">{world_score}</div>
<div class="wp">{scorer.phase(world_score)}</div>
<h2 style="margin-top:18px;">Regionengewichtung</h2>
<div class="weights">{wt_html}</div>
<h2>Scores nach Region</h2>
<div class="grid">{cards}</div>
<div><h2>🔔 Aktive Alerts</h2>{al_html}</div>
<footer>Quellen: FRED · ECB/Eurostat · IMF WEO · BLS · NBS China · BOJ.
Scores 0–100 (höher = stabiler). <strong>Kein Anlageberatung.</strong>
</footer></body></html>"""
