"""
The Odds API Client & Market Engine
Gestiona cuotas de mercado, cuotas de apertura y actuales, desmargenado (No-Vig) y detección del mejor precio.
Métricas y cálculos:
- Moneyline local y visitante por casa de apuestas
- Cuota de apertura y cuota actual
- Timestamp de consulta ISO-8601
- Detección de la mejor cuota disponible en el mercado
- Probabilidad implícita bruta: 1 / cuota decimal
- Probabilidad sin margen (No-Vig) mediante normalización proporcional:
    P_no_vig = P_raw / sum(P_raw)
- Detección de movimiento de línea (Line Movement)
- Almacenamiento de cuota de cierre para CLV (Closing Line Value)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

SOURCE_URL_ODDS = "https://the-odds-api.com/sports/nfl-odds.html"
SOURCE_NAME_ODDS = "The Odds API & Sportsbook Aggregator"

def american_to_decimal(american: int) -> float:
    """Convierte momio americano a cuota decimal europea."""
    if american > 0:
        return round(1.0 + (american / 100.0), 3)
    else:
        return round(1.0 + (100.0 / abs(american)), 3)

def decimal_to_american(decimal_odds: float) -> int:
    """Convierte cuota decimal a momio americano."""
    if decimal_odds >= 2.0:
        return int(round((decimal_odds - 1.0) * 100))
    else:
        return int(round(-100.0 / (decimal_odds - 1.0)))

def remove_vig_multiplicative(odds_home: float, odds_away: float) -> Tuple[float, float, float]:
    """
    Elimina el margen de la casa de apuestas por el método multiplicativo estándar.
    Retorna: (p_home_no_vig, p_away_no_vig, vig_percentage)
    """
    if odds_home <= 1.0 or odds_away <= 1.0:
        return 0.5, 0.5, 0.0
    
    p_home_raw = 1.0 / odds_home
    p_away_raw = 1.0 / odds_away
    total_implied = p_home_raw + p_away_raw
    vig = (total_implied - 1.0) * 100.0

    p_home_no_vig = p_home_raw / total_implied
    p_away_no_vig = p_away_raw / total_implied

    return round(p_home_no_vig, 4), round(p_away_no_vig, 4), round(vig, 2)

class MarketOddsTracker:
    def __init__(self, game_id: str, home_team: str, away_team: str):
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team
        self.source = SOURCE_NAME_ODDS
        self.source_url = SOURCE_URL_ODDS
        self.extracted_at = datetime.now(timezone.utc).isoformat()
        self.books: Dict[str, Dict[str, Any]] = {}

    def add_book_odds(
        self,
        book_name: str,
        open_home_decimal: float,
        open_away_decimal: float,
        curr_home_decimal: float,
        curr_away_decimal: float,
        closing_home_decimal: float = None,
        closing_away_decimal: float = None
    ):
        p_home_nv, p_away_nv, vig = remove_vig_multiplicative(curr_home_decimal, curr_away_decimal)
        
        # Movimiento de cuota
        home_move = round(curr_home_decimal - open_home_decimal, 3)
        away_move = round(curr_away_decimal - open_away_decimal, 3)

        self.books[book_name] = {
            "open_odds": {
                "home": open_home_decimal,
                "away": open_away_decimal,
                "home_american": decimal_to_american(open_home_decimal),
                "away_american": decimal_to_american(open_away_decimal)
            },
            "current_odds": {
                "home": curr_home_decimal,
                "away": curr_away_decimal,
                "home_american": decimal_to_american(curr_home_decimal),
                "away_american": decimal_to_american(curr_away_decimal)
            },
            "closing_odds": {
                "home": closing_home_decimal,
                "away": closing_away_decimal
            } if closing_home_decimal else None,
            "raw_implied_prob": {
                "home": round((1.0 / curr_home_decimal) * 100, 2),
                "away": round((1.0 / curr_away_decimal) * 100, 2)
            },
            "no_vig_prob": {
                "home": round(p_home_nv * 100, 2),
                "away": round(p_away_nv * 100, 2)
            },
            "vig_pct": vig,
            "line_movement": {
                "home_delta": home_move,
                "away_delta": away_move,
                "steam_trend": "HOME_STEAM" if home_move < -0.10 else ("AWAY_STEAM" if away_move < -0.10 else "STABLE")
            }
        }

    def get_market_summary(self) -> Dict[str, Any]:
        """Calcula las mejores cuotas del mercado y el consenso sin margen."""
        if not self.books:
            return {}

        best_home_odds = max(b["current_odds"]["home"] for b in self.books.values())
        best_away_odds = max(b["current_odds"]["away"] for b in self.books.values())
        
        best_home_book = next(name for name, b in self.books.items() if b["current_odds"]["home"] == best_home_odds)
        best_away_book = next(name for name, b in self.books.items() if b["current_odds"]["away"] == best_away_odds)

        # Consenso promedio No-Vig
        avg_home_nv = sum(b["no_vig_prob"]["home"] for b in self.books.values()) / len(self.books)
        avg_away_nv = sum(b["no_vig_prob"]["away"] for b in self.books.values()) / len(self.books)

        return {
            "source": self.source,
            "source_url": self.source_url,
            "extracted_at": self.extracted_at,
            "best_odds": {
                "home": {
                    "odds_decimal": best_home_odds,
                    "odds_american": decimal_to_american(best_home_odds),
                    "sportsbook": best_home_book
                },
                "away": {
                    "odds_decimal": best_away_odds,
                    "odds_american": decimal_to_american(best_away_odds),
                    "sportsbook": best_away_book
                }
            },
            "consensus_no_vig_prob": {
                "home": round(avg_home_nv, 2),
                "away": round(avg_away_nv, 2)
            },
            "books_detail": self.books
        }
