"""
NFL Official Injury Report Parser
Extrae y cataloga el reporte oficial de lesiones por equipo.
Métricas y atributos:
- Estatus oficial del partido: OUT, DOUBTFUL, QUESTIONABLE, ACTIVE
- Estatus de entrenamientos durante la semana: DNP (Did Not Participate), LP (Limited Participant), FP (Full Participant)
- Posiciones clave cubiertas:
  * QB (Titular y Suplente)
  * OL (LT, LG, C, RG, RT)
  * Receptores y corredores (WR1, WR2, WR-Slot, TE1, RB1, RB2)
  * Defensivos clave (Edge Rushers, DL interior, MLB, CB1, Safety)
- Metadatos: timestamp de actualización oficial y fuente.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

SOURCE_URL_INJURIES = "https://www.nfl.com/injuries/"
SOURCE_NAME_INJURIES = "NFL Official Injury Report"

class InjuryReport:
    def __init__(self, team_abbr: str, last_updated: str = None):
        self.team = team_abbr
        self.source = SOURCE_NAME_INJURIES
        self.source_url = SOURCE_URL_INJURIES
        self.last_updated = last_updated or datetime.now(timezone.utc).isoformat()
        self.players: List[Dict[str, Any]] = []

    def add_player(
        self,
        name: str,
        position: str,
        game_status: str,  # OUT, DOUBTFUL, QUESTIONABLE, CLEARED
        practice_status: str,  # DNP, LP, FP
        injury_type: str,
        is_starter: bool = True,
        tier_impact: str = "HIGH"  # HIGH (QB, LT, Edge, CB1), MEDIUM (WR2, C, DT), LOW (depth)
    ):
        self.players.append({
            "name": name,
            "position": position,
            "game_status": game_status.upper(),
            "practice_status": practice_status.upper(),
            "injury_type": injury_type,
            "is_starter": is_starter,
            "tier_impact": tier_impact.upper()
        })

    def get_offensive_line_health(self) -> Dict[str, Any]:
        """Calcula el porcentaje de salud y titulares ausentes en la línea ofensiva."""
        ol_positions = {"LT", "LG", "C", "RG", "RT", "OT", "OG"}
        ol_injuries = [p for p in self.players if p["position"] in ol_positions and p["is_starter"]]
        out_or_doubtful = [p for p in ol_injuries if p["game_status"] in ["OUT", "DOUBTFUL"]]
        questionable = [p for p in ol_injuries if p["game_status"] == "QUESTIONABLE"]
        
        # Penalización estimada sobre PBWR/RBWR
        penalty = (len(out_or_doubtful) * 1.5) + (len(questionable) * 0.6)
        return {
            "ol_starters_out": [p["name"] + f" ({p['position']})" for p in out_or_doubtful],
            "ol_starters_questionable": [p["name"] + f" ({p['position']})" for p in questionable],
            "ol_penalty_points": round(penalty, 2),
            "ol_status": "CRITICAL" if len(out_or_doubtful) >= 2 else ("IMPAIRED" if len(out_or_doubtful) == 1 else "HEALTHY")
        }

    def get_qb_health_status(self) -> Dict[str, Any]:
        """Evalúa el estado del QB titular."""
        qb_injuries = [p for p in self.players if p["position"] == "QB" and p["is_starter"]]
        if not qb_injuries:
            return {"status": "HEALTHY", "name": "Titular en plenitud", "penalty": 0.0}
        
        qb = qb_injuries[0]
        if qb["game_status"] in ["OUT", "DOUBTFUL"]:
            return {"status": "OUT", "name": qb["name"], "penalty": 4.5, "details": qb}
        elif qb["game_status"] == "QUESTIONABLE":
            return {"status": "QUESTIONABLE", "name": qb["name"], "penalty": 1.8, "details": qb}
        return {"status": "PROBABLE/CLEARED", "name": qb["name"], "penalty": 0.0, "details": qb}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_url": self.source_url,
            "extracted_at": self.last_updated,
            "team": self.team,
            "players": self.players,
            "ol_health": self.get_offensive_line_health(),
            "qb_health": self.get_qb_health_status()
        }
