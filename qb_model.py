"""
Submodelo de Quarterbacks (QB Model)
Evalúa al mariscal de campo titular y calcula el Downgrade Delta si existe lesión o duda:
Métricas ponderadas:
- EPA por jugada de pase (dropback EPA)
- CPOE (Completion Percentage Over Expected)
- Passer Rating general y Rating bajo presión
- Yardas de pase, TD%, INT% y Fumbles perdidos
- Tasa de sacks (Sack%)
- Reemplazo y nivel del QB2
"""

from typing import Dict, Any

class QBModel:
    @staticmethod
    def _normalize(val: float, min_val: float, max_val: float) -> float:
        return max(0.0, min(100.0, ((val - min_val) / (max_val - min_val)) * 100.0))

    @classmethod
    def evaluate_qb(cls, qb_data: Dict[str, Any], injury_status: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calcula el rating cuantificado del QB (0 a 100) y el impacto de su disponibilidad.
        """
        epa = qb_data.get("epa_dropback", 0.0)
        cpoe = qb_data.get("cpoe", 0.0)
        rating = qb_data.get("passer_rating", 85.0)
        press_rating = qb_data.get("pass_rating_under_pressure", 65.0)
        sack_pct = qb_data.get("sack_pct", 7.0)
        tds = qb_data.get("touchdowns", 15)
        ints = qb_data.get("interceptions", 8)
        fumbles = qb_data.get("fumbles_lost", 2)
        
        # Puntuaciones normalizadas
        s_epa = cls._normalize(epa, -0.20, 0.40) * 0.25
        s_cpoe = cls._normalize(cpoe, -7.0, 9.0) * 0.20
        s_rating = cls._normalize(rating, 60.0, 115.0) * 0.15
        s_press = cls._normalize(press_rating, 40.0, 95.0) * 0.15
        s_sack = cls._normalize(14.0 - sack_pct, 4.0, 14.0) * 0.10
        s_ball_sec = cls._normalize(10.0 - (ints * 0.8 + fumbles * 0.5), 0.0, 10.0) * 0.15

        base_qb_score = round(s_epa + s_cpoe + s_rating + s_press + s_sack + s_ball_sec, 2)

        # Ajuste por lesión o estatus
        effective_score = base_qb_score
        penalty_pts = 0.0
        downgrade_note = "QB titular al 100%"

        if injury_status:
            stat = injury_status.get("status", "HEALTHY")
            if stat in ["OUT", "DOUBTFUL"]:
                downgrade_epa = qb_data.get("backup_downgrade_epa", -0.18)
                penalty_pts = abs(downgrade_epa) * 25.0
                effective_score = max(20.0, base_qb_score - penalty_pts)
                downgrade_note = f"QB titular no jugará. Inicia {qb_data.get('backup_name')}. Penalización estimada: -{penalty_pts:.1f} pts de rating."
            elif stat == "QUESTIONABLE":
                penalty_pts = 8.0
                effective_score = max(25.0, base_qb_score - penalty_pts)
                downgrade_note = f"QB titular en duda ({injury_status.get('name')}). Penalización de incertidumbre: -{penalty_pts:.1f} pts."

        return {
            "qb_name": qb_data.get("starter_name"),
            "base_rating": base_qb_score,
            "effective_rating": round(effective_score, 2),
            "penalty_applied": round(penalty_pts, 2),
            "status_note": downgrade_note,
            "metrics": {
                "epa_dropback": epa,
                "cpoe": cpoe,
                "passer_rating": rating,
                "under_pressure_rating": press_rating,
                "sack_pct": sack_pct,
                "ball_security_penalties": (ints + fumbles)
            }
        }
