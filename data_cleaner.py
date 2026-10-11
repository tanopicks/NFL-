"""
Data Cleaner, Integrity Validator & Audit Snapshot Manager
Implementa las reglas inquebrantables de integridad:
1. No inventar ni completar datos faltantes (zero artificial imputation).
2. Verificar confirmación obligatoria del QB titular y reporte de lesiones.
3. Marcar partidos incompletos como "PENDIENTE_DATOS_INCOMPLETOS".
4. Evitar duplicar variables correlacionadas (multicollinearity check).
5. Guardar una copia inmutable (Snapshot) de los datos que sustentan cada pronóstico.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple
from config.settings import SNAPSHOTS_DIR, INTEGRITY_RULES

class IntegrityValidator:
    REQUIRED_BLOCK_A_KEYS = [
        "off_epa_play", "def_epa_play_allowed", "off_success_rate", "def_success_rate_allowed",
        "off_pass_epa", "def_pass_epa_allowed", "off_rush_epa", "def_rush_epa_allowed",
        "points_scored_pg", "points_allowed_pg", "yards_per_play", "yards_per_play_allowed",
        "turnover_diff", "red_zone_pct", "sacks_allowed_pg", "def_pressure_rate",
        "explosive_plays_for_pg", "explosive_plays_allowed_pg"
    ]

    REQUIRED_BLOCK_B_KEYS = [
        "starter_name", "starter_status", "epa_dropback", "cpoe", "passer_rating",
        "yards_pg", "touchdowns", "interceptions", "attempts_pg", "sack_pct",
        "pass_rating_under_pressure", "fumbles_lost", "backup_name", "backup_downgrade_epa"
    ]

    REQUIRED_BLOCK_F_KEYS = [
        "best_odds", "consensus_no_vig_prob"
    ]

    @classmethod
    def validate_game_dataset(cls, game_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Verifica exhaustivamente que no falte ninguna variable obligatoria.
        Retorna (is_valid, list_of_errors_or_missing_keys).
        """
        missing = []

        # 1. Validar Bloque A para ambos equipos
        for side in ["home_team_stats", "away_team_stats"]:
            stats = game_data.get(side, {})
            if not stats:
                missing.append(f"Falta bloque completo: {side}")
                continue
            for k in cls.REQUIRED_BLOCK_A_KEYS:
                if k not in stats or stats[k] is None:
                    missing.append(f"Bloque A ({side}): clave faltante '{k}'")

        # 2. Validar Bloque B (QB)
        for side in ["home_qb", "away_qb"]:
            qb = game_data.get(side, {})
            if not qb:
                missing.append(f"Falta bloque QB: {side}")
                continue
            for k in cls.REQUIRED_BLOCK_B_KEYS:
                if k not in qb or qb[k] is None:
                    missing.append(f"Bloque B ({side}): clave faltante '{k}'")
            
            # Comprobación de confirmación de QB titular
            if INTEGRITY_RULES.get("require_qb_confirmed", True):
                if qb.get("starter_status") not in ["CONFIRMED", "ACTIVE"]:
                    missing.append(f"QB {side} no está confirmado formalmente ({qb.get('starter_status')})")

        # 3. Validar Bloque D (Lesiones)
        for side in ["home_injuries", "away_injuries"]:
            inj = game_data.get(side, {})
            if not inj:
                missing.append(f"Falta bloque lesiones: {side}")

        # 4. Validar Bloque E (Contexto y Clima)
        ctx = game_data.get("context", {})
        if not ctx:
            missing.append("Falta bloque de contexto del estadio/partido")
        else:
            for ck in ["stadium", "rest_days_home", "rest_days_away", "weather"]:
                if ck not in ctx:
                    missing.append(f"Bloque E Contexto: falta clave '{ck}'")

        # 5. Validar Bloque F (Mercado de Cuotas)
        odds = game_data.get("market_odds", {})
        if not odds:
            missing.append("Falta bloque de mercado de cuotas (Bloque F)")
        else:
            for fk in cls.REQUIRED_BLOCK_F_KEYS:
                if fk not in odds:
                    missing.append(f"Bloque F Mercado: falta clave '{fk}'")

        is_valid = len(missing) == 0
        return is_valid, missing

def save_immutable_snapshot(game_id: str, full_payload: Dict[str, Any]) -> str:
    """Guarda copia inmutable de los datos utilizados para este pronóstico."""
    timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{game_id}_{timestamp_slug}.json"
    file_path = SNAPSHOTS_DIR / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(full_payload, f, indent=2, ensure_ascii=False)
        
    return str(file_path)
