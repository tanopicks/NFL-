"""
NFL Quantum Edge - Local Server & Pipeline API
Servidor HTTP local con soporte para servir la interfaz UI y API endpoints:
- GET / : Interfaz web UI
- POST /api/run_pipeline : Ejecuta la pipeline completa en segundo plano y devuelve el reporte
- GET /api/report : Retorna el último reporte en formato JSON
- GET /api/backtest : Ejecuta y retorna las métricas de backtesting
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core_engine.weekly_runner import run_weekly_pipeline
from backtesting.chronological_runner import ChronologicalRunner
from config.settings import HISTORICAL_DIR, DATA_DIR

PORT = 8080

class QuantumEdgeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "ui"), **kwargs)

    def do_POST(self):
        if self.path == "/api/run_pipeline":
            try:
                report = run_weekly_pipeline()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(report, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self.send_error(404, "Endpoint no encontrado")

    def do_GET(self):
        if self.path == "/api/report":
            report_file = DATA_DIR / "weekly_intelligence_report.json"
            if report_file.exists():
                with open(report_file, "r", encoding="utf-8") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(data.encode("utf-8"))
            else:
                self.send_error(404, "Reporte no generado aún")
            return
        elif self.path == "/api/backtest":
            hist_file = HISTORICAL_DIR / "nfl_historical_50_games.json"
            if hist_file.exists():
                with open(hist_file, "r", encoding="utf-8") as f:
                    games = json.load(f)
                runner = ChronologicalRunner(games)
                results = runner.run_backtest()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(results, ensure_ascii=False).encode("utf-8"))
            else:
                self.send_error(404, "Dataset histórico no encontrado")
            return

        # Para cualquier otra ruta, servir archivos estáticos desde ui/
        super().do_GET()

def start():
    # Generar pipeline inicial si no existe
    report_file = DATA_DIR / "weekly_intelligence_report.json"
    if not report_file.exists():
        run_weekly_pipeline()

    with socketserver.TCPServer(("", PORT), QuantumEdgeHandler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print(f"==================================================")
        print(f"[+] NFL Predictive System corriendo en: {url}")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")

if __name__ == "__main__":
    start()
