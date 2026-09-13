from pathlib import Path

from models import AppConfig, DayBatch, Order, ShipmentInfo
from services import LiverpoolService


class Driver:
    def __init__(self):
        self.urls = []

    def get(self, url):
        self.urls.append(url)

    def quit(self):
        pass


driver = Driver()
service = LiverpoolService(AppConfig(Path("."), Path("."), "Default"))
service._init_driver = lambda: driver
service._check_and_handle_login = lambda _driver: None


def capture(_driver, order):
    order.shipments = [ShipmentInfo(carrier="UPS", tracking_number="1ZTEST")]
    return 1


service._capture_shipments_from_shipping_tab = capture
days = {
    "2026-09-13": DayBatch("2026-09-13", [Order("123", "https://example.com/123", "2026-09-13", "", "")]),
    "2026-09-12": DayBatch("2026-09-12", [Order("999", "https://example.com/999", "2026-09-12", "", "")]),
}
result = service.sync_shipments(days, ["2026-09-13"])
assert result == {"orders": 1, "orders_with_shipments": 1, "shipments": 1, "errors": 0}
assert driver.urls == ["https://example.com/123"]
assert days["2026-09-13"].orders[0].shipments[0].tracking_number == "1ZTEST"
print("shipment sync: ok")
