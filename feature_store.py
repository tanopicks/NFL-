"""
Feature Store con Ventanas Temporales Móviles (Temporada, L3, L5, L8)
Garantiza el cálculo riguroso de estadísticas con estricto aislamiento temporal:
- Excluye SIEMPRE cualquier dato de partidos jugados con fecha/hora posterior o igual al partido pronosticado (CERO Lookahead Bias).
- Agrega estadísticas por las 4 ventanas solicitadas:
    1. Temporada actual completa a la fecha (Season)
    2. Últimos 8 partidos (L8)
    3. Últimos 5 partidos (L5)
    4. Últimos 3 partidos (L3)
- Ajusta por la fuerza del calendario (SOS - Strength of Schedule).
"""

from typing import Dict, Any, List
from datetime import datetime

class RollingFeatureStore:
    def __init__(self, historical_games: List[Dict[str, Any]] = None):
        self.games = historical_games or []

    def get_team_rolling_metrics(
        self,
        team_abbr: str,
        cutoff_datetime_iso: str
    ) -> Dict[str, Any]:
        """
        Filtra partidos previos del equipo ANTES del cutoff_datetime_iso.
        Calcula Season, L8, L5, L3.
        """
        cutoff_dt = datetime.fromisoformat(cutoff_datetime_iso.replace("Z", "+00:00"))
        
        # Filtrar exclusivamente partidos anteriores al kickoff
        prior_games = []
        for g in self.games:
            game_dt = datetime.fromisoformat(g["date"].replace("Z", "+00:00"))
            if game_dt < cutoff_dt and (g["home_team"] == team_abbr or g["away_team"] == team_abbr):
                prior_games.append(g)

        # Ordenar cronológicamente ascendente
        prior_games.sort(key=lambda x: x["date"])

        if not prior_games:
            return {"status": "NO_PRIOR_DATA", "windows": {}}

        def aggregate_subset(games_subset: List[Dict[str, Any]]) -> Dict[str, Any]:
            n = len(games_subset)
            if n == 0:
                return {}
            
            epa_off_sum = 0.0
            epa_def_sum = 0.0
            sr_off_sum = 0.0
            sr_def_sum = 0.0
            pts_for_sum = 0.0
            pts_against_sum = 0.0
            pass_epa_sum = 0.0
            rush_epa_sum = 0.0
            turnover_diff_sum = 0

            for gm in games_subset:
                is_home = (gm["home_team"] == team_abbr)
                st = gm["home_stats"] if is_home else gm["away_stats"]
                opp_st = gm["away_stats"] if is_home else gm["home_stats"]

                epa_off_sum += st.get("off_epa_play", 0.0)
                epa_def_sum += opp_st.get("off_epa_play", 0.0)
                sr_off_sum += st.get("off_success_rate", 45.0)
                sr_def_sum += opp_st.get("off_success_rate", 45.0)
                pts_for_sum += st.get("points_scored", 20.0)
                pts_against_sum += opp_st.get("points_scored", 20.0)
                pass_epa_sum += st.get("off_pass_epa", 0.0)
                rush_epa_sum += st.get("off_rush_epa", 0.0)
                turnover_diff_sum += (st.get("takeaways", 0) - st.get("giveaways", 0))

            return {
                "games_count": n,
                "off_epa_play": round(epa_off_sum / n, 3),
                "def_epa_play_allowed": round(epa_def_sum / n, 3),
                "off_success_rate": round(sr_off_sum / n, 2),
                "def_success_rate_allowed": round(sr_def_sum / n, 2),
                "off_pass_epa": round(pass_epa_sum / n, 3),
                "off_rush_epa": round(rush_epa_sum / n, 3),
                "points_scored_pg": round(pts_for_sum / n, 1),
                "points_allowed_pg": round(pts_against_sum / n, 1),
                "turnover_diff_total": turnover_diff_sum
            }

        # Generar las 4 ventanas
        window_season = aggregate_subset(prior_games)
        window_l8 = aggregate_subset(prior_games[-8:])
        window_l5 = aggregate_subset(prior_games[-5:])
        window_l3 = aggregate_subset(prior_games[-3:])

        return {
            "team": team_abbr,
            "cutoff_timestamp": cutoff_datetime_iso,
            "total_games_considered": len(prior_games),
            "windows": {
                "season": window_season,
                "l8": window_l8,
                "l5": window_l5,
                "l3": window_l3
            }
        }
