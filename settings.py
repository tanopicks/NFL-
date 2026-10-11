"""
NFL Predictive & Value System - Configuration Settings
Define umbrales conservadores de valor esperado, calibración, pesos y parámetros operativos.
"""

from pathlib import Path
from typing import Dict, Any

# Rutas del sistema
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
STORAGE_DIR = BASE_DIR / "storage"
SNAPSHOTS_DIR = STORAGE_DIR / "snapshots"
HISTORICAL_DIR = STORAGE_DIR / "historical"

# Asegurar directorios
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)

# Umbrales conservadores de apuestas
CONSERVATIVE_CRITERIA = {
    # Umbral mínimo de Valor Esperado (+EV) para clasificar como APUESTA CANDIDATA
    "min_ev_edge_pct": 3.5,        # 3.5% de valor esperado mínimo
    "max_ev_edge_cap": 25.0,       # Edge sospechoso por encima del 25% (posible dato erróneo/no confirmado)
    "min_odds": 1.45,              # Evitar favoritos extremos (riesgo asimétrico negativo)
    "max_odds": 4.50,              # Evitar underdogs de lotería alta varianza
    "margin_of_safety_pct": 2.0,   # Margen de seguridad sobre cuota justa (Fair Odds * 1.02)
    "max_brier_score_allowed": 0.22, # Límite de calibración histórica del modelo
    "kelly_fraction": 0.25,        # Criterio fraccional de Kelly conservador (Quarter-Kelly)
    "max_bankroll_risk_per_bet": 0.02, # Máximo 2% del bankroll en una sola apuesta
}

# Reglas de integridad
INTEGRITY_RULES = {
    "require_qb_confirmed": True,
    "max_hours_since_injury_report": 72.0,
    "require_all_6_blocks": True,
    "allow_imputation": False,     # PROHIBIDO imputar datos faltantes
}

# Ventanas de análisis y ponderación temporal
ANALYSIS_WINDOWS = {
    "season": {"name": "Temporada Actual", "weight": 0.35},
    "l8": {"name": "Últimos 8 Partidos", "weight": 0.25},
    "l5": {"name": "Últimos 5 Partidos", "weight": 0.25},
    "l3": {"name": "Últimos 3 Partidos", "weight": 0.15},
}

# Ponderación de factores en el choque de enfrentamiento
MATCHUP_WEIGHTS = {
    "passing_game": 0.28,      # EPA Pase + CPOE vs Defensa Aérea + Presión
    "pass_defense_rush": 0.22, # Capacidad defensiva contra pase y generación de sacks
    "rushing_game": 0.12,      # EPA Carrera + Stuff Rate vs Defensa Terrestre
    "trench_ol_dl": 0.15,      # Pass/Run Block Win Rate vs Pass Rush / Run Stop
    "situational": 0.13,       # Red Zone TD% + 3ra oportunidad + Explosivas
    "context_factors": 0.10,   # Descanso, viaje, huso horario, clima extremo, rivalidad
}
