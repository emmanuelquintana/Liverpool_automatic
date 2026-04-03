# viewmodel.py
import threading
from pathlib import Path
from typing import Dict, List, Callable, Optional

from models import AppConfig, DayBatch
from services import LiverpoolService

# Rutas absolutas junto al script
AUTO_SAVE_PATH = str(Path(__file__).resolve().parent / "orders_auto_save.json")
_AUTO_SAVE_BACKUP = str(Path(__file__).resolve().parent / "orders_auto_save.bak.json")


class LiverpoolViewModel:
    def __init__(self, config: AppConfig):
        self.config = config
        self.days: Dict[str, DayBatch] = {}
        self._log_callback: Optional[Callable[[str], None]] = None
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._cancel_event = threading.Event()

        self.service = LiverpoolService(
            config,
            log_callback=self._log_proxy,
            progress_callback=self._progress_proxy,
            cancel_event=self._cancel_event,
        )

    def _log_proxy(self, msg: str):
        if self._log_callback:
            self._log_callback(msg)

    def _progress_proxy(self, current: int, total: int, label: str = ""):
        if self._progress_callback:
            self._progress_callback(current, total, label)

    def set_log_callback(self, cb: Callable[[str], None]):
        self._log_callback = cb

    def set_progress_callback(self, cb: Callable[[int, int, str], None]):
        self._progress_callback = cb

    def request_cancel(self):
        self._cancel_event.set()

    def _reset_cancel(self):
        self._cancel_event.clear()

    def get_batch_stats(self, selected_dates: List[str]) -> dict:
        stats = {"ok": 0, "error": 0, "skipped": 0, "total": 0}
        for date in selected_dates:
            batch = self.days.get(date)
            if not batch:
                continue
            for order in batch.orders:
                stats["total"] += 1
                if order.status == "ok":
                    stats["ok"] += 1
                elif "error" in order.status:
                    stats["error"] += 1
                elif order.status == "skipped":
                    stats["skipped"] += 1
        return stats

    def _record_history(self, event_type: str, dates: List[str], stats: dict = None):
        try:
            from history import record
            record(event_type, dates, stats or {})
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────

    def scan_orders(self):
        self._reset_cancel()
        self.days = self.service.scan_orders()
        try:
            import shutil, os
            if os.path.exists(AUTO_SAVE_PATH):
                shutil.copy2(AUTO_SAVE_PATH, _AUTO_SAVE_BACKUP)
            self.service.save_orders_to_json(self.days, AUTO_SAVE_PATH)
        except Exception as e:
            self._log_proxy(f"[WARN] Auto-guardado falló: {e}")
        total = sum(len(b.orders) for b in self.days.values())
        self._record_history("scan", list(self.days.keys()), {"total": total})

    def get_dates_summary(self):
        return sorted(
            [(d, len(batch.orders)) for d, batch in self.days.items()],
            key=lambda x: x[0],
        )

    def process_details_dry_run(self, selected_dates: List[str]):
        self._reset_cancel()
        self.service.process_details_dry_run(self.days, selected_dates)
        stats = self.get_batch_stats(selected_dates)
        self._record_history("process_dry_run", selected_dates, stats)

    def accept_and_download_labels(self, selected_dates: List[str]):
        if not self.days:
            raise RuntimeError("Primero ejecuta el escaneo de órdenes (Fase 1).")
        self._reset_cancel()
        self.service.accept_and_download_labels(self.days, selected_dates)
        stats = self.get_batch_stats(selected_dates)
        self._record_history("accept_download", selected_dates, stats)

    def merge_labels(self, selected_dates):
        self.service.merge_labels_for_dates(self.days, selected_dates)
        self._record_history("merge_labels", selected_dates)

    def scan_old_orders_5_days_ago(self):
        from datetime import datetime, timedelta
        self._reset_cancel()
        today = datetime.now()
        start_str = (today - timedelta(days=5)).strftime("%Y-%m-%d")
        end_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        self.days = self.service.scan_orders_in_range(start_str, end_str)
        self._record_history("scan_old", list(self.days.keys()))
        return f"{start_str} al {end_str}"

    def process_old_orders_execution(self, selected_dates: List[str]):
        self._reset_cancel()
        self.service.process_old_orders_execution(self.days, selected_dates)
        stats = self.get_batch_stats(selected_dates)
        self._record_history("process_old", selected_dates, stats)

    def save_orders_json(self, filepath: str):
        self.service.save_orders_to_json(self.days, filepath)

    def load_orders_json(self, filepath: str):
        self.days = self.service.load_orders_from_json(filepath)

    def reprocess_orders_json(self, selected_dates: List[str]):
        self._reset_cancel()
        self.service.reprocess_orders_execution(self.days, selected_dates)
        stats = self.get_batch_stats(selected_dates)
        self._record_history("reprocess", selected_dates, stats)