"""
Pro Football Reference (PFR) Stats Scraper & Trench Extractor
Métricas:
- Pass Block Win Rate (PBWR) & Run Block Win Rate (RBWR)
- Pass Rush Win Rate (PRWR) & Run Stop Rate
- Presiones defensivas generadas (QB hurries, knockdowns, blitzes)
- Tasa de captura / Sacks permitidos
- Puntos por serie ofensiva (Points Per Drive - PPD)
- Eficiencia de 3ra y 4ta oportunidad
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

SOURCE_URL_PFR = "https://www.pro-football-reference.com/"
SOURCE_NAME_PFR = "Pro Football Reference"

def build_pfr_advanced_record(
    team_abbr: str,
    pass_block_win_rate: float,
    run_block_win_rate: float,
    pass_rush_win_rate: float,
    run_stop_rate: float,
    blitz_rate_def: float,
    points_per_drive: float,
    third_down_conv_pct: float,
    third_down_def_pct_allowed: float,
    fourth_down_conv_pct: float
) -> Dict[str, Any]:
    """Construye métricas de trincheras y situación de PFR."""
    return {
        "source": SOURCE_NAME_PFR,
        "source_url": SOURCE_URL_PFR,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "team": team_abbr,
        "pass_block_win_rate": float(pass_block_win_rate),
        "run_block_win_rate": float(run_block_win_rate),
        "pass_rush_win_rate": float(pass_rush_win_rate),
        "run_stop_rate": float(run_stop_rate),
        "blitz_rate_def": float(blitz_rate_def),
        "points_per_drive": float(points_per_drive),
        "third_down_conv_pct": float(third_down_conv_pct),
        "third_down_def_pct_allowed": float(third_down_def_pct_allowed),
        "fourth_down_conv_pct": float(fourth_down_conv_pct),
    }
