"""
Matchup Breakdown Engine
Calcula las 6 colisiones clave entre ambos equipos:
1. Ataque aéreo frente a defensa aérea
2. Ataque terrestre frente a defensa terrestre
3. Presión defensiva frente a protección de la OL
4. Success Rate de ataque frente a Success Rate permitido
5. Eficiencia en tercera oportunidad y zona roja
6. Jugadas explosivas a favor frente a permitidas
"""

from typing import Dict, Any

class MatchupEngine:
    @staticmethod
    def _normalize(val: float, min_val: float, max_val: float) -> float:
        return max(0.0, min(100.0, ((val - min_val) / (max_val - min_val)) * 100.0))

    @classmethod
    def evaluate_side_matchup(
        cls,
        off_team: Dict[str, Any],
        off_qb_eval: Dict[str, Any],
        off_pfr: Dict[str, Any],
        off_injuries: Dict[str, Any],
        def_team: Dict[str, Any],
        def_pfr: Dict[str, Any],
        def_injuries: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evalúa la ofensiva del equipo A contra la defensiva del equipo B.
        """
        # 1. Aire vs Defensa Aérea
        # off_pass_epa y qb_effective_rating vs def_pass_epa_allowed y presión defensiva
        off_air_epa = off_team.get("off_pass_epa", 0.0)
        def_air_allowed = def_team.get("def_pass_epa_allowed", 0.0)
        # Diferencial neto de pase
        air_diff = off_air_epa - def_air_allowed
        qb_rating = off_qb_eval.get("effective_rating", 50.0)
        air_score = cls._normalize(air_diff, -0.30, 0.30) * 0.6 + qb_rating * 0.4

        # 2. Carrera vs Defensa Terrestre
        off_rush_epa = off_team.get("off_rush_epa", 0.0)
        def_rush_allowed = def_team.get("def_rush_epa_allowed", 0.0)
        rush_diff = off_rush_epa - def_rush_allowed
        ground_score = cls._normalize(rush_diff, -0.25, 0.25)

        # 3. Presión defensiva vs Protección de la OL
        pbwr = off_pfr.get("pass_block_win_rate", 58.0)
        prwr = def_pfr.get("pass_rush_win_rate", 42.0)
        # Descuento si la OL tiene lesionados
        ol_penalty = off_injuries.get("ol_health", {}).get("ol_penalty_points", 0.0)
        adjusted_pbwr = max(30.0, pbwr - (ol_penalty * 2.0))
        trench_diff = adjusted_pbwr - prwr
        trench_score = cls._normalize(trench_diff, -20.0, 30.0)

        # 4. Success Rate ofensivo vs permitido
        off_sr = off_team.get("off_success_rate", 44.0)
        def_sr_allowed = def_team.get("def_success_rate_allowed", 44.0)
        sr_diff = off_sr - def_sr_allowed
        sr_score = cls._normalize(sr_diff, -15.0, 15.0)

        # 5. Tercera oportunidad y Zona Roja
        rz_off = off_team.get("red_zone_pct", 55.0)
        rz_def = def_team.get("def_red_zone_pct_allowed", 55.0)
        third_off = off_pfr.get("third_down_conv_pct", 40.0)
        third_def = def_pfr.get("third_down_def_pct_allowed", 40.0)
        sit_diff = ((rz_off - rz_def) * 0.5) + ((third_off - third_def) * 0.5)
        situational_score = cls._normalize(sit_diff, -25.0, 25.0)

        # 6. Jugadas Explosivas
        exp_for = off_team.get("explosive_plays_for_pg", 4.5)
        exp_allowed = def_team.get("explosive_plays_allowed_pg", 4.5)
        exp_diff = exp_for - exp_allowed
        explosive_score = cls._normalize(exp_diff, -4.0, 4.0)

        # Puntuación global del enfrentamiento (0 - 100)
        composite_score = (
            air_score * 0.28 +
            ground_score * 0.15 +
            trench_score * 0.18 +
            sr_score * 0.15 +
            situational_score * 0.14 +
            explosive_score * 0.10
        )

        return {
            "air_matchup_score": round(air_score, 1),
            "ground_matchup_score": round(ground_score, 1),
            "trench_protection_score": round(trench_score, 1),
            "success_rate_advantage": round(sr_score, 1),
            "situational_clutch_score": round(situational_score, 1),
            "explosive_advantage_score": round(explosive_score, 1),
            "composite_offensive_strength": round(composite_score, 2),
            "key_factors": {
                "air_epa_diff": round(air_diff, 3),
                "rush_epa_diff": round(rush_diff, 3),
                "trench_diff_adj": round(trench_diff, 1),
                "sr_diff": round(sr_diff, 1),
                "red_zone_diff": round(rz_off - rz_def, 1)
            }
        }
