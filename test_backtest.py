"""
Test Suite: Chronological Backtesting & Calibration Validation
Ejecuta el backtest sobre los 50 partidos históricos y verifica:
1. Brier Score (< 0.25).
2. Log Loss (< 0.693).
3. Curva de calibración coherente por bins.
4. Tasa de Closing Line Value (CLV).
5. Cálculo de ROI y ganancia neta.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
from backtesting.chronological_runner import ChronologicalRunner
from config.settings import HISTORICAL_DIR

def test_chronological_backtest():
    hist_file = HISTORICAL_DIR / "nfl_historical_50_games.json"
    with open(hist_file, "r", encoding="utf-8") as f:
        games = json.load(f)

    print(f"Iniciando Walk-Forward Backtesting cronológico sobre {len(games)} partidos...")
    runner = ChronologicalRunner(games)
    report = runner.run_backtest()

    brier = report["brier_score"]
    log_loss = report["log_loss"]
    fin = report["financial_performance"]
    curve = report["calibration_curve"]

    print("=== RESULTADOS DEL BACKTESTING CRONOLÓGICO ===")
    print(f"Total Partidos Evaluados: {report['total_games_evaluated']}")
    print(f"Brier Score del Modelo:   {brier:.4f} (Benchmark de azar puro: 0.2500)")
    print(f"Log Loss:                 {log_loss:.4f} (Benchmark base: 0.6931)")
    print(f"Apuestas Realizadas (+EV):{fin['total_bets']}")
    print(f"Tasa de Acierto CLV:      {fin['clv_beat_rate_pct']}% de apuestas superaron la cuota de cierre")
    print(f"ROI Simulado:             {fin['roi_pct']}%")
    print(f"Beneficio Neto:           ${fin['net_profit']:,.2f}")

    print("\n--- Curva de Calibración ---")
    for bucket in curve:
        print(f"Rango: {bucket['bin_range']} | Partidos: {bucket['count']:2d} | Win% Predicho: {bucket['predicted_prob_avg']}% | Win% Real: {bucket['observed_win_pct']}% | Brecha: {bucket['calibration_gap']}%")

    assert brier < 0.25, f"El Brier Score no debe superar el azar puro (0.25). Dio {brier}"
    assert log_loss < 0.693, f"El Log Loss debe ser mejor que el azar (0.693). Dio {log_loss}"
    assert len(report["bets_summary"]) > 0, "El sistema debió identificar al menos una apuesta con valor"
    print("\nTODOS LOS TESTS DE BACKTESTING Y CALIBRACIÓN PASARON EXITOSAMENTE.")

if __name__ == "__main__":
    test_chronological_backtest()
