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
        # Auto-guardar tras escaneo
        try:
            self.service.save_orders_to_json(self.days, "orders_auto_save.json")
        except Exception as e:
            self._log_proxy(f"[WARN] Auto-guardado falló: {e}")

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

    def scan_old_orders_5_days_ago(self):
        """
        Calcula el rango de 'hace 5 días' hasta 'ayer' (inclusive) y escanea.
        Ej: Si hoy es 4, busca del 30 (hace 5 días) al 3 (ayer).
        """
        from datetime import datetime, timedelta
        
        today = datetime.now()
        start_date = today - timedelta(days=5)
        end_date = today - timedelta(days=1) # Hasta ayer
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Escaneo de rango
        self.days = self.service.scan_orders_in_range(start_str, end_str)
        return f"{start_str} al {end_str}"

    def process_old_orders_execution(self, selected_dates: List[str]):
        """
        Ejecuta el proceso (screenshots + guías) para las fechas seleccionadas
        (se asume que son de la sección de antiguos).
        """
        self.service.process_old_orders_execution(self.days, selected_dates)

    def save_orders_json(self, filepath: str):
        self.service.save_orders_to_json(self.days, filepath)

    def load_orders_json(self, filepath: str):
        self.days = self.service.load_orders_from_json(filepath)

    def reprocess_orders_json(self, selected_dates: List[str]):
        self.service.reprocess_orders_execution(self.days, selected_dates)