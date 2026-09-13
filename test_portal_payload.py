from models import DayBatch, Order, ShipmentInfo
from portal_client import build_payload


batch = DayBatch("2026-09-12", [Order(
    order_id="123",
    url="https://marketplace.liverpool.com.mx/orders/detail/123",
    fecha_clave="2026-09-12",
    fecha_texto="12/09/2026 - 06:00",
    estado="Pendiente de envío",
    shipments=[ShipmentInfo(carrier="UPS", tracking_number="1Z6751V50439609622", tracking_url="https://www.ups.com/track")],
)])
payload = build_payload({batch.date: batch}, [batch.date])
assert payload["days"][0]["orders"][0]["shipments"][0]["carrier"] == "UPS"
print("portal payload: ok")
