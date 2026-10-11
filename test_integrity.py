"""
Test Suite: Reglas de Integridad y Validación
Verifica:
1. No invención/imputación de datos faltantes.
2. Detección de QB sin confirmar -> Marcado formal como PENDIENTE.
3. Validación de los 6 bloques completos de datos (A, B, C, D, E, F).
4. Guardado de snapshots inmutables para trazabilidad y auditoría.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
from data_pipeline.data_cleaner import IntegrityValidator, save_immutable_snapshot
from config.settings import DATA_DIR, SNAPSHOTS_DIR

def test_integrity_validation():
    slate_file = DATA_DIR / "slate_week.json"
    with open(slate_file, "r", encoding="utf-8") as f:
        slate = json.load(f)

    matchups = slate["matchups"]
    print(f"Probando {len(matchups)} partidos en la jornada...")

    # Validar que los partidos completos pasen
    for game in matchups:
        is_valid, errors = IntegrityValidator.validate_game_dataset(game)
        if game["game_id"] == "GAME_CIN_MIA":
            assert is_valid is False, "El partido CIN@MIA debería fallar por falta de confirmación de QB"
            assert any("no está confirmado formalmente" in e for e in errors), f"Error de confirmación esperado no detectado: {errors}"
            print(f"  [PASS] Integridad estricta comprobada en CIN@MIA: {errors}")
        else:
            assert is_valid is True, f"El partido {game['game_id']} debería ser válido. Errores: {errors}"
            save_immutable_snapshot(game["game_id"], game)
            print(f"  [PASS] Partido {game['game_id']} validado y snapshot guardado.")

if __name__ == "__main__":
    test_integrity_validation()
    print("TODOS LOS TESTS DE INTEGRIDAD PASARON CORRECTAMENTE.")
