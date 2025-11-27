# models.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class OrderItem:
    title: str
    qty: int
    screenshot_path: Path | None = None


@dataclass
class Order:
    order_id: str
    url: str
    fecha_clave: str       # YYYY-MM-DD
    fecha_texto: str       # "dd/mm/yyyy - hh:mm"
    estado: str
    items: List[OrderItem] = field(default_factory=list)
    status: str = "pending"   # "pending", "ok", "skipped", "error", etc.


@dataclass
class DayBatch:
    date: str  # YYYY-MM-DD
    orders: List[Order] = field(default_factory=list)


@dataclass
class AppConfig:
    """
    Configuración general de la app (rutas, perfil de Edge, etc.)
    Los valores por defecto se ponen en main.py usando config.py
    """
    base_dir: Path
    edge_user_data_dir: Path
    edge_profile_name: str
