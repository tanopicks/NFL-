"""
NFL Quantum Edge - Python Analytics & Monte Carlo Simulation Engine
Modelado de 6 Bloques Ponderados & Generador de Recomendaciones de Apuestas (+EV)
"""

import json
import math
import random
from pathlib import Path
from typing import Dict, Any, List

class NFLBettingEngine:
    def __init__(self, data_path: str = None, weights_path: str = None):
        base_dir = Path(__file__).parent.parent
        self.data_path = Path(data_path) if data_path else base_dir / "data" / "teams_data.json"
        self.weights_path = Path(weights_path) if weights_path else base_dir / "config" / "weights.json"
        
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
            
        with open(self.weights_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
            
        self.weights = self.config.get("weights", {
            "qb_passing": 0.25,
            "pass_defense": 0.20,
            "general_offense": 0.15,
            "trenches_ol_dl": 0.10,
            "rushing_game": 0.08,
            "situational_clutch": 0.07,
            "contextual_adjustments": 0.15
        })

    def _normalize(self, val: float, min_val: float, max_val: float) -> float:
        return max(0.0, min(100.0, ((val - min_val) / (max_val - min_val)) * 100.0))

    def calculate_qb_score(self, team: Dict[str, Any]) -> float:
        qb = team["b1_qb_passing"]
        s_epa = self._normalize(qb["epa_dropback"], -0.15, 0.35) * 0.22
        s_cpoe = self._normalize(qb["cpoe"], -6.0, 8.0) * 0.15
        s_anya = self._normalize(qb["any_a"], 4.5, 9.0) * 0.15
        s_qbr = self._normalize(qb["qbr"], 35.0, 85.0) * 0.12
        s_succ = self._normalize(qb["success_rate"], 38.0, 58.0) * 0.10
        s_press = self._normalize(qb["passing_under_pressure_rating"], 50.0, 95.0) * 0.10
        s_td_int = self._normalize(qb["td_pct"] - qb["int_pct"], -2.0, 6.0) * 0.08
        s_sack = self._normalize(15.0 - qb["sack_pct"], 5.0, 15.0) * 0.08
        return s_epa + s_cpoe + s_anya + s_qbr + s_succ + s_press + s_td_int + s_sack

    def calculate_pass_defense_score(self, team: Dict[str, Any]) -> float:
        d = team["b2_pass_defense"]
        s_epa = self._normalize(0.25 - d["def_pass_epa"], 0.0, 0.40) * 0.25
        s_succ = self._normalize(55.0 - d["pass_success_rate_allowed"], 0.0, 20.0) * 0.20
        s_press = self._normalize(d["pressure_rate"], 20.0, 45.0) * 0.20
        s_sack = self._normalize(d["sack_rate"], 3.5, 10.0) * 0.15
        s_cpoe = self._normalize(4.0 - d["cpoe_allowed"], 0.0, 10.0) * 0.10
        s_third = self._normalize(50.0 - d["third_down_def_pct"], 0.0, 25.0) * 0.10
        return s_epa + s_succ + s_press + s_sack + s_cpoe + s_third

    def calculate_general_offense_score(self, team: Dict[str, Any]) -> float:
        o = team["b3_general_offense"]
        s_epa = self._normalize(o["off_epa_per_play"], -0.10, 0.25) * 0.25
        s_ppd = self._normalize(o["points_per_drive"], 1.2, 3.2) * 0.25
        s_succ = self._normalize(o["drive_success_rate"], 60.0, 85.0) * 0.20
        s_ypp = self._normalize(o["yards_per_play"], 4.5, 6.8) * 0.15
        s_third = self._normalize(o["third_down_conv_pct"], 30.0, 52.0) * 0.15
        return s_epa + s_ppd + s_succ + s_ypp + s_third

    def calculate_trench_advantage(self, ol_team: Dict[str, Any], dl_team: Dict[str, Any]) -> float:
        ol = ol_team["b4_trenches_ol_dl"]
        dl = dl_team["b4_trenches_ol_dl"]
        pass_trench = ol["pass_block_win_rate"] - dl["pass_rush_win_rate"]
        press_diff = dl["dl_pressure_rate"] - ol["ol_pressure_rate_allowed"]
        run_trench = ol["run_block_win_rate"] - dl["run_stop_rate"]
        return self._normalize(pass_trench + (run_trench * 0.8) - (press_diff * 0.5), -30.0, 30.0)

    def calculate_rushing_score(self, off_team: Dict[str, Any], def_team: Dict[str, Any]) -> float:
        r = off_team["b5_rushing_game"]
        s_epa = self._normalize(r["rush_epa_per_play"], -0.15, 0.15) * 0.30
        s_succ = self._normalize(r["rush_success_rate"], 35.0, 55.0) * 0.25
        s_ybc = self._normalize(r["yards_before_contact"], 1.2, 3.5) * 0.25
        s_stuff = self._normalize(25.0 - r["stuff_rate"], 5.0, 20.0) * 0.20
        return s_epa + s_succ + s_ybc + s_stuff

    def calculate_situational_score(self, off_team: Dict[str, Any], def_team: Dict[str, Any]) -> float:
        s = off_team["b6_situational"]
        ds = def_team["b6_situational"]
        rz_adv = self._normalize(s["red_zone_td_pct"] - ds["def_red_zone_td_pct"], -30.0, 30.0) * 0.40
        third_short = self._normalize(s["third_and_short_conv"], 50.0, 90.0) * 0.30
        fourth_conv = self._normalize(s["fourth_down_conv_pct"], 40.0, 80.0) * 0.30
        return rz_adv + third_short + fourth_conv

    def simulate_matchup(self, matchup: Dict[str, Any], iterations: int = 10000) -> Dict[str, Any]:
        home = self.dataset["teams"][matchup["home_team"]]
        away = self.dataset["teams"][matchup["away_team"]]
        
        home_qb = self.calculate_qb_score(home)
        away_qb = self.calculate_qb_score(away)
        home_pdef = self.calculate_pass_defense_score(home)
        away_pdef = self.calculate_pass_defense_score(away)
        home_off = self.calculate_general_offense_score(home)
        away_off = self.calculate_general_offense_score(away)
        home_trench = self.calculate_trench_advantage(home, away)
        away_trench = self.calculate_trench_advantage(away, home)
        home_rush = self.calculate_rushing_score(home, away)
        away_rush = self.calculate_rushing_score(away, home)
        home_sit = self.calculate_situational_score(home, away)
        away_sit = self.calculate_situational_score(away, home)

        # Composite power ratings
        home_air = (home_qb * 0.6) + ((100.0 - away_pdef) * 0.4)
        away_air = (away_qb * 0.6) + ((100.0 - home_pdef) * 0.4)

        w = self.weights
        w_base = w["qb_passing"] + w["pass_defense"] + w["general_offense"] + w["trenches_ol_dl"] + w["rushing_game"] + w["situational_clutch"]

        home_power = (
            (home_air * (w["qb_passing"] + w["pass_defense"])) +
            (home_off * w["general_offense"]) +
            (home_trench * w["trenches_ol_dl"]) +
            (home_rush * w["rushing_game"]) +
            (home_sit * w["situational_clutch"])
        ) / w_base

        away_power = (
            (away_air * (w["qb_passing"] + w["pass_defense"])) +
            (away_off * w["general_offense"]) +
            (away_trench * w["trenches_ol_dl"]) +
            (away_rush * w["rushing_game"]) +
            (away_sit * w["situational_clutch"])
        ) / w_base

        # Context adjustments
        home_field = 1.8
        weather_penalty = 0.0
        w_data = matchup.get("weather", {})
        if not w_data.get("is_dome", False):
            if w_data.get("wind_mph", 0) >= 15:
                weather_penalty += (w_data.get("wind_mph") - 14) * 0.35
            if w_data.get("temp_f", 70) <= 32:
                weather_penalty += 1.2

        base_pts = 21.8
        scale = 0.32

        mean_home = base_pts + ((home_power - 50.0) * scale) + (home_field / 2.0) - (weather_penalty / 2.0)
        mean_away = base_pts + ((away_power - 50.0) * scale) - (home_field / 2.0) - (weather_penalty / 2.0)

        # Monte Carlo Iterations
        home_wins = 0
        away_wins = 0
        spread_covers = 0
        total_overs = 0
        
        market_spread = matchup["market_action_network"]["current_spread"]
        market_total = matchup["market_action_network"]["current_total"]

        for _ in range(iterations):
            # Normal distribution with NFL standard score variance (~9.5 std per team)
            sim_home = random.gauss(mean_home, 9.5)
            sim_away = random.gauss(mean_away, 9.5)
            
            if sim_home > sim_away:
                home_wins += 1
            else:
                away_wins += 1

            if (sim_home - sim_away) > -market_spread:
                spread_covers += 1

            if (sim_home + sim_away) > market_total:
                total_overs += 1

        home_win_pct = (home_wins / iterations) * 100.0
        away_win_pct = (away_wins / iterations) * 100.0
        spread_cover_pct = (spread_covers / iterations) * 100.0
        over_pct = (total_overs / iterations) * 100.0

        projected_spread = round(mean_away - mean_home, 1)
        projected_total = round(mean_home + mean_away, 1)

        return {
            "matchup_id": matchup["id"],
            "home_team": home["name"],
            "away_team": away["name"],
            "projected_score": f"{away['name']} {mean_away:.1f} @ {home['name']} {mean_home:.1f}",
            "fair_spread_home": projected_spread,
            "fair_total": projected_total,
            "home_win_prob": round(home_win_pct, 1),
            "away_win_prob": round(away_win_pct, 1),
            "spread_cover_prob": round(spread_cover_pct, 1),
            "total_over_prob": round(over_pct, 1)
        }

    def generate_full_weekly_report(self) -> List[Dict[str, Any]]:
        results = []
        for m in self.dataset.get("matchups_week", []):
            res = self.simulate_matchup(m)
            results.append(res)
        return results

if __name__ == "__main__":
    engine = NFLBettingEngine()
    report = engine.generate_full_weekly_report()
    print("=== NFL QUANTUM EDGE - PROYECCIONES SEMANALES ===")
    for r in report:
        print(f"\n{r['away_team']} @ {r['home_team']}")
        print(f"  Proyección: {r['projected_score']}")
        print(f"  Spread Justo: {r['fair_spread_home']} | Total Justo: {r['fair_total']}")
        print(f"  Win%: {r['home_team']} {r['home_win_prob']}% | {r['away_team']} {r['away_win_prob']}%")
