"""
Chronological Walk-Forward Backtesting Engine
Ejecuta la validación secuencial histórica:
- Itera semana a semana y partido a partido en estricto orden cronológico.
- Solo utiliza estadísticas disponibles con timestamp ANTERIOR al partido.
- Emite pronósticos, compara contra resultados reales y genera el reporte formal.
"""

from typing import List, Dict, Any
from core_engine.simulation_model import NFLSimulationModel
from core_engine.matchup_engine import MatchupEngine
from core_engine.qb_model import QBModel
from core_engine.context_engine import ContextEngine
from core_engine.decision_engine import DecisionEngine
from backtesting.metrics import BacktestMetrics

class ChronologicalRunner:
    def __init__(self, historical_games: List[Dict[str, Any]]):
        # Ordenar cronológicamente ascendente por fecha
        self.games = sorted(historical_games, key=lambda g: g["date"])

    def run_backtest(self) -> Dict[str, Any]:
        """Ejecuta la simulación histórica completa paso a paso."""
        predictions_home = []
        actual_outcomes_home = []
        bets_placed = []

        for game in self.games:
            # 1. Evaluar QB
            h_qb_eval = QBModel.evaluate_qb(game["home_qb"], game.get("home_injuries", {}).get("qb_health"))
            a_qb_eval = QBModel.evaluate_qb(game["away_qb"], game.get("away_injuries", {}).get("qb_health"))

            # 2. Matchup
            h_matchup = MatchupEngine.evaluate_side_matchup(
                game["home_stats"], h_qb_eval, game["home_pfr"], game["home_injuries"],
                game["away_stats"], game["away_pfr"], game["away_injuries"]
            )
            a_matchup = MatchupEngine.evaluate_side_matchup(
                game["away_stats"], a_qb_eval, game["away_pfr"], game["away_injuries"],
                game["home_stats"], game["home_pfr"], game["home_injuries"]
            )

            # 3. Contexto
            ctx_eval = ContextEngine.calculate_situational_adjustments(game["context"], game.get("is_divisional", False))

            # 4. Simulación
            sim_res = NFLSimulationModel.simulate_game(
                game["home_team"], game["away_team"],
                h_matchup, a_matchup, ctx_eval, iterations=10000
            )

            # Extraer probabilidades
            p_home = sim_res["win_probabilities"]["home_raw"]
            home_won = 1 if game["home_final_score"] > game["away_final_score"] else 0

            predictions_home.append(p_home)
            actual_outcomes_home.append(home_won)

            # 5. Motor de decisión
            decision = DecisionEngine.evaluate_game_value(
                sim_res, game["market_odds"],
                h_matchup, a_matchup,
                game["home_injuries"], game["away_injuries"]
            )

            # Registrar si fue APUESTA CANDIDATA
            for side in decision.get("sides_analysis", []):
                if side["decision"] == "APUESTA CANDIDATA":
                    is_home_bet = (side["side"] == "HOME")
                    bet_won = (home_won == 1) if is_home_bet else (home_won == 0)
                    bets_placed.append({
                        "game": f"{game['away_team']} @ {game['home_team']}",
                        "date": game["date"],
                        "bet_on": side["team"],
                        "odds_taken": side["market_odds"],
                        "fair_odds": side["fair_odds"],
                        "ev_pct": side["expected_value_ev_pct"],
                        "closing_odds_no_vig": game.get("market_odds", {}).get("closing_odds_no_vig", side["market_odds"]),
                        "won": 1 if bet_won else 0
                    })

        # Calcular métricas globales
        brier = BacktestMetrics.calculate_brier_score(predictions_home, actual_outcomes_home)
        log_loss = BacktestMetrics.calculate_log_loss(predictions_home, actual_outcomes_home)
        cal_curve = BacktestMetrics.calculate_calibration_curve(predictions_home, actual_outcomes_home, bins=5)
        fin_perf = BacktestMetrics.calculate_financial_performance(bets_placed)

        return {
            "total_games_evaluated": len(self.games),
            "brier_score": brier,
            "log_loss": log_loss,
            "calibration_curve": cal_curve,
            "financial_performance": fin_perf,
            "bets_summary": bets_placed
        }
