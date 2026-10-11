"""
Context & Field Adjustments Engine
Evalúa:
- Condición de local y visitante (ventaja de localía dinámica, no fija)
- Estadio, superficie (Turf vs Grass) y altitud (Denver +5280 ft)
- Días de descanso (descanso normal vs semana corta vs bye week)
- Distancia de viaje y cambios de husos horarios
- Temperatura extrema, viento severo y precipitaciones
- Rivalidad divisional (partido divisional)
- Forma reciente ajustada por calidad de rival (SOS)
"""

from typing import Dict, Any

class ContextEngine:
    @classmethod
    def calculate_situational_adjustments(
        cls,
        context: Dict[str, Any],
        is_divisional: bool = False
    ) -> Dict[str, Any]:
        """
        Calcula ajustes netos de puntos proyectados para el equipo local y visitante.
        """
        # 1. Ventaja base de localía (histórica moderna NFL: ~1.4 - 1.8 pts)
        stadium = context.get("stadium", {})
        altitude = stadium.get("altitude_ft", 0)
        
        # Boost de altitud para el local (ej. Denver en Mile High)
        altitude_boost = 0.0
        if altitude > 4000:
            altitude_boost = 0.9
        elif altitude > 1000:
            altitude_boost = 0.3

        base_home_field = 1.5 + altitude_boost

        # 2. Días de descanso diferencial
        rest_home = context.get("rest_days_home", 7)
        rest_away = context.get("rest_days_away", 7)
        rest_diff = rest_home - rest_away
        rest_adj = (rest_diff * 0.25) # Cada día de descanso extra aporta ~0.25 pts

        # 3. Viaje y huso horario para el visitante
        travel_miles = context.get("travel_miles_away", 500)
        tz_crossed = context.get("tz_crossed_away", 0)
        travel_penalty = 0.0
        if travel_miles > 1800 or tz_crossed >= 2:
            travel_penalty = 0.5 + (tz_crossed * 0.25)

        # 4. Clima y condiciones
        weather = context.get("weather", {})
        scoring_factor = weather.get("impact_on_scoring", 1.0)
        passing_factor = weather.get("impact_on_passing", 1.0)
        wind_mph = weather.get("wind_mph", 0.0)
        temp_f = weather.get("temp_f", 65.0)

        # Si hay viento > 18 mph o frío < 25°F se reduce la anotación global y se comprimen las ventajas
        total_points_drag = 0.0
        if wind_mph >= 15:
            total_points_drag += (wind_mph - 14) * 0.4
        if temp_f <= 28:
            total_points_drag += 1.5

        # 5. Partido divisional: reduce la varianza y la ventaja de localía en un ~25%
        if is_divisional:
            base_home_field *= 0.75

        net_home_advantage = base_home_field + rest_adj + travel_penalty

        return {
            "net_home_advantage_points": round(net_home_advantage, 2),
            "altitude_boost": altitude_boost,
            "rest_adjustment": round(rest_adj, 2),
            "travel_penalty_away": round(travel_penalty, 2),
            "weather_drag_points": round(total_points_drag, 2),
            "passing_efficiency_multiplier": round(passing_factor, 2),
            "scoring_multiplier": round(scoring_factor, 2),
            "is_divisional": is_divisional,
            "details": {
                "stadium": stadium.get("name", "Estadio NFL"),
                "altitude_ft": altitude,
                "surface": stadium.get("surface", "Turf"),
                "dome": stadium.get("dome", False),
                "temp_f": temp_f,
                "wind_mph": wind_mph,
                "weather_condition": weather.get("condition", "Normal")
            }
        }
