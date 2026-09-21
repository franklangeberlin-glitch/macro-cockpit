"""
Global Macro Cockpit — Streamlit Cloud Edition
Daten: FRED Live-API + IMF/ECB-Schätzwerte
Cache: täglich (86.400 s), manuell über Sidebar zurücksetzbar
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

from modules.data_loader import DataLoader
from modules.scoring import MacroScorer
from modules.charts import ChartBuilder
from modules.alerts import AlertEngine
from modules.report import ReportExporter

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Macro Cockpit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main{padding-top:.4rem;}
.score-big{font-size:3rem;font-weight:700;line-height:1;}
.pbadge{display:inline-block;padding:3px 11px;border-radius:18px;
        font-size:.76rem;font-weight:600;margin-left:7px;}
div[data-testid="stMetric"]{
    background:rgba(255,255,255,.03);
    border:1px solid rgba(255,255,255,.08);
    border-radius:8px;padding:10px 14px;}
.acrit{background:#3d1515;border:1px solid #a32d2d;
       border-radius:6px;padding:9px 13px;margin:5px 0;color:#ffaaaa;}
.awarn{background:#3d2e10;border:1px solid #b07020;
       border-radius:6px;padding:9px 13px;margin:5px 0;color:#ffd080;}
.aok  {background:#0f3020;border:1px solid #1d9e75;
       border-radius:6px;padding:9px 13px;margin:5px 0;color:#80ffcc;}
.stTabs [data-baseweb="tab"]{font-size:.93rem;font-weight:500;}
footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ── Instanzen ──────────────────────────────────────────────────────
scorer  = MacroScorer()
charts  = ChartBuilder()

def sc(s):  return scorer.color(s)
def ph(s):  return scorer.phase(s)
def badge(s):
    c = sc(s)
    return (f'<span class="pbadge" style="background:{c}22;'
            f'color:{c};border:1px solid {c}55;">{ph(s)}</span>')

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Einstellungen")

    # FRED-Key: erst aus Streamlit-Secrets, dann manuell eingebbar
    default_key = ""
    try:
        default_key = st.secrets["FRED_API_KEY"]
    except Exception:
        pass
    api_key = st.text_input(
        "FRED API-Key",
        value=default_key,
        type="password",
        help="Kostenlos: https://fred.stlouisfed.org/docs/api/api_key.html",
    )

    st.divider()
    st.subheader("🔔 Alert-Schwellenwerte")
    tc = st.slider("Kritisch unter", 10, 60, 35)
    tw = st.slider("Warnung unter",  30, 70, 50)

    st.divider()
    st.subheader("🌍 Weltindex-Gewichtung")
    w_usa = st.slider("USA",      0, 100, 35)
    w_ez  = st.slider("Eurozone", 0, 100, 20)
    w_cn  = st.slider("China",    0, 100, 25)
    w_jp  = st.slider("Japan",    0, 100,  5)
    w_rest = max(0, 100 - w_usa - w_ez - w_cn - w_jp)
    st.caption(f"Rest (EM/Asien): {w_rest}%")
    WW = {"USA": w_usa, "Eurozone": w_ez, "China": w_cn, "Japan": w_jp}

    st.divider()
    st.subheader("📅 Historischer Zeitraum")
    hist_years = st.selectbox("Jahre zurück", [2, 3, 5, 10], index=1)

    st.divider()
    if st.button("🔄  Daten jetzt aktualisieren", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    st.caption("Daten werden täglich automatisch erneuert.")


# ── Daten — 24h-Cache (Streamlit Cloud) ────────────────────────────
@st.cache_data(ttl=86_400, show_spinner=False)
def load(key: str, years: int) -> dict:
    loader = DataLoader(key)
    return loader.load_all(years_back=years)


# ── Laden ──────────────────────────────────────────────────────────
st.title("🌐 Global Macro Cockpit")
st.caption(
    "Echtzeit-Makroökonomisches Scoring · "
    "USA: FRED Live-Daten · EZ/China/Japan: FRED + IMF/ECB · "
    "Tägliche Auto-Aktualisierung"
)

if not api_key:
    st.warning("⚠️ Bitte FRED API-Key in der Sidebar oder in den Streamlit-Secrets eintragen.")
    st.info("Kostenlos registrieren: https://fred.stlouisfed.org/docs/api/api_key.html")
    st.stop()

with st.spinner("⏳ Lade Daten von FRED..."):
    try:
        DATA = load(api_key, hist_years)
        ts   = datetime.now().strftime("%H:%M:%S")
        st.success(f"✅ Daten geladen — {ts} Uhr  (Cache: 24 h)")
    except Exception as e:
        st.error(f"❌ FRED-Fehler: {e}")
        st.stop()

REGIONS = ["USA", "Eurozone", "China", "Japan"]
SCORES  = {r: scorer.compute(DATA[r]) for r in REGIONS}
tw_sum  = sum(WW.values()) or 1
WORLD   = round(sum(SCORES[r]["total"] * WW[r] / tw_sum for r in WW))
ALERTS  = AlertEngine(tc, tw).evaluate(SCORES, DATA)

# ── Weltindex-Banner ───────────────────────────────────────────────
st.divider()
cw, cu, ce, cc, cj = st.columns([2.2, 1, 1, 1, 1])
with cw:
    c = sc(WORLD)
    st.markdown(
        f'<div style="padding:5px 0;">'
        f'<span style="font-size:.78rem;color:#777;">WELTINDEX</span><br>'
        f'<span class="score-big" style="color:{c};">{WORLD}</span>'
        f'{badge(WORLD)}</div>',
        unsafe_allow_html=True)

for r, col_ref in zip(REGIONS, [cu, ce, cc, cj]):
    s, c = SCORES[r]["total"], sc(SCORES[r]["total"])
    with col_ref:
        st.markdown(
            f'<div style="padding:5px 0;border-left:3px solid {c};padding-left:11px;">'
            f'<span style="font-size:.76rem;color:#888;">{r}</span><br>'
            f'<span style="font-size:1.85rem;font-weight:700;color:{c};">{s}</span>'
            f'{badge(s)}</div>',
            unsafe_allow_html=True)
st.divider()

# ── Region-Tabs ────────────────────────────────────────────────────
tabs = st.tabs(["🇺🇸  USA", "🇪🇺  Eurozone", "🇨🇳  China", "🇯🇵  Japan",
                "🌍  Vergleich", "🔔  Alerts"])

for region, tab in zip(REGIONS, tabs[:4]):
    with tab:
        s = SCORES[region]
        d = DATA[region]

        # Block-Karten
        cols = st.columns(6)
        for i, (key, lbl) in enumerate([
            ("total","Gesamt"),("growth","Konjunktur"),
            ("leading","Frühindikatoren"),("policy","Inflation & Zinsen"),
            ("fiscal","Fiskalstress"),("exogenous","Exogene Risiken"),
        ]):
            v, c = s[key], sc(s[key])
            with cols[i]:
                st.markdown(
                    f'<div style="text-align:center;padding:7px 2px;">'
                    f'<div style="font-size:.68rem;color:#888;margin-bottom:2px;">{lbl}</div>'
                    f'<div style="font-size:1.9rem;font-weight:700;color:{c};">{v}</div>'
                    f'<div style="font-size:.67rem;color:{c};margin-top:1px;">'
                    f'{ph(v) if key=="total" else ""}</div></div>',
                    unsafe_allow_html=True)

        st.divider()

        # Haupt-Charts (Score-Verlauf + Zinskurve/Inflation)
        st.plotly_chart(charts.region_charts(d, region),
                        use_container_width=True)

        # Kerndaten-KPIs
        st.subheader("📌 Kerndaten")
        r1 = st.columns(4)
        for (lbl, val, unit), col in zip([
            ("BIP-Wachstum",      d.get("gdp_growth"),  "% ann."),
            ("Arbeitslosenquote", d.get("unrate"),       "%"),
            ("CPI YoY",           d.get("cpi_yoy"),      "%"),
            ("Leitzins",          d.get("policy_rate"),  "%"),
        ], r1):
            if val is not None:
                col.metric(lbl, f"{val:.2f} {unit}".strip())

        r2 = st.columns(4)
        for (lbl, val, unit), col in zip([
            ("Zinskurve 10J-2J", d.get("yield_spread"), "bp"),
            ("Core CPI",         d.get("core_cpi_yoy"), "%"),
            ("Schuldenquote",    d.get("debt_gdp"),     "% BIP"),
            ("GPR-Index",        d.get("gpr_index"),    ""),
        ], r2):
            if val is not None:
                col.metric(lbl, f"{val:.1f} {unit}".strip())

        # Indikatoren-Tabelle
        with st.expander(f"📋 Alle Indikatoren & Quellen — {region}"):
            rows = []
            IND = [
                ("gdp_growth","BIP-Wachstum","% ann.","gdp_s"),
                ("unrate","Arbeitslosenquote","%","unrate_s"),
                ("cpi_yoy","CPI YoY","%","cpi_s"),
                ("core_cpi_yoy","Core CPI","%","core_s"),
                ("policy_rate","Leitzins","%","realrate_s"),
                ("yield_spread","Zinskurve 10J-2J","bp","yield_s"),
                ("debt_gdp","Schuldenquote","% BIP","debt_s"),
                ("deficit_gdp","Primärdefizit","% BIP","deficit_s"),
                ("gpr_index","GPR-Index","","gpr_s"),
                ("oil_yoy","Ölpreis YoY","%","oil_s"),
                ("gas_yoy","Gaspreise YoY","%","gas_s"),
                ("food_yoy","Lebensmittel YoY","%","food_s"),
            ]
            ind = s.get("indicators", {})
            for key, lbl, unit, sk in IND:
                v = d.get(key)
                if v is None:
                    continue
                rows.append({
                    "Indikator":     lbl,
                    "Wert":          f"{v:.2f} {unit}".strip()
                                     if isinstance(v, float) else str(v),
                    "Score (0–100)": ind.get(sk, "—"),
                    "Quelle":        d.get(f"{key}_src", "FRED"),
                    "Stand":         d.get(f"{key}_date", "aktuell"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True,
                column_config={"Score (0–100)": st.column_config.ProgressColumn(
                    "Score (0–100)", min_value=0, max_value=100)})
            st.caption(d.get("source_note", "FRED / ECB / IMF"))


# ── Vergleichs-Tab ─────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Regionenvergleich — Radar & Block-Scores")
    st.plotly_chart(charts.comparison(SCORES, REGIONS),
                    use_container_width=True)

    rows = [{"Region": r, "Gesamt": SCORES[r]["total"],
             "Phase": ph(SCORES[r]["total"]),
             "Konjunktur": SCORES[r]["growth"],
             "Frühindikatoren": SCORES[r]["leading"],
             "Inflation/Zinsen": SCORES[r]["policy"],
             "Fiskalstress": SCORES[r]["fiscal"],
             "Exogene Risiken": SCORES[r]["exogenous"]}
            for r in REGIONS]
    df = pd.DataFrame(rows)
    num_cols = ["Gesamt","Konjunktur","Frühindikatoren",
                "Inflation/Zinsen","Fiskalstress","Exogene Risiken"]
    st.dataframe(
        df.style.background_gradient(subset=num_cols,
                                     cmap="RdYlGn", vmin=0, vmax=100),
        use_container_width=True, hide_index=True)

    st.subheader("Historischer Score-Verlauf — alle Regionen")
    st.plotly_chart(charts.all_regions_trend(DATA),
                    use_container_width=True)

    st.subheader("Modell-Gewichtung")
    st.plotly_chart(charts.weight_donut(), use_container_width=True)


# ── Alert-Tab ──────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("🔔 Alert-System")
    if not ALERTS:
        st.markdown('<div class="aok">✅ Keine aktiven Alerts.</div>',
                    unsafe_allow_html=True)
    else:
        st.caption(f"{len(ALERTS)} Alert(s) aktiv")
        for a in ALERTS:
            css  = "acrit" if a["level"] == "crit" else "awarn"
            icon = "🔴" if a["level"] == "crit" else "🟡"
            st.markdown(
                f'<div class="{css}"><strong>{icon} {a["title"]}</strong>'
                f'<br><small>{a["detail"]}</small></div>',
                unsafe_allow_html=True)

    st.divider()
    st.subheader("📄 Report exportieren")
    c1, c2 = st.columns(2)
    with c1:
        focus = st.selectbox("Fokus-Region", REGIONS + ["Alle"])
    with c2:
        html = ReportExporter().build_html(
            SCORES, DATA, ALERTS, focus, WORLD, WW)
        st.download_button(
            "📥  HTML-Report herunterladen", data=html,
            file_name=f"macro-report-{datetime.now().strftime('%Y-%m-%d')}.html",
            mime="text/html", use_container_width=True)
