"""
scoring.py — Gewichtetes 0–100 Makro-Scoring-Modell
 
Blöcke:
  Konjunktur        30 %
  Frühindikatoren   25 %
  Inflation/Zinsen  15 %
  Fiskalstress      15 %
  Exogene Risiken   15 %
"""
import numpy as np
 
 
def _clip(v, lo=0, hi=100):
    return int(max(lo, min(hi, v)))
 
 
def lin(x, xmin, xmax, rev=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 50
    s = (x - xmin) / (xmax - xmin) * 100
    return _clip(100 - s if rev else s)
 
 
class MacroScorer:
    BLOCK_W = dict(growth=0.30, leading=0.25, policy=0.15,
                   fiscal=0.15, exogenous=0.15)
 
    def compute(self, d: dict) -> dict:
        i = {}
        # Konjunktur
        i["gdp_s"]      = lin(d.get("gdp_growth"),  -3,   6)
        i["unrate_s"]   = lin(d.get("unrate"),        3,  11, rev=True)
        i["payroll_s"]  = lin(d.get("payrolls"),    -50, 400)
        # Frühindikatoren
        i["yield_s"]    = lin(d.get("yield_spread"), -2.0, 2.5)
        # Inflation
        i["cpi_s"]      = lin(d.get("cpi_yoy"),       0,   9, rev=True)
        i["core_s"]     = lin(d.get("core_cpi_yoy"),  0,   7, rev=True)
        rate = d.get("policy_rate") or 3.0
        cpi  = d.get("cpi_yoy")    or 3.0
        i["realrate_s"] = lin(rate - cpi, -4, 6, rev=True)
        # Fiskal
        i["debt_s"]     = lin(d.get("debt_gdp"),    20, 220, rev=True)
        i["deficit_s"]  = lin(d.get("deficit_gdp"), -2,  12, rev=True)
        # Exogen
        i["gpr_s"]      = lin(d.get("gpr_index"),    0, 350, rev=True)
        i["oil_s"]      = lin(d.get("oil_yoy"),    -30,  80, rev=True)
        i["gas_s"]      = lin(d.get("gas_yoy"),    -50, 150, rev=True)
        i["food_s"]     = lin(d.get("food_yoy"),    -5,  15, rev=True)
 
        growth    = _clip(0.40*i["gdp_s"] + 0.35*i["unrate_s"] + 0.15*i["payroll_s"] + 0.10*i["gdp_s"])
        leading   = _clip(0.50*i["yield_s"] + 0.30*i["gdp_s"]  + 0.20*i["unrate_s"])
        policy    = _clip(0.40*i["cpi_s"]   + 0.35*i["core_s"] + 0.25*i["realrate_s"])
        fiscal    = _clip(0.55*i["debt_s"]  + 0.45*i["deficit_s"])
        exogenous = _clip(0.40*i["gpr_s"]   + 0.30*i["oil_s"]  + 0.20*i["gas_s"] + 0.10*i["food_s"])
        total     = _clip(
            self.BLOCK_W["growth"]    * growth +
            self.BLOCK_W["leading"]   * leading +
            self.BLOCK_W["policy"]    * policy +
            self.BLOCK_W["fiscal"]    * fiscal +
            self.BLOCK_W["exogenous"] * exogenous
        )
        return dict(total=total, growth=growth, leading=leading,
                    policy=policy, fiscal=fiscal, exogenous=exogenous,
                    indicators=i)
 
    @staticmethod
    def phase(s: float) -> str:
        if s <= 20: return "Depression"
        if s <= 40: return "Rezession"
        if s <= 55: return "Erholung"
        if s <= 70: return "Aufschwung"
        if s <= 85: return "Späte Expansion"
        return "Peak / Überhitzung"
 
    @staticmethod
    def color(s: float) -> str:
        if s <= 30: return "#e24b4a"
        if s <= 45: return "#ef9f27"
        if s <= 62: return "#378add"
        if s <= 78: return "#639922"
        return "#1d9e75"
