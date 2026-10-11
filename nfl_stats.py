"""
NFL Stats Scraper & Model Feeder
Extrae métricas avanzadas de eficiencia de equipos y estadísticas de jugadores/QB.
Métricas:
- EPA/play ofensivo y defensivo permitido
- Success Rate ofensivo y defensivo permitido
- EPA de pase ofensivo y defensivo permitido
- EPA de carrera ofensivo y defensivo permitido
- PPG y Opp PPG
- Yardas/jugada y permitidas
- Turnover differential
- Sacks permitidos y tasa de presión
- Red zone TD%
- Jugadas explosivas generadas (pases >= 20 yds, carreras >= 10 yds) y permitidas
- Métricas QB: dropback EPA, CPOE, Passer rating, Any/A, TD/INT, sacked%, under pressure rating, fumbles
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

SOURCE_URL_STATS = "https://www.nfl.com/stats/player-stats/"
SOURCE_NAME = "NFL.com NextGen & Official Stats"

def build_team_efficiency_record(
    team_abbr: str,
    off_epa_play: float,
    def_epa_play_allowed: float,
    off_success_rate: float,
    def_success_rate_allowed: float,
    off_pass_epa: float,
    def_pass_epa_allowed: float,
    off_rush_epa: float,
    def_rush_epa_allowed: float,
    points_scored_pg: float,
    points_allowed_pg: float,
    yards_per_play: float,
    yards_per_play_allowed: float,
    turnover_diff: int,
    red_zone_pct: float,
    def_red_zone_pct_allowed: float,
    sacks_allowed_pg: float,
    def_pressure_rate: float,
    explosive_plays_for_pg: float,
    explosive_plays_allowed_pg: float
) -> Dict[str, Any]:
    """Construye el registro estricto del Bloque A (Eficiencia de Equipos)."""
    return {
        "source": SOURCE_NAME,
        "source_url": SOURCE_URL_STATS,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "team": team_abbr,
        # EPA global
        "off_epa_play": float(off_epa_play),
        "def_epa_play_allowed": float(def_epa_play_allowed),
        # Success Rate
        "off_success_rate": float(off_success_rate),
        "def_success_rate_allowed": float(def_success_rate_allowed),
        # Pase EPA
        "off_pass_epa": float(off_pass_epa),
        "def_pass_epa_allowed": float(def_pass_epa_allowed),
        # Carrera EPA
        "off_rush_epa": float(off_rush_epa),
        "def_rush_epa_allowed": float(def_rush_epa_allowed),
        # Puntos & Yardas
        "points_scored_pg": float(points_scored_pg),
        "points_allowed_pg": float(points_allowed_pg),
        "yards_per_play": float(yards_per_play),
        "yards_per_play_allowed": float(yards_per_play_allowed),
        # Balones y Situacional
        "turnover_diff": int(turnover_diff),
        "red_zone_pct": float(red_zone_pct),
        "def_red_zone_pct_allowed": float(def_red_zone_pct_allowed),
        # Presión y Sacks
        "sacks_allowed_pg": float(sacks_allowed_pg),
        "def_pressure_rate": float(def_pressure_rate),
        # Jugadas explosivas
        "explosive_plays_for_pg": float(explosive_plays_for_pg),
        "explosive_plays_allowed_pg": float(explosive_plays_allowed_pg),
    }

def build_qb_record(
    starter_name: str,
    starter_status: str,  # CONFIRMED, QUESTIONABLE, OUT
    epa_dropback: float,
    cpoe: float,
    passer_rating: float,
    yards_pg: float,
    tds: int,
    interceptions: int,
    attempts_pg: float,
    sack_pct: float,
    pass_rating_under_pressure: float,
    fumbles_lost: int,
    backup_name: str,
    backup_status: str,
    backup_downgrade_epa: float  # Pérdida de EPA esperada si juega backup (ej: -0.18)
) -> Dict[str, Any]:
    """Construye el registro estricto del Bloque B (Quarterback)."""
    return {
        "source": SOURCE_NAME,
        "source_url": SOURCE_URL_STATS,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "starter_name": starter_name,
        "starter_status": starter_status,
        "epa_dropback": float(epa_dropback),
        "cpoe": float(cpoe),
        "passer_rating": float(passer_rating),
        "yards_pg": float(yards_pg),
        "touchdowns": int(tds),
        "interceptions": int(interceptions),
        "attempts_pg": float(attempts_pg),
        "sack_pct": float(sack_pct),
        "pass_rating_under_pressure": float(pass_rating_under_pressure),
        "fumbles_lost": int(fumbles_lost),
        "backup_name": backup_name,
        "backup_status": backup_status,
        "backup_downgrade_epa": float(backup_downgrade_epa)
    }
