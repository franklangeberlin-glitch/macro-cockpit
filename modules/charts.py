"""
charts.py — Alle Plotly-Visualisierungen für den Macro Cockpit
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from modules.scoring import MacroScorer

scorer = MacroScorer()

REGION_COLORS = {"USA": "#378add", "Eurozone": "#1d9e75",
                 "China": "#e24b4a", "Japan": "#ef9f27"}
GRID = "rgba(255,255,255,0.06)"
TXT  = "#aaaaaa"
BG   = "rgba(0,0,0,0)"


def _base_layout(fig, height=340, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#cccccc")),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=TXT, size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        margin=dict(l=8, r=8, t=36, b=8),
        hovermode="x unified",
        height=height,
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False,
                     tickfont=dict(size=10))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False,
                     tickfont=dict(size=10))
    return fig


def _phase_bands(fig, row=1, col=1):
    for lo, hi, rgba, lbl in [
        (0, 20,  "rgba(226,75,74,0.10)",   "Depression"),
        (21, 40, "rgba(239,159,39,0.10)",  "Rezession"),
        (41, 55, "rgba(55,138,221,0.08)",  "Erholung"),
        (56, 70, "rgba(99,153,34,0.08)",   "Aufschwung"),
        (71, 85, "rgba(29,158,117,0.08)",  "Späte Expansion"),
        (86,100, "rgba(29,158,117,0.14)",  "Peak"),
    ]:
        fig.add_hrect(
            y0=lo, y1=hi, fillcolor=rgba, line_width=0,
            row=row, col=col,
            annotation_text=lbl,
            annotation_position="right",
            annotation_font_size=8,
            annotation_font_color="rgba(200,200,200,0.35)",
        )


def _hex_rgba(hex_col: str, alpha: float) -> str:
    h = hex_col.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


class ChartBuilder:

    def region_charts(self, d: dict, region: str) -> go.Figure:
        col = REGION_COLORS.get(region, "#378add")
        months = list(d.get("hist_months",
                     pd.date_range(end=pd.Timestamp.today(),
                                   periods=36, freq="MS")))
        hist_s = d.get("hist_score", [])
        hist_y = d.get("hist_yield", [])
        hist_c = d.get("hist_cpi",   [])
        y_lbl  = d.get("yield_label", "Zinskurve 10J-2J (bp)")
        c_lbl  = d.get("cpi_label",   "CPI YoY (%)")

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"📈  Score-Verlauf — {region}",
                f"📉  Zinskurve & Inflation — {region}",
            ),
            horizontal_spacing=0.09,
        )

        if hist_s:
            n = min(len(months), len(hist_s))
            x, y = months[:n], hist_s[:n]
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines", name="Macro-Score",
                line=dict(color=col, width=2),
                fill="tozeroy",
                fillcolor=_hex_rgba(col, 0.08),
                hovertemplate="%{y:.0f}<extra></extra>",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=[x[-1]], y=[y[-1]], mode="markers+text",
                marker=dict(color=col, size=9),
                text=[f"  {y[-1]}"],
                textposition="middle right",
                textfont=dict(color=col, size=12),
                showlegend=False,
                hoverinfo="skip",
            ), row=1, col=1)

        _phase_bands(fig, 1, 1)
        fig.update_yaxes(range=[0, 100], title_text="Score (0–100)", row=1, col=1)

        if hist_y:
            n = min(len(months), len(hist_y))
            fig.add_trace(go.Scatter(
                x=months[:n], y=hist_y[:n], name=y_lbl,
                line=dict(color=col, width=1.8),
                hovertemplate="%{y:.2f} bp<extra></extra>",
            ), row=1, col=2)
            fig.add_hline(y=0, line_dash="dot",
                          line_color="rgba(255,90,90,0.5)", line_width=1,
                          annotation_text="Inversion",
                          annotation_font_size=8,
                          annotation_font_color="rgba(255,90,90,0.55)",
                          row=1, col=2)

        if hist_c:
            n = min(len(months), len(hist_c))
            cpi_col = "#e24b4a" if region != "China" else "#7f77dd"
            fig.add_trace(go.Scatter(
                x=months[:n], y=hist_c[:n], name=c_lbl,
                line=dict(color=cpi_col, width=1.5, dash="dot"),
                hovertemplate="%{y:.1f}%<extra></extra>",
                yaxis="y4",
            ), row=1, col=2)

        fig.update_layout(
            yaxis4=dict(overlaying="y2", side="right",
                        title="CPI %", showgrid=False,
                        tickfont=dict(size=10))
        )
        )
        fig.update_yaxes(title_text="Spread bp", row=1, col=2)
        _base_layout(fig, height=330)
        return fig

    def comparison(self, scores: dict, regions: list) -> go.Figure:
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Radar — Block-Scores", "Gesamt-Score Vergleich"),
            specs=[[{"type": "polar"}, {"type": "xy"}]],
            horizontal_spacing=0.12,
        )
        cats = ["Konjunktur", "Frühindikatoren", "Inflation/Zinsen",
                "Fiskalstress", "Exogene Risiken"]
        keys = ["growth", "leading", "policy", "fiscal", "exogenous"]

        for r in regions:
            s = scores[r]
            v = [s[k] for k in keys] + [s[keys[0]]]
            c = REGION_COLORS.get(r, "#888")
            fig.add_trace(go.Scatterpolar(
                r=v, theta=cats + [cats[0]],
                fill="toself", name=r,
                line=dict(color=c, width=1.5),
                fillcolor=_hex_rgba(c, 0.10),
                hovertemplate="%{theta}: %{r:.0f}<extra>" + r + "</extra>",
            ), row=1, col=1)

        totals = [scores[r]["total"] for r in regions]
        colors = [REGION_COLORS.get(r, "#888") for r in regions]
        fig.add_trace(go.Bar(
            x=regions, y=totals, marker_color=colors,
            name="Gesamt",
            text=[f"{s}<br>{scorer.phase(s)}" for s in totals],
            textposition="outside", textfont=dict(size=11),
            showlegend=False,
            hovertemplate="%{x}: %{y}<extra></extra>",
        ), row=1, col=2)

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100],
                                tickfont=dict(size=9), gridcolor=GRID),
                angularaxis=dict(tickfont=dict(size=10)),
                bgcolor=BG,
            )
        )
        fig.update_yaxes(range=[0, 110], row=1, col=2)
        _base_layout(fig, height=390)
        return fig

    def all_regions_trend(self, data: dict) -> go.Figure:
        fig = go.Figure()
        for region, col in REGION_COLORS.items():
            d = data.get(region, {})
            months = list(d.get("hist_months", []))
            hist   = d.get("hist_score", [])
            if not hist:
                continue
            n = min(len(months), len(hist))
            fig.add_trace(go.Scatter(
                x=months[:n], y=hist[:n], mode="lines", name=region,
                line=dict(color=col, width=2),
                hovertemplate=f"{region}: %{{y:.0f}}<extra></extra>",
            ))
        _phase_bands(fig)
        fig.update_yaxes(range=[0, 100], title_text="Score (0–100)")
        _base_layout(fig, height=320, title="Score-Verlauf — alle Regionen")
        return fig

    def weight_donut(self) -> go.Figure:
        labels = ["Konjunktur 30%", "Frühindikatoren 25%",
                  "Inflation 15%", "Fiskalstress 15%", "Exogene 15%"]
        values = [30, 25, 15, 15, 15]
        colors = ["#378add", "#1d9e75", "#ef9f27", "#e24b4a", "#7f77dd"]
        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker=dict(colors=colors, line=dict(color="#111", width=2)),
            hole=0.55, textinfo="label+percent",
            textfont=dict(size=10), hoverinfo="label+value",
        ))
        _base_layout(fig, height=260)
        fig.update_layout(showlegend=False)
        return fig
