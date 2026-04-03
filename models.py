# models.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class OrderItem:
    title: str
    qty: int
    screenshot_path: Path | None = None

    def to_dict(self):
        return {
            "title": self.title,
            "qty": self.qty,
            "screenshot_path": str(self.screenshot_path) if self.screenshot_path else None
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            title=data.get("title", ""),
            qty=data.get("qty", 1),
            screenshot_path=Path(data["screenshot_path"]) if data.get("screenshot_path") else None
        )


@dataclass
class Order:
    order_id: str
    url: str
    fecha_clave: str       # YYYY-MM-DD
    fecha_texto: str       # "dd/mm/yyyy - hh:mm"
    estado: str
    items: List[OrderItem] = field(default_factory=list)
    status: str = "pending"   # "pending", "ok", "skipped", "error", etc.

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "url": self.url,
            "fecha_clave": self.fecha_clave,
            "fecha_texto": self.fecha_texto,
            "estado": self.estado,
            "items": [item.to_dict() for item in self.items],
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            order_id=data.get("order_id", ""),
            url=data.get("url", ""),
            fecha_clave=data.get("fecha_clave", ""),
            fecha_texto=data.get("fecha_texto", ""),
            estado=data.get("estado", ""),
            items=[OrderItem.from_dict(i) for i in data.get("items", [])],
            status=data.get("status", "pending")
        )


@dataclass
class DayBatch:
    date: str  # YYYY-MM-DD
    orders: List[Order] = field(default_factory=list)

    def to_dict(self):
        return {
            "date": self.date,
            "orders": [o.to_dict() for o in self.orders]
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            date=data.get("date", ""),
            orders=[Order.from_dict(o) for o in data.get("orders", [])]
        )


@dataclass
class AppConfig:
    """
    Configuración general de la app (rutas, perfil de Edge, etc.)
    Los valores por defecto se ponen en main.py usando config.py
    """
    base_dir: Path
    edge_user_data_dir: Path
    edge_profile_name: str
    timeout: int = 120
    fallback_driver: str = r"C:\WebDrivers\msedgedriver.exe"
    overwrite_outputs: bool = True
