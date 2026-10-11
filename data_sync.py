"""
NFL Quantum Edge - Data Pipeline Sync
Módulo de sincronización para actualizar estadísticas, clima en vivo y momios de mercado.
"""

import json
import urllib.request
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "teams_data.json"

def fetch_weather_openmeteo(lat: float, lon: float):
    """Consulta clima en tiempo real para estadios al aire libre."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            current = data.get("current", {})
            temp_c = current.get("temperature_2m", 20)
            temp_f = round((temp_c * 9/5) + 32, 1)
            wind_kmh = current.get("wind_speed_10m", 10)
            wind_mph = round(wind_kmh * 0.621371, 1)
            precip = current.get("precipitation", 0)
            return {
                "temp_f": temp_f,
                "wind_mph": wind_mph,
                "precip_pct": 80 if precip > 0 else 10,
                "condition": "Rain" if precip > 0 else ("Windy" if wind_mph > 15 else "Clear/Partly Cloudy")
            }
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None

def update_dataset():
    print("Sincronizando pipeline de datos NFL Quantum Edge...")
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Dataset cargado correctamente con {len(data['teams'])} equipos y {len(data['matchups_week'])} partidos.")
    else:
        print("Archivo de datos no encontrado.")

if __name__ == "__main__":
    update_dataset()
