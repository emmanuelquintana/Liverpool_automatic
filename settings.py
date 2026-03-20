# settings.py
"""
Persistencia de configuración de usuario entre sesiones.
Guarda y carga settings.json en el mismo directorio que el script.
"""
import json
from pathlib import Path

_SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"


def load_settings() -> dict:
    """Carga settings.json. Devuelve {} si no existe o es inválido."""
    try:
        if _SETTINGS_FILE.exists():
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_settings(data: dict):
    """Guarda el diccionario en settings.json (merge con lo existente)."""
    try:
        current = load_settings()
        current.update(data)
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] No se pudo guardar settings: {e}")
