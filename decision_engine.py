"""
Decision Engine & Conservative Value Filter (+EV)
Aplica los criterios estrictos y conservadores:
1. Calcula Cuota Justa (Fair Odds = 1 / P_estimada)
2. Compara con la Mejor Cuota Disponible en el mercado y la Probabilidad Implícita Sin Margen (No-Vig)
3. Estima la Ventaja Real:
    EV = (P_estimada * Cuota_disponible) - 1
    Edge_pct = (P_estimada - P_no_vig) * 100
4. Regla Antifavoritismo:
    Bajo NINGUNA circunstancia se aprueba una apuesta solo por tener alta probabilidad de ganar.
    Requiere EV positivo >= umbral conservador (ej: >= 3.5%) y margen de seguridad sobre la cuota justa.
5. Emite la decisión categórica:
    - APUESTA CANDIDATA
    - ESPERAR
    - DEJAR PASAR
6. Detalla los factores a favor y las incertidumbres de lesiones.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from config.settings import CONSERVATIVE_CRITERIA

class DecisionEngine:
    @classmethod
    def evaluate_game_value(
        cls,
        sim_result: Dict[str, Any],
        market_summary: Dict[str, Any],
        home_matchup: Dict[str, Any],
        away_matchup: Dict[str, Any],
        home_injuries: Dict[str, Any],
        away_injuries: Dict[str, Any],
        is_data_complete: bool = True,
        incomplete_reasons: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calcula el valor esperado de cada lado y emite el dictamen formal.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # Si los datos no están 100% completos, dictamen categórico obligatorio
        if not is_data_complete:
            return {
                "decision": "PENDIENTE",
                "decision_label": "PENDIENTE (DATOS INCOMPLETOS)",
                "reason": "El partido no cuenta con el 100% de datos confirmados o falta reporte oficial.",
                "pending_reasons": incomplete_reasons or ["Faltan métricas obligatorias"],
                "updated_at": now_iso,
                "candidate_bets": []
            }

        p_home = sim_result["win_probabilities"]["home_raw"]
        p_away = sim_result["win_probabilities"]["away_raw"]

        fair_odds_home = round(1.0 / p_home, 3) if p_home > 0 else 999.0
        fair_odds_away = round(1.0 / p_away, 3) if p_away > 0 else 999.0

        best_odds = market_summary.get("best_odds", {})
        consensus_nv = market_summary.get("consensus_no_vig_prob", {})

        home_market_odds = best_odds.get("home", {}).get("odds_decimal", 1.90)
        away_market_odds = best_odds.get("away", {}).get("odds_decimal", 1.90)

        home_nv_prob = consensus_nv.get("home", (1.0 / home_market_odds) * 100) / 100.0
        away_nv_prob = consensus_nv.get("away", (1.0 / away_market_odds) * 100) / 100.0

        # Cálculo de Valor Esperado (EV) y Edge porcentual
        ev_home = round(((p_home * home_market_odds) - 1.0) * 100, 2)
        ev_away = round(((p_away * away_market_odds) - 1.0) * 100, 2)

        edge_home_pts = round((p_home - home_nv_prob) * 100, 2)
        edge_away_pts = round((p_away - away_nv_prob) * 100, 2)

        # Criterios de filtro conservador
        min_ev = CONSERVATIVE_CRITERIA["min_ev_edge_pct"]
        min_odds = CONSERVATIVE_CRITERIA["min_odds"]
        max_odds = CONSERVATIVE_CRITERIA["max_odds"]
        margin_sec = 1.0 + (CONSERVATIVE_CRITERIA["margin_of_safety_pct"] / 100.0)

        # Evaluar lesiones críticas en duda (si hay dudas en QB o múltiples en OL -> ESPERAR)
        home_qb_status = home_injuries.get("qb_health", {}).get("status", "HEALTHY")
        away_qb_status = away_injuries.get("qb_health", {}).get("status", "HEALTHY")
        home_ol_crit = home_injuries.get("ol_health", {}).get("ol_status") == "CRITICAL"
        away_ol_crit = away_injuries.get("ol_health", {}).get("ol_status") == "CRITICAL"

        has_critical_doubt = (
            home_qb_status == "QUESTIONABLE" or
            away_qb_status == "QUESTIONABLE" or
            home_ol_crit or away_ol_crit
        )

        decisions = []
        for team_type, team_name, prob, fair_odd, mkt_odd, ev, edge, qb_st, opp_qb_st in [
            ("HOME", sim_result["home_team"], p_home, fair_odds_home, home_market_odds, ev_home, edge_home_pts, home_qb_status, away_qb_status),
            ("AWAY", sim_result["away_team"], p_away, fair_odds_away, away_market_odds, ev_away, edge_away_pts, away_qb_status, home_qb_status)
        ]:
            # Margen de seguridad: la cuota de mercado debe superar la cuota justa por un margen
            meets_margin = mkt_odd >= (fair_odd * margin_sec)
            odds_in_range = min_odds <= mkt_odd <= max_odds
            ev_qualifies = ev >= min_ev

            if ev_qualifies and meets_margin and odds_in_range:
                if has_critical_doubt:
                    status = "ESPERAR"
                    reason = f"Existe +EV ({ev}%), pero hay incertidumbre de lesiones clave pendientes de confirmación."
                else:
                    status = "APUESTA CANDIDATA"
                    reason = f"Cumple todos los criterios conservadores: EV +{ev}%, cuota {mkt_odd} superior a cuota justa {fair_odd} con margen de seguridad."
            elif ev > 0.0:
                status = "DEJAR PASAR"
                reason = f"Valor esperado marginal (+{ev}%) insuficiente para superar el umbral de varianza ({min_ev}% mín requerido)."
            else:
                status = "DEJAR PASAR"
                reason = f"Sin valor esperado frente al mercado (EV: {ev}%). Cuota ofrecida {mkt_odd} por debajo de la cuota justa requerida {fair_odd}."

            decisions.append({
                "side": team_type,
                "team": team_name,
                "estimated_prob_pct": round(prob * 100, 2),
                "fair_odds": fair_odd,
                "market_odds": mkt_odd,
                "no_vig_market_prob_pct": round((home_nv_prob if team_type == "HOME" else away_nv_prob) * 100, 2),
                "expected_value_ev_pct": ev,
                "market_edge_pct": edge,
                "decision": status,
                "decision_reason": reason,
                "sportsbook": best_odds.get(team_type.lower(), {}).get("sportsbook", "Consenso")
            })

        # Decisión global del partido
        candidates = [d for d in decisions if d["decision"] == "APUESTA CANDIDATA"]
        waits = [d for d in decisions if d["decision"] == "ESPERAR"]

        if candidates:
            global_dec = "APUESTA CANDIDATA"
        elif waits:
            global_dec = "ESPERAR"
        else:
            global_dec = "DEJAR PASAR"

        # Factores estadísticos destacados
        factors_home = [
            f"Fuerza combinada: {home_matchup['composite_offensive_strength']} pts",
            f"Diferencial EPA pase: {home_matchup['key_factors']['air_epa_diff']:+.3f}",
            f"Diferencial Success Rate: {home_matchup['key_factors']['sr_diff']:+.1f}%"
        ]
        factors_away = [
            f"Fuerza combinada: {away_matchup['composite_offensive_strength']} pts",
            f"Diferencial EPA pase: {away_matchup['key_factors']['air_epa_diff']:+.3f}",
            f"Diferencial Success Rate: {away_matchup['key_factors']['sr_diff']:+.1f}%"
        ]

        return {
            "game_id": sim_result.get("game_id", f"{sim_result['away_team']}@{sim_result['home_team']}"),
            "home_team": sim_result["home_team"],
            "away_team": sim_result["away_team"],
            "global_decision": global_dec,
            "projected_score": sim_result["projected_scores"]["display"],
            "fair_spread": sim_result["fair_spread_home"],
            "fair_total": sim_result["fair_total"],
            "sides_analysis": decisions,
            "statistical_factors": {
                "favoring_home": factors_home,
                "favoring_away": factors_away
            },
            "injuries_and_uncertainties": {
                "home_qb": home_injuries.get("qb_health", {}).get("status_note", home_qb_status),
                "away_qb": away_injuries.get("qb_health", {}).get("status_note", away_qb_status),
                "home_ol": home_injuries.get("ol_health", {}).get("ol_status", "HEALTHY"),
                "away_ol": away_injuries.get("ol_health", {}).get("ol_status", "HEALTHY")
            },
            "updated_at": now_iso
        }
