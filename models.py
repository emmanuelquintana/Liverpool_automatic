# models.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class OrderItem:
    title: str
    qty: int
    screenshot_path: Path | None = None
    sku_oferta: str = ""
    talla: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "qty": self.qty,
            "screenshot_path": str(self.screenshot_path) if self.screenshot_path else None,
            "sku_oferta": self.sku_oferta,
            "talla": self.talla,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            title=data.get("title", ""),
            qty=data.get("qty", 1),
            screenshot_path=Path(data["screenshot_path"]) if data.get("screenshot_path") else None,
            sku_oferta=data.get("sku_oferta", ""),
            talla=data.get("talla", ""),
        )


@dataclass
class ShipmentInfo:
    carrier: str = ""
    guide_status: str = ""
    guide_type: str = ""
    tracking_number: str = ""
    tracking_url: str = ""
    logistics_charge_status: str = ""

    def to_dict(self):
        return {
            "carrier": self.carrier,
            "guide_status": self.guide_status,
            "guide_type": self.guide_type,
            "tracking_number": self.tracking_number,
            "tracking_url": self.tracking_url,
            "logistics_charge_status": self.logistics_charge_status,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            carrier=data.get("carrier", ""),
            guide_status=data.get("guide_status", ""),
            guide_type=data.get("guide_type", ""),
            tracking_number=data.get("tracking_number", ""),
            tracking_url=data.get("tracking_url", ""),
            logistics_charge_status=data.get("logistics_charge_status", ""),
        )


@dataclass
class Order:
    order_id: str
    url: str
    fecha_clave: str       # YYYY-MM-DD
    fecha_texto: str       # "dd/mm/yyyy - hh:mm"
    estado: str
    items: List[OrderItem] = field(default_factory=list)
    shipments: List[ShipmentInfo] = field(default_factory=list)
    status: str = "pending"   # "pending", "ok", "skipped", "error", etc.

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "url": self.url,
            "fecha_clave": self.fecha_clave,
            "fecha_texto": self.fecha_texto,
            "estado": self.estado,
            "items": [item.to_dict() for item in self.items],
            "shipments": [shipment.to_dict() for shipment in self.shipments],
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
            shipments=[ShipmentInfo.from_dict(i) for i in data.get("shipments", [])],
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
    headless: bool = False
    download_dir: Path | None = None
