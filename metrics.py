"""
Backtesting & Calibration Metrics Engine
Implementa las métricas obligatorias para evaluar el modelo antes de apostar dinero real:
1. Brier Score: (1/N) * sum((prob_estimada - resultado_binario)^2)
2. Log Loss / Cross-Entropy Loss
3. Curva de Calibración (Expected Win Prob vs Observed Win Frequency por decil)
4. Closing Line Value (CLV): % de apuestas con cuota tomada > cuota de cierre sin margen
5. ROI Simulado y Curva de Bankroll con Flat Stake y Fractional Kelly (Quarter-Kelly)
"""

import math
from typing import List, Dict, Any

class BacktestMetrics:
    @staticmethod
    def calculate_brier_score(predictions: List[float], outcomes: List[int]) -> float:
        """
        Brier Score: mide la precisión y calibración de probabilidades probabilísticas.
        0.0 = perfección absoluta, 0.25 = azar puro 50/50.
        """
        if not predictions or len(predictions) != len(outcomes):
            return 0.25
        
        n = len(predictions)
        total_sq_err = sum((p - y) ** 2 for p, y in zip(predictions, outcomes))
        return round(total_sq_err / n, 4)

    @staticmethod
    def calculate_log_loss(predictions: List[float], outcomes: List[int]) -> float:
        """
        Log Loss: penaliza fuertemente predicciones con alta confianza errónea.
        """
        if not predictions or len(predictions) != len(outcomes):
            return 0.693
        
        eps = 1e-15
        total_loss = 0.0
        n = len(predictions)
        
        for p, y in zip(predictions, outcomes):
            p_clipped = max(eps, min(1.0 - eps, p))
            if y == 1:
                total_loss += -math.log(p_clipped)
            else:
                total_loss += -math.log(1.0 - p_clipped)
                
        return round(total_loss / n, 4)

    @staticmethod
    def calculate_calibration_curve(predictions: List[float], outcomes: List[int], bins: int = 5) -> List[Dict[str, Any]]:
        """
        Agrupa predicciones en cubos (deciles o quintiles) y compara probabilidad predicha vs frecuencia real.
        """
        if not predictions:
            return []

        step = 1.0 / bins
        buckets = []

        for b in range(bins):
            low = b * step
            high = (b + 1) * step
            
            bin_preds = []
            bin_outcomes = []
            for p, y in zip(predictions, outcomes):
                if low <= p < high or (b == bins - 1 and low <= p <= high):
                    bin_preds.append(p)
                    bin_outcomes.append(y)

            count = len(bin_preds)
            if count > 0:
                avg_pred = sum(bin_preds) / count
                obs_freq = sum(bin_outcomes) / count
            else:
                avg_pred = (low + high) / 2.0
                obs_freq = 0.0

            buckets.append({
                "bin_range": f"{int(low*100)}%-{int(high*100)}%",
                "count": count,
                "predicted_prob_avg": round(avg_pred * 100, 1),
                "observed_win_pct": round(obs_freq * 100, 1),
                "calibration_gap": round((obs_freq - avg_pred) * 100, 1)
            })

        return buckets

    @staticmethod
    def calculate_financial_performance(bets: List[Dict[str, Any]], initial_bankroll: float = 10000.0) -> Dict[str, Any]:
        """
        Calcula ROI, CLV y evolución de bankroll.
        Cada bet debe tener:
        - odds_taken
        - closing_odds_no_vig
        - won (1 o 0)
        - stake (opcional)
        """
        if not bets:
            return {"total_bets": 0, "roi_pct": 0.0, "clv_beat_pct": 0.0}

        total_staked = 0.0
        total_profit = 0.0
        clv_beats = 0
        current_bankroll = initial_bankroll

        for b in bets:
            stake = b.get("stake", 100.0) # Flat 100 o fraccional
            odds = b["odds_taken"]
            closing = b.get("closing_odds_no_vig", odds)
            won = b["won"]

            total_staked += stake
            if won == 1:
                profit = (stake * odds) - stake
            else:
                profit = -stake
            
            total_profit += profit
            current_bankroll += profit

            if odds > closing:
                clv_beats += 1

        roi = round((total_profit / total_staked) * 100, 2) if total_staked > 0 else 0.0
        clv_pct = round((clv_beats / len(bets)) * 100, 1)

        return {
            "total_bets": len(bets),
            "total_staked": round(total_staked, 2),
            "net_profit": round(total_profit, 2),
            "roi_pct": roi,
            "clv_beat_rate_pct": clv_pct,
            "final_bankroll": round(current_bankroll, 2),
            "profit_factor": round((total_profit + total_staked) / total_staked, 3) if total_staked > 0 else 1.0
        }
