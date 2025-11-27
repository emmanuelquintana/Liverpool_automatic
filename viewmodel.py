# viewmodel.py
from typing import Dict, List, Callable, Optional

from models import AppConfig, DayBatch
from services import LiverpoolService


class LiverpoolViewModel:
    """
    ViewModel:
    - Mantiene el estado (days)
    - Expone métodos simples al View
    - Orquesta el service
    """
    def __init__(self, config: AppConfig):
        self.config = config
        self.days: Dict[str, DayBatch] = {}
        self._log_callback: Optional[Callable[[str], None]] = None
        self.service = LiverpoolService(config, log_callback=self._log_proxy)

    def _log_proxy(self, msg: str):
        if self._log_callback:
            self._log_callback(msg)

    def set_log_callback(self, cb: Callable[[str], None]):
        self._log_callback = cb

    def scan_orders(self):
        self.days = self.service.scan_orders()

    def get_dates_summary(self):
        return sorted(
            [(d, len(batch.orders)) for d, batch in self.days.items()],
            key=lambda x: x[0],
        )

    def process_details_dry_run(self, selected_dates: List[str]):
        self.service.process_details_dry_run(self.days, selected_dates)

    def accept_and_download_labels(self, selected_dates: List[str]):
        if not self.days:
            raise RuntimeError("Primero ejecuta el escaneo de órdenes (Fase 1).")
        self.service.accept_and_download_labels(self.days, selected_dates)

    def merge_labels(self, selected_dates):
        """
        Fase 3 (botón 4): unir guías de las fechas seleccionadas.
        """
        self.service.merge_labels_for_dates(self.days, selected_dates)