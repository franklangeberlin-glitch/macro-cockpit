"""alerts.py — Regelbasiertes Alert-System"""
from modules.scoring import MacroScorer
scorer = MacroScorer()


class AlertEngine:
    def __init__(self, thresh_crit=35, thresh_warn=50):
        self.tc = thresh_crit
        self.tw = thresh_warn

    def evaluate(self, scores: dict, data: dict) -> list:
        al = []
        for r, s in scores.items():
            d = data.get(r, {})
            if s["total"] <= self.tc:
                al.append(dict(level="crit",
                    title=f"{r}: Gesamt-Score kritisch ({s['total']})",
                    detail=f"Phase: {scorer.phase(s['total'])}. Sofortige Beobachtung empfohlen."))
            elif s["total"] <= self.tw:
                al.append(dict(level="warn",
                    title=f"{r}: Erhöhtes Risiko (Score {s['total']})",
                    detail=f"Score unter Warnschwelle {self.tw}. Phase: {scorer.phase(s['total'])}."))
            if s["fiscal"] <= self.tc:
                al.append(dict(level="crit",
                    title=f"{r}: Fiskalstress kritisch ({s['fiscal']})",
                    detail="Sehr hohe Schuldenquote und/oder Haushaltsdefizit."))
            if s["exogenous"] <= self.tc:
                al.append(dict(level="crit",
                    title=f"{r}: Exogene Risiken akut ({s['exogenous']})",
                    detail="GPR-Index und/oder Rohstoffschocks auf kritischem Niveau."))
            elif s["exogenous"] <= self.tw:
                al.append(dict(level="warn",
                    title=f"{r}: Exogene Risiken erhöht ({s['exogenous']})",
                    detail="Geopolitische Spannungen oder Rohstoffpreisschock."))
            spread = d.get("yield_spread")
            if spread is not None and spread < 0:
                al.append(dict(level="warn",
                    title=f"{r}: Zinskurve invertiert ({spread:.2f} bp)",
                    detail="Historisch robustes Rezessionssignal 6–18 Monate voraus."))
            cpi = d.get("cpi_yoy")
            if cpi and cpi > 4.0:
                al.append(dict(level="warn",
                    title=f"{r}: CPI deutlich über Ziel ({cpi:.1f}%)",
                    detail="Restriktiver Zinsdruck begrenzt Wachstumsspielraum."))
            debt = d.get("debt_gdp")
            if debt and debt > 150:
                al.append(dict(level="crit",
                    title=f"{r}: Schuldenquote extrem hoch ({debt:.0f}% BIP)",
                    detail="Fiskalischer Handlungsspielraum stark eingeschränkt."))
        return al
