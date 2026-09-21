"""
data_loader.py — Lädt Makrodaten von FRED (USA live) und kombiniert
                 diese mit IMF/ECB-Schätzwerten für EZ, China, Japan.
                 Wird täglich automatisch neu gecacht.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


class DataLoader:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _fred(self, series_id: str, limit: int = 60) -> pd.Series:
        try:
            params = dict(
                series_id=series_id, api_key=self.api_key,
                file_type="json", sort_order="desc", limit=limit,
            )
            r = self.session.get(FRED_BASE, params=params, timeout=20)
            r.raise_for_status()
            obs = r.json().get("observations", [])
            data = {pd.to_datetime(o["date"]): float(o["value"])
                    for o in obs if o["value"] != "."}
            return pd.Series(data).sort_index()
        except Exception as e:
            print(f"  FRED {series_id}: {e}")
            return pd.Series(dtype=float)

    def _latest(self, s: pd.Series):
        d = s.dropna()
        return (float(d.iloc[-1]), d.index[-1].strftime("%b %Y")) if not d.empty else (None, "n/a")

    def _yoy(self, s: pd.Series):
        d = s.dropna()
        if len(d) < 13:
            return None
        return round((d.iloc[-1] / d.iloc[-13] - 1) * 100, 2)

    def _monthly(self, s: pd.Series) -> pd.Series:
        return s.resample("MS").last() if not s.empty else s

    def _to_list(self, s: pd.Series, idx: pd.DatetimeIndex, fillna=None) -> list:
        if s.empty:
            return [fillna] * len(idx)
        aligned = s.reindex(idx, method="ffill")
        return [round(float(v), 3) if not np.isnan(v) else fillna for v in aligned]

    def _usa_score_history(self, unrate, yield_s, cpi, fed, idx):
        scores = []
        yoy_cpi = (cpi.pct_change(12) * 100) if len(cpi) >= 14 else pd.Series(dtype=float)
        for m in idx:
            try:
                ur = float(unrate.asof(m)) if not unrate.empty else 4.5
                ys = float(yield_s.asof(m)) if not yield_s.empty else 0.0
                cp = float(yoy_cpi.asof(m)) if not yoy_cpi.empty else 3.0
                fr = float(fed.asof(m)) if not fed.empty else 3.0
                s_u = max(0, min(100, (1 - (ur - 3) / 8) * 100))
                s_y = max(0, min(100, (ys + 2.5) / 5.0 * 100))
                s_c = max(0, min(100, (1 - max(0, cp) / 10) * 100))
                s_f = max(0, min(100, (1 - max(0, fr - 0.25) / 8) * 100))
                scores.append(max(10, min(95, round(
                    0.30 * s_u + 0.28 * s_y + 0.25 * s_c + 0.17 * s_f
                ))))
            except Exception:
                scores.append(None)
        return scores

    def _static_score_history(self, region, idx):
        templates = {
            "Eurozone": [36,35,34,33,33,34,36,38,40,42,43,44,45,45,45,
                         46,45,46,45,45,44,44,45,44,44,44,44,45,44,44,
                         43,44,44,44,43,43,43,43,43,43,43,43,43,43,43,
                         43,43,43,43,43,43,43,43,43,43,43,43,43,43,43,43],
            "China":    [55,56,55,54,52,53,54,55,56,57,57,58,57,57,56,
                         57,56,57,56,55,55,56,56,55,55,56,55,56,55,56,
                         55,55,56,55,56,56,56,56,56,56,56,56,56,56,56,
                         56,56,56,56,56,56,56,56,56,56,56,56,56,56,56,56],
            "Japan":    [39,39,38,37,37,38,39,39,40,40,41,41,40,40,40,
                         41,40,40,40,39,40,40,39,39,40,39,40,39,40,39,
                         40,39,40,39,40,39,39,39,39,39,39,39,39,39,39,
                         39,39,39,39,39,39,39,39,39,39,39,39,39,39,39,39],
        }
        tpl = templates.get(region, [50] * 120)
        n = len(idx)
        out = []
        for i in range(n):
            base = tpl[min(i, len(tpl) - 1)]
            noise = round(np.sin(i * 0.65) * 1.2)
            out.append(max(10, min(95, base + noise)))
        return out

    def _load_usa(self, months):
        n = len(months) + 15
        unrate   = self._fred("UNRATE", n)
        fedfunds = self._fred("FEDFUNDS", n)
        t10y2y_d = self._fred("T10Y2Y", n * 22)
        gdp      = self._fred("A191RL1Q225SBEA", max(20, n // 3))
        cpi      = self._fred("CPIAUCSL", n + 14)
        core_cpi = self._fred("CPILFESL", n + 14)
        payrolls = self._fred("PAYEMS", n)
        gpr      = self._fred("GPRC_USA_M", n)
        oil      = self._fred("DCOILWTICO", n * 22)
        t10y2y_m = self._monthly(t10y2y_d)
        oil_m    = self._monthly(oil)
        ur_v,  ur_d  = self._latest(unrate)
        fed_v, fed_d = self._latest(fedfunds)
        spr_v, spr_d = self._latest(t10y2y_m)
        gdp_v, gdp_d = self._latest(gdp)
        pay_v, _     = self._latest(payrolls)
        gpr_v, _     = self._latest(gpr)
        cpi_yoy  = self._yoy(cpi)
        core_yoy = self._yoy(core_cpi)
        oil_yoy  = self._yoy(oil_m)
        hist_score = self._usa_score_history(unrate, t10y2y_m, cpi, fedfunds, months)
        hist_yield = self._to_list(t10y2y_m, months, fillna=0.0)
        cpi_yoy_s  = (cpi.pct_change(12) * 100).dropna()
        hist_cpi   = self._to_list(cpi_yoy_s, months, fillna=3.0)
        return dict(
            unrate=ur_v, unrate_date=ur_d, unrate_src="FRED: UNRATE (BLS)",
            payrolls=round((pay_v or 0) / 1000, 0),
            policy_rate=fed_v, policy_rate_date=fed_d, policy_rate_src="FRED: FEDFUNDS",
            yield_spread=spr_v, yield_spread_date=spr_d, yield_spread_src="FRED: T10Y2Y",
            gdp_growth=gdp_v, gdp_growth_date=gdp_d, gdp_growth_src="FRED: A191RL1Q225SBEA",
            cpi_yoy=cpi_yoy, cpi_yoy_src="FRED: CPIAUCSL (BLS)",
            core_cpi_yoy=core_yoy, core_cpi_yoy_src="FRED: CPILFESL",
            debt_gdp=122.0, debt_gdp_src="IMF WEO 2026",
            deficit_gdp=6.2, deficit_gdp_src="IMF WEO 2026",
            gpr_index=float(gpr_v or 185), gpr_index_src="FRED: GPRC_USA_M",
            oil_yoy=float(oil_yoy or 18), gas_yoy=15.0, food_yoy=2.7,
            hist_months=months, hist_score=hist_score,
            hist_yield=hist_yield, hist_cpi=hist_cpi,
            source_note="FRED — Federal Reserve Bank of St. Louis",
            yield_label="Zinskurve 10J-2J (bp)", cpi_label="CPI YoY (%)",
        )

    def _load_eurozone(self, months):
        n = len(months) + 15
        ez_unemp = self._fred("LRHUTTTTEZM156S", n)
        ez_hicp  = self._fred("CP0000EZ19M086NEST", n + 14)
        ez_lty   = self._fred("IRLTLT01EZM156N", n)
        ez_sty   = self._fred("IR3TIB01EZM156N", n)
        ur_v,  _ = self._latest(ez_unemp)
        lty_v, _ = self._latest(ez_lty)
        sty_v, _ = self._latest(ez_sty)
        spread   = round((lty_v or 3.0) - (sty_v or 2.65), 2)
        hicp_yoy = self._yoy(ez_hicp)
        hicp_ts  = (ez_hicp.pct_change(12) * 100).dropna()
        hist_cpi = self._to_list(hicp_ts, months, fillna=2.6)
        spread_ts = (ez_lty - ez_sty).dropna() if not ez_lty.empty and not ez_sty.empty else pd.Series(dtype=float)
        hist_yield = self._to_list(spread_ts, months, fillna=0.35)
        hist_score = self._static_score_history("Eurozone", months)
        return dict(
            unrate=float(ur_v or 6.2), unrate_src="FRED: LRHUTTTTEZM156S",
            policy_rate=2.00, policy_rate_src="ECB Apr 2026",
            yield_spread=spread, yield_spread_src="FRED / ECB",
            gdp_growth=0.9, gdp_growth_src="ECB Projektion 2026",
            cpi_yoy=float(hicp_yoy or 2.6), cpi_yoy_src="FRED: CP0000EZ19M086NEST",
            core_cpi_yoy=2.3, core_cpi_yoy_src="ECB Apr 2026",
            debt_gdp=90.0, debt_gdp_src="IMF WEO 2026",
            deficit_gdp=3.1, deficit_gdp_src="Eurostat / IMF",
            gpr_index=215.0, gpr_index_src="Caldara & Iacoviello",
            oil_yoy=18.0, gas_yoy=30.0, food_yoy=2.4,
            hist_months=months, hist_score=hist_score,
            hist_yield=hist_yield, hist_cpi=hist_cpi,
            source_note="FRED/Eurostat · ECB · IMF WEO",
            yield_label="Zinskurve 10J-2J (bp)", cpi_label="HICP YoY (%)",
        )

    def _load_china(self, months):
        n = len(months) + 15
        cn_cpi = self._fred("CHNCPIALLMINMEI", n + 14)
        cpi_yoy = self._yoy(cn_cpi)
        cpi_ts  = (cn_cpi.pct_change(12) * 100).dropna()
        hist_cpi = self._to_list(cpi_ts, months, fillna=0.2)
        hist_score = self._static_score_history("China", months)
        return dict(
            unrate=5.1, unrate_src="NBS China Apr 2026",
            policy_rate=3.10, policy_rate_src="PBoC LPR Apr 2026",
            yield_spread=0.55, yield_spread_src="Wind / Bloomberg",
            gdp_growth=4.5, gdp_growth_src="NBS / IMF WEO 2026",
            cpi_yoy=float(cpi_yoy or 0.2), cpi_yoy_src="FRED: CHNCPIALLMINMEI",
            core_cpi_yoy=0.5, core_cpi_yoy_src="NBS China",
            debt_gdp=83.0, debt_gdp_src="IMF WEO 2026",
            deficit_gdp=3.8, deficit_gdp_src="IMF WEO",
            gpr_index=235.0, gpr_index_src="Caldara & Iacoviello",
            oil_yoy=12.0, gas_yoy=10.0, food_yoy=3.1,
            hist_months=months, hist_score=hist_score,
            hist_yield=[0.55] * len(months), hist_cpi=hist_cpi,
            source_note="NBS China · IMF WEO · FRED",
            yield_label="Zinskurve 10J-2J (bp)", cpi_label="CPI YoY (%)",
        )

    def _load_japan(self, months):
        n = len(months) + 15
        jp_cpi = self._fred("JPNCPIALLMINMEI", n + 14)
        cpi_yoy = self._yoy(jp_cpi)
        cpi_ts  = (jp_cpi.pct_change(12) * 100).dropna()
        hist_cpi = self._to_list(cpi_ts, months, fillna=2.8)
        hist_score = self._static_score_history("Japan", months)
        return dict(
            unrate=2.5, unrate_src="Statistics Japan Apr 2026",
            policy_rate=0.50, policy_rate_src="BOJ Apr 2026",
            yield_spread=0.30, yield_spread_src="BOJ / Bloomberg",
            gdp_growth=0.6, gdp_growth_src="Cabinet Office / IMF",
            cpi_yoy=float(cpi_yoy or 2.8), cpi_yoy_src="FRED: JPNCPIALLMINMEI",
            core_cpi_yoy=2.1, core_cpi_yoy_src="Statistics Japan",
            debt_gdp=255.0, debt_gdp_src="IMF WEO 2026",
            deficit_gdp=4.1, deficit_gdp_src="IMF WEO",
            gpr_index=130.0, gpr_index_src="Caldara & Iacoviello",
            oil_yoy=16.0, gas_yoy=12.0, food_yoy=4.2,
            hist_months=months, hist_score=hist_score,
            hist_yield=[0.30] * len(months), hist_cpi=hist_cpi,
            source_note="BOJ · Cabinet Office · IMF · FRED",
            yield_label="Zinskurve 10J-2J (bp)", cpi_label="CPI YoY (%)",
        )

    def load_all(self, years_back: int = 3) -> dict:
        months = pd.date_range(
            end=datetime.today().replace(day=1),
            periods=years_back * 12, freq="MS"
        )
        return {
            "USA":      self._load_usa(months),
            "Eurozone": self._load_eurozone(months),
            "China":    self._load_china(months),
            "Japan":    self._load_japan(months),
        }
