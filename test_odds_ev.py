"""
Test Suite: Desmargenado No-Vig y Filtro Conservador de Valor Esperado (+EV)
Verifica:
1. Normalización estricta de probabilidades sin margen (No-Vig sum = 1.0).
2. Regla Antifavoritismo: un favorito al 80% con cuota 1.10 TIENE EV NEGATIVO y es marcado DEJAR PASAR.
3. Clasificación obligatoria de +EV en APUESTA CANDIDATA vs ESPERAR vs DEJAR PASAR.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_pipeline.scrapers.odds_client import remove_vig_multiplicative
from core_engine.decision_engine import DecisionEngine

def test_no_vig_and_ev_criteria():
    print("Probando fórmulas No-Vig y reglas conservadoras de valor...")

    # 1. Test No-Vig
    p_h, p_a, vig = remove_vig_multiplicative(1.91, 1.91)
    assert abs((p_h + p_a) - 1.0) < 0.001, f"La suma de probabilidades no-vig debe ser 1.0. Dio {p_h + p_a}"
    assert vig > 4.0, f"El vig debería rondar ~4.7%. Dio {vig}%"
    print(f"  [PASS] No-Vig normalizado correctamente: P_home={p_h}, P_away={p_a}, Vig={vig}%")

    # 2. Regla antifavoritismo: Probabilidad alta (85%), pero cuota mezquina (1.10)
    sim_fake = {
        "home_team": "KC", "away_team": "CAR",
        "projected_scores": {"display": "CAR 13.0 @ KC 31.0"},
        "fair_spread_home": -18.0, "fair_total": 44.0,
        "win_probabilities": {"home_raw": 0.85, "away_raw": 0.15, "home": 85.0, "away": 15.0}
    }
    mkt_fake = {
        "best_odds": {"home": {"odds_decimal": 1.10, "sportsbook": "DraftKings"}, "away": {"odds_decimal": 7.50, "sportsbook": "FanDuel"}},
        "consensus_no_vig_prob": {"home": 88.0, "away": 12.0}
    }
    m_eval = {"composite_offensive_strength": 60.0, "key_factors": {"air_epa_diff": 0.20, "sr_diff": 8.0}}
    inj_clear = {"qb_health": {"status": "HEALTHY"}, "ol_health": {"ol_status": "HEALTHY"}}

    dec = DecisionEngine.evaluate_game_value(sim_fake, mkt_fake, m_eval, m_eval, inj_clear, inj_clear)
    home_bet = next(s for s in dec["sides_analysis"] if s["side"] == "HOME")

    # EV = (0.85 * 1.10) - 1 = -0.065 (-6.5%)
    assert home_bet["decision"] == "DEJAR PASAR", f"El favorito sin valor DEBE ser 'DEJAR PASAR'. Dio {home_bet['decision']}"
    assert home_bet["expected_value_ev_pct"] < 0, f"El EV debe ser negativo. Dio {home_bet['expected_value_ev_pct']}%"
    print(f"  [PASS] Regla antifavoritismo probada con éxito: Favorito 85% a cuota 1.10 -> {home_bet['decision']} (EV: {home_bet['expected_value_ev_pct']}%)")

    # 3. Test de Apuesta Candidata genuina (+EV >= 3.5% y con margen de seguridad)
    sim_value = {
        "home_team": "BAL", "away_team": "TB",
        "projected_scores": {"display": "TB 20.0 @ BAL 27.5"},
        "fair_spread_home": -7.5, "fair_total": 47.5,
        "win_probabilities": {"home_raw": 0.72, "away_raw": 0.28, "home": 72.0, "away": 28.0}
    }
    mkt_value = {
        "best_odds": {"home": {"odds_decimal": 1.55, "sportsbook": "Pinnacle"}, "away": {"odds_decimal": 2.70, "sportsbook": "Pinnacle"}},
        "consensus_no_vig_prob": {"home": 62.0, "away": 38.0}
    }
    # Fair odds BAL = 1 / 0.72 = 1.388. Mercado ofrece 1.55. EV = (0.72 * 1.55) - 1 = +11.6%
    dec_val = DecisionEngine.evaluate_game_value(sim_value, mkt_value, m_eval, m_eval, inj_clear, inj_clear)
    bal_bet = next(s for s in dec_val["sides_analysis"] if s["side"] == "HOME")
    assert bal_bet["decision"] == "APUESTA CANDIDATA", f"Debería ser APUESTA CANDIDATA. Dio {bal_bet['decision']}"
    assert bal_bet["expected_value_ev_pct"] > 5.0, f"EV esperado alto no alcanzado: {bal_bet['expected_value_ev_pct']}%"
    print(f"  [PASS] Apuesta Candidata +EV validada: BAL cuota {bal_bet['market_odds']} vs justa {bal_bet['fair_odds']} -> {bal_bet['decision']} (EV: +{bal_bet['expected_value_ev_pct']}%)")

if __name__ == "__main__":
    test_no_vig_and_ev_criteria()
    print("TODOS LOS TESTS DE ODDS Y +EV PASARON EXITOSAMENTE.")
