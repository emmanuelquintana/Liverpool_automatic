# main.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import customtkinter as ctk

from models import AppConfig
from config import (
    DEFAULT_BASE_DIR,
    DEFAULT_EDGE_USER_DATA_DIR,
    DEFAULT_EDGE_PROFILE_NAME,
)
from settings import load_settings


def _setup_file_logging():
    """Configura un log rotativo: liverpool_auto.log (máx 5 MB × 3 backups)."""
    log_file = Path(__file__).resolve().parent / "liverpool_auto.log"
    handler = RotatingFileHandler(
        str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s  %(message)s", datefmt="[%Y-%m-%d %H:%M:%S]")
    )
    logger = logging.getLogger("liverpool")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def main():
    saved = load_settings()

    # Apariencia debe configurarse ANTES de importar view
    appearance = saved.get("appearance_mode", "Dark")
    ctk.set_appearance_mode(appearance)
    ctk.set_default_color_theme("dark-blue")

    # Log a archivo
    _setup_file_logging()

    base_dir = Path(saved.get("base_dir", str(DEFAULT_BASE_DIR)))
    config = AppConfig(
        base_dir=base_dir,
        edge_user_data_dir=DEFAULT_EDGE_USER_DATA_DIR,
        edge_profile_name=DEFAULT_EDGE_PROFILE_NAME,
    )

    # Importar aquí para que ctk ya esté configurado
    from view import LiverpoolApp
    app = LiverpoolApp(config)
    app.mainloop()


if __name__ == "__main__":
    main()
