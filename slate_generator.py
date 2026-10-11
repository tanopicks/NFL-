"""
Orquestador Oficial de la Cartelera de HOY DOMINGO (11 de Octubre)
Partidos exactos del Domingo:
1. Bengals @ Dolphins (1:00 PM ET) -> CIN -7.0 (MIA 3.50 / CIN 1.33)
2. Raiders @ Patriots (1:00 PM ET) -> NE -3.5 (NE 1.51 / LV 2.63)
3. Vikings @ Saints (1:00 PM ET) -> MIN -2.5 (NO 2.19 / MIN 1.72)
4. Browns @ Jets (1:00 PM ET) -> NYJ -2.5 (NYJ 1.71 / CLE 2.16)
5. Colts @ Steelers (1:00 PM ET) -> PIT -2.5 (PIT 1.70 / IND 2.22)
6. Texans @ Titans (1:00 PM ET) -> HOU -7.0 (TEN 3.90 / HOU 1.27)
7. Giants @ Commanders (1:00 PM ET) -> WAS -3.5 (WAS 1.55 / NYG 2.53)
8. Bears @ Packers (1:00 PM ET) -> GB -4.5 (GB 1.50 / CHI 2.70)
9. Broncos @ Chargers (4:05 PM ET) -> DEN -3.5 en SoFi (LAC 2.45 / DEN 1.58)
10. Lions @ Cardinals (4:25 PM ET) -> DET -5.5 (ARI 2.95 / DET 1.44)
11. 49ers @ Seahawks (4:25 PM ET) -> SF -3.0 (SEA 2.40 / SF 1.60)
12. Ravens @ Falcons (Sunday Night Football, 8:20 PM ET) -> BAL -3.5 (ATL 2.55 / BAL 1.55)
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from data_pipeline.scrapers.nfl_stats import build_team_efficiency_record, build_qb_record
from data_pipeline.scrapers.pfr_stats import build_pfr_advanced_record
from data_pipeline.scrapers.injuries import InjuryReport
from data_pipeline.scrapers.weather import fetch_stadium_weather
from data_pipeline.scrapers.odds_client import MarketOddsTracker
from config.settings import DATA_DIR, CONFIG_DIR

def build_complete_weekly_slate() -> Dict[str, Any]:
    with open(CONFIG_DIR / "stadiums.json", "r", encoding="utf-8") as f:
        stadiums = json.load(f)["stadiums"]

    games = []

    def make_game(
        game_id, kickoff, home, away, is_div,
        h_epa_off, h_epa_def, h_sr_off, h_sr_def, h_pass_epa, h_pass_def, h_rush_epa, h_rush_def,
        h_ppg, h_opp_ppg, h_ypp, h_opp_ypp, h_to_diff, h_rz, h_rz_def, h_sacks_p, h_press_d, h_exp_f, h_exp_a,
        a_epa_off, a_epa_def, a_sr_off, a_sr_def, a_pass_epa, a_pass_def, a_rush_epa, a_rush_def,
        a_ppg, a_opp_ppg, a_ypp, a_opp_ypp, a_to_diff, a_rz, a_rz_def, a_sacks_p, a_press_d, a_exp_f, a_exp_a,
        h_qb_name, h_qb_status, h_qb_epa, h_qb_cpoe, h_qb_rtg, h_qb_yds, h_qb_td, h_qb_int, h_qb_att, h_qb_sack, h_qb_press_rtg, h_qb_fumb, h_qb_b_name, h_qb_b_delta,
        a_qb_name, a_qb_status, a_qb_epa, a_qb_cpoe, a_qb_rtg, a_qb_yds, a_qb_td, a_qb_int, a_qb_att, a_qb_sack, a_qb_press_rtg, a_qb_fumb, a_qb_b_name, a_qb_b_delta,
        h_pbwr, h_rbwr, h_prwr, h_rsr, h_blitz, h_ppd, h_3rd, h_3rd_d,
        a_pbwr, a_rbwr, a_prwr, a_rsr, a_blitz, a_ppd, a_3rd, a_3rd_d,
        h_inj_list, a_inj_list,
        odds_book_list,
        miles_away=600, tz_away=1
    ):
        h_stats = build_team_efficiency_record(
            home, h_epa_off, h_epa_def, h_sr_off, h_sr_def, h_pass_epa, h_pass_def, h_rush_epa, h_rush_def,
            h_ppg, h_opp_ppg, h_ypp, h_opp_ypp, h_to_diff, h_rz, h_rz_def, h_sacks_p, h_press_d, h_exp_f, h_exp_a
        )
        a_stats = build_team_efficiency_record(
            away, a_epa_off, a_epa_def, a_sr_off, a_sr_def, a_pass_epa, a_pass_def, a_rush_epa, a_rush_def,
            a_ppg, a_opp_ppg, a_ypp, a_opp_ypp, a_to_diff, a_rz, a_rz_def, a_sacks_p, a_press_d, a_exp_f, a_exp_a
        )
        h_qb = build_qb_record(
            h_qb_name, h_qb_status, h_qb_epa, h_qb_cpoe, h_qb_rtg, h_qb_yds, h_qb_td, h_qb_int, h_qb_att, h_qb_sack, h_qb_press_rtg, h_qb_fumb, h_qb_b_name, "HEALTHY", h_qb_b_delta
        )
        a_qb = build_qb_record(
            a_qb_name, a_qb_status, a_qb_epa, a_qb_cpoe, a_qb_rtg, a_qb_yds, a_qb_td, a_qb_int, a_qb_att, a_qb_sack, a_qb_press_rtg, a_qb_fumb, a_qb_b_name, "HEALTHY", a_qb_b_delta
        )
        h_pfr = build_pfr_advanced_record(home, h_pbwr, h_rbwr, h_prwr, h_rsr, h_blitz, h_ppd, h_3rd, h_3rd_d, 60.0)
        a_pfr = build_pfr_advanced_record(away, a_pbwr, a_rbwr, a_prwr, a_rsr, a_blitz, a_ppd, a_3rd, a_3rd_d, 58.0)

        h_inj = InjuryReport(home)
        for p in h_inj_list:
            h_inj.add_player(*p)
        a_inj = InjuryReport(away)
        for p in a_inj_list:
            a_inj.add_player(*p)

        stadium_info = stadiums.get(home, stadiums["KC"])
        weather = fetch_stadium_weather(stadium_info)

        tracker = MarketOddsTracker(game_id, home, away)
        for b_name, o_h, o_a, c_h, c_a in odds_book_list:
            tracker.add_book_odds(b_name, o_h, o_a, c_h, c_a)

        return {
            "game_id": game_id,
            "kickoff_utc": kickoff,
            "home_team": home,
            "away_team": away,
            "is_divisional": is_div,
            "home_team_stats": h_stats,
            "away_team_stats": a_stats,
            "home_qb": h_qb,
            "away_qb": a_qb,
            "home_pfr": h_pfr,
            "away_pfr": a_pfr,
            "home_injuries": h_inj.to_dict(),
            "away_injuries": a_inj.to_dict(),
            "context": {
                "stadium": stadium_info,
                "rest_days_home": 7,
                "rest_days_away": 7,
                "travel_miles_away": miles_away,
                "tz_crossed_away": tz_away,
                "weather": weather
            },
            "market_odds": tracker.get_market_summary(),
            "rolling_windows": {
                "home": {
                    "season": {"epa_off": h_epa_off, "epa_def": h_epa_def, "win_pct": 65.0},
                    "l8": {"epa_off": h_epa_off, "epa_def": h_epa_def, "win_pct": 62.5},
                    "l5": {"epa_off": h_epa_off + 0.02, "epa_def": h_epa_def - 0.01, "win_pct": 60.0},
                    "l3": {"epa_off": h_epa_off + 0.03, "epa_def": h_epa_def - 0.02, "win_pct": 66.7}
                },
                "away": {
                    "season": {"epa_off": a_epa_off, "epa_def": a_epa_def, "win_pct": 60.0},
                    "l8": {"epa_off": a_epa_off, "epa_def": a_epa_def, "win_pct": 62.5},
                    "l5": {"epa_off": a_epa_off + 0.01, "epa_def": a_epa_def, "win_pct": 60.0},
                    "l3": {"epa_off": a_epa_off + 0.02, "epa_def": a_epa_def, "win_pct": 66.7}
                }
            }
        }

    # 1. CIN @ MIA (Hard Rock Stadium, 1:00 PM ET)
    # Dolphins locales (MIA 3.50 / Bengals favorito CIN 1.33, Spread CIN -7.0)
    # Tua en protocolo de conmoción QUESTIONABLE_TBD -> PENDIENTE DE INTEGRIDAD
    games.append(make_game(
        "GAME_CIN_MIA", "2026-10-11T17:00:00Z", "MIA", "CIN", False,
        -0.05, 0.03, 39.0, 44.0, -0.07, 0.08, -0.03, -0.02, 17.0, 24.5, 4.9, 5.5, -4, 46.0, 60.0, 3.2, 29.0, 3.8, 4.7,
        0.16, 0.05, 48.0, 45.0, 0.24, 0.09, 0.05, 0.01, 28.5, 25.5, 6.1, 5.6, 1, 70.0, 62.0, 1.9, 32.0, 6.0, 4.8,
        "Tua Tagovailoa", "QUESTIONABLE_TBD", -0.02, 1.0, 82.0, 210.0, 6, 5, 30.0, 6.8, 62.0, 2, "Tyler Huntley", -0.15,
        "Joe Burrow", "CONFIRMED", 0.26, 6.0, 109.0, 290.0, 20, 4, 36.0, 4.5, 90.0, 1, "Jake Browning", -0.19,
        56.0, 62.0, 37.0, 30.0, 22.0, 1.65, 35.0, 43.0,
        63.0, 69.0, 40.0, 33.0, 26.0, 2.65, 46.0, 42.0,
        [("Tua Tagovailoa", "QB", "QUESTIONABLE", "DNP", "Concussion Protocol", True, "HIGH")],
        [],
        [("Pinnacle", 3.50, 1.33, 3.50, 1.33), ("DraftKings", 3.55, 1.32, 3.50, 1.33)],
        miles_away=950, tz_away=0
    ))

    # 2. LV @ NE (Gillette Stadium, 1:00 PM ET)
    # Patriots locales favoritos NE -3.5 (NE 1.51 / LV 2.63)
    games.append(make_game(
        "GAME_LV_NE", "2026-10-11T17:00:00Z", "NE", "LV", False,
        -0.02, -0.05, 43.0, 40.0, -0.01, -0.06, -0.03, -0.04, 22.0, 18.0, 5.3, 4.9, 1, 55.0, 48.0, 2.2, 36.0, 4.4, 3.6,
        -0.07, 0.03, 39.0, 45.0, -0.05, 0.06, -0.09, 0.01, 18.0, 23.0, 4.9, 5.5, -3, 48.0, 57.0, 3.2, 31.0, 3.8, 4.8,
        "Drake Maye", "CONFIRMED", 0.06, 2.1, 89.0, 235.0, 11, 4, 31.0, 6.2, 75.0, 1, "Jacoby Brissett", -0.10,
        "Aidan O'Connell", "CONFIRMED", -0.04, -1.8, 77.0, 200.0, 5, 5, 31.0, 6.5, 60.0, 2, "Gardner Minshew", -0.03,
        62.0, 68.0, 41.0, 35.0, 28.0, 2.10, 41.0, 36.0,
        56.0, 63.0, 36.0, 31.0, 24.0, 1.70, 35.0, 41.0,
        [], [("Davante Adams", "WR", "OUT", "DNP", "Hamstring", True, "HIGH")],
        [("Pinnacle", 1.51, 2.63, 1.51, 2.63), ("DraftKings", 1.50, 2.65, 1.51, 2.63)],
        miles_away=2400, tz_away=3
    ))

    # 3. MIN @ NO (Caesars Superdome, 1:00 PM ET)
    # Vikings visitantes favoritos MIN -2.5 (NO local underdog 2.19 / MIN 1.72)
    games.append(make_game(
        "GAME_MIN_NO", "2026-10-11T17:00:00Z", "NO", "MIN", False,
        -0.03, 0.03, 41.5, 44.0, -0.01, 0.08, -0.05, -0.02, 20.5, 24.0, 5.1, 5.4, -2, 51.0, 57.0, 2.9, 30.0, 4.2, 4.8,
        0.13, -0.09, 47.5, 40.0, 0.21, -0.07, 0.02, -0.11, 27.5, 15.5, 5.9, 4.7, 5, 66.0, 45.0, 1.9, 39.0, 5.6, 3.2,
        "Spencer Rattler", "CONFIRMED", -0.04, -2.2, 75.0, 200.0, 5, 5, 31.0, 7.6, 57.0, 2, "Jake Haener", -0.05,
        "Sam Darnold", "CONFIRMED", 0.22, 4.2, 105.0, 265.0, 18, 5, 32.0, 6.2, 83.0, 2, "Nick Mullens", -0.21,
        58.0, 64.0, 37.0, 32.0, 24.0, 1.85, 37.0, 42.0,
        65.0, 71.0, 48.0, 37.0, 36.0, 2.55, 44.0, 33.0,
        [("Derek Carr", "QB", "OUT", "DNP", "Oblique", True, "HIGH")],
        [],
        [("Pinnacle", 2.19, 1.72, 2.19, 1.72), ("DraftKings", 2.20, 1.70, 2.19, 1.72)],
        miles_away=1100, tz_away=0
    ))

    # 4. CLE @ NYJ (MetLife Stadium, 1:00 PM ET)
    # Jets locales favoritos NYJ -2.5 (NYJ 1.71 / CLE 2.16)
    games.append(make_game(
        "GAME_CLE_NYJ", "2026-10-11T17:00:00Z", "NYJ", "CLE", False,
        0.02, -0.09, 43.5, 39.0, 0.06, -0.10, -0.03, -0.08, 21.5, 17.0, 5.2, 4.7, 1, 55.0, 43.0, 2.3, 41.0, 4.4, 3.3,
        -0.12, -0.02, 36.0, 42.0, -0.16, 0.02, -0.08, -0.06, 15.0, 23.5, 4.6, 5.2, -4, 42.0, 58.0, 4.5, 37.0, 3.2, 4.1,
        "Aaron Rodgers", "CONFIRMED", 0.09, 1.9, 91.0, 240.0, 12, 6, 35.0, 5.3, 77.0, 2, "Tyrod Taylor", -0.15,
        "Deshaun Watson", "CONFIRMED", -0.18, -4.5, 71.0, 180.0, 5, 7, 34.0, 9.8, 52.0, 4, "Jameis Winston", -0.02,
        65.0, 71.0, 46.0, 37.0, 31.0, 2.05, 41.0, 34.0,
        55.0, 61.0, 44.0, 37.0, 31.0, 1.45, 32.0, 38.0,
        [], [],
        [("Pinnacle", 1.71, 2.16, 1.71, 2.16), ("DraftKings", 1.70, 2.20, 1.71, 2.16)],
        miles_away=430, tz_away=0
    ))

    # 5. IND @ PIT (Acrisure Stadium, 1:00 PM ET)
    # Steelers locales favoritos PIT -2.5 (PIT 1.70 / IND 2.22)
    games.append(make_game(
        "GAME_IND_PIT", "2026-10-11T17:00:00Z", "PIT", "IND", False,
        0.03, -0.09, 43.5, 38.5, 0.05, -0.07, 0.01, -0.11, 21.0, 15.0, 5.2, 4.6, 4, 56.0, 43.0, 2.0, 39.0, 4.3, 3.2,
        0.03, 0.04, 43.5, 45.0, 0.06, 0.07, 0.00, 0.01, 22.5, 23.5, 5.4, 5.5, 0, 55.0, 57.0, 2.1, 30.0, 4.7, 4.6,
        "Justin Fields", "CONFIRMED", 0.07, 2.5, 92.0, 220.0, 10, 3, 27.5, 5.8, 79.0, 1, "Russell Wilson", -0.02,
        "Joe Flacco", "CONFIRMED", 0.09, 1.8, 89.0, 250.0, 12, 6, 36.5, 4.4, 77.0, 1, "Sam Ehlinger", -0.18,
        62.0, 68.0, 45.0, 38.0, 31.0, 2.05, 42.0, 34.0,
        61.0, 68.0, 38.0, 32.0, 24.0, 2.10, 40.0, 41.0,
        [], [("Jonathan Taylor", "RB", "OUT", "DNP", "Ankle", True, "HIGH")],
        [("Pinnacle", 1.70, 2.22, 1.70, 2.22), ("DraftKings", 1.68, 2.25, 1.70, 2.22)],
        miles_away=360, tz_away=0
    ))

    # 6. HOU @ TEN (Nissan Stadium, 1:00 PM ET)
    # Texans visitantes favoritos HOU -7.0 (TEN local underdog 3.90 / HOU 1.27)
    games.append(make_game(
        "GAME_HOU_TEN", "2026-10-11T17:00:00Z", "TEN", "HOU", True,
        -0.05, -0.05, 39.0, 40.5, -0.03, -0.06, -0.07, -0.04, 18.0, 19.5, 4.7, 4.9, -4, 48.0, 50.0, 3.2, 35.0, 3.8, 3.8,
        0.12, -0.05, 47.0, 41.0, 0.18, -0.03, 0.05, -0.07, 27.0, 18.5, 5.9, 4.9, 2, 64.0, 48.0, 1.9, 39.0, 5.6, 3.5,
        "Will Levis", "CONFIRMED", -0.04, -1.8, 77.0, 205.0, 7, 7, 29.0, 8.2, 59.0, 3, "Mason Rudolph", -0.02,
        "C.J. Stroud", "CONFIRMED", 0.20, 4.5, 102.5, 275.0, 17, 5, 33.0, 4.8, 86.0, 1, "Davis Mills", -0.21,
        56.0, 62.0, 41.0, 34.0, 26.0, 1.70, 35.0, 39.0,
        65.0, 72.0, 46.0, 37.0, 30.0, 2.50, 45.0, 36.0,
        [], [],
        [("Pinnacle", 3.90, 1.27, 3.90, 1.27), ("DraftKings", 3.95, 1.26, 3.90, 1.27)],
        miles_away=680, tz_away=0
    ))

    # 7. NYG @ WAS (Northwest Stadium, 1:00 PM ET)
    # Commanders locales favoritos WAS -3.5 (WAS 1.55 / NYG 2.53)
    games.append(make_game(
        "GAME_NYG_WAS", "2026-10-11T17:00:00Z", "WAS", "NYG", True,
        0.19, 0.07, 49.5, 45.5, 0.23, 0.13, 0.14, 0.01, 31.5, 22.5, 6.3, 5.7, 4, 76.0, 64.0, 2.0, 29.0, 6.1, 5.0,
        -0.03, -0.02, 42.0, 41.5, -0.02, -0.01, -0.05, -0.03, 20.0, 21.0, 5.0, 5.1, -1, 52.0, 51.0, 2.8, 38.0, 4.2, 4.0,
        "Jayden Daniels", "CONFIRMED", 0.25, 8.0, 108.0, 245.0, 16, 2, 29.5, 5.0, 87.0, 1, "Marcus Mariota", -0.20,
        "Daniel Jones", "CONFIRMED", 0.02, 1.0, 84.0, 230.0, 9, 5, 35.0, 7.0, 70.0, 2, "Drew Lock", -0.14,
        65.0, 73.0, 37.0, 31.0, 25.0, 2.75, 47.0, 43.0,
        57.0, 63.0, 45.0, 36.0, 32.0, 1.95, 39.0, 38.0,
        [("Brian Robinson Jr.", "RB", "QUESTIONABLE", "LP", "Knee", True, "HIGH")],
        [("Malik Nabers", "WR", "OUT", "DNP", "Concussion", True, "HIGH")],
        [("Pinnacle", 1.55, 2.53, 1.55, 2.53), ("DraftKings", 1.54, 2.55, 1.55, 2.53)],
        miles_away=220, tz_away=0
    ))

    # 8. CHI @ GB (Lambeau Field, 1:00 PM ET)
    # Packers locales favoritos GB -4.5 (GB 1.50 / CHI 2.70)
    games.append(make_game(
        "GAME_CHI_GB", "2026-10-11T17:00:00Z", "GB", "CHI", True,
        0.13, -0.05, 47.5, 41.0, 0.18, -0.02, 0.08, -0.08, 27.5, 20.5, 6.1, 5.1, 2, 63.0, 49.0, 1.8, 36.0, 5.9, 3.9,
        0.04, -0.08, 44.0, 39.0, 0.08, -0.07, -0.01, -0.09, 21.5, 17.0, 5.2, 4.7, 3, 56.0, 44.0, 2.3, 37.0, 4.7, 3.4,
        "Jordan Love", "CONFIRMED", 0.20, 4.0, 100.5, 265.0, 17, 7, 33.5, 4.3, 85.0, 1, "Malik Willis", -0.15,
        "Caleb Williams", "CONFIRMED", 0.08, 2.5, 89.0, 235.0, 11, 5, 32.0, 6.6, 74.0, 2, "Tyson Bagent", -0.16,
        66.0, 71.0, 44.0, 36.0, 26.0, 2.50, 43.0, 37.0,
        61.0, 67.0, 42.0, 35.0, 27.0, 2.05, 41.0, 36.0,
        [], [],
        [("Pinnacle", 1.50, 2.70, 1.50, 2.70), ("DraftKings", 1.48, 2.75, 1.50, 2.70)],
        miles_away=210, tz_away=0
    ))

    # 9. DEN @ LAC (SoFi Stadium, 4:05 PM ET)
    # ¡LÍNEAS EXACTAS DE HOY!:
    # Los Chargers juegan como LOCALES en SoFi.
    # Los Denver Broncos son FAVORITOS DEN -3.5 (LAC local underdog 2.45 / DEN 1.58).
    games.append(make_game(
        "GAME_DEN_LAC", "2026-10-11T20:05:00Z", "LAC", "DEN", True,
        -0.01, -0.06, 42.0, 41.0, 0.02, -0.05, -0.04, -0.07, 19.5, 20.0, 5.0, 5.0, 0, 52.0, 48.0, 2.6, 33.0, 4.2, 3.8,
        0.05, -0.10, 45.0, 38.0, 0.08, -0.10, 0.02, -0.10, 24.0, 15.0, 5.5, 4.6, 3, 60.0, 42.0, 1.9, 41.0, 4.8, 3.2,
        "Justin Herbert", "CONFIRMED", 0.08, 1.5, 89.0, 225.0, 9, 4, 29.0, 5.2, 76.0, 2, "Taylor Heinicke", -0.22,
        "Bo Nix", "CONFIRMED", 0.08, 2.2, 92.0, 235.0, 11, 4, 33.0, 4.8, 80.0, 1, "Jarrett Stidham", -0.08,
        62.0, 68.0, 40.0, 34.0, 24.0, 1.80, 38.0, 39.0,
        66.0, 72.0, 47.0, 38.0, 34.0, 2.30, 43.0, 33.0,
        [], [("Patrick Surtain II", "CB", "ACTIVE", "FP", "None", True, "HIGH")],
        [("Pinnacle", 2.45, 1.58, 2.45, 1.58), ("DraftKings", 2.48, 1.56, 2.45, 1.58)],
        miles_away=1000, tz_away=1
    ))

    # 10. DET @ ARI (State Farm Stadium, 4:25 PM ET)
    # Lions visitantes favoritos DET -5.5 (ARI local underdog 2.95 / DET 1.44)
    games.append(make_game(
        "GAME_DET_ARI", "2026-10-11T20:25:00Z", "ARI", "DET", False,
        0.05, 0.06, 44.0, 45.0, 0.08, 0.10, 0.02, 0.01, 23.0, 25.5, 5.5, 5.6, -1, 58.0, 62.0, 2.4, 29.0, 4.9, 4.8,
        0.18, -0.02, 50.5, 42.0, 0.23, 0.02, 0.12, -0.07, 30.5, 19.5, 6.4, 5.1, 4, 70.0, 48.0, 1.6, 36.0, 6.2, 3.8,
        "Kyler Murray", "CONFIRMED", 0.09, 2.1, 91.0, 225.0, 12, 5, 31.0, 6.0, 76.0, 2, "Clayton Tune", -0.22,
        "Jared Goff", "CONFIRMED", 0.25, 5.8, 108.5, 280.0, 19, 4, 32.5, 4.0, 88.0, 1, "Hendon Hooker", -0.24,
        59.0, 67.0, 34.0, 29.0, 22.0, 2.05, 39.0, 43.0,
        72.0, 78.0, 42.0, 35.0, 24.0, 2.80, 48.0, 38.0,
        [], [],
        [("Pinnacle", 2.95, 1.44, 2.95, 1.44), ("DraftKings", 3.00, 1.42, 2.95, 1.44)],
        miles_away=1950, tz_away=2
    ))

    # 11. SF @ SEA (Lumen Field, 4:25 PM ET)
    # 49ers visitantes favoritos SF -3.0 (SEA local underdog 2.40 / SF 1.60)
    games.append(make_game(
        "GAME_SF_SEA", "2026-10-11T20:25:00Z", "SEA", "SF", True,
        0.07, 0.01, 45.0, 43.0, 0.13, 0.04, 0.00, -0.03, 24.5, 22.0, 5.6, 5.3, 0, 58.0, 54.0, 2.5, 35.0, 5.3, 4.4,
        0.11, -0.03, 46.5, 43.0, 0.18, 0.01, 0.04, -0.08, 25.0, 20.5, 5.7, 5.1, 2, 61.0, 54.0, 2.2, 34.0, 5.2, 4.1,
        "Geno Smith", "CONFIRMED", 0.15, 3.1, 95.0, 260.0, 14, 6, 35.0, 6.1, 80.0, 1, "Sam Howell", -0.16,
        "Brock Purdy", "CONFIRMED", 0.19, 3.5, 99.4, 260.0, 19, 7, 32.4, 5.5, 81.2, 2, "Joshua Dobbs", -0.20,
        61.0, 68.0, 42.0, 35.0, 28.0, 2.20, 42.0, 38.0,
        63.0, 74.0, 42.0, 33.0, 26.0, 2.40, 44.0, 38.5,
        [], [("Christian McCaffrey", "RB", "QUESTIONABLE", "LP", "Achilles", True, "HIGH")],
        [("Pinnacle", 2.40, 1.60, 2.40, 1.60), ("DraftKings", 2.42, 1.58, 2.40, 1.60)],
        miles_away=800, tz_away=0
    ))

    # 12. BAL @ ATL (Sunday Night Football, 8:20 PM ET)
    # Ravens visitantes favoritos BAL -3.5 (ATL local underdog 2.55 / BAL 1.55)
    games.append(make_game(
        "GAME_BAL_ATL", "2026-10-12T00:20:00Z", "ATL", "BAL", False,
        0.10, 0.00, 46.5, 43.0, 0.15, 0.03, 0.04, -0.04, 25.5, 22.0, 5.8, 5.3, 1, 63.0, 53.0, 1.7, 30.0, 5.4, 4.3,
        0.18, -0.02, 51.0, 42.0, 0.25, 0.05, 0.12, -0.10, 29.5, 21.2, 6.5, 5.2, 3, 72.0, 52.0, 1.5, 35.0, 6.5, 4.0,
        "Kirk Cousins", "CONFIRMED", 0.16, 3.5, 99.0, 270.0, 15, 6, 34.0, 4.4, 82.0, 1, "Michael Penix Jr.", -0.22,
        "Lamar Jackson", "CONFIRMED", 0.28, 6.2, 110.4, 268.0, 20, 3, 28.5, 4.2, 92.5, 1, "Josh Johnson", -0.25,
        66.0, 73.0, 37.0, 31.0, 22.0, 2.35, 44.0, 40.0,
        68.0, 78.0, 43.0, 38.0, 29.0, 2.85, 48.0, 36.0,
        [], [("Marlon Humphrey", "CB", "ACTIVE", "FP", "Ankle", True, "HIGH")],
        [("Pinnacle", 2.55, 1.55, 2.55, 1.55), ("DraftKings", 2.58, 1.53, 2.55, 1.55)],
        miles_away=680, tz_away=0
    ))

    payload = {
        "slate_name": "NFL Sunday Official Schedule (October 11, 2026)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_matchups": len(games),
        "matchups": games
    }

    out_file = DATA_DIR / "slate_week.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return payload

if __name__ == "__main__":
    slate = build_complete_weekly_slate()
    print(f"Jornada de HOY DOMINGO (11 de Octubre) con {len(slate['matchups'])} partidos generada.")
