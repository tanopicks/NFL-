"""
Full Automated Weekly Pipeline Runner
Ejecuta la pipeline completa de extremo a extremo:
1. Carga o actualiza la jornada con las 5 fuentes.
2. Valida la integridad estricta (no imputación, comprobación de QB y lesiones).
3. Evalúa los 6 bloques estadísticos obligatorios (A, B, C, D, E, F).
4. Aplica el modelo de simulación y genera cuotas justas.
5. Emite dictamen conservador: APUESTA CANDIDATA, ESPERAR o DEJAR PASAR (o PENDIENTE).
6. Guarda snapshots inmutables para auditoría.
7. Exporta el reporte semanal completo para la interfaz web.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from config.settings import DATA_DIR
from data_pipeline.slate_generator import build_complete_weekly_slate
from data_pipeline.data_cleaner import IntegrityValidator, save_immutable_snapshot
from core_engine.qb_model import QBModel
from core_engine.matchup_engine import MatchupEngine
from core_engine.context_engine import ContextEngine
from core_engine.simulation_model import NFLSimulationModel
from core_engine.decision_engine import DecisionEngine

def run_weekly_pipeline() -> Dict[str, Any]:
    print(">>> Iniciando Pipeline Semanal Automático NFL...")
    slate = build_complete_weekly_slate()
    matchups = slate.get("matchups", [])
    
    analyzed_games = []
    summary_counts = {"CANDIDATA": 0, "ESPERAR": 0, "DEJAR_PASAR": 0, "PENDIENTE": 0}

    for game in matchups:
        game_id = game["game_id"]
        print(f"\nProcesando encuentro: {game['away_team']} @ {game['home_team']} (ID: {game_id})")

        # 1. Comprobación de integridad
        is_valid, errors = IntegrityValidator.validate_game_dataset(game)

        if not is_valid:
            print(f"  [ALERTA DE INTEGRIDAD] Partido incompleto: {errors}")
            summary_counts["PENDIENTE"] += 1
            game_analysis = {
                "game_id": game_id,
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "global_decision": "PENDIENTE",
                "decision_badge": "PENDIENTE_DATOS_INCOMPLETOS",
                "reason": "Bloques obligatorios incompletos o estatus de QB/lesiones sin confirmar oficialmente.",
                "pending_issues": errors,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "raw_game": game
            }
            analyzed_games.append(game_analysis)
            continue

        # 2. Guardar snapshot inmutable para auditoría
        snapshot_file = save_immutable_snapshot(game_id, game)

        # 3. Modelado de Quarterbacks
        home_qb_eval = QBModel.evaluate_qb(game["home_qb"], game["home_injuries"].get("qb_health"))
        away_qb_eval = QBModel.evaluate_qb(game["away_qb"], game["away_injuries"].get("qb_health"))

        # 4. Colisiones ofensivas/defensivas (Matchup breakdown)
        home_matchup = MatchupEngine.evaluate_side_matchup(
            game["home_team_stats"], home_qb_eval, game["home_pfr"], game["home_injuries"],
            game["away_team_stats"], game["away_pfr"], game["away_injuries"]
        )
        away_matchup = MatchupEngine.evaluate_side_matchup(
            game["away_team_stats"], away_qb_eval, game["away_pfr"], game["away_injuries"],
            game["home_team_stats"], game["home_pfr"], game["home_injuries"]
        )

        # 5. Ajustes contextuales y de campo
        ctx_eval = ContextEngine.calculate_situational_adjustments(game["context"], game.get("is_divisional", False))

        # 6. Simulación estocástica
        sim_res = NFLSimulationModel.simulate_game(
            game["home_team"], game["away_team"],
            home_matchup, away_matchup, ctx_eval, iterations=20000
        )

        # 7. Motor de Decisión Conservador (+EV)
        decision = DecisionEngine.evaluate_game_value(
            sim_res, game["market_odds"],
            home_matchup, away_matchup,
            game["home_injuries"], game["away_injuries"]
        )

        global_dec = decision["global_decision"]
        if global_dec == "APUESTA CANDIDATA":
            summary_counts["CANDIDATA"] += 1
        elif global_dec == "ESPERAR":
            summary_counts["ESPERAR"] += 1
        else:
            summary_counts["DEJAR_PASAR"] += 1

        print(f"  -> Decisión: {global_dec} | Proyección: {decision['projected_score']}")
        for side in decision["sides_analysis"]:
            print(f"     {side['side']} ({side['team']}): Prob {side['estimated_prob_pct']}% | Cuota Justa: {side['fair_odds']} | Cuota Mercado: {side['market_odds']} | EV: {side['expected_value_ev_pct']:+}% -> {side['decision']}")

        # Enriquecer reporte con todos los bloques
        full_game_report = {
            **decision,
            "snapshot_file": snapshot_file,
            "kickoff_utc": game["kickoff_utc"],
            "block_a_efficiency": {
                "home": game["home_team_stats"],
                "away": game["away_team_stats"]
            },
            "block_b_qb": {
                "home": home_qb_eval,
                "away": away_qb_eval
            },
            "block_c_matchup": {
                "home_off_vs_away_def": home_matchup,
                "away_off_vs_home_def": away_matchup
            },
            "block_d_injuries": {
                "home": game["home_injuries"],
                "away": game["away_injuries"]
            },
            "block_e_context": ctx_eval,
            "block_f_market": game["market_odds"],
            "rolling_windows": game["rolling_windows"]
        }
        analyzed_games.append(full_game_report)

    output_payload = {
        "title": "NFL Predictive & Conservative +EV Value System - Weekly Intelligence Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary_counts,
        "games": analyzed_games
    }

    # Guardar reporte en data/weekly_intelligence_report.json y ui/report_data.json
    with open(DATA_DIR / "weekly_intelligence_report.json", "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    ui_file = BASE_DIR / "ui" / "report_data.json"
    with open(ui_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print(f"\n>>> Pipeline completado. Reporte guardado en {ui_file}")
    return output_payload

if __name__ == "__main__":
    run_weekly_pipeline()
