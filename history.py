# history.py
"""
Registro persistente de operaciones realizadas → history.json
Máximo 100 entradas (FIFO).
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

_HISTORY_FILE = Path(__file__).resolve().parent / "history.json"
_MAX_ENTRIES = 100


def record(event_type: str, dates: List[str], stats: Optional[dict] = None):
    """Registra un evento en el historial."""
    try:
        history = _load()
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "dates": dates,
            "stats": stats or {},
        })
        # FIFO: mantener solo las últimas N entradas
        history = history[-_MAX_ENTRIES:]
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] history.record falló: {e}")


def get_recent(n: int = 30) -> List[dict]:
    """Devuelve las últimas N entradas del historial (más reciente primero)."""
    return list(reversed(_load()[-n:]))


def _load() -> List[dict]:
    try:
        if _HISTORY_FILE.exists():
            with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []
