"""
Simulation Model & True Win Probability Estimator
Modela el resultado del partido mediante simulación estocástica y distribuciones estadísticas:
- Integra las fuerzas ofensivas/defensivas y ajustes contextuales.
- Realiza 20,000 iteraciones considerando la varianza real de puntos por partido de la NFL (~9.2 - 9.8 std).
- Genera:
  * Probabilidad pura estimada de victoria (Home / Away Win Prob %)
  * Puntos proyectados de cada equipo
  * Spread justo proyectado
  * Total de puntos justo
"""

import math
import random
from typing import Dict, Any, Tuple

class NFLSimulationModel:
    @classmethod
    def simulate_game(
        cls,
        home_team_name: str,
        away_team_name: str,
        home_matchup_eval: Dict[str, Any],
        away_matchup_eval: Dict[str, Any],
        context_eval: Dict[str, Any],
        iterations: int = 25000,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        Calcula probabilidades puras de victoria para ambos equipos.
        """
        random.seed(random_seed)

        home_str = home_matchup_eval["composite_offensive_strength"]
        away_str = away_matchup_eval["composite_offensive_strength"]

        # Base de anotación promedio de la liga moderna (~21.8 puntos por equipo)
        league_base_pts = 21.8
        pts_scale = 0.30

        # Puntos base esperados antes de contexto
        raw_home_pts = league_base_pts + ((home_str - 50.0) * pts_scale)
        raw_away_pts = league_base_pts + ((away_str - 50.0) * pts_scale)

        # Aplicar ajustes de contexto
        home_adv = context_eval.get("net_home_advantage_points", 1.5)
        weather_drag = context_eval.get("weather_drag_points", 0.0)
        scoring_mult = context_eval.get("scoring_multiplier", 1.0)

        mean_home = (raw_home_pts + (home_adv / 2.0) - (weather_drag / 2.0)) * scoring_mult
        mean_away = (raw_away_pts - (home_adv / 2.0) - (weather_drag / 2.0)) * scoring_mult

        # Simulación de Monte Carlo
        home_wins = 0
        away_wins = 0
        ties = 0

        # Varianza de anotación NFL: desviación estándar ~9.5
        nfl_std = 9.5

        for _ in range(iterations):
            sim_h = random.gauss(mean_home, nfl_std)
            sim_a = random.gauss(mean_away, nfl_std)

            # En caso de empate en tiempo reglamentario, simulación de overtime (53% posesión / ventaja)
            if abs(sim_h - sim_a) < 0.1:
                if random.random() < 0.52:
                    home_wins += 1
                else:
                    away_wins += 1
            elif sim_h > sim_a:
                home_wins += 1
            else:
                away_wins += 1

        p_home = home_wins / iterations
        p_away = away_wins / iterations

        fair_spread = round(mean_away - mean_home, 1)  # Negativo = Home favorito
        fair_total = round(mean_home + mean_away, 1)

        return {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "projected_scores": {
                "home": round(mean_home, 1),
                "away": round(mean_away, 1),
                "display": f"{away_team_name} {mean_away:.1f} @ {home_team_name} {mean_home:.1f}"
            },
            "win_probabilities": {
                "home": round(p_home * 100, 2),
                "away": round(p_away * 100, 2),
                "home_raw": round(p_home, 4),
                "away_raw": round(p_away, 4)
            },
            "fair_spread_home": fair_spread,
            "fair_total": fair_total,
            "simulation_iterations": iterations
        }
